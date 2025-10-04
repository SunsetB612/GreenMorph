"""
豆包Seedream4.0图像生成器
专门用于旧物改造项目的图像生成
"""

import os
import io
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from PIL import Image
from loguru import logger
from volcenginesdkarkruntime import Ark
from volcenginesdkarkruntime.types.images.images import SequentialImageGenerationOptions
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

from app.config import settings


class DoubaoSeedreamGenerator:
    """豆包Seedream4.0图像生成器"""
    
    def __init__(self, api_key: str = None):
        # 使用火山引擎Ark官方API key
        self.api_key = api_key or os.environ.get("ARK_API_KEY")
        
        if not self.api_key:
            logger.error("❌ 豆包API密钥未设置，请设置环境变量 ARK_API_KEY")
            raise ValueError("豆包API密钥未设置")
        
        # 初始化客户端
        self.client = Ark(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=self.api_key,
        )
        
        logger.info("✅ 豆包Seedream4.0客户端初始化成功")
    
    
    async def generate_final_effect_image(
        self,
        analysis_result: Dict[str, Any],
        user_requirements: str,
        target_style: str
    ) -> Image.Image:
        """生成最终改造效果图 - 基于数据库中的分析结果"""
        try:
            logger.info("🎨 开始生成最终改造效果图（基于数据库分析结果）...")
            
            # 构建基于分析结果的改造提示词
            prompt = self._build_redesign_prompt(
                analysis_result, user_requirements, target_style
            )
            
            # 使用文生图模式（基于分析结果生成）
            logger.info("📝 使用文生图模式（基于数据库分析结果）")
            response = self.client.images.generate(
                model="doubao-seedream-4-0-250828",
                prompt=prompt,
                size="2K",
                response_format="url",
                watermark=True
            )
            logger.info("✅ 文生图模式成功")
            
            if not response.data:
                raise Exception("豆包API返回空数据")
            
            # 下载生成的图像
            result_image = await self._download_image(response.data[0].url)
            
            logger.info("✅ 最终改造效果图生成成功")
            return result_image
            
        except Exception as e:
            logger.error(f"❌ 最终改造效果图生成失败: {str(e)}")
            raise Exception(f"改造效果图生成失败: {str(e)}")
    
    async def generate_final_effect_image_from_url(
        self,
        source_image_url: str,
        user_requirements: str,
        target_style: str,
        max_retries: int = 3
    ) -> Image.Image:
        """使用豆包(Ark SDK)基于源图URL进行图生图生成最终效果图"""
        
        # 构建平衡的提示词（图生图需要明确但合理的变化指令）
        creative_prompts = self._get_creative_prompts()
        
        # 提取用户需求中的关键变化词汇，使用更温和的表达
        transformation_keywords = []
        if "拆分" in user_requirements or "重组" in user_requirements:
            transformation_keywords.extend(["thoughtfully restructured", "creatively rebuilt", "smart reconfiguration"])
        if "改变用途" in user_requirements or "新功能" in user_requirements:
            transformation_keywords.extend(["cleverly repurposed", "enhanced functionality", "practical innovation"])
        if "创意" in user_requirements:
            transformation_keywords.extend(["creative renovation", "innovative upgrade", "artistic enhancement"])
        
        # 如果没有明确的变化关键词，添加默认的适度变化提示
        if not transformation_keywords:
            transformation_keywords = ["thoughtfully renovated", "creatively improved", "tastefully upgraded"]
        
        # 构建平衡的提示词
            short_prompt = ", ".join([
            f"Practical transformation: {', '.join(transformation_keywords[:2])}",
            f"elegant creative renovation",
                f"for {user_requirements}",
            "visible improvements while maintaining functionality",
            "creative upcycling with practical focus",
                *creative_prompts[:2],
            "enhanced aesthetics and usability",
            "realistic, high quality, professional result"
        ])
        
        # 先尝试下载图片到本地，然后重新上传到更稳定的服务
        local_image = None
        try:
            logger.info(f"🔄 尝试下载源图到本地: {source_image_url}")
            local_image = await self._download_image(source_image_url)
            logger.info("✅ 源图下载成功，准备重新上传")
        except Exception as e:
            logger.warning(f"⚠️ 源图下载失败: {e}")
        
        # 构建提示词
        short_prompt = f"Thoughtfully transformed {user_requirements}, creative design, practical improvements, quality renovation"
        
        # 重试机制
        for attempt in range(max_retries):
            try:
                logger.info(f"🎨 使用豆包图生图生成最终改造效果图（尝试 {attempt + 1}/{max_retries}）...")
                logger.info(f"📎 源图URL: {source_image_url}")
                logger.info(f"🎯 增强变化提示词: {short_prompt}")
                
                # 尝试不同的URL格式和策略
                current_url = source_image_url
                if attempt == 1 and local_image:
                    # 第二次尝试：使用base64直接传输
                    try:
                        logger.info("🔄 尝试重新上传图片到OSS...")
                        from app.shared.utils.cloud_storage import smart_upload_pil_image
                        
                        # 直接上传PIL图像
                        new_url = await smart_upload_pil_image(local_image, "retry_image.jpg")
                        if new_url:
                            current_url = new_url
                            logger.info(f"✅ OSS重新上传成功，新URL: {current_url}")
                        else:
                            raise Exception("OSS重新上传失败")
                    except Exception as upload_error:
                        logger.warning(f"⚠️ OSS重新上传失败，尝试base64: {upload_error}")
                        # 降级到base64直传
                        try:
                            import base64
                            import io
                            
                            # 转换为base64
                            img_buffer = io.BytesIO()
                            local_image.save(img_buffer, format='JPEG', quality=95)
                            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
                            
                            # 使用data URL格式
                            current_url = f"data:image/jpeg;base64,{img_base64}"
                            logger.info("✅ 使用base64格式直接传输")
                        except Exception as base64_error:
                            logger.warning(f"⚠️ base64转换失败: {base64_error}")
                            # 最后降级到URL重试
                            current_url = f"{source_image_url}?retry={attempt}&t={int(__import__('time').time())}"
                elif attempt > 1:
                    # 其他尝试：添加时间戳参数
                    import time
                    current_url = f"{source_image_url}?t={int(time.time())}&retry={attempt}"
                    logger.info(f"🔄 使用带时间戳的URL: {current_url}")
                
                # Ark官方文档：images.generate 支持 image 参数传入URL（单图输入单图输出）
                # 添加更多参数来增强变化程度
                response = self.client.images.generate(
                    model="doubao-seedream-4-0-250828",
                    prompt=short_prompt,
                    image=current_url,
                    size="2K",
                    response_format="url",
                    watermark=True,
                    # 注意：以下参数可能需要根据实际API支持情况调整
                    # guidance_scale=8.0,  # 提高引导强度，让AI更严格遵循提示词
                    # strength=0.8,        # 增加变化强度，0.8表示较大变化
                )
                
                if not response.data:
                    raise Exception("豆包图生图API返回空数据")
                
                result_image = await self._download_image(response.data[0].url)
                logger.info("✅ 豆包图生图最终效果图生成成功")
                return result_image
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"⚠️ 豆包图生图尝试 {attempt + 1}/{max_retries} 失败: {error_msg}")
                
                # 如果是URL下载超时，且还有重试次数，则继续重试
                if "Timeout while downloading url" in error_msg and attempt < max_retries - 1:
                    import asyncio
                    wait_time = (attempt + 1) * 2  # 递增等待时间：2s, 4s, 6s
                    logger.info(f"🔄 URL超时，等待 {wait_time}s 后重试（{attempt + 2}/{max_retries}）...")
                    await asyncio.sleep(wait_time)
                    continue
                
                # 最后一次尝试失败，或者非超时错误，直接抛出
                if attempt == max_retries - 1:
                    logger.error(f"❌ 豆包图生图所有尝试均失败: {error_msg}")
                    raise Exception(f"豆包图生图失败（{max_retries}次尝试）: {error_msg}")
                
        # 理论上不会到达这里
        raise Exception("未知错误")

    async def generate_final_effect_image_from_bytes(
        self,
        image_bytes: bytes,
        user_requirements: str,
        target_style: str,
        negative_prompt: str | None = None,
        strength: float = 0.55,
        guidance_scale: float = 7.5,
        steps: int = 28,
        size: str = "2K",
    ) -> Image.Image:
        """使用本地源图二进制进行图生图（当前SDK无直接i2i参数时退回文生图）。
        后续如SDK提供i2i端点，可在此处替换为真正的图生图调用。
        """
        try:
            logger.info("🎨 使用本地源图二进制进行改造（模拟i2i，当前回退t2i）...")
            creative_prompts = self._get_creative_prompts()
            short_prompt = ", ".join([
                f"creative redesign",
                f"for {user_requirements}",
                *creative_prompts[:2],
                "realistic, high quality"
            ])
            # TODO: 当SDK支持i2i时，改为：images.img2img(image=image_bytes, prompt=..., strength=...)
            # 优先尝试HTTP i2i接口（APIYI），使用本地bytes作为源图：将其上传为多部分或base64
            # 这里按你提供的JSON接口规范，传递image为数组URL；由于我们有本地bytes，采用先上传到临时图床或直接退回t2i。
            # 为保证可用性，这里仍使用t2i回退生成；当需要切换到HTTP i2i时，可在此接入requests.post到settings.seedream_api_base。
            response = self.client.images.generate(
                model="doubao-seedream-4-0-250828",
                prompt=short_prompt,
                size=size,
                response_format="url",
                watermark=True
            )
            if not response.data:
                raise Exception("豆包生成返回空数据")
            result_image = await self._download_image(response.data[0].url)
            logger.info("✅ 本地源图改造生成成功（当前为t2i回退实现）")
            return result_image
        except Exception as e:
            logger.error(f"❌ 本地源图改造生成失败: {e}")
            raise

    async def generate_final_effect_image_i2i_http(
        self,
        image_urls: list[str],
        user_requirements: str,
        target_style: str,
        max_images: int = 1
    ) -> Image.Image:
        """通过APIYI HTTP接口调用Seedream4 i2i，使用公网可访问的图片URL数组。
        返回第一张生成结果为PIL Image。
        """
        import requests
        from io import BytesIO
        try:
            if not settings.seedream_api_key:
                raise Exception("未配置 SEEDREAM_API_KEY")
            api_url = f"{settings.seedream_api_base.rstrip('/')}/v1/images/generations"
            creative_prompts = self._get_creative_prompts()
            prompt = ", ".join([
                f"creative redesign",
                f"for {user_requirements}",
                *creative_prompts[:2],
                "realistic, high quality"
            ])
            payload = {
                "model": "doubao-seedream-4-0-250828",
                "prompt": prompt,
                "image": image_urls,
                "sequential_image_generation": "auto",
                "sequential_image_generation_options": {"max_images": max_images}
            }
            headers = {
                "Authorization": f"Bearer {settings.seedream_api_key}",
                "Content-Type": "application/json"
            }
            resp = requests.post(api_url, json=payload, headers=headers, timeout=60)
            if resp.status_code != 200:
                raise Exception(f"HTTP {resp.status_code}: {resp.text}")
            data = resp.json()
            # 兼容不同返回结构，尽量取第一个url
            gen_url = None
            if isinstance(data, dict):
                # 常见结构: {data: {url: ...}} 或 {data: [{url: ...}]}
                d = data.get("data")
                if isinstance(d, dict):
                    gen_url = d.get("url")
                elif isinstance(d, list) and d:
                    gen_url = d[0].get("url")
                if not gen_url and "url" in data:
                    gen_url = data.get("url")
            if not gen_url:
                raise Exception(f"返回中未找到生成URL: {data}")
            # 下载生成图片
            img_resp = requests.get(gen_url, timeout=60)
            if img_resp.status_code != 200:
                raise Exception(f"下载生成图失败 HTTP {img_resp.status_code}")
            return Image.open(BytesIO(img_resp.content))
        except Exception as e:
            logger.error(f"❌ HTTP i2i生成失败: {e}")
            raise
    
    async def generate_all_images_in_conversation(
        self,
        analysis_result: Dict[str, Any],
        steps: List[Dict[str, Any]],
        source_image_url: str,
        user_requirements: str,
        target_style: str
    ) -> Dict[str, Any]:
        """在同一个对话会话中生成最终效果图和所有步骤图"""
        try:
            logger.info(f"🎬 开始同会话多轮生成：最终效果图 + {len(steps)} 个步骤图")
            
            # 构建初始对话提示
            conversation_prompt = f"""我需要你帮我完成一个旧物改造的完整设计。

源图片: {source_image_url}
改造需求: {user_requirements}
创意改造: 不限风格，鼓励创新

请按以下顺序生成图片：
1. 首先生成最终改造效果图
2. 然后生成{len(steps)}个改造步骤图

第一张图：最终效果图
{self._build_final_effect_prompt(user_requirements, target_style)}"""
            
            # 第一轮：生成最终效果图
            logger.info("🎨 第1轮：生成最终效果图...")
            try:
                final_response = self.client.images.generate(
                    model="doubao-seedream-4-0-250828",
                    prompt=conversation_prompt,
                    image=source_image_url,
                    size="2K",
                    response_format="url",
                    watermark=True
                )
            except Exception as e:
                logger.error(f"最终效果图生成失败: {e}")
                raise
            
            if not final_response.data:
                raise Exception("最终效果图生成失败")
            
            final_image = await self._download_image(final_response.data[0].url)
            final_image_url = final_response.data[0].url
            logger.info("✅ 最终效果图生成成功")
            
            # 第二轮开始：基于最终效果图生成步骤图
            step_images = []
            current_image_url = source_image_url
            
            for i, step in enumerate(steps):
                step_num = i + 1
                progress = (step_num) / len(steps)
                
                # 构建步骤对话提示
                step_conversation_prompt = f"""继续我们的改造设计对话。

你刚才生成了最终效果图: {final_image_url}
现在请生成第{step_num}个改造步骤图({step_num}/{len(steps)})：

步骤名称: {step.get('title', f'步骤{step_num}')}
步骤描述: {step.get('description', '')}
进度: {progress*100:.0f}%

要求：
- 显示从原图向最终效果图转变的{progress*100:.0f}%进度
- 重点展现{step.get('title', '改造过程')}中的结构变化
- 保持原有的颜色、材质和表面处理
- 主要改变形状、比例和结构布局
- 与最终效果图保持一致的材质风格和颜色方案
- 展现逐步的结构改造连贯性"""
                
                logger.info(f"🔧 第{step_num+1}轮：生成步骤{step_num}图像...")
                
                step_response = self.client.images.generate(
                    model="doubao-seedream-4-0-250828",
                    prompt=step_conversation_prompt,
                    image=current_image_url,
                    size="2K",
                    response_format="url",
                    watermark=True
                )
                
                if step_response.data:
                    step_image = await self._download_image(step_response.data[0].url)
                    step_images.append(step_image)
                    current_image_url = step_response.data[0].url  # 下一步的输入
                    logger.info(f"✅ 步骤{step_num}生成成功")
                else:
                    logger.warning(f"⚠️ 步骤{step_num}生成失败，使用占位图")
                    step_images.append(Image.new('RGB', (512, 512), 'lightgray'))
            
            return {
                'final_image': final_image,
                'step_images': step_images,
                'conversation_context': '对话上下文已建立'
            }
            
        except Exception as e:
            logger.error(f"❌ 同会话多轮生成失败: {str(e)}")
            raise Exception(f"同会话生成失败: {str(e)}")

    def _build_final_effect_prompt(self, user_requirements: str, target_style: str) -> str:
        """构建最终效果图的对话提示"""
        return f"Structural renovation of furniture, for {user_requirements}, keep original colors and surface finish, focus on shape and function changes, realistic size and proportions, practical design, high quality"
    
    async def generate_step_images(
        self,
        analysis_result: Dict[str, Any],
        steps: List[Dict[str, Any]],
        source_image_url: Optional[str] = None,
        final_result_image: Optional[Image.Image] = None
    ) -> List[Image.Image]:
        """生成改造步骤图像 - 革命性新流程：从原图到最终效果图的真实渐进过程"""
        try:
            logger.info(f"🎬 开始革命性渐进式生成 {len(steps)} 个改造步骤图像...")
            logger.info(f"🔍 初始源图URL: {source_image_url}")
            
            # 检查URL类型
            if source_image_url:
                if "oss-cn-shanghai.aliyuncs.com" in source_image_url:
                    logger.info("✅ 使用OSS URL进行图生图")
                elif "i.ibb.co" in source_image_url:
                    logger.warning("⚠️ 使用ImgBB URL，可能导致超时")
                else:
                    logger.info(f"🔍 使用其他URL: {source_image_url[:50]}...")
            else:
                logger.warning("⚠️ 源图URL为空，将使用文生图模式")
            
            logger.info(f"🎯 是否有最终效果图引导: {'是' if final_result_image else '否'}")
            
            # 基于分析结果构建物品信息
            item_type = analysis_result.get('main_objects', ['furniture'])[0] if analysis_result.get('main_objects') else 'furniture'
            materials = analysis_result.get('materials', [])
            material_desc = ', '.join([str(m).replace('MaterialType.', '').lower() for m in materials]) if materials else 'wood'
            colors = analysis_result.get('colors', [])
            color_desc = ', '.join(colors) if colors else 'natural'
            condition = analysis_result.get('condition', 'used')
            features = analysis_result.get('features', [])
            feature_desc = ', '.join(features[:3]) if features else 'basic structure'
            
            step_images = []
            current_image_url = source_image_url  # 当前步骤的输入图像URL
            
            # 如果有最终效果图，先上传它以便引导步骤生成
            final_result_url = None
            if final_result_image:
                try:
                    logger.info("🔄 上传最终效果图作为目标引导...")
                    from app.shared.utils.cloud_storage import smart_upload_pil_image
                    final_result_url = await smart_upload_pil_image(final_result_image, "final_target.jpg")
                    logger.info(f"✅ 最终效果图上传成功: {final_result_url}")
                except Exception as e:
                    logger.warning(f"⚠️ 最终效果图上传失败: {e}")
            
            # 计算每个步骤的变化强度（从0%到100%）
            total_steps = len(steps)
            step_progress_ratios = [(i + 1) / total_steps for i in range(total_steps)]
            
            # 逐步生成每个步骤图像
            for i, step in enumerate(steps):
                step_num = i + 1
                progress_ratio = step_progress_ratios[i]
                logger.info(f"🔧 生成步骤 {step_num}/{len(steps)}: {step.get('title', '未知步骤')} (进度: {progress_ratio*100:.0f}%)")
                
                # 构建当前步骤的详细提示词
                title = step.get('title', f'改造步骤{step_num}')
                description = step.get('description', '')
                materials_needed = step.get('materials_needed', [])
                tools_needed = step.get('tools_needed', [])
                image_prompt = step.get('image_prompt', '')
                
                # 优化的步骤图提示词，更详细和具体，无文字
                if "拆" in description or "分解" in description:
                    step_prompt = f"{item_type} disassembly process, {description.lower()}, showing structural changes, step {step_num} of renovation, no text, no labels, clean image"
                elif "重组" in description or "组装" in description:
                    step_prompt = f"{item_type} reconstruction process, {description.lower()}, new structure forming, step {step_num} of renovation, no text, no labels, clean image"
                elif "改造" in description or "转换" in description:
                    step_prompt = f"{item_type} transformation process, {description.lower()}, significant structural changes, step {step_num} of renovation, no text, no labels, clean image"
                elif "清洁" in description or "准备" in description:
                    step_prompt = f"{item_type} preparation and cleaning, {description.lower()}, surface treatment, step {step_num} of renovation, no text, no labels, clean image"
                elif "上色" in description or "涂装" in description:
                    step_prompt = f"{item_type} painting and finishing, {description.lower()}, color application, step {step_num} of renovation, no text, no labels, clean image"
                else:
                    step_prompt = f"{item_type} renovation process, {description.lower()}, visible improvements, step {step_num} of renovation, no text, no labels, clean image"
                
                logger.info(f"🎯 步骤 {step_num} 革命性提示词: {step_prompt}")
                
                # 尝试基于当前图像生成下一步
                step_image = None
                if current_image_url:
                    # 使用图生图模式
                    for attempt in range(2):
                        try:
                            logger.info(f"🎨 步骤 {step_num} 图生图模式（尝试 {attempt + 1}/2）")
                            logger.info(f"📎 输入图像URL: {current_image_url}")
                            
                            response = self.client.images.generate(
                                model="doubao-seedream-4-0-250828",
                                prompt=step_prompt,
                                image=current_image_url,
                                size="2K",
                                response_format="url",
                                watermark=True,
                                # 步骤图也使用增强变化参数
                                # guidance_scale=8.0,  # 提高引导强度
                                # strength=0.7,        # 步骤间适中变化强度
                            )
                            
                            if response.data:
                                step_image = await self._download_image(response.data[0].url)
                                # 更新当前图像URL为刚生成的图像URL，供下一步使用
                                current_image_url = response.data[0].url
                                logger.info(f"✅ 步骤 {step_num} 图生图成功，已更新为下一步输入")
                                break
                                
                        except Exception as e:
                            error_msg = str(e)
                            logger.warning(f"⚠️ 步骤 {step_num} 图生图尝试 {attempt + 1}/2 失败: {error_msg}")
                            if "Timeout while downloading url" in error_msg and attempt < 1:
                                logger.info(f"🔄 步骤 {step_num} URL超时，等待2s后重试（2/2）...")
                                import asyncio
                                await asyncio.sleep(2)
                                continue
                            else:
                                break
                
                # 如果图生图失败，使用文生图模式
                if step_image is None:
                    try:
                        logger.info(f"📝 步骤 {step_num} 降级到文生图模式")
                        response = self.client.images.generate(
                            model="doubao-seedream-4-0-250828",
                            prompt=step_prompt,
                            size="2K",
                            response_format="url",
                            watermark=True
                        )
                        
                        if response.data:
                            try:
                                step_image = await self._download_image(response.data[0].url)
                                # 更新当前图像URL
                                current_image_url = response.data[0].url
                                logger.info(f"✅ 步骤 {step_num} 文生图成功")
                            except Exception as download_error:
                                logger.error(f"❌ 步骤 {step_num} 文生图下载失败: {download_error}")
                                step_image = None
                        else:
                            logger.error(f"❌ 步骤 {step_num} 文生图API返回空数据")
                            step_image = None
                        
                    except Exception as e:
                        logger.error(f"❌ 步骤 {step_num} 文生图API调用失败: {str(e)}")
                        step_image = None
                
                # 如果所有方法都失败，创建占位图
                if step_image is None:
                    logger.warning(f"⚠️ 步骤 {step_num} 所有生成方法都失败，创建占位图")
                    step_image = self._create_step_placeholder(step_num, step.get('title', '改造步骤'))
                
                step_images.append(step_image)
                logger.info(f"✅ 步骤 {step_num} 完成，共生成 {len(step_images)} 张图像")
            
            logger.info(f"🎉 渐进式步骤图像生成完成，共 {len(step_images)} 张")
            return step_images
            
        except Exception as e:
            logger.error(f"❌ 渐进式步骤图像生成失败: {str(e)}")
            raise Exception(f"步骤图像生成失败: {str(e)}")
    
    def _build_redesign_prompt(
        self,
        analysis_result: Dict[str, Any],
        user_requirements: str,
        target_style: str
    ) -> str:
        """构建基于数据库分析结果的改造提示词"""
        main_objects = analysis_result.get('main_objects', ['furniture'])
        materials = analysis_result.get('materials', [])
        colors = analysis_result.get('colors', [])
        condition = analysis_result.get('condition', 'used')
        age_estimate = analysis_result.get('age_estimate', '')
        damage_assessment = analysis_result.get('damage_assessment', [])
        
        item_type = main_objects[0] if main_objects else 'furniture'
        material_desc = ', '.join([str(m) for m in materials]) if materials else 'wood'
        color_desc = ', '.join(colors) if colors else 'natural'
        
        # 根据风格类型构建特定的提示词
        creative_prompts = self._get_creative_prompts()
        
        # 构建基于分析结果的详细改造提示词
        prompt_parts = [
            # 1. 基于分析结果的物品描述
            f"Restore and redesign a {condition} {item_type}",
            f"original materials: {material_desc}",
            f"original colors: {color_desc}",
        ]
        
        # 2. 添加年龄和损坏信息
        if age_estimate:
            prompt_parts.append(f"estimated age: {age_estimate}")
        if damage_assessment:
            damage_desc = ', '.join(damage_assessment[:3])  # 只取前3个损坏描述
            prompt_parts.append(f"current condition: {damage_desc}")
        
        # 3. 改造目标
        prompt_parts.extend([
            f"transform into creative innovative design",
            f"redesign for: {user_requirements}",
        ])
        
        # 4. 风格特定描述
        prompt_parts.extend(creative_prompts)
        
        # 5. 质量要求
        prompt_parts.extend([
            "realistic furniture restoration, authentic materials",
            "professional craftsmanship, high quality workmanship",
            "practical, functional design improvements",
            "maintain original function and usability",
        ])
        
        # 6. 避免幻觉
        prompt_parts.extend([
            "no fantasy elements, no unrealistic features",
            "real-world furniture design, practical improvements",
        ])
        
        # 7. 摄影质量
        prompt_parts.extend([
            "professional product photography, clean white background",
            "sharp focus, accurate colors, realistic lighting",
            "studio quality, commercial photography"
        ])
        
        full_prompt = ", ".join(prompt_parts)
        logger.info(f"📝 基于数据库分析结果的改造提示词: {full_prompt}")
        
        return full_prompt
    
    def _get_creative_prompts(self) -> List[str]:
        """获取通用的创意提示词"""
        return [
            "innovative design with creative elements",
            "bold structural transformation",
            "functional and aesthetic improvements",
            "unique material combinations",
            "creative upcycling approach"
        ]
    
    def _create_step_placeholder(self, step_num: int, step_title: str) -> Image.Image:
        """创建步骤占位图"""
        try:
            from PIL import ImageDraw, ImageFont
            
            # 创建占位图像
            image = Image.new('RGB', (512, 512), '#F0F0F0')
            draw = ImageDraw.Draw(image)
            
            # 绘制边框
            draw.rectangle([10, 10, 502, 502], outline='#CCCCCC', width=2)
            
            # 添加文字
            try:
                # 尝试使用默认字体
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            except:
                font_large = None
                font_small = None
            
            # 步骤编号
            step_text = f"步骤 {step_num}"
            draw.text((256, 200), step_text, fill='#666666', font=font_large, anchor='mm')
            
            # 步骤标题
            title_text = step_title[:20] + "..." if len(step_title) > 20 else step_title
            draw.text((256, 250), title_text, fill='#888888', font=font_small, anchor='mm')
            
            # 提示信息
            error_text = "图像生成失败"
            draw.text((256, 300), error_text, fill='#999999', font=font_small, anchor='mm')
            
            logger.info(f"✅ 创建步骤 {step_num} 占位图")
            return image
            
        except Exception as e:
            logger.error(f"❌ 创建占位图失败: {e}")
            # 返回最简单的占位图
            return Image.new('RGB', (512, 512), '#F0F0F0')
    
    async def _download_image(self, image_url: str) -> Image.Image:
        """下载图像"""
        try:
            import aiohttp
            import ssl
            import certifi
            
            # 设置更完善的请求头和SSL配置
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            }
            
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            timeout = aiohttp.ClientTimeout(total=30)
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            async with aiohttp.ClientSession(
                timeout=timeout, 
                connector=connector, 
                headers=headers
            ) as session:
                async with session.get(image_url, allow_redirects=True) as response:
                    if response.status == 200:
                        # 检查内容类型
                        content_type = response.headers.get("Content-Type", "")
                        logger.info(f"📥 下载图像，Content-Type: {content_type}")
                        
                        image_data = await response.read()
                        
                        # 验证数据不为空
                        if not image_data:
                            raise Exception("下载的图像数据为空")
                        
                        logger.info(f"📥 图像数据大小: {len(image_data)} bytes")
                        
                        # 尝试打开图像
                        try:
                            image = Image.open(io.BytesIO(image_data))
                            # 转换为RGB格式，确保兼容性
                            if image.mode != 'RGB':
                                image = image.convert('RGB')
                            logger.info(f"✅ 图像解析成功，尺寸: {image.size}")
                            return image
                        except Exception as img_error:
                            logger.error(f"❌ 图像解析失败: {img_error}")
                            # 保存原始数据用于调试
                            debug_path = f"debug_image_{hash(image_url) % 10000}.dat"
                            with open(debug_path, 'wb') as f:
                                f.write(image_data[:1000])  # 只保存前1000字节用于调试
                            logger.error(f"已保存调试数据到: {debug_path}")
                            raise Exception(f"图像格式无效或损坏: {img_error}")
                    else:
                        raise Exception(f"图像下载失败: HTTP {response.status} - {response.reason}")
                        
        except Exception as e:
            logger.error(f"❌ 图像下载失败: {str(e)}")
            logger.error(f"❌ 问题URL: {image_url}")
            raise Exception(f"图像下载失败: {str(e)}")
    
    def validate_requirements(self) -> bool:
        """验证环境要求"""
        try:
            # 检查API密钥
            if not self.api_key:
                logger.error("❌ 豆包API密钥未设置")
                return False
            
            # 检查客户端初始化
            if not self.client:
                logger.error("❌ 豆包客户端未初始化")
                return False
            
            logger.info("✅ 豆包Seedream4.0环境验证通过")
            return True
            
        except Exception as e:
            logger.error(f"❌ 环境验证失败: {str(e)}")
            return False
