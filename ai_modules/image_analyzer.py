"""
图片特征提取和分析模块
使用多模态大模型分析旧物的主要结构和特征
"""

import base64
import io
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
from loguru import logger

from app.shared.models import ImageAnalysisResponse, MaterialType
from app.config import settings


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
            logger.info(f"AI分析结果: {ai_analysis}")
            result = ImageAnalysisResponse(
                main_objects=ai_analysis.get('objects', []),
                materials=ai_analysis.get('materials', []),
                colors=ai_analysis.get('colors', []),  # 从AI分析中获取颜色
                condition=ai_analysis.get('condition', '未知'),
                dimensions=ai_analysis.get('dimensions', basic_info['dimensions']),  # 优先使用AI分析的尺寸
                features=ai_analysis.get('features', []),
                confidence=ai_analysis.get('confidence', 0.8),
                appearance=ai_analysis.get('appearance'),
                structure=ai_analysis.get('structure'),
                status=ai_analysis.get('status')
            )
            
            logger.info(f"图片分析完成，识别到 {len(result.main_objects)} 个主要物体")
            logger.info(f"主要物体: {result.main_objects}")
            logger.info(f"材料类型: {result.materials}")
            logger.info(f"物品状态: {result.condition}")
            logger.info(f"分析置信度: {result.confidence}")
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
        
        return {
            'dimensions': dimensions,
            'colors': []  # 颜色信息由AI分析提供
        }
    
    
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
        return """请仔细分析这张图像中显示的旧物品，专注于识别和提取**单个主要旧物**的客观特征信息。

**重要提示**：
- 如果图像中有多个物品，请选择**最主要、最突出的旧物**进行分析
- 忽略背景物品、装饰品、小物件等次要元素
- 专注于一个可以独立进行改造的主要物品

请按照以下结构输出分析结果：

**1. 物品类型识别**
- 物品的具体类型（如椅子、桌子、柜子、架子等）
- 物品的原始用途和功能
- 物品的基本尺寸特征（大、中、小等）

**2. 材质详细分析**
- 主要材质类型（木头、金属、塑料、布料、玻璃等）
- 材质的具体特征（如木材种类、金属类型、表面处理等）
- 材质的磨损程度和保存状态
- 材质的颜色和纹理特征

**3. 结构特征描述**
- 物品的整体结构（框架、支撑、连接方式等）
- 关键结构部件（如抽屉、门板、支架、把手、装饰元素等）
- 结构完整性和稳定性评估
- 可拆卸或可调整的部件

**4. 外观特征**
- 物品的整体形状和轮廓
- 装饰元素和设计细节
- 表面处理方式（油漆、清漆、未处理等）
- 颜色搭配和视觉特征

**5. 物品状态评估**
- 整体保存状态（良好/一般/较差）
- 主要磨损部位和程度
- 需要修复或处理的问题
- 物品的清洁程度

请确保分析客观、准确，专注于描述**单个主要旧物**的现有特征，不要涉及改造建议。

请以JSON格式返回结果，包含以下字段：
- objects: 主要物体列表（只包含一个主要物品）
- materials: 材料类型列表
- condition: 物品状态描述
- features: 关键特征列表
- confidence: 分析置信度(0-1)
- dimensions: 尺寸信息
- appearance: 外观特征描述
- structure: 结构特征描述
- status: 状态评估"""
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """解析AI响应"""
        try:
            import json
            import re
            
            # 尝试提取JSON代码块
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                data = json.loads(json_str)
                return self._convert_ai_data(data)
            
            # 尝试直接解析JSON
            if response.strip().startswith('{'):
                data = json.loads(response)
                return self._convert_ai_data(data)
            else:
                # 如果不是JSON格式，尝试提取信息
                return self._extract_info_from_text(response)
        except Exception as e:
            logger.warning(f"AI响应解析失败: {str(e)}")
            return self._get_default_analysis()
    
    def _convert_ai_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """转换AI返回的数据格式"""
        try:
            # 提取主要物体
            objects = []
            if 'objects' in data and isinstance(data['objects'], list):
                for obj in data['objects']:
                    if isinstance(obj, dict) and 'type' in obj:
                        objects.append(obj['type'])
                    elif isinstance(obj, str):
                        objects.append(obj)
            
            # 提取材料
            materials = []
            if 'materials' in data and isinstance(data['materials'], list):
                for material in data['materials']:
                    if isinstance(material, dict) and 'type' in material:
                        material_type = self._map_material_type(material['type'])
                        if material_type:
                            materials.append(material_type)
                    elif isinstance(material, str):
                        material_type = self._map_material_type(material)
                        if material_type:
                            materials.append(material_type)
            
            # 提取颜色信息
            colors = []
            if 'colors' in data and isinstance(data['colors'], list):
                for color in data['colors']:
                    if isinstance(color, str):
                        colors.append(color)
                    elif isinstance(color, dict) and 'name' in color:
                        colors.append(color['name'])
            elif 'appearance' in data:
                # 从外观特征中提取颜色
                if isinstance(data['appearance'], dict):
                    color_info = data['appearance'].get('color', '')
                    if color_info and isinstance(color_info, str):
                        colors.append(color_info)
                elif isinstance(data['appearance'], str):
                    # 如果appearance是字符串，尝试从中提取颜色信息
                    import re
                    # 查找颜色相关的描述
                    color_patterns = [
                        r'颜色[：:]\s*([^，,;。]+)',
                        r'色调[：:]\s*([^，,;。]+)',
                        r'主色调[：:]\s*([^，,;。]+)',
                        r'color_scheme[：:]\s*([^，,;。]+)',
                        r'([^，,;。]*色[^，,;。]*)',
                    ]
                    for pattern in color_patterns:
                        matches = re.findall(pattern, data['appearance'])
                        for match in matches:
                            if match and len(match.strip()) > 0 and '色' in match:
                                colors.append(match.strip())
                                break
                        if colors:  # 如果找到颜色就停止
                            break
            
            # 提取特征
            features = []
            if 'features' in data and isinstance(data['features'], list):
                for feature in data['features']:
                    if isinstance(feature, dict):
                        # 如果是字典，提取name和description
                        name = feature.get('name', '')
                        desc = feature.get('description', '')
                        if name and desc:
                            features.append(f"{name}: {desc}")
                        elif name:
                            features.append(name)
                        elif desc:
                            features.append(desc)
                    elif isinstance(feature, str):
                        features.append(feature)
            
            # 提取状态信息
            condition = "未知"
            if 'condition' in data:
                if isinstance(data['condition'], dict):
                    condition = data['condition'].get('overall', '未知')
                else:
                    condition = str(data['condition'])
            elif 'status' in data:
                # 如果没有condition字段，尝试从status字段提取
                if isinstance(data['status'], dict):
                    condition = data['status'].get('general_condition', data['status'].get('overall_condition', '未知'))
                elif isinstance(data['status'], str):
                    # 从字符串中提取状态信息
                    import re
                    status_match = re.search(r'general_condition[：:]\s*([^;]+)', data['status'])
                    if status_match:
                        condition = status_match.group(1).strip()
                    else:
                        # 如果没有找到，尝试提取第一个描述
                        parts = data['status'].split(';')
                        if parts:
                            condition = parts[0].strip()
            
            # 提取外观特征
            appearance = None
            if 'appearance' in data:
                if isinstance(data['appearance'], dict):
                    appearance_parts = []
                    for key, value in data['appearance'].items():
                        if isinstance(value, str):
                            appearance_parts.append(f"{key}: {value}")
                    appearance = "; ".join(appearance_parts)
                elif isinstance(data['appearance'], str):
                    appearance = data['appearance']
            
            # 提取结构特征
            structure = None
            if 'structure' in data:
                if isinstance(data['structure'], dict):
                    structure_parts = []
                    for key, value in data['structure'].items():
                        if isinstance(value, str):
                            structure_parts.append(f"{key}: {value}")
                        elif isinstance(value, list):
                            # 处理列表中的字典或字符串
                            list_items = []
                            for item in value:
                                if isinstance(item, dict):
                                    # 如果是字典，提取关键信息
                                    if 'component' in item and 'connection' in item:
                                        list_items.append(f"{item['component']}: {item['connection']}")
                                    else:
                                        list_items.append(str(item))
                                else:
                                    list_items.append(str(item))
                            structure_parts.append(f"{key}: {', '.join(list_items)}")
                    structure = "; ".join(structure_parts)
                elif isinstance(data['structure'], str):
                    structure = data['structure']
            
            # 提取状态评估
            status = None
            if 'status' in data:
                if isinstance(data['status'], dict):
                    status_parts = []
                    for key, value in data['status'].items():
                        if isinstance(value, str):
                            status_parts.append(f"{key}: {value}")
                        elif isinstance(value, list):
                            # 处理列表中的字典或字符串
                            list_items = []
                            for item in value:
                                if isinstance(item, dict):
                                    # 如果是字典，提取关键信息
                                    if 'location' in item and 'description' in item:
                                        list_items.append(f"{item['location']}: {item['description']}")
                                    else:
                                        list_items.append(str(item))
                                else:
                                    list_items.append(str(item))
                            status_parts.append(f"{key}: {', '.join(list_items)}")
                    status = "; ".join(status_parts)
                elif isinstance(data['status'], str):
                    status = data['status']
            
            # 提取尺寸信息
            dimensions = None
            if 'dimensions' in data and isinstance(data['dimensions'], dict):
                dimensions = {}
                for key, value in data['dimensions'].items():
                    if isinstance(value, (int, float)):
                        dimensions[key] = float(value)
                    elif isinstance(value, str):
                        # 尝试提取数字，处理"约80-90厘米"这样的格式
                        import re
                        numbers = re.findall(r'\d+\.?\d*', value)
                        if numbers:
                            dimensions[key] = float(numbers[0])
                        else:
                            dimensions[key] = 0.0
            
            # 处理置信度，确保是float类型
            confidence = data.get('confidence', 0.8)
            if isinstance(confidence, str):
                try:
                    confidence = float(confidence)
                except ValueError:
                    confidence = 0.8
            elif not isinstance(confidence, (int, float)):
                confidence = 0.8
            
            return {
                'objects': objects,
                'materials': materials,
                'colors': colors,
                'condition': condition,
                'features': features,
                'confidence': float(confidence),
                'appearance': appearance,
                'structure': structure,
                'status': status,
                'dimensions': dimensions
            }
            
        except Exception as e:
            logger.warning(f"AI数据转换失败: {str(e)}")
            logger.warning(f"原始数据: {data}")
            logger.warning(f"数据类型: {type(data)}")
            return self._get_default_analysis()
    
    def _map_material_type(self, material: str) -> str:
        """将中文材料类型映射为英文枚举值"""
        material_mapping = {
            '木材': 'wood',
            '木头': 'wood',
            '木质': 'wood',
            '金属': 'metal',
            '铁': 'metal',
            '钢': 'metal',
            '布料': 'fabric',
            '织物': 'fabric',
            '玻璃': 'glass',
            '陶瓷': 'ceramic',
            '塑料': 'plastic',
            '皮革': 'leather',
            '纸张': 'paper',
            '纸': 'paper',
            '清漆': 'wood',  # 清漆通常用于木材表面
            '油漆': 'wood',  # 油漆通常用于木材表面
            'wood': 'wood',
            'metal': 'metal',
            'fabric': 'fabric',
            'glass': 'glass',
            'ceramic': 'ceramic',
            'plastic': 'plastic',
            'leather': 'leather',
            'paper': 'paper'
        }
        
        # 尝试直接匹配
        if material.lower() in material_mapping:
            return material_mapping[material.lower()]
        
        # 尝试部分匹配
        for key, value in material_mapping.items():
            if key in material or material in key:
                return value
        
        # 默认返回 wood（木材）
        return 'wood'
    
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
            'confidence': 0.6,
            'appearance': '外观特征需要进一步分析',
            'structure': '结构特征需要进一步分析',
            'status': '状态评估需要进一步分析'
        }
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """获取默认分析结果"""
        return {
            'objects': ['未知物体'],
            'materials': [],
            'condition': '状态未知',
            'features': [],
            'confidence': 0.3,
            'appearance': '外观特征未知',
            'structure': '结构特征未知',
            'status': '状态评估未知'
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
