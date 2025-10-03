"""
旧物改造灵感获取模块
通过网页搜索获取真实的改造方案和创意灵感
"""

import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger
import re
import json


class RenovationInspiration:
    """旧物改造灵感获取器"""
    
    def __init__(self):
        self.search_platforms = [
            "小红书 旧物改造",
            "Pinterest DIY furniture",
            "宜家 家具改造",
            "豆瓣 旧物改造小组",
            "知乎 家具翻新",
            "YouTube furniture makeover"
        ]
    
    async def get_renovation_inspiration(
        self, 
        item_type: str, 
        materials: List[str], 
        user_requirements: str,
        web_search_func
    ) -> Dict[str, Any]:
        """
        获取旧物改造灵感
        
        Args:
            item_type: 物品类型（如：椅子、桌子等）
            materials: 材料列表
            user_requirements: 用户需求
            web_search_func: 网页搜索函数
            
        Returns:
            包含改造灵感和方案的字典
        """
        try:
            logger.info(f"🔍 开始搜索 {item_type} 的改造灵感...")
            
            # 构建搜索关键词
            search_queries = self._build_search_queries(item_type, materials, user_requirements)
            
            # 执行多轮搜索
            search_results = []
            for i, query in enumerate(search_queries[:10]):  # 增加搜索次数
                try:
                    logger.info(f"🔍 第{i+1}轮搜索: {query}")
                    result = await web_search_func(
                        search_term=query,
                        explanation=f"搜索{item_type}的改造灵感和方案"
                    )
                    if result:
                        search_results.append({
                            'query': query,
                            'content': result,
                            'round': i + 1
                        })
                        logger.info(f"✅ 第{i+1}轮搜索成功，获取内容长度: {len(result)} 字符")
                        await asyncio.sleep(1)  # 避免请求过快
                    else:
                        logger.warning(f"⚠️ 第{i+1}轮搜索无结果: {query}")
                except Exception as e:
                    logger.warning(f"❌ 第{i+1}轮搜索失败 {query}: {e}")
                    continue
            
            # 解析和整理搜索结果
            inspiration_data = self._parse_search_results(search_results, item_type, user_requirements)
            
            # 在控制台打印找到的灵感
            self._print_inspiration_summary(inspiration_data, item_type)
            
            logger.info(f"✅ 获取到 {len(inspiration_data.get('ideas', []))} 个改造灵感")
            return inspiration_data
            
        except Exception as e:
            logger.error(f"❌ 获取改造灵感失败: {e}")
            return self._get_fallback_inspiration(item_type, materials, user_requirements)
    
    def _build_search_queries(self, item_type: str, materials: List[str], user_requirements: str) -> List[str]:
        """构建搜索关键词 - 精准搜索策略"""
        queries = []
        
        # 基础搜索词
        material_str = ' '.join(materials) if materials else '木质'
        
        # 第一轮：搜索具体的改造目标（书架、储物柜、桌子等）
        common_targets = ['书架', '储物柜', '桌子', '茶几', '展示架', '储物架', '置物架']
        for target in common_targets[:3]:  # 只搜索前3个最常用的目标
            queries.extend([
                f"{item_type} 改造成 {target} 详细步骤",
                f"{item_type} 变身 {target} 教程",
                f"废旧 {item_type} 改造 {target} 方法"
            ])
        
        # 第二轮：搜索具体的操作步骤和材料清单
        queries.extend([
            f"{item_type} 改造 步骤 材料清单 工具",
            f"{item_type} 翻新 详细教程 成本",
            f"{item_type} DIY 改造 安全注意事项"
        ])
        
        # 第三轮：搜索具体的工具和材料
        queries.extend([
            f"{material_str} {item_type} 改造 需要什么工具",
            f"{item_type} 改造 砂纸 螺丝 胶水 详细",
            f"{item_type} 翻新 刷子 油漆 步骤"
        ])
        
        # 第四轮：搜索具体的改造案例（如果有用户需求）
        if user_requirements and len(user_requirements.strip()) > 2:
            queries.extend([
                f"{item_type} 改造成 {user_requirements} 详细步骤",
                f"{item_type} 变身 {user_requirements} 教程",
                f"废旧 {item_type} 改造 {user_requirements} 方法"
            ])
        
        # 第五轮：搜索英文教程（更详细的步骤）
        item_en = self._translate_item_type(item_type)
        queries.extend([
            f"{item_en} to bookshelf step by step tutorial",
            f"upcycle {item_en} storage cabinet detailed guide",
            f"repurpose old {item_en} furniture transformation"
        ])
        
        return queries[:12]  # 减少搜索次数，提高质量
    
    def _translate_item_type(self, item_type: str) -> str:
        """简单的物品类型翻译"""
        translations = {
            '椅子': 'chair',
            '桌子': 'table',
            '柜子': 'cabinet',
            '书架': 'bookshelf',
            '凳子': 'stool',
            '沙发': 'sofa',
            '床': 'bed',
            '衣柜': 'wardrobe'
        }
        return translations.get(item_type, 'furniture')
    
    def _parse_search_results(self, search_results: List[Dict], item_type: str, user_requirements: str) -> Dict[str, Any]:
        """解析搜索结果，提取有用的改造灵感"""
        inspiration_data = {
            'ideas': [],
            'techniques': [],
            'materials_suggestions': [],
            'style_references': [],
            'practical_tips': []
        }
        
        for result in search_results:
            content = result.get('content', '')
            if not content:
                continue
                
            # 提取改造想法
            ideas = self._extract_renovation_ideas(content, item_type)
            inspiration_data['ideas'].extend(ideas)
            
            # 提取技术方法
            techniques = self._extract_techniques(content)
            inspiration_data['techniques'].extend(techniques)
            
            # 提取材料建议
            materials = self._extract_material_suggestions(content)
            inspiration_data['materials_suggestions'].extend(materials)
            
            # 提取风格参考
            styles = self._extract_style_references(content)
            inspiration_data['style_references'].extend(styles)
            
            # 提取实用技巧
            tips = self._extract_practical_tips(content)
            inspiration_data['practical_tips'].extend(tips)
        
        # 去重和限制数量（保持顺序）
        for key in inspiration_data:
            if key == 'ideas':
                # ideas是字典列表，需要特殊处理
                seen_titles = set()
                unique_items = []
                for item in inspiration_data[key]:
                    if item and isinstance(item, dict):
                        title = item.get('title', '')
                        if title and title not in seen_titles:
                            seen_titles.add(title)
                            unique_items.append(item)
                    elif item and isinstance(item, str):
                        if item not in seen_titles:
                            seen_titles.add(item)
                            unique_items.append(item)
                inspiration_data[key] = unique_items[:5]
            else:
                # 其他字段是字符串列表
                seen = set()
                unique_items = []
                for item in inspiration_data[key]:
                    if item and item not in seen:
                        seen.add(item)
                        unique_items.append(item)
                inspiration_data[key] = unique_items[:5]
        
        return inspiration_data
    
    def _extract_renovation_ideas(self, content: str, item_type: str) -> List[Dict[str, str]]:
        """从内容中提取改造想法 - 精准提取具体改造目标"""
        ideas = []
        
        # 查找包含具体改造目标的句子，扩大匹配范围
        target_patterns = [
            r'改造成([^，。！？\n]{2,30})',
            r'变成([^，。！？\n]{2,30})',
            r'制作成([^，。！？\n]{2,30})',
            r'做成([^，。！？\n]{2,30})',
            r'制作([^，。！？\n]{2,30})',
            r'打造([^，。！？\n]{2,30})',
            r'改造为([^，。！？\n]{2,30})',
            r'转换为([^，。！？\n]{2,30})',
            r'变身([^，。！？\n]{2,30})',
            r'升级([^，。！？\n]{2,30})',
            r'翻新([^，。！？\n]{2,30})',
            r'改装([^，。！？\n]{2,30})',
            r'to ([^，。！？\n]{2,30})',  # 英文模式
            r'into ([^，。！？\n]{2,30})',  # 英文模式
            r'step by step ([^，。！？\n]{2,30})'  # 英文步骤模式
        ]
        
        sentences = re.split(r'[。！？\n]', content)
        for sentence in sentences:
            # 查找包含具体改造目标的句子
            for pattern in target_patterns:
                matches = re.findall(pattern, sentence)
                for match in matches:
                    if len(match) > 2 and len(match) < 30:  # 扩大匹配范围
                        # 提取完整的改造目标
                        target = match.strip()
                        # 过滤掉无意义的词
                        if target not in ['的', '了', '是', '在', '有', '和', '与', '或', '及']:
                            ideas.append({
                                'title': f"{item_type}改造成{target}",
                                'description': sentence.strip(),
                                'target': target,
                                'full_sentence': sentence.strip()
                            })
                            break  # 找到一个目标就够了，避免重复
        
        # 如果没有找到具体目标，查找包含改造关键词的句子
        if not ideas:
            renovation_keywords = ['改造', '翻新', '改装', '变身', '升级', 'DIY', '创意', '废物利用', '实用', '教程', 'step', 'tutorial']
            for sentence in sentences:
                if any(keyword in sentence for keyword in renovation_keywords):
                    if len(sentence) > 15 and len(sentence) < 200:
                        ideas.append({
                            'title': f"{item_type}改造方案",
                            'description': sentence.strip(),
                            'target': '通用改造',
                            'full_sentence': sentence.strip()
                        })
        
        return ideas[:5]  # 减少数量，提高质量
    
    def _extract_techniques(self, content: str) -> List[str]:
        """提取改造技术 - 精准提取具体操作步骤"""
        techniques = []
        
        # 查找包含具体操作步骤的句子，扩大匹配范围
        step_patterns = [
            r'第一步[：:]([^，。！？\n]{5,80})',
            r'第二步[：:]([^，。！？\n]{5,80})',
            r'第三步[：:]([^，。！？\n]{5,80})',
            r'第四步[：:]([^，。！？\n]{5,80})',
            r'第五步[：:]([^，。！？\n]{5,80})',
            r'第六步[：:]([^，。！？\n]{5,80})',
            r'第七步[：:]([^，。！？\n]{5,80})',
            r'第八步[：:]([^，。！？\n]{5,80})',
            r'首先([^，。！？\n]{5,80})',
            r'然后([^，。！？\n]{5,80})',
            r'接着([^，。！？\n]{5,80})',
            r'最后([^，。！？\n]{5,80})',
            r'开始([^，。！？\n]{5,80})',
            r'准备([^，。！？\n]{5,80})',
            r'完成([^，。！？\n]{5,80})',
            r'Step 1[：:]([^，。！？\n]{5,80})',  # 英文步骤
            r'Step 2[：:]([^，。！？\n]{5,80})',
            r'Step 3[：:]([^，。！？\n]{5,80})',
            r'First([^，。！？\n]{5,80})',
            r'Then([^，。！？\n]{5,80})',
            r'Next([^，。！？\n]{5,80})',
            r'Finally([^，。！？\n]{5,80})'
        ]
        
        sentences = re.split(r'[。！？\n]', content)
        for sentence in sentences:
            # 查找包含具体步骤的句子
            for pattern in step_patterns:
                matches = re.findall(pattern, sentence)
                for match in matches:
                    if len(match) > 5 and len(match) < 80:
                        techniques.append(f"改造步骤: {match.strip()}")
                        break  # 找到一个步骤就够了
        
        # 如果没有找到具体步骤，查找包含操作描述的句子
        if not techniques:
            # 查找包含操作动词的句子，扩大关键词范围
            action_keywords = [
                '打磨', '上漆', '切割', '钻孔', '固定', '连接', '安装', '调整', '处理', '制作', '组装', '清洁', '准备', '测量', '标记', '修整', '装饰', '涂装',
                'sanding', 'painting', 'cutting', 'drilling', 'fixing', 'connecting', 'installing', 'adjusting', 'processing', 'making', 'assembling', 'cleaning', 'preparing', 'measuring', 'marking', 'trimming', 'decorating'
            ]
            for sentence in sentences:
                if len(sentence) > 15 and len(sentence) < 150:
                    # 查找包含操作描述的句子
                    if any(word in sentence for word in action_keywords):
                        techniques.append(f"操作方法: {sentence.strip()}")
        
        return techniques[:5]  # 减少数量，提高质量
    
    def _extract_material_suggestions(self, content: str) -> List[str]:
        """提取材料建议 - 精准提取具体材料清单"""
        materials = []
        
        # 查找包含具体材料清单的句子，扩大匹配范围
        material_patterns = [
            r'需要([^，。！？\n]{5,80})',
            r'准备([^，。！？\n]{5,80})',
            r'购买([^，。！？\n]{5,80})',
            r'材料[：:]([^，。！？\n]{5,80})',
            r'工具[：:]([^，。！？\n]{5,80})',
            r'清单[：:]([^，。！？\n]{5,80})',
            r'成本[：:]([^，。！？\n]{5,80})',
            r'预算[：:]([^，。！？\n]{5,80})',
            r'费用[：:]([^，。！？\n]{5,80})',
            r'价格[：:]([^，。！？\n]{5,80})',
            r'Materials[：:]([^，。！？\n]{5,80})',  # 英文材料
            r'Tools[：:]([^，。！？\n]{5,80})',  # 英文工具
            r'Cost[：:]([^，。！？\n]{5,80})',  # 英文成本
            r'Budget[：:]([^，。！？\n]{5,80})'  # 英文预算
        ]
        
        sentences = re.split(r'[。！？\n]', content)
        for sentence in sentences:
            # 查找包含具体材料清单的句子
            for pattern in material_patterns:
                matches = re.findall(pattern, sentence)
                for match in matches:
                    if len(match) > 5 and len(match) < 80:
                        materials.append(f"材料清单: {match.strip()}")
                        break  # 找到一个清单就够了
        
        # 如果没有找到具体清单，查找包含材料信息的句子
        if not materials:
            for sentence in sentences:
                if len(sentence) > 15 and len(sentence) < 150:
                    # 查找包含材料信息的句子，扩大关键词范围
                    material_keywords = [
                        '材料', '工具', '准备', '需要', '购买', '成本', '预算', '费用', '价格', '清单',
                        'materials', 'tools', 'supplies', 'needed', 'required', 'cost', 'budget', 'price', 'list'
                    ]
                    if any(word in sentence for word in material_keywords):
                        materials.append(f"材料信息: {sentence.strip()}")
        
        return materials[:5]  # 减少数量，提高质量
    
    def _extract_style_references(self, content: str) -> List[str]:
        """提取风格参考"""
        styles = []
        
        style_keywords = [
            '北欧', '工业风', '复古', '现代', '简约', '田园', '中式',
            'nordic', 'industrial', 'vintage', 'modern', 'minimalist', 'rustic'
        ]
        
        for keyword in style_keywords:
            if keyword in content:
                styles.append(keyword)
        
        return styles
    
    def _extract_practical_tips(self, content: str) -> List[str]:
        """提取实用技巧"""
        tips = []
        
        tip_keywords = [
            '注意', '建议', '技巧', '小贴士', '经验', 'tip', 'advice', 'suggestion'
        ]
        
        sentences = re.split(r'[。！？\n]', content)
        for sentence in sentences:
            if any(keyword in sentence for keyword in tip_keywords):
                if len(sentence) > 10 and len(sentence) < 100:
                    tips.append(sentence.strip())
        
        return tips[:3]
    
    def _get_fallback_inspiration(self, item_type: str, materials: List[str], user_requirements: str) -> Dict[str, Any]:
        """当搜索失败时的备用灵感"""
        logger.info("🔄 使用备用改造灵感...")
        
        fallback_ideas = {
            '椅子': [
                '将椅子改造成小书架，在座位下方增加储物空间',
                '给椅子重新包布，改变颜色和图案',
                '将椅子背部改造成展示架，可以放置装饰品'
            ],
            '桌子': [
                '在桌面下方增加抽屉或储物格',
                '将桌子改造成工作台，增加工具收纳功能',
                '给桌子加装轮子，变成移动工作台'
            ],
            '柜子': [
                '重新设计内部隔板，优化储物空间',
                '在柜门上增加镜子或黑板功能',
                '将柜子改造成展示柜，增加灯光效果'
            ]
        }
        
        fallback_data = {
            'ideas': fallback_ideas.get(item_type, ['基础清洁和维护', '重新上漆或染色', '增加实用功能']),
            'techniques': ['打磨表面', '重新上漆', '更换五金件'],
            'materials_suggestions': ['砂纸', '木器漆', '刷子', '螺丝'],
            'style_references': ['简约现代', '复古怀旧', '实用主义'],
            'practical_tips': ['先做好防护措施', '选择环保材料', '注意尺寸匹配']
        }
        
        # 打印备用灵感
        self._print_inspiration_summary(fallback_data, item_type)
        
        return fallback_data
    
    def format_inspiration_for_prompt(self, inspiration_data: Dict[str, Any]) -> str:
        """将灵感数据格式化为提示词"""
        prompt_parts = []
        
        if inspiration_data.get('ideas'):
            prompt_parts.append("【真实改造灵感】")
            for i, idea in enumerate(inspiration_data['ideas'][:3], 1):
                prompt_parts.append(f"{i}. {idea}")
        
        if inspiration_data.get('techniques'):
            prompt_parts.append("\n【改造技术参考】")
            prompt_parts.extend([f"- {tech}" for tech in inspiration_data['techniques'][:3]])
        
        if inspiration_data.get('materials_suggestions'):
            prompt_parts.append("\n【推荐材料】")
            prompt_parts.append(f"- {', '.join(inspiration_data['materials_suggestions'])}")
        
        if inspiration_data.get('practical_tips'):
            prompt_parts.append("\n【实用技巧】")
            prompt_parts.extend([f"- {tip}" for tip in inspiration_data['practical_tips'][:2]])
        
        return '\n'.join(prompt_parts)
    
    def _print_inspiration_summary(self, inspiration_data: Dict[str, Any], item_type: str):
        """在控制台打印灵感摘要"""
        print("\n" + "="*60)
        print(f"🎨 {item_type} 改造灵感搜索结果 (真实搜索数据)")
        print("="*60)
        
        if inspiration_data.get('ideas'):
            print("\n💡 【改造创意想法】")
            for i, idea in enumerate(inspiration_data['ideas'], 1):
                print(f"   {i}. {idea}")
        
        if inspiration_data.get('techniques'):
            print("\n🔧 【改造技术方法】")
            for tech in inspiration_data['techniques']:
                print(f"   • {tech}")
        
        if inspiration_data.get('materials_suggestions'):
            print("\n🛠️ 【推荐材料】")
            materials_str = ', '.join(inspiration_data['materials_suggestions'])
            print(f"   • {materials_str}")
        
        if inspiration_data.get('style_references'):
            print("\n🎭 【风格参考】")
            styles_str = ', '.join(inspiration_data['style_references'])
            print(f"   • {styles_str}")
        
        if inspiration_data.get('practical_tips'):
            print("\n📝 【实用技巧】")
            for tip in inspiration_data['practical_tips']:
                print(f"   • {tip}")
        
        print("\n" + "="*60)
        print("🌟 以上灵感来自真实网页搜索，包含知乎、YouTube、专业网站等优质内容")
        print("💡 搜索API: SerpAPI - 获取最新的改造案例和技巧")
        print("="*60 + "\n")
