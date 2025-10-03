"""
多模态大模型API调用模块
支持OpenAI、Anthropic、Replicate等多种多模态大模型
"""

import base64
import json
import asyncio
import re
from typing import Dict, Any, Optional, List
import aiohttp
from loguru import logger

from app.config import settings
from .renovation_inspiration import RenovationInspiration


class MultimodalAPI:
    """多模态大模型API客户端"""
    
    def __init__(self):
        self.tongyi_client = None
        self.inspiration_engine = RenovationInspiration()
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
        target_materials: List[str] = None,
        web_search_func = None
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
            # 1. 获取网页搜索灵感（如果提供了搜索函数）
            inspiration_data = None
            if web_search_func:
                try:
                    main_objects = image_analysis.get('main_objects', ['furniture'])
                    item_type = main_objects[0] if main_objects else 'furniture'
                    materials = [str(m).replace('MaterialType.', '') for m in image_analysis.get('materials', [])]
                    
                    print(f"\n🔍 开始为 {item_type} 搜索改造灵感...")
                    print(f"📋 用户需求: {user_requirements}")
                    print(f"🏗️ 材料类型: {', '.join(materials) if materials else '未知'}")
                    
                    inspiration_data = await self.inspiration_engine.get_renovation_inspiration(
                        item_type=item_type,
                        materials=materials,
                        user_requirements=user_requirements,
                        web_search_func=web_search_func
                    )
                    
                    if inspiration_data and inspiration_data.get('ideas'):
                        logger.info(f"✅ 网页搜索灵感获取成功，找到 {len(inspiration_data['ideas'])} 个现实案例")
                        print(f"📊 找到的现实案例:")
                        for i, idea in enumerate(inspiration_data['ideas'][:3], 1):
                            print(f"  {i}. {idea.get('title', '未知标题')}")
                            print(f"     描述: {idea.get('description', '无描述')[:100]}...")
                    else:
                        logger.warning("⚠️ 搜索结果为空，将使用严格约束模式")
                        inspiration_data = {'ideas': [], 'constraints': ['strict_reality_mode']}
                except Exception as e:
                    logger.warning(f"⚠️ 网页搜索灵感获取失败，使用严格约束模式: {e}")
                    inspiration_data = {'ideas': [], 'constraints': ['strict_reality_mode']}
            else:
                print("\n⚠️ 未提供网页搜索功能，使用严格约束模式")
                inspiration_data = {'ideas': [], 'constraints': ['strict_reality_mode']}
            
            # 2. 构建改造计划提示词（包含搜索到的灵感）
            prompt = self._build_redesign_prompt(
                image_analysis, user_requirements, target_style, target_materials, inspiration_data
            )
            
            # 调试：打印搜索结果是否被正确集成
            if inspiration_data and inspiration_data.get('ideas'):
                print(f"\n🔍 搜索结果已集成到提示词中:")
                print(f"   📊 找到 {len(inspiration_data['ideas'])} 个现实案例")
                for i, idea in enumerate(inspiration_data['ideas'][:2], 1):
                    if isinstance(idea, dict):
                        print(f"   {i}. {idea.get('title', '未知')}: {idea.get('description', '无描述')[:50]}...")
                    else:
                        print(f"   {i}. {idea[:50]}...")
                print(f"   ✅ 搜索结果将强制约束AI生成现实方案")
            else:
                print(f"\n⚠️ 搜索结果为空，将使用严格约束模式")
            
            # 打印提示词内容，用于调试
            logger.info("🔍 发送给AI的提示词:")
            logger.info(f"提示词长度: {len(prompt)} 字符")
            logger.info(f"前1000字符: {prompt[:1000]}")
            logger.info(f"后1000字符: {prompt[-1000:]}")
            
            # 3. 调用通义千问生成文本
            if self.tongyi_client:
                response = await self._generate_text_with_tongyi(prompt)
                
                # 打印AI响应内容，用于调试
                logger.info("🔍 AI响应内容:")
                logger.info(f"响应长度: {len(response)} 字符")
                logger.info("完整响应内容:")
                logger.info(response)
            else:
                raise Exception("通义千问客户端未初始化")
            
            # 解析响应
            return await self._parse_redesign_response(response)
            
        except Exception as e:
            logger.error(f"改造计划生成失败: {str(e)}")
            raise Exception(f"改造计划生成失败: {str(e)}")
    
    def _build_redesign_prompt(
        self,
        image_analysis: Dict[str, Any],
        user_requirements: str,
        target_style: str,
        target_materials: List[str] = None,
        inspiration_data: Dict[str, Any] = None
    ) -> str:
        """构建改造计划提示词 - 简化版"""
        
        materials_text = ", ".join(target_materials) if target_materials else "保持原有材料"
        
        # 构建搜索结果约束部分
        search_constraints = self._build_search_constraints(inspiration_data)
        
        return f"""你是一个专业的旧物改造设计师。请基于以下信息生成改造计划：

【物品信息】
- 主要物体: {', '.join(image_analysis.get('objects', []))}
- 材料类型: {', '.join(image_analysis.get('materials', []))}
- 物品状态: {image_analysis.get('condition', '未知')}
- 关键特征: {', '.join(image_analysis.get('features', []))}

【用户需求】
{user_requirements if user_requirements else "无特定要求，请根据物品特征自主设计改造方案"}

【改造目标】
- 重点改造结构和功能，保持原有材料和颜色
- 材料风格: {materials_text}

{search_constraints}

【核心要求】
1. 必须生成6-8个具体步骤，每个步骤都要有明确目的
2. 每个步骤包含：标题、描述、材料、工具、时间、难度、安全注意事项
3. 步骤之间要有逻辑顺序，体现渐进式改造过程
4. 使用常见工具和材料，成本控制在合理范围内
5. 改造后的物品必须有实际使用价值

请生成JSON格式的改造计划，包含：
1. 改造概述和设计理念
2. 详细步骤列表（标题、描述、材料、工具、时间、难度、安全注意事项）
3. 每个步骤的图像生成提示词
4. 总成本估算
5. 可持续性评分(1-10)
6. 改造小贴士

【关键约束】
- 步骤数量：必须6-8个步骤，这是硬性要求
- 每个步骤都要有具体的改造内容，不能是空步骤
- 步骤之间要有逻辑顺序，体现渐进式改造过程"""
    
    def _build_search_constraints(self, inspiration_data: Dict[str, Any]) -> str:
        """构建搜索约束 - 基于搜索结果指导AI生成"""
        if not inspiration_data or not inspiration_data.get('ideas'):
            return "【搜索指导】\n- 基于物品特征自主设计改造方案，确保实用可行"
        
        sections = []
        sections.append("【搜索指导 - 参考真实案例】")
        
        # 提取具体的改造目标
        targets = []
        for idea in inspiration_data.get('ideas', []):
            if isinstance(idea, dict) and idea.get('target'):
                target = idea.get('target')
                if target and target != '通用改造':
                    targets.append(target)
        
        if targets:
            sections.append(f"【推荐改造目标】")
            sections.append(f"- 建议将物品改造成：{', '.join(targets[:3])}")
            sections.append(f"- 优先考虑以上改造目标")
        
        # 提取具体的技术方法
        if inspiration_data.get('techniques'):
            sections.append(f"\n【参考技术方法】")
            for tech in inspiration_data['techniques'][:3]:
                sections.append(f"- {tech}")
            sections.append(f"- 可以参考以上技术方法")
        
        # 提取具体的材料要求
        if inspiration_data.get('materials_suggestions'):
            sections.append(f"\n【参考材料清单】")
            for material in inspiration_data['materials_suggestions'][:3]:
                sections.append(f"- {material}")
            sections.append(f"- 可以参考以上材料选择")
        
        # 指导性约束
        sections.append(f"\n【设计指导】")
        sections.append(f"- 优先参考搜索结果中的改造方案")
        sections.append(f"- 使用搜索结果中提到的工具和材料")
        sections.append(f"- 确保改造方案现实可行")
        sections.append(f"- 如果搜索结果不足，可以基于物品特征自主设计")
        
        return '\n'.join(sections)
    
    def _format_inspiration_section(self, inspiration_data: Dict[str, Any]) -> str:
        """格式化灵感数据为提示词部分 - 已废弃，使用_build_search_constraints替代"""
        return ""
    
    async def _parse_redesign_response(self, response: str) -> Dict[str, Any]:
        """解析改造计划响应"""
        try:
            # 处理AI返回的markdown格式JSON
            if '```json' in response:
                # 提取```json和```之间的内容
                start = response.find('```json') + 7
                end = response.find('```', start)
                if end > start:
                    json_content = response[start:end].strip()
                    logger.info(f"🔍 提取的JSON内容: {json_content[:200]}...")
                    parsed_data = json.loads(json_content)
                    
                    # 修复字段名映射问题
                    if '详细步骤列表' in parsed_data:
                        steps_data = parsed_data.pop('详细步骤列表')
                        # 修复步骤内部的字段名映射
                        for idx, step in enumerate(steps_data):
                            # 添加step_number字段
                            step['step_number'] = idx + 1
                            if '标题' in step:
                                step['title'] = step.pop('标题')
                            if '描述' in step:
                                step['description'] = step.pop('描述')
                            if '材料' in step:
                                materials_str = step.pop('材料')
                                # 将字符串转换为列表
                                if isinstance(materials_str, str):
                                    # 处理多种分隔符：、，, ;
                                    materials_list = re.split(r'[、，,;]', materials_str)
                                    step['materials_needed'] = await self._optimize_materials_list([m.strip() for m in materials_list if m.strip()])
                                else:
                                    step['materials_needed'] = await self._optimize_materials_list(materials_str)
                            if '工具' in step:
                                tools_str = step.pop('工具')
                                # 将字符串转换为列表
                                if isinstance(tools_str, str):
                                    # 处理多种分隔符：、，, ;
                                    tools_list = re.split(r'[、，,;]', tools_str)
                                    step['tools_needed'] = await self._optimize_tools_list([t.strip() for t in tools_list if t.strip()])
                                else:
                                    step['tools_needed'] = await self._optimize_tools_list(tools_str)
                            if '时间' in step:
                                step['estimated_time'] = step.pop('时间')
                            if '难度' in step:
                                step['difficulty'] = step.pop('难度')
                            if '安全注意事项' in step:
                                step['safety_notes'] = step.pop('安全注意事项')
                        parsed_data['steps'] = steps_data
                        logger.info(f"✅ 已修复字段名映射: 详细步骤列表 -> steps，并修复了步骤内部字段")
                    
                    return parsed_data
            
            # 尝试直接解析JSON
            if response.strip().startswith('{'):
                parsed_data = json.loads(response)
                # 确保步骤有step_number字段
                if 'steps' in parsed_data:
                    for idx, step in enumerate(parsed_data['steps']):
                        if 'step_number' not in step:
                            step['step_number'] = idx + 1
                return parsed_data
            else:
                # 如果不是JSON，尝试提取信息
                return self._extract_plan_from_text(response)
        except Exception as e:
            logger.error(f"改造计划解析失败: {str(e)}")
            raise Exception(f"无法生成有效的改造计划: {str(e)}")
    
    def _extract_plan_from_text(self, text: str) -> Dict[str, Any]:
        """从文本中提取改造计划"""
        # 先打印AI返回的内容，看看实际生成了什么
        logger.info("🔍 AI返回的原始内容:")
        logger.info(f"内容长度: {len(text)} 字符")
        logger.info(f"前500字符: {text[:500]}")
        logger.info(f"后500字符: {text[-500:]}")
        
        # 当AI返回非JSON格式时，直接报错，不使用通用计划
        logger.error("AI返回非JSON格式，无法生成针对性改造计划")
        raise Exception("AI无法生成有效的改造计划，请检查输入参数或重试")
    
    
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

            要求：
            - 提示词应该详细具体，便于AI图像生成模型理解
            - 不要包含任何文字、标签、水印或文本元素
            - 纯图像内容，无文字覆盖
            - 确保生成的图像是干净的，没有任何文字
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
    
    async def generate_comprehensive_plan(
        self,
        image_analysis: Dict[str, Any],
        user_requirements: str,
        target_style: str,
        inspiration_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成完备的改造方案 - 专门用于生成详细计划"""
        logger.info("🔧 开始生成完备改造方案...")
        
        try:
            # 构建增强的提示词
            comprehensive_prompt = self._build_comprehensive_prompt(
                image_analysis=image_analysis,
                user_requirements=user_requirements,
                target_style=target_style,
                inspiration_data=inspiration_data
            )
            
            logger.info(f"📝 完备方案提示词长度: {len(comprehensive_prompt)} 字符")
            
            # 调用AI生成完备方案
            response = await self._generate_text_with_tongyi(comprehensive_prompt)
            
            # 解析响应
            comprehensive_plan = self._parse_comprehensive_response(response)
            
            logger.info(f"✅ 完备方案生成成功，包含 {len(comprehensive_plan.get('steps', []))} 个步骤")
            return comprehensive_plan
            
        except Exception as e:
            logger.error(f"❌ 生成完备方案失败: {e}")
            raise Exception(f"无法生成完备改造方案: {str(e)}")
    
    def _build_comprehensive_prompt(
        self,
        image_analysis: Dict[str, Any],
        user_requirements: str,
        target_style: str,
        inspiration_data: Dict[str, Any]
    ) -> str:
        """构建完备方案的提示词"""
        
        # 格式化材料信息
        materials = image_analysis.get('materials', [])
        materials_text = ', '.join(materials) if materials else '未知材料'
        
        # 格式化灵感数据
        inspiration_section = self._format_inspiration_section(inspiration_data)
        
        return f"""你是一个专业的旧物改造设计师。请基于以下信息生成一个非常详细和完备的改造计划：

        【物品信息】
        - 主要物体: {', '.join(image_analysis.get('objects', []))}
        - 材料类型: {', '.join(image_analysis.get('materials', []))}
        - 物品状态: {image_analysis.get('condition', '未知')}
        - 关键特征: {', '.join(image_analysis.get('features', []))}

        【用户需求】
        {user_requirements if user_requirements else "无特定要求，请根据物品特征和系统设计原则自主设计改造方案"}

        【改造目标】
        - 重点改造结构和功能，保持原有材料和颜色
        - 材料风格: {materials_text}

        {inspiration_section}
        
        【完备方案要求】
        1. 必须生成6-8个详细步骤，每个步骤都要具体可操作
        2. 每个步骤必须包含：标题、详细描述、所需材料、所需工具、预估时间、难度等级、安全注意事项
        3. 步骤之间要有逻辑顺序，体现渐进式改造过程
        4. 必须基于搜索结果中的真实案例进行设计
        5. 禁止生成任何不现实的改造方案
        6. 所有材料、工具、时间、成本都要基于实际情况
        7. 必须考虑改造后的实际使用价值
        8. 每个步骤都要有明确的目的和预期效果
        
        【严格约束】
        - 禁止建议使用专业工具或设备
        - 禁止生成过于复杂的结构设计
        - 禁止建议使用昂贵或难以获得的材料
        - 禁止生成可能造成安全风险的步骤
        - 必须基于物品的实际情况进行改造
        - 必须确保每个步骤都是普通人可以完成的
        
        【输出格式要求】
        请严格按照以下JSON格式输出，不要包含任何其他文字：
        {{
            "title": "改造方案标题",
            "description": "改造方案描述",
            "steps": [
                {{
                    "title": "步骤标题",
                    "description": "详细步骤描述",
                    "materials_needed": ["材料1", "材料2"],
                    "tools_needed": ["工具1", "工具2"],
                    "estimated_time": "预估时间",
                    "difficulty": "难度等级",
                    "safety_notes": "安全注意事项"
                }}
            ],
            "total_cost": "总成本估算",
            "sustainability_score": 8,
            "tips": ["改造小贴士1", "改造小贴士2"]
        }}
        
        请生成一个完整、详细、可操作的改造方案。"""
    
    def _parse_comprehensive_response(self, response: str) -> Dict[str, Any]:
        """解析完备方案响应"""
        try:
            # 处理AI返回的markdown格式JSON
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                if end > start:
                    json_content = response[start:end].strip()
                    logger.info(f"🔍 提取的JSON内容: {json_content[:200]}...")
                    return json.loads(json_content)
            
            # 尝试直接解析JSON
            if response.strip().startswith('{'):
                return json.loads(response)
            else:
                raise Exception("响应不是有效的JSON格式")
                
        except Exception as e:
            logger.error(f"完备方案解析失败: {str(e)}")
            raise Exception(f"无法解析完备改造方案: {str(e)}")
    
    async def _optimize_materials_list(self, materials: List[str]) -> List[str]:
        """使用AI智能优化材料清单，去重并分类"""
        if not materials:
            return []
        
        # 如果材料数量较少，直接去重返回
        if len(materials) <= 5:
            return list(dict.fromkeys(materials))  # 保持顺序去重
        
        # 使用AI优化材料清单
        try:
            materials_text = "、".join(materials)
            prompt = f"""
请优化以下材料清单，去除重复和冗余项目，保留所有必要的材料：

原始材料清单：{materials_text}

要求：
1. 去除完全重复的项目
2. 合并同义词（如"木板"和"木材"合并为"木材"）
3. 去除过于细分的项目（如"120目砂纸"、"240目砂纸"合并为"砂纸组"）
4. 保留所有必要的材料，不要过度精简
5. 按重要性排序

请直接返回优化后的材料清单，用"、"分隔，不要添加其他说明。
"""
            
            # 使用通义千问优化
            optimized_text = await self._generate_text_with_tongyi(prompt)
            
            # 解析优化结果
            if optimized_text:
                optimized_materials = [m.strip() for m in optimized_text.split('、') if m.strip()]
                if optimized_materials:
                    return optimized_materials
            
        except Exception as e:
            logger.warning(f"AI优化材料清单失败: {e}，使用基础去重")
        
        # 备用方案：基础去重
        return list(dict.fromkeys(materials))
    
    async def _optimize_tools_list(self, tools: List[str]) -> List[str]:
        """使用AI智能优化工具清单，去重并分类"""
        if not tools:
            return []
        
        # 如果工具数量较少，直接去重返回
        if len(tools) <= 5:
            return list(dict.fromkeys(tools))  # 保持顺序去重
        
        # 使用AI优化工具清单
        try:
            tools_text = "、".join(tools)
            prompt = f"""
请优化以下工具清单，去除重复和冗余项目，保留所有必要的工具：

原始工具清单：{tools_text}

要求：
1. 去除完全重复的项目
2. 合并同义词（如"螺丝刀"和"起子"合并为"螺丝刀"）
3. 去除过于细分的项目（如"120目砂纸"、"240目砂纸"合并为"砂纸组"）
4. 保留所有必要的工具，不要过度精简
5. 按重要性排序

请直接返回优化后的工具清单，用"、"分隔，不要添加其他说明。
"""
            
            # 使用通义千问优化
            optimized_text = await self._generate_text_with_tongyi(prompt)
            
            # 解析优化结果
            if optimized_text:
                optimized_tools = [t.strip() for t in optimized_text.split('、') if t.strip()]
                if optimized_tools:
                    return optimized_tools
            
        except Exception as e:
            logger.warning(f"AI优化工具清单失败: {e}，使用基础去重")
        
        # 备用方案：基础去重
        return list(dict.fromkeys(tools))
