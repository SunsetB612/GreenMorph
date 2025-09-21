"""
图片特征提取和分析模块
使用多模态大模型分析旧物的主要结构和特征
"""

import base64
import io
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import cv2
import numpy as np
from loguru import logger

from models import ImageAnalysisResponse, MaterialType
from config import settings


class ImageAnalyzer:
    """图片分析器"""
    
    def __init__(self):
        self.supported_formats = ['JPEG', 'PNG', 'WEBP']
        
    async def analyze_image(self, image_data: bytes) -> ImageAnalysisResponse:
        """
        分析图片，提取旧物的主要结构和特征
        
        Args:
            image_data: 图片二进制数据
            
        Returns:
            ImageAnalysisResponse: 分析结果
        """
        try:
            # 加载和处理图片
            image = self._load_image(image_data)
            
            # 基础图片信息提取
            basic_info = self._extract_basic_info(image)
            
            # 使用多模态大模型进行深度分析
            ai_analysis = await self._ai_analyze_image(image)
            
            # 合并分析结果
            result = ImageAnalysisResponse(
                main_objects=ai_analysis.get('objects', []),
                materials=ai_analysis.get('materials', []),
                colors=basic_info['colors'],
                condition=ai_analysis.get('condition', '未知'),
                dimensions=basic_info['dimensions'],
                features=ai_analysis.get('features', []),
                confidence=ai_analysis.get('confidence', 0.8)
            )
            
            logger.info(f"图片分析完成，识别到 {len(result.main_objects)} 个主要物体")
            return result
            
        except Exception as e:
            logger.error(f"图片分析失败: {str(e)}")
            raise Exception(f"图片分析失败: {str(e)}")
    
    def _load_image(self, image_data: bytes) -> Image.Image:
        """加载图片"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # 转换为RGB格式
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 调整图片大小
            image.thumbnail(settings.max_image_size, Image.Resampling.LANCZOS)
            
            return image
        except Exception as e:
            raise Exception(f"图片加载失败: {str(e)}")
    
    def _extract_basic_info(self, image: Image.Image) -> Dict[str, Any]:
        """提取基础图片信息"""
        # 获取图片尺寸
        width, height = image.size
        dimensions = {
            'width': width,
            'height': height,
            'aspect_ratio': round(width / height, 2)
        }
        
        # 提取主要颜色
        colors = self._extract_dominant_colors(image)
        
        return {
            'dimensions': dimensions,
            'colors': colors
        }
    
    def _extract_dominant_colors(self, image: Image.Image, num_colors: int = 5) -> List[str]:
        """提取主要颜色"""
        try:
            # 将图片转换为numpy数组
            img_array = np.array(image)
            
            # 重塑数组为像素列表
            pixels = img_array.reshape(-1, 3)
            
            # 使用K-means聚类提取主要颜色
            from sklearn.cluster import KMeans
            
            kmeans = KMeans(n_clusters=num_colors, random_state=42, n_init=10)
            kmeans.fit(pixels)
            
            # 获取聚类中心（主要颜色）
            colors = kmeans.cluster_centers_.astype(int)
            
            # 转换为十六进制颜色代码
            color_hex = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in colors]
            
            return color_hex
            
        except Exception as e:
            logger.warning(f"颜色提取失败，使用默认方法: {str(e)}")
            # 备用方法：简单采样
            return self._simple_color_extraction(image, num_colors)
    
    def _simple_color_extraction(self, image: Image.Image, num_colors: int = 5) -> List[str]:
        """简单的颜色提取方法"""
        # 缩小图片以加快处理
        small_image = image.resize((50, 50))
        pixels = list(small_image.getdata())
        
        # 随机采样颜色
        import random
        sample_colors = random.sample(pixels, min(num_colors, len(pixels)))
        
        return [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in sample_colors]
    
    async def _ai_analyze_image(self, image: Image.Image) -> Dict[str, Any]:
        """使用AI模型分析图片"""
        try:
            # 将图片转换为base64
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='JPEG', quality=95)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            # 构建分析提示词
            analysis_prompt = self._build_analysis_prompt()
            
            # 调用多模态大模型API
            from multimodal_api import MultimodalAPI
            api_client = MultimodalAPI()
            
            result = await api_client.analyze_image_with_vision(
                image_base64=img_base64,
                prompt=analysis_prompt
            )
            
            return self._parse_ai_response(result)
            
        except Exception as e:
            logger.error(f"AI图片分析失败: {str(e)}")
            # 返回默认分析结果
            return self._get_default_analysis()
    
    def _build_analysis_prompt(self) -> str:
        """构建图片分析提示词"""
        return """
        请详细分析这张旧物图片，提取以下信息：
        
        1. 主要物体：识别图片中的主要物体和家具类型
        2. 材料类型：分析物体的主要材料（木材、金属、布料、玻璃、陶瓷、塑料、皮革、纸张等）
        3. 物品状态：评估物品的磨损程度和整体状态
        4. 关键特征：识别物体的独特特征、结构特点、装饰元素等
        5. 改造潜力：评估物品的改造潜力和可能性
        
        请以JSON格式返回结果，包含以下字段：
        - objects: 主要物体列表
        - materials: 材料类型列表
        - condition: 物品状态描述
        - features: 关键特征列表
        - confidence: 分析置信度(0-1)
        """
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """解析AI响应"""
        try:
            import json
            # 尝试解析JSON响应
            if response.strip().startswith('{'):
                return json.loads(response)
            else:
                # 如果不是JSON格式，尝试提取信息
                return self._extract_info_from_text(response)
        except Exception as e:
            logger.warning(f"AI响应解析失败: {str(e)}")
            return self._get_default_analysis()
    
    def _extract_info_from_text(self, text: str) -> Dict[str, Any]:
        """从文本中提取信息"""
        # 简单的文本解析逻辑
        objects = []
        materials = []
        features = []
        
        # 材料关键词映射
        material_keywords = {
            'wood': ['木', '木材', '木质', 'wood', 'wooden'],
            'metal': ['金属', '铁', '钢', 'metal', 'steel', 'iron'],
            'fabric': ['布料', '织物', 'fabric', 'cloth', 'textile'],
            'glass': ['玻璃', 'glass'],
            'ceramic': ['陶瓷', '瓷器', 'ceramic', 'porcelain'],
            'plastic': ['塑料', 'plastic'],
            'leather': ['皮革', 'leather'],
            'paper': ['纸张', '纸', 'paper']
        }
        
        text_lower = text.lower()
        
        # 检测材料
        for material, keywords in material_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                materials.append(material)
        
        return {
            'objects': objects,
            'materials': materials,
            'condition': '需要进一步分析',
            'features': features,
            'confidence': 0.6
        }
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """获取默认分析结果"""
        return {
            'objects': ['未知物体'],
            'materials': [],
            'condition': '状态未知',
            'features': [],
            'confidence': 0.3
        }
    
    def validate_image(self, image_data: bytes) -> bool:
        """验证图片格式和大小"""
        try:
            # 检查文件大小
            if len(image_data) > settings.max_file_size:
                return False
            
            # 检查图片格式
            image = Image.open(io.BytesIO(image_data))
            if image.format not in self.supported_formats:
                return False
            
            return True
            
        except Exception:
            return False
