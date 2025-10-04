"""
云存储服务模块
支持阿里云OSS和ImgBB等云存储服务
"""

import os
import requests
import tempfile
import io
from typing import Optional
from loguru import logger
from PIL import Image
from app.config import settings

# 导入阿里云OSS支持
try:
    from .aliyun_oss import upload_to_oss, upload_pil_to_oss, upload_bytes_to_oss
    OSS_AVAILABLE = True
    logger.info("✅ 阿里云OSS支持已加载")
except ImportError as e:
    OSS_AVAILABLE = False
    logger.warning(f"⚠️ 阿里云OSS不可用: {e}")

# 云存储优先级：OSS > ImgBB
def should_use_oss() -> bool:
    """动态检查是否应该使用OSS"""
    return OSS_AVAILABLE and bool(os.getenv('ALIYUN_OSS_ACCESS_KEY_ID'))


class CloudStorageService:
    """云存储服务"""
    
    def __init__(self):
        self.imgbb_api_key = settings.imgbb_api_key
        self.enable_cloud_storage = settings.enable_cloud_storage
        
        if not self.imgbb_api_key:
            logger.warning("ImgBB API密钥未配置，云存储功能将被禁用")
            self.enable_cloud_storage = False
    
    async def upload_to_imgbb(self, image_data: bytes, filename: str = None) -> Optional[str]:
        """
        上传图片到ImgBB云存储
        
        Args:
            image_data: 图片二进制数据
            filename: 文件名（可选）
            
        Returns:
            str: 云存储的公开URL，失败返回None
        """
        if not self.enable_cloud_storage or not self.imgbb_api_key:
            logger.warning("云存储功能未启用或API密钥未配置")
            return None
        
        try:
            logger.info(f"开始上传图片到ImgBB: {filename or 'unnamed'}")
            
            # 构建请求
            url = "https://api.imgbb.com/1/upload"
            payload = {
                "key": self.imgbb_api_key,
            }
            files = {
                "image": ("image.jpg", image_data, "image/jpeg"),
            }
            
            # 发送请求
            response = requests.post(url, data=payload, files=files, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    cloud_url = result["data"]["url"]
                    logger.info(f"✅ 图片上传到ImgBB成功: {cloud_url}")
                    return cloud_url
                else:
                    error_msg = result.get('error', {}).get('message', '未知错误')
                    logger.error(f"❌ ImgBB上传失败: {error_msg}")
                    return None
            else:
                logger.error(f"❌ ImgBB HTTP错误: {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("❌ ImgBB上传超时")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ ImgBB网络错误: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ ImgBB上传异常: {str(e)}")
            return None
    
    async def upload_image(self, image_data: bytes, filename: str = None) -> Optional[str]:
        """
        上传图片到云存储（统一接口）
        
        Args:
            image_data: 图片二进制数据
            filename: 文件名（可选）
            
        Returns:
            str: 云存储的公开URL，失败返回None
        """
        if not self.enable_cloud_storage:
            logger.info("云存储功能已禁用，跳过上传")
            return None
        
        # 目前只支持ImgBB，后续可以扩展其他云存储服务
        return await self.upload_to_imgbb(image_data, filename)
    
    def is_cloud_storage_enabled(self) -> bool:
        """检查云存储功能是否启用"""
        return self.enable_cloud_storage and bool(self.imgbb_api_key)
    
    def get_service_info(self) -> dict:
        """获取云存储服务信息"""
        return {
            "enabled": self.is_cloud_storage_enabled(),
            "provider": "ImgBB" if self.imgbb_api_key else "None",
            "api_configured": bool(self.imgbb_api_key)
        }


async def upload_pil_image_to_imgbb(pil_image: Image.Image, filename: str = "image.jpg") -> Optional[str]:
    """
    上传PIL图像到ImgBB
    
    Args:
        pil_image: PIL图像对象
        filename: 文件名
        
    Returns:
        str: ImgBB的公开URL，失败返回None
    """
    try:
        # 将PIL图像转换为bytes
        img_buffer = io.BytesIO()
        # 确保图像是RGB格式
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        pil_image.save(img_buffer, format='JPEG', quality=95)
        img_bytes = img_buffer.getvalue()
        
        # 使用现有的upload_to_imgbb函数
        return await upload_to_imgbb_bytes(img_bytes, filename)
    except Exception as e:
        logger.error(f"PIL图像上传失败: {e}")
        return None


async def upload_to_imgbb_bytes(image_data: bytes, filename: str = "image.jpg") -> Optional[str]:
    """
    上传图片字节数据到ImgBB
    
    Args:
        image_data: 图片二进制数据
        filename: 文件名
        
    Returns:
        str: ImgBB的公开URL，失败返回None
    """
    try:
        import base64
        
        if not settings.imgbb_api_key:
            logger.warning("ImgBB API密钥未配置")
            return None
        
        logger.info(f"开始上传图片到ImgBB: {filename}")
        
        # 将图片数据编码为base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # 准备上传数据
        upload_data = {
            'key': settings.imgbb_api_key,
            'image': image_base64,
            'name': filename
        }
        
        # 发送上传请求
        response = requests.post(
            'https://api.imgbb.com/1/upload',
            data=upload_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                image_url = result['data']['url']
                logger.info(f"✅ 图片上传到ImgBB成功: {image_url}")
                return image_url
            else:
                logger.error(f"ImgBB上传失败: {result}")
                return None
        else:
            logger.error(f"ImgBB API请求失败: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"上传到ImgBB时发生错误: {e}")
        return None


# ============ 智能云存储接口 ============

async def smart_upload_file(file_path: str, filename: str = "image.jpg") -> Optional[str]:
    """智能文件上传：优先OSS，降级ImgBB"""
    if should_use_oss():
        logger.info("🚀 使用阿里云OSS上传文件...")
        try:
            url = await upload_to_oss(file_path, filename)
            if url:
                logger.info(f"✅ OSS上传成功: {url}")
                return url
            else:
                logger.warning("⚠️ OSS上传失败，降级到ImgBB")
        except Exception as e:
            logger.warning(f"⚠️ OSS上传异常，降级到ImgBB: {e}")
    
    # 降级到ImgBB
    logger.info("📸 降级使用ImgBB上传...")
    cloud_service = CloudStorageService()
    
    # 读取文件并上传
    try:
        with open(file_path, 'rb') as f:
            image_data = f.read()
        return await cloud_service.upload_to_imgbb(image_data, filename)
    except Exception as e:
        logger.error(f"❌ 文件读取失败: {e}")
        return None

async def smart_upload_pil_image(pil_image: Image.Image, filename: str = "image.jpg") -> Optional[str]:
    """智能PIL图像上传：优先OSS，降级ImgBB"""
    if should_use_oss():
        logger.info("🚀 使用阿里云OSS上传PIL图像...")
        try:
            url = await upload_pil_to_oss(pil_image, filename)
            if url:
                logger.info(f"✅ OSS PIL上传成功: {url}")
                return url
            else:
                logger.warning("⚠️ OSS PIL上传失败，降级到ImgBB")
        except Exception as e:
            logger.warning(f"⚠️ OSS PIL上传异常，降级到ImgBB: {e}")
    
    # 降级到ImgBB
    logger.info("📸 降级使用ImgBB上传PIL图像...")
    return await upload_pil_image_to_imgbb(pil_image, filename)
