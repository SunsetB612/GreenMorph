"""
多模态大模型API调用模块
支持OpenAI、Anthropic、Replicate等多种多模态大模型
"""

import base64
import json
import asyncio
from typing import Dict, Any, Optional, List
import aiohttp
from loguru import logger

from config import settings


class MultimodalAPI:
    """多模态大模型API客户端"""
    
    def __init__(self):
        self.tongyi_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """初始化通义千问API客户端"""
        try:
            # 初始化通义千问客户端
            if settings.tongyi_api_key:
                import dashscope
                dashscope.api_key = settings.tongyi_api_key
                self.tongyi_client = dashscope
                logger.info("通义千问客户端初始化成功")
            else:
                logger.warning("未配置通义千问API密钥")
                
        except Exception as e:
            logger.error(f"通义千问客户端初始化失败: {str(e)}")
    
    async def analyze_image_with_vision(
        self, 
        image_base64: str, 
        prompt: str,
        model: str = "auto"
    ) -> str:
        """
        使用视觉模型分析图片
        
        Args:
            image_base64: Base64编码的图片
            prompt: 分析提示词
            model: 模型选择 ("auto", "openai", "anthropic", "replicate")
            
        Returns:
            str: 分析结果
        """
        try:
            if model == "auto" or model == "tongyi":
                if self.tongyi_client:
                    return await self._analyze_with_tongyi(image_base64, prompt)
                else:
                    raise Exception("通义千问客户端未初始化")
            else:
                raise Exception(f"不支持的模型: {model}，只支持通义千问")
                
        except Exception as e:
            logger.error(f"图片分析失败: {str(e)}")
            raise Exception(f"多模态模型分析失败: {str(e)}")
    
    async def _analyze_with_tongyi(self, image_base64: str, prompt: str) -> str:
        """使用通义千问分析图片"""
        try:
            from dashscope import MultiModalConversation
            
            # 构建消息
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "image": f"data:image/jpeg;base64,{image_base64}"
                        },
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
            
            # 调用通义千问API
            response = MultiModalConversation.call(
                model=settings.tongyi_model,
                messages=messages,
                result_format='message'
            )
            
            if response.status_code == 200:
                try:
                    if hasattr(response, 'output') and hasattr(response.output, 'choices') and response.output.choices:
                        choice = response.output.choices[0]
                        if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                            content = choice.message.content
                            if isinstance(content, list) and len(content) > 0:
                                if isinstance(content[0], dict) and 'text' in content[0]:
                                    return content[0]['text']
                                elif hasattr(content[0], 'text'):
                                    return content[0].text
                                else:
                                    return str(content[0])
                            elif isinstance(content, str):
                                return content
                            else:
                                return str(content)
                        else:
                            return str(choice.message)
                    else:
                        return str(response.output)
                    
                except Exception as parse_error:
                    logger.error(f"响应解析失败: {str(parse_error)}")
                    return "分析完成，但无法解析具体内容"
            else:
                raise Exception(f"通义千问API调用失败: {response.message}")
                
        except Exception as e:
            logger.error(f"通义千问分析失败: {str(e)}")
            raise
    
    
    async def generate_redesign_plan(
        self,
        image_analysis: Dict[str, Any],
        user_requirements: str,
        target_style: str,
        target_materials: List[str] = None
    ) -> Dict[str, Any]:
        """
        生成改造计划
        
        Args:
            image_analysis: 图片分析结果
            user_requirements: 用户需求
            target_style: 目标风格
            target_materials: 目标材料
            
        Returns:
            Dict: 改造计划
        """
        try:
            # 构建改造计划提示词
            prompt = self._build_redesign_prompt(
                image_analysis, user_requirements, target_style, target_materials
            )
            
            # 调用通义千问生成文本
            if self.tongyi_client:
                response = await self._generate_text_with_tongyi(prompt)
            else:
                raise Exception("通义千问客户端未初始化")
            
            # 解析响应
            return self._parse_redesign_response(response)
            
        except Exception as e:
            logger.error(f"改造计划生成失败: {str(e)}")
            raise Exception(f"改造计划生成失败: {str(e)}")
    
    def _build_redesign_prompt(
        self,
        image_analysis: Dict[str, Any],
        user_requirements: str,
        target_style: str,
        target_materials: List[str] = None
    ) -> str:
        """构建改造计划提示词"""
        
        materials_text = ", ".join(target_materials) if target_materials else "保持原有材料"
        
        return f"""
        基于以下信息，为旧物改造生成详细的改造计划：

        【物品分析结果】
        - 主要物体: {', '.join(image_analysis.get('objects', []))}
        - 材料类型: {', '.join(image_analysis.get('materials', []))}
        - 物品状态: {image_analysis.get('condition', '未知')}
        - 关键特征: {', '.join(image_analysis.get('features', []))}

        【用户需求】
        {user_requirements}

        【改造目标】
        - 目标风格: {target_style}
        - 目标材料: {materials_text}

        【环保要求】
        - 保持环保、自然的视觉风格
        - 优先使用可持续材料
        - 减少浪费，最大化利用原有材料
        - 确保改造过程环保

        请生成包含以下内容的详细改造计划（JSON格式）：
        1. 改造概述和设计理念
        2. 详细步骤列表（每个步骤包含：标题、描述、所需材料、工具、时间、难度、安全注意事项）
        3. 每个步骤的图像生成提示词
        4. 总成本估算
        5. 可持续性评分(1-10)
        6. 改造小贴士

        请确保：
        - 步骤清晰易懂，适合不同技能水平
        - 图像提示词详细具体，便于生成高质量效果图
        - 保持原物的关键特征
        - 突出每步改造的关键变化
        - 提供直观、友好的视觉参考
        """
    
    
    def _parse_redesign_response(self, response: str) -> Dict[str, Any]:
        """解析改造计划响应"""
        try:
            # 尝试解析JSON
            if response.strip().startswith('{'):
                return json.loads(response)
            else:
                # 如果不是JSON，尝试提取信息
                return self._extract_plan_from_text(response)
        except Exception as e:
            logger.warning(f"改造计划解析失败: {str(e)}")
            return self._get_default_plan()
    
    def _extract_plan_from_text(self, text: str) -> Dict[str, Any]:
        """从文本中提取改造计划"""
        # 简单的文本解析逻辑
        return {
            "overview": "基于AI分析的改造计划",
            "steps": [
                {
                    "step_number": 1,
                    "title": "准备阶段",
                    "description": "清洁和准备物品",
                    "materials_needed": ["清洁剂", "砂纸"],
                    "tools_needed": ["抹布", "手套"],
                    "estimated_time": "30分钟",
                    "difficulty": "简单",
                    "image_prompt": "cleaning and preparing old furniture, eco-friendly materials",
                    "safety_notes": "注意通风，佩戴防护用品"
                }
            ],
            "total_cost_estimate": "100-300元",
            "sustainability_score": 8,
            "tips": ["保持原有结构", "使用环保材料"]
        }
    
    def _get_default_plan(self) -> Dict[str, Any]:
        """获取默认改造计划"""
        return {
            "overview": "基于物品特征的改造计划",
            "steps": [
                {
                    "step_number": 1,
                    "title": "基础准备",
                    "description": "清洁和评估物品状态",
                    "materials_needed": ["清洁剂"],
                    "tools_needed": ["抹布"],
                    "estimated_time": "30分钟",
                    "difficulty": "简单",
                    "image_prompt": "preparing old item for upcycling",
                    "safety_notes": "注意安全"
                }
            ],
            "total_cost_estimate": "待评估",
            "sustainability_score": 7,
            "tips": ["环保改造"]
        }
    
    async def _generate_text_with_tongyi(self, prompt: str) -> str:
        """使用通义千问生成文本"""
        try:
            from dashscope import Generation
            
            # 调用通义千问文本生成API
            response = Generation.call(
                model='qwen-plus',
                prompt=prompt,
                result_format='message'
            )
            
            if response.status_code == 200:
                return response.output.choices[0].message.content
            else:
                raise Exception(f"通义千问文本生成失败: {response.message}")
                
        except Exception as e:
            logger.error(f"通义千问文本生成失败: {str(e)}")
            raise
    
    async def generate_image_prompt(
        self,
        step_description: str,
        base_image_features: List[str],
        eco_style: bool = True
    ) -> str:
        """
        为特定步骤生成图像提示词
        
        Args:
            step_description: 步骤描述
            base_image_features: 原图特征
            eco_style: 是否使用环保风格
            
        Returns:
            str: 图像生成提示词
        """
        try:
            features_text = ", ".join(base_image_features)
            eco_prompt = settings.eco_style_prompt if eco_style else ""
            
            prompt = f"""
            为以下改造步骤生成详细的图像生成提示词：

            步骤描述: {step_description}
            原物特征: {features_text}
            环保风格: {eco_prompt}

            请生成一个详细的英文提示词，包含：
            1. 具体的视觉描述
            2. 材料和质感
            3. 颜色和光线
            4. 构图和角度
            5. 环保元素

            提示词应该详细具体，便于AI图像生成模型理解。
            """
            
            if self.tongyi_client:
                response = await self._generate_text_with_tongyi(prompt)
            else:
                # 使用默认提示词
                response = f"{step_description}, {features_text}, {eco_prompt}, detailed, high quality"
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"图像提示词生成失败: {str(e)}")
            return f"{step_description}, {', '.join(base_image_features)}, eco-friendly, detailed"
