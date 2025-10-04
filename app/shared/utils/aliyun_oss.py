"""
阿里云OSS文件上传工具
更稳定的图片存储方案，替代ImgBB
"""
import os
import uuid
import logging
from typing import Optional
from PIL import Image
import io
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

try:
    import oss2
    OSS_AVAILABLE = True
except ImportError:
    OSS_AVAILABLE = False
    logger.warning("阿里云OSS SDK未安装，请运行: pip install oss2")

class AliyunOSSUploader:
    def __init__(self):
        self.access_key_id = os.getenv('ALIYUN_OSS_ACCESS_KEY_ID')
        self.access_key_secret = os.getenv('ALIYUN_OSS_ACCESS_KEY_SECRET')
        self.bucket_name = os.getenv('ALIYUN_OSS_BUCKET_NAME')
        self.endpoint = os.getenv('ALIYUN_OSS_ENDPOINT', 'oss-cn-hangzhou.aliyuncs.com')
        
        self.bucket = None
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        if OSS_AVAILABLE and all([self.access_key_id, self.access_key_secret, self.bucket_name]):
            try:
                auth = oss2.Auth(self.access_key_id, self.access_key_secret)
                self.bucket = oss2.Bucket(auth, self.endpoint, self.bucket_name)
                logger.info("✅ 阿里云OSS初始化成功")
            except Exception as e:
                logger.error(f"❌ 阿里云OSS初始化失败: {e}")
        else:
            logger.warning("⚠️ 阿里云OSS配置不完整，将使用备用方案")

    def _sync_upload_file(self, file_path: str, object_name: str) -> Optional[str]:
        """同步上传文件"""
        try:
            if not self.bucket:
                return None
                
            # 上传文件
            result = self.bucket.put_object_from_file(object_name, file_path)
            
            if result.status == 200:
                # 生成公网访问URL
                url = f"https://{self.bucket_name}.{self.endpoint}/{object_name}"
                logger.info(f"✅ OSS上传成功: {url}")
                return url
            else:
                logger.error(f"❌ OSS上传失败，状态码: {result.status}")
                return None
                
        except Exception as e:
            logger.error(f"❌ OSS上传异常: {e}")
            return None

    def _sync_upload_bytes(self, image_data: bytes, object_name: str) -> Optional[str]:
        """同步上传字节数据"""
        try:
            if not self.bucket:
                return None
                
            # 上传字节数据
            result = self.bucket.put_object(object_name, image_data)
            
            if result.status == 200:
                # 生成公网访问URL
                url = f"https://{self.bucket_name}.{self.endpoint}/{object_name}"
                logger.info(f"✅ OSS字节上传成功: {url}")
                return url
            else:
                logger.error(f"❌ OSS字节上传失败，状态码: {result.status}")
                return None
                
        except Exception as e:
            logger.error(f"❌ OSS字节上传异常: {e}")
            return None

    async def upload_file(self, file_path: str, filename: str = None) -> Optional[str]:
        """异步上传文件"""
        if not self.bucket:
            logger.warning("OSS未配置，跳过上传")
            return None
            
        if not filename:
            filename = f"images/{uuid.uuid4().hex}.jpg"
        else:
            filename = f"images/{filename}"
            
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self._sync_upload_file, 
            file_path, 
            filename
        )

    async def upload_pil_image(self, pil_image: Image.Image, filename: str = "image.jpg") -> Optional[str]:
        """异步上传PIL图像"""
        if not self.bucket:
            logger.warning("OSS未配置，跳过上传")
            return None
            
        try:
            # 转换PIL图像为字节
            img_buffer = io.BytesIO()
            pil_image.save(img_buffer, format='JPEG', quality=95)
            image_data = img_buffer.getvalue()
            
            # 生成唯一文件名
            object_name = f"images/{uuid.uuid4().hex}_{filename}"
            
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor,
                self._sync_upload_bytes,
                image_data,
                object_name
            )
            
        except Exception as e:
            logger.error(f"❌ PIL图像上传失败: {e}")
            return None

    async def upload_bytes(self, image_data: bytes, filename: str = "image.jpg") -> Optional[str]:
        """异步上传字节数据"""
        if not self.bucket:
            logger.warning("OSS未配置，跳过上传")
            return None
            
        object_name = f"images/{uuid.uuid4().hex}_{filename}"
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._sync_upload_bytes,
            image_data,
            object_name
        )

# 全局实例
oss_uploader = AliyunOSSUploader()

# 便捷函数
async def upload_to_oss(file_path: str, filename: str = None) -> Optional[str]:
    """上传文件到阿里云OSS"""
    return await oss_uploader.upload_file(file_path, filename)

async def upload_pil_to_oss(pil_image: Image.Image, filename: str = "image.jpg") -> Optional[str]:
    """上传PIL图像到阿里云OSS"""
    return await oss_uploader.upload_pil_image(pil_image, filename)

async def upload_bytes_to_oss(image_data: bytes, filename: str = "image.jpg") -> Optional[str]:
    """上传字节数据到阿里云OSS"""
    return await oss_uploader.upload_bytes(image_data, filename)
