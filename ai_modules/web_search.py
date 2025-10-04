"""
Web搜索模块
支持Google Search API、SerpAPI、百度搜索API、必应搜索API等
"""

import asyncio
import aiohttp
import hashlib
import time
import urllib.parse
from typing import Optional, List, Dict, Any
from loguru import logger
from app.config import settings


class WebSearchService:
    """网页搜索服务"""
    
    def __init__(self):
        # 原有配置
        self.google_api_key = settings.google_search_api_key
        self.google_engine_id = settings.google_search_engine_id
        self.serpapi_key = settings.serpapi_key
        self.enable_search = settings.enable_web_search
        
        # 国内搜索API配置
        self.baidu_api_key = settings.baidu_search_api_key
        self.baidu_secret_key = settings.baidu_search_secret_key
        self.bing_api_key = settings.bing_search_api_key
        self.sogou_api_key = settings.sogou_search_api_key
        
        # 搜索优先级配置
        self.search_priority = settings.search_priority.split(',')
    
    async def search_realistic_renovation_cases(self, item_type: str, materials: List[str], target_style: str) -> List[Dict[str, Any]]:
        """
        搜索现实改造案例，获取更多实用参考
        
        Args:
            item_type: 物品类型（如椅子、桌子等）
            materials: 材料列表
            target_style: 目标风格
            
        Returns:
            现实改造案例列表
        """
        if not self.enable_search:
            logger.warning("网页搜索功能已禁用")
            return []
        
        # 构建更具体的搜索查询
        material_str = " ".join(materials[:3])  # 只取前3个材料
        queries = [
            f"{item_type} 改造 DIY 实用 教程",
            f"{item_type} {material_str} 旧物改造 现实案例",
            f"{target_style} {item_type} 改造 步骤 教程",
            f"废旧 {item_type} 改造 实用 家庭",
            f"{item_type} 改造 成本低 易操作"
        ]
        
        all_results = []
        
        for query in queries:
            try:
                logger.info(f"🔍 搜索现实改造案例: {query}")
                results = await self.search(query, num_results=3)
                
                # 过滤和增强结果
                for result in results:
                    if self._is_realistic_case(result):
                        result['search_query'] = query
                        result['relevance_score'] = self._calculate_relevance(result, item_type, materials, target_style)
                        all_results.append(result)
                
                # 避免重复搜索
                if len(all_results) >= 8:
                    break
                    
            except Exception as e:
                logger.warning(f"搜索查询失败: {query}, 错误: {e}")
                continue
        
        # 按相关性排序并去重
        unique_results = self._deduplicate_results(all_results)
        sorted_results = sorted(unique_results, key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        logger.info(f"✅ 找到 {len(sorted_results)} 个现实改造案例")
        return sorted_results[:8]  # 返回最多8个最相关的案例
    
    def _is_realistic_case(self, result: Dict[str, Any]) -> bool:
        """判断是否为现实改造案例"""
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        
        # 现实改造案例的关键词
        realistic_keywords = [
            'diy', '教程', '步骤', '实用', '简单', '易操作', '成本低',
            '家庭', '改造', '翻新', '修复', '再利用', '环保',
            '工具', '材料', '时间', '难度', '安全'
        ]
        
        # 避免的词汇（过于理想化或不现实的）
        unrealistic_keywords = [
            '艺术', '创意', '概念', '设计', '展示', '展览',
            '专业', '复杂', '昂贵', '高端', '定制'
        ]
        
        # 检查是否包含现实关键词
        has_realistic = any(keyword in title or keyword in snippet for keyword in realistic_keywords)
        
        # 检查是否包含不现实关键词
        has_unrealistic = any(keyword in title or keyword in snippet for keyword in unrealistic_keywords)
        
        return has_realistic and not has_unrealistic
    
    def _calculate_relevance(self, result: Dict[str, Any], item_type: str, materials: List[str], target_style: str) -> float:
        """计算搜索结果的相关性分数"""
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        text = f"{title} {snippet}"
        
        score = 0.0
        
        # 物品类型匹配
        if item_type.lower() in text:
            score += 2.0
        
        # 材料匹配
        for material in materials:
            if material.lower() in text:
                score += 1.0
        
        # 风格匹配
        if target_style.lower() in text:
            score += 1.5
        
        # 现实性关键词加分
        realistic_bonus = [
            'diy', '教程', '步骤', '实用', '简单', '成本低',
            '工具', '材料', '时间', '安全'
        ]
        
        for keyword in realistic_bonus:
            if keyword in text:
                score += 0.5
        
        return score
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重搜索结果"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
    
    async def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        执行网页搜索
        
        Args:
            query: 搜索关键词
            num_results: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        if not self.enable_search:
            logger.warning("网页搜索功能已禁用")
            return []
        
        # 按优先级尝试不同的搜索API
        for search_provider in self.search_priority:
            search_provider = search_provider.strip()
            
            try:
                if search_provider == "baidu" and self.baidu_api_key and self.baidu_secret_key:
                    logger.info(f"🔍 尝试使用百度搜索API: {query}")
                    result = await self._baidu_search(query, num_results)
                    if result:
                        return result
                        
                elif search_provider == "bing" and self.bing_api_key:
                    logger.info(f"🔍 尝试使用必应搜索API: {query}")
                    result = await self._bing_search(query, num_results)
                    if result:
                        return result
                        
                elif search_provider == "google" and self.google_api_key and self.google_engine_id:
                    logger.info(f"🔍 尝试使用Google搜索API: {query}")
                    result = await self._google_search(query, num_results)
                    if result:
                        return result
                        
                elif search_provider == "serpapi" and self.serpapi_key:
                    logger.info(f"🔍 尝试使用SerpAPI: {query}")
                    result = await self._serpapi_search(query, num_results)
                    if result:
                        return result
                        
            except Exception as e:
                logger.warning(f"❌ {search_provider}搜索失败: {e}")
                continue
        
        logger.warning("❌ 所有搜索API都不可用")
        return []
    
    async def _google_search(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """使用Google Custom Search API"""
        try:
            from googleapiclient.discovery import build
            
            logger.info(f"🔍 使用Google Search API搜索: {query}")
            
            # 构建搜索服务
            service = build("customsearch", "v1", developerKey=self.google_api_key)
            
            # 执行搜索
            result = service.cse().list(
                q=query,
                cx=self.google_engine_id,
                num=min(num_results, 10),  # Google API最多返回10个结果
                lr='lang_zh-CN|lang_en',  # 中英文结果
                safe='active'  # 安全搜索
            ).execute()
            
            # 解析结果
            search_results = []
            for item in result.get('items', []):
                search_results.append({
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'source': 'google'
                })
            
            logger.info(f"✅ Google搜索完成，获取到 {len(search_results)} 个结果")
            return search_results
            
        except Exception as e:
            logger.error(f"❌ Google搜索失败: {e}")
            return []
    
    async def _serpapi_search(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """使用SerpAPI"""
        try:
            import requests
            
            logger.info(f"🔍 使用SerpAPI搜索: {query}")
            
            # 配置搜索参数
            params = {
                "engine": "google",
                "q": query,
                "api_key": self.serpapi_key,
                "num": min(num_results, 10),
                "hl": "zh-cn",  # 中文界面
                "gl": "cn"      # 中国地区
            }
            
            # 使用requests直接调用SerpAPI
            url = "https://serpapi.com/search"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # 解析结果
                        search_results = []
                        for item in data.get('organic_results', []):
                            search_results.append({
                                'title': item.get('title', ''),
                                'link': item.get('link', ''),
                                'snippet': item.get('snippet', ''),
                                'source': 'serpapi'
                            })
                        
                        logger.info(f"✅ SerpAPI搜索完成，获取到 {len(search_results)} 个结果")
                        return search_results
                    else:
                        logger.error(f"❌ SerpAPI返回错误状态: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"❌ SerpAPI搜索失败: {e}")
            return []
    
    async def _baidu_search(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """使用百度搜索API"""
        try:
            import requests
            
            logger.info(f"🔍 使用百度搜索API: {query}")
            
            # 百度搜索API需要签名验证
            timestamp = str(int(time.time()))
            sign_string = f"{self.baidu_api_key}{query}{timestamp}{self.baidu_secret_key}"
            sign = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
            
            # 构建请求参数
            params = {
                'q': query,
                'timestamp': timestamp,
                'apikey': self.baidu_api_key,
                'sign': sign,
                'rn': min(num_results, 10),  # 结果数量
                'format': 'json'
            }
            
            # 发送请求
            url = "https://api.baidu.com/json/sms/service/v2/search"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # 解析百度搜索结果
                        search_results = []
                        if 'data' in data and 'results' in data['data']:
                            for item in data['data']['results'][:num_results]:
                                search_results.append({
                                    'title': item.get('title', ''),
                                    'link': item.get('url', ''),
                                    'snippet': item.get('content', ''),
                                    'source': 'baidu'
                                })
                        
                        logger.info(f"✅ 百度搜索完成，获取到 {len(search_results)} 个结果")
                        return search_results
                    else:
                        logger.error(f"❌ 百度搜索API返回错误状态: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"❌ 百度搜索失败: {e}")
            return []
    
    async def _bing_search(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """使用必应搜索API"""
        try:
            logger.info(f"🔍 使用必应搜索API: {query}")
            
            # 必应搜索API v7
            url = "https://api.bing.microsoft.com/v7.0/search"
            headers = {
                'Ocp-Apim-Subscription-Key': self.bing_api_key,
                'Content-Type': 'application/json'
            }
            params = {
                'q': query,
                'count': min(num_results, 50),  # 必应API最多返回50个结果
                'mkt': 'zh-CN',  # 中文市场
                'safeSearch': 'Moderate'  # 安全搜索
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # 解析必应搜索结果
                        search_results = []
                        if 'webPages' in data and 'value' in data['webPages']:
                            for item in data['webPages']['value'][:num_results]:
                                search_results.append({
                                    'title': item.get('name', ''),
                                    'link': item.get('url', ''),
                                    'snippet': item.get('snippet', ''),
                                    'source': 'bing'
                                })
                        
                        logger.info(f"✅ 必应搜索完成，获取到 {len(search_results)} 个结果")
                        return search_results
                    else:
                        logger.error(f"❌ 必应搜索API返回错误状态: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"❌ 必应搜索失败: {e}")
            return []
    
    async def search_text_only(self, query: str, num_results: int = 5) -> str:
        """
        搜索并返回纯文本结果
        
        Args:
            query: 搜索关键词
            num_results: 返回结果数量
            
        Returns:
            合并的搜索结果文本
        """
        results = await self.search(query, num_results)
        
        if not results:
            return ""
        
        # 合并搜索结果为文本
        text_results = []
        for result in results:
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            if title and snippet:
                text_results.append(f"{title}: {snippet}")
        
        return '\n'.join(text_results)


# 全局搜索服务实例
web_search_service = WebSearchService()


async def web_search(search_term: str, explanation: str = "", num_results: int = 5) -> str:
    """
    网页搜索函数（兼容现有接口）
    
    Args:
        search_term: 搜索关键词
        explanation: 搜索说明（用于日志）
        num_results: 返回结果数量
        
    Returns:
        搜索结果文本
    """
    logger.info(f"🔍 网页搜索: {search_term} ({explanation})")
    
    try:
        result = await web_search_service.search_text_only(search_term, num_results)
        
        if result:
            logger.info(f"✅ 搜索成功，获取到内容长度: {len(result)} 字符")
        else:
            logger.warning("⚠️ 搜索未返回有效结果")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 网页搜索异常: {e}")
        return ""
