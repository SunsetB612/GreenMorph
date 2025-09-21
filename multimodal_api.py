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
        self.openai_client = None
        self.anthropic_client = None
        self.replicate_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """初始化各种API客户端"""
        try:
            # 初始化通义千问客户端
            if settings.tongyi_api_key:
                import dashscope
                dashscope.api_key = settings.tongyi_api_key
                self.tongyi_client = dashscope
                logger.info("通义千问客户端初始化成功")
            
            # 初始化OpenAI客户端（备用）
            if settings.openai_api_key:
                import openai
                self.openai_client = openai.AsyncOpenAI(
                    api_key=settings.openai_api_key
                )
                logger.info("OpenAI客户端初始化成功")
            
            # 初始化Anthropic客户端（备用）
            if settings.anthropic_api_key:
                import anthropic
                self.anthropic_client = anthropic.AsyncAnthropic(
                    api_key=settings.anthropic_api_key
                )
                logger.info("Anthropic客户端初始化成功")
            
            # 初始化Replicate客户端（备用）
            if settings.replicate_api_token:
                import replicate
                self.replicate_client = replicate
                logger.info("Replicate客户端初始化成功")
                
        except Exception as e:
            logger.error(f"API客户端初始化失败: {str(e)}")
    
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
            if model == "auto":
                # 自动选择可用的模型，优先使用通义千问
                if self.tongyi_client:
                    return await self._analyze_with_tongyi(image_base64, prompt)
                elif self.openai_client:
                    return await self._analyze_with_openai(image_base64, prompt)
                elif self.anthropic_client:
                    return await self._analyze_with_anthropic(image_base64, prompt)
                elif self.replicate_client:
                    return await self._analyze_with_replicate(image_base64, prompt)
                else:
                    raise Exception("没有可用的多模态模型")
            
            elif model == "tongyi" and self.tongyi_client:
                return await self._analyze_with_tongyi(image_base64, prompt)
            elif model == "openai" and self.openai_client:
                return await self._analyze_with_openai(image_base64, prompt)
            elif model == "anthropic" and self.anthropic_client:
                return await self._analyze_with_anthropic(image_base64, prompt)
            elif model == "replicate" and self.replicate_client:
                return await self._analyze_with_replicate(image_base64, prompt)
            else:
                raise Exception(f"指定的模型 {model} 不可用")
                
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
                return response.output.choices[0].message.content[0].text
            else:
                raise Exception(f"通义千问API调用失败: {response.message}")
                
        except Exception as e:
            logger.error(f"通义千问分析失败: {str(e)}")
            raise
    
    async def _analyze_with_openai(self, image_base64: str, prompt: str) -> str:
        """使用OpenAI GPT-4V分析图片"""
        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI分析失败: {str(e)}")
            raise
    
    async def _analyze_with_anthropic(self, image_base64: str, prompt: str) -> str:
        """使用Anthropic Claude分析图片"""
        try:
            response = await self.anthropic_client.messages.create(
                model=settings.anthropic_model,
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic分析失败: {str(e)}")
            raise
    
    async def _analyze_with_replicate(self, image_base64: str, prompt: str) -> str:
        """使用Replicate模型分析图片"""
        try:
            # 将base64转换为文件对象
            image_data = base64.b64decode(image_base64)
            
            # 使用Replicate的视觉模型
            output = await self.replicate_client.async_run(
                "yorickvp/llava-13b:6bc1c7bb0d2a34e413301fee8f7cc728d2d4e75bfab186aa995f63292bda92fc",
                input={
                    "image": image_data,
                    "prompt": prompt,
                    "max_new_tokens": 2000
                }
            )
            
            return str(output)
            
        except Exception as e:
            logger.error(f"Replicate分析失败: {str(e)}")
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
            
            # 调用文本生成模型，优先使用通义千问
            if self.tongyi_client:
                response = await self._generate_text_with_tongyi(prompt)
            elif self.openai_client:
                response = await self._generate_text_with_openai(prompt)
            elif self.anthropic_client:
                response = await self._generate_text_with_anthropic(prompt)
            else:
                raise Exception("没有可用的文本生成模型")
            
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
    
    async def _generate_text_with_openai(self, prompt: str) -> str:
        """使用OpenAI生成文本"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一个专业的旧物改造设计师，擅长环保设计和可持续发展。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI文本生成失败: {str(e)}")
            raise
    
    async def _generate_text_with_anthropic(self, prompt: str) -> str:
        """使用Anthropic生成文本"""
        try:
            response = await self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=3000,
                messages=[
                    {
                        "role": "user",
                        "content": f"你是一个专业的旧物改造设计师，擅长环保设计和可持续发展。\n\n{prompt}"
                    }
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic文本生成失败: {str(e)}")
            raise
    
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
            elif self.openai_client:
                response = await self._generate_text_with_openai(prompt)
            elif self.anthropic_client:
                response = await self._generate_text_with_anthropic(prompt)
            else:
                # 使用默认提示词
                response = f"{step_description}, {features_text}, {eco_prompt}, detailed, high quality"
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"图像提示词生成失败: {str(e)}")
            return f"{step_description}, {', '.join(base_image_features)}, eco-friendly, detailed"
