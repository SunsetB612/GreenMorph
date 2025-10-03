"""
图像生成模块
基于结构控制生成改造效果图和步骤示意图
使用ControlNet等技术保持原物结构特征
"""

import base64
import io
import os
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import cv2
import numpy as np
import torch
# from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
# from diffusers import DDIMScheduler
# from controlnet_aux import CannyDetector, OpenposeDetector
from loguru import logger

from app.config import settings


class ImageGenerator:
    """图像生成器"""
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipeline = None
        self.controlnet = None
        self.canny_detector = None
        self.openpose_detector = None
        
        # 两级降级系统配置 - 简化版
        self.use_doubao = True      # 优先使用豆包Seedream4.0（高质量+国内友好）
        self.use_tongyi = True      # 备用通义千问（国内友好）
        self.use_fallback = True    # 最终备用方案
        
        # 初始化顺序：豆包Seedream4.0 -> 通义千问 -> 备用方案
        self._initialize_models()
    
    def _initialize_models(self):
        """初始化图像生成模型"""
        try:
            # 第一优先级：豆包Seedream4.0
            if self.use_doubao:
                logger.info("初始化豆包Seedream4.0 API")
                from ai_modules.doubao_generator import DoubaoSeedreamGenerator
                self.doubao_generator = DoubaoSeedreamGenerator()
                logger.info("豆包Seedream4.0 API初始化完成")
            
            # 第二优先级：通义千问
            if self.use_tongyi:
                logger.info("初始化通义千问图像生成API")
                # 使用通义千问API，无需加载本地模型
                self.pipeline = None
                self.controlnet = None
                self.canny_detector = None
                self.openpose_detector = None
                logger.info("通义千问图像生成API初始化完成")
            
        except Exception as e:
            logger.error(f"图像生成API初始化失败: {str(e)}")
            # 使用备用方案
            self._initialize_fallback_models()
    
    def _initialize_fallback_models(self):
        """初始化备用模型"""
        try:
            logger.info("使用备用图像生成方案")
            # 这里可以添加备用的图像生成方案
            # 比如使用Replicate API或其他服务
            pass
        except Exception as e:
            logger.error(f"备用模型初始化失败: {str(e)}")
    
    async def _generate_with_tongyi(self, prompt: str, original_image: Image.Image = None) -> Image.Image:
        """使用通义千问API生成图像"""
        try:
            from dashscope import ImageSynthesis
            import dashscope
            
            # 设置API密钥
            dashscope.api_key = settings.tongyi_api_key
            
            # 调用通义千问图像生成API
            # 确保prompt是字符串格式
            if not isinstance(prompt, str):
                prompt = str(prompt)
            
            # 添加超时设置
            import asyncio
            
            def sync_call():
                return ImageSynthesis.call(
                    model='wanx-v1',
                    prompt=prompt,
                    n=1,
                    size='1024*1024'
                )
            
            # 设置60秒超时
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, sync_call),
                timeout=60.0
            )
            
            if response.status_code == 200:
                # 下载生成的图像
                import requests
                from io import BytesIO
                
                image_url = response.output.results[0].url
                img_response = requests.get(image_url, timeout=30)
                img_data = BytesIO(img_response.content)
                
                return Image.open(img_data)
            else:
                raise Exception(f"通义千问图像生成失败: {response.message}")
                
        except Exception as e:
            logger.error(f"通义千问图像生成失败: {str(e)}")
            # 返回原图作为备用
            return original_image if original_image else Image.new('RGB', (512, 512), 'white')
    
    async def generate_final_effect_image(
        self,
        original_image: Image.Image,
        redesign_plan: Dict[str, Any],
        user_requirements: str,
        target_style: str
    ) -> Image.Image:
        """
        生成最终改造效果图
        
        Args:
            original_image: 原始图片
            redesign_plan: 改造计划
            user_requirements: 用户需求
            target_style: 目标风格
            
        Returns:
            Image.Image: 最终效果图
        """
        try:
            # 构建图像生成提示词
            prompt = self._build_final_image_prompt(
                redesign_plan, user_requirements, target_style
            )
            
            # 构建负面提示词（用于约束）
            original_info = redesign_plan.get('original_analysis', {})
            negative_prompt = self._build_negative_prompt(original_info)
            
            # 将负面提示词整合到正面提示词中
            enhanced_prompt = f"{prompt}. Avoid: {negative_prompt}"
            
            logger.info(f"增强的提示词: {enhanced_prompt}")
            
            # 两级降级系统：豆包Seedream4.0 -> 通义千问 -> 备用方案
            result_image = None
            
            # 第一级：尝试豆包Seedream4.0（高质量+国内友好）
            if self.use_doubao:
                try:
                    # 从改造计划中提取分析结果
                    analysis_result = redesign_plan.get('original_analysis', {})
                    result_image = await self.doubao_generator.generate_final_effect_image(
                        analysis_result=analysis_result,
                        user_requirements=user_requirements,
                        target_style=target_style
                    )
                    logger.info("✅ 豆包Seedream4.0 API 生成成功（第一级）")
                except Exception as e:
                    logger.warning(f"⚠️ 豆包Seedream4.0 API 失败: {str(e)}")
                    result_image = None
            
            # 第二级：降级到通义千问（国内友好）
            if result_image is None and self.use_tongyi:
                try:
                    result_image = await self._generate_with_tongyi(enhanced_prompt, original_image)
                    logger.info("✅ 通义千问 API 生成成功（第二级降级）")
                except Exception as e:
                    logger.warning(f"⚠️ 通义千问 API 失败: {str(e)}")
                    result_image = None
            
            # 第三级：最终备用方案
            if result_image is None and self.use_fallback:
                try:
                    result_image = await self._generate_fallback_image(original_image, enhanced_prompt)
                    logger.info("✅ 备用方案生成成功（第三级降级）")
                except Exception as e:
                    logger.error(f"❌ 所有方案都失败: {str(e)}")
                    result_image = original_image  # 返回原图作为最后备用
            
            # 后处理
            result_image = self._post_process_image(result_image, original_image)
            
            logger.info("最终效果图生成完成")
            return result_image
            
        except Exception as e:
            logger.error(f"最终效果图生成失败: {str(e)}")
            raise Exception(f"效果图生成失败: {str(e)}")
    
    async def generate_all_images_in_conversation(
        self,
        source_image_url: str,
        redesign_plan: Dict[str, Any],
        user_requirements: str,
        target_style: str,
        steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """在同一对话中生成最终效果图和步骤图"""
        if self.use_doubao:
            try:
                analysis_result = redesign_plan.get('original_analysis', {})
                return await self.doubao_generator.generate_all_images_in_conversation(
                    analysis_result=analysis_result,
                    steps=steps,
                    source_image_url=source_image_url,
                    user_requirements=user_requirements,
                    target_style=target_style
                )
            except Exception as e:
                logger.warning(f"同会话生成失败，降级到分离模式: {e}")
                # 降级到原有的分离生成模式
                final_image = await self.generate_final_effect_image_from_url(
                    source_image_url, redesign_plan, user_requirements, target_style
                )
                step_images = await self.generate_step_images(
                    original_image=None, steps=steps, base_features=[], 
                    redesign_plan=redesign_plan, final_result_image=final_image
                )
                return {
                    'final_image': final_image,
                    'step_images': step_images,
                    'conversation_context': '降级到分离模式'
                }
        
        raise Exception("豆包生成器不可用")

    async def generate_final_effect_image_from_url(
        self,
        source_image_url: str,
        redesign_plan: Dict[str, Any],
        user_requirements: str,
        target_style: str
    ) -> Image.Image:
        """基于源图URL进行图生图生成，失败则抛出异常"""
        try:
            # 优先使用豆包Ark官方i2i（URL直接传给SDK），失败再下载回退
            if self.use_doubao:
                try:
                    result_image = await self.doubao_generator.generate_final_effect_image_from_url(
                        source_image_url=source_image_url,
                        user_requirements=user_requirements,
                        target_style=target_style
                    )
                    if result_image is not None:
                        return result_image
                except Exception as e:
                    logger.warning(f"豆包Ark i2i重试中: {e}")
                    # 注意：这可能只是重试过程中的失败，最终可能会成功
            # 下载源图，做备用策略
            original_image = await self._download_image_to_pil(source_image_url)
            if original_image is None:
                raise Exception("源图下载失败")
            prompt = self._build_final_image_prompt(
                redesign_plan, user_requirements, target_style
            )
            original_info = redesign_plan.get('original_analysis', {})
            negative_prompt = self._build_negative_prompt(original_info)
            enhanced_prompt = f"{prompt}. Avoid: {negative_prompt}"
            result_image = await self._generate_fallback_image(original_image, enhanced_prompt)
            return self._post_process_image(result_image, original_image)
        except Exception as e:
            logger.error(f"基于URL的图生图失败: {e}")
            raise

    async def generate_final_effect_image_from_local_path(
        self,
        local_path: str,
        redesign_plan: Dict[str, Any],
        user_requirements: str,
        target_style: str
    ) -> Image.Image:
        """优先使用本地文件二进制进行生成（i2i可用则走bytes，否则回退t2i/备用）"""
        try:
            with open(local_path, 'rb') as f:
                image_bytes = f.read()
            # 优先尝试豆包本地bytes入口（当前内部仍回退t2i）
            if self.use_doubao:
                try:
                    result_image = await self.doubao_generator.generate_final_effect_image_from_bytes(
                        image_bytes=image_bytes,
                        user_requirements=user_requirements,
                        target_style=target_style
                    )
                    if result_image is not None:
                        return result_image
                except Exception as e:
                    logger.warning(f"豆包本地bytes生成失败: {e}")
            # 回退：读取为PIL并使用备用增强
            original_image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            prompt = self._build_final_image_prompt(
                redesign_plan, user_requirements, target_style
            )
            original_info = redesign_plan.get('original_analysis', {})
            negative_prompt = self._build_negative_prompt(original_info)
            enhanced_prompt = f"{prompt}. Avoid: {negative_prompt}"
            result_image = await self._generate_fallback_image(original_image, enhanced_prompt)
            return self._post_process_image(result_image, original_image)
        except Exception as e:
            logger.error(f"基于本地路径的生成失败: {e}")
            raise

    async def _download_image_to_pil(self, url: str) -> Optional[Image.Image]:
        """下载远程图片为PIL对象（增强：UA/证书/重试/回退requests）"""
        import ssl
        from io import BytesIO
        import asyncio
        try:
            import aiohttp
            import certifi
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            }
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            timeout = aiohttp.ClientTimeout(total=20)
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(timeout=timeout, connector=connector, headers=headers) as session:
                # 简单重试2次
                for attempt in range(2):
                    try:
                        async with session.get(url, allow_redirects=True) as resp:
                            if resp.status == 200:
                                ctype = resp.headers.get("Content-Type", "")
                                data = await resp.read()
                                if not ctype.startswith("image/"):
                                    # 仍尝试用PIL打开（部分CDN未返回类型）
                                    pass
                                from PIL import Image as PILImage
                                return PILImage.open(BytesIO(data)).convert('RGB')
                            else:
                                logger.warning(f"下载图片失败: HTTP {resp.status} {resp.reason}")
                    except Exception as ie:
                        logger.warning(f"下载尝试失败({attempt+1}/2): {ie}")
                        await asyncio.sleep(0.6 * (attempt+1))
        except Exception as e:
            logger.warning(f"aiohttp下载流程异常: {e}")
        # 回退：requests
        try:
            import requests, certifi
            r = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            }, timeout=20, verify=certifi.where(), allow_redirects=True)
            if r.status_code == 200:
                from PIL import Image as PILImage
                return PILImage.open(BytesIO(r.content)).convert('RGB')
            else:
                logger.warning(f"requests下载失败: HTTP {r.status_code}")
        except Exception as e:
            logger.warning(f"requests回退失败: {e}")
        return None
    
    async def generate_step_images(
        self,
        original_image: Image.Image,
        steps: List[Dict[str, Any]],
        base_features: List[str],
        redesign_plan: Dict[str, Any] = None,
        final_result_image: Optional[Image.Image] = None
    ) -> List[Image.Image]:
        """
        生成各步骤的改造示意图
        
        Args:
            original_image: 原始图片
            steps: 改造步骤列表
            base_features: 原图特征
            
        Returns:
            List[Image.Image]: 步骤图像列表
        """
        try:
            step_images = []
            
            for i, step in enumerate(steps):
                logger.info(f"生成第 {i+1} 步图像: {step.get('title', '未知步骤')}")
                
                # 为每个步骤生成图像 - 两级降级系统
                step_image = None
                
                # 第一级：尝试豆包Seedream4.0
                if self.use_doubao:
                    try:
                        # 从改造计划中提取分析结果
                        analysis_result = redesign_plan.get('original_analysis', {}) if redesign_plan else {}
                        # 尝试获取源图URL（用于图生图）
                        source_image_url = redesign_plan.get('source_image_url') if redesign_plan else None
                        logger.info(f"🔍 调试：redesign_plan keys = {list(redesign_plan.keys()) if redesign_plan else 'None'}")
                        logger.info(f"🔍 调试：source_image_url from plan = {source_image_url}")
                        step_images = await self.doubao_generator.generate_step_images(
                            analysis_result=analysis_result,
                            steps=[step],
                            source_image_url=source_image_url,  # 传入源图URL进行图生图
                            final_result_image=final_result_image  # 传入最终效果图作为目标引导
                        )
                        step_image = step_images[0] if step_images else None
                        if step_image:
                            logger.info(f"✅ 豆包Seedream4.0 步骤 {i+1} 生成成功")
                    except Exception as e:
                        logger.warning(f"⚠️ 豆包Seedream4.0 步骤 {i+1} 失败: {str(e)}")
                        step_image = None
                
                # 第二级：降级到通义千问
                if step_image is None and self.use_tongyi:
                    try:
                        step_prompt = step.get('image_prompt', f"step {i+1}: {step.get('title', '改造步骤')}")
                        step_image = await self._generate_with_tongyi(step_prompt, original_image)
                        if step_image:
                            logger.info(f"✅ 通义千问 步骤 {i+1} 生成成功")
                    except Exception as e:
                        logger.warning(f"⚠️ 通义千问 步骤 {i+1} 失败: {str(e)}")
                        step_image = None
                
                # 第三级：最终备用方案
                if step_image is None:
                    try:
                        step_image = await self._generate_step_image(
                            original_image, step, base_features, i
                        )
                        logger.info(f"✅ 备用方案 步骤 {i+1} 生成成功")
                    except Exception as e:
                        logger.warning(f"⚠️ 备用方案 步骤 {i+1} 失败: {str(e)}")
                        step_image = original_image
                
                step_images.append(step_image)
            
            logger.info(f"所有步骤图像生成完成，共 {len(step_images)} 张")
            return step_images
            
        except Exception as e:
            logger.error(f"步骤图像生成失败: {str(e)}")
            raise Exception(f"步骤图像生成失败: {str(e)}")
    
    def _extract_control_structure(self, image: Image.Image) -> Image.Image:
        """提取结构控制信息"""
        try:
            # 转换为numpy数组
            img_array = np.array(image)
            
            # 使用Canny边缘检测提取结构
            canny_image = self.canny_detector(img_array)
            
            # 转换为PIL图像
            control_image = Image.fromarray(canny_image)
            
            return control_image
            
        except Exception as e:
            logger.error(f"结构提取失败: {str(e)}")
            # 返回原图作为备用
            return image
    
    def _build_final_image_prompt(
        self,
        redesign_plan: Dict[str, Any],
        user_requirements: str,
        target_style: str
    ) -> str:
        """构建最终图像提示词"""
        
        # 从改造计划中提取原物信息
        original_info = redesign_plan.get('original_analysis', {})
        main_objects = original_info.get('main_objects', ['furniture'])
        materials = original_info.get('materials', [])
        colors = original_info.get('colors', [])
        structure = original_info.get('structure', '')
        condition = original_info.get('condition', '')
        
        # 构建具体的物品描述
        item_type = main_objects[0] if main_objects else 'furniture'
        material_desc = ', '.join(materials) if materials else 'wood'
        color_desc = ', '.join(colors) if colors else 'natural'
        
        # 增强的创意提示词结构
        prompt_parts = []
        
        # 1. 创意改造描述
        prompt_parts.append(f"Creative renovation of {item_type}")
        prompt_parts.append("innovative upcycling design")
        prompt_parts.append("unique functional transformation")
        
        # 2. 保持原有材质和颜色
        if materials:
            prompt_parts.append(f"preserving original {material_desc} material")
        if colors:
            prompt_parts.append(f"maintaining {color_desc} color palette")
        
        # 3. 结构改造重点
        prompt_parts.append("dramatic structural transformation")
        prompt_parts.append("functional redesign with aesthetic appeal")
        if user_requirements:
            prompt_parts.append(f"specifically designed for {user_requirements}")
        
        # 4. 创意元素
        prompt_parts.append("creative use of existing components")
        prompt_parts.append("innovative assembly and arrangement")
        prompt_parts.append("artistic yet practical design")
        
        # 5. 视觉质量
        prompt_parts.append("high-quality craftsmanship")
        prompt_parts.append("professional finish and attention to detail")
        prompt_parts.append("visually striking and unique appearance")
        
        # 6. 现实性约束
        prompt_parts.append("realistic and achievable design")
        prompt_parts.append("practical for everyday use")
        prompt_parts.append("appropriate proportions and scale")
        
        # 7. 摄影质量
        prompt_parts.append("studio photography, clean background")
        prompt_parts.append("professional lighting, high resolution")
        prompt_parts.append("sharp focus, excellent composition")
        
        # 8. 无文字要求
        prompt_parts.append("no text, no labels, no watermarks, clean image without any text elements")
        
        # 组合完整提示词
        full_prompt = ', '.join(prompt_parts)
        
        # 清理多余的逗号和空格
        full_prompt = ', '.join([part.strip() for part in full_prompt.split(',') if part.strip()])
        
        logger.info(f"生成的图像提示词: {full_prompt}")
        
        return full_prompt
    
    def _build_negative_prompt(self, original_info: Dict[str, Any]) -> str:
        """构建负面提示词，避免不想要的元素"""
        
        main_objects = original_info.get('main_objects', ['furniture'])
        item_type = main_objects[0] if main_objects else 'furniture'
        
        # 基础负面提示词
        negative_parts = [
            "low quality", "blurry", "distorted", "unrealistic", "unsafe",
            "harmful materials", "toxic", "dangerous", "broken", "damaged",
            "incomplete", "partial", "cut off", "cropped", "weird proportions",
            "unrealistic colors", "artificial", "fake", "synthetic",
            "overly bright", "overly dark", "poor lighting", "bad composition"
        ]
        
        # 只避免完全不相关的物品类型（允许创意改造）
        # 注释掉过于严格的限制，允许更大的创意空间
        # if item_type != 'furniture':
        #     negative_parts.append(f"different furniture type")
        #     negative_parts.append(f"not a {item_type}")
        
        # 只避免完全错误的结构，允许创意改造
        negative_parts.extend([
            "wrong size", "incorrect scale"
        ])
        
        # 避免不实用和奇怪的设计
        negative_parts.extend([
            "cluttered", "messy", "chaotic", "abstract art", "sculpture", "non-functional", 
            "impractical", "unusable", "weird geometry", "strange shapes", "artistic installation",
            "museum piece", "decorative only", "non-furniture", "abstract design"
        ])
        
        negative_prompt = ', '.join(negative_parts)
        logger.info(f"生成的负面提示词: {negative_prompt}")
        
        return negative_prompt
    
    async def _generate_with_controlnet(
        self,
        control_image: Image.Image,
        prompt: str,
        original_image: Image.Image
    ) -> Image.Image:
        """使用ControlNet生成图像"""
        try:
            prompt_text, negative_prompt = prompt if isinstance(prompt, tuple) else (prompt, "")
            
            # 生成图像
            result = self.pipeline(
                prompt=prompt_text,
                image=control_image,
                negative_prompt=negative_prompt,
                num_inference_steps=20,
                guidance_scale=7.5,
                controlnet_conditioning_scale=0.8,
                height=512,
                width=512
            )
            
            return result.images[0]
            
        except Exception as e:
            logger.error(f"ControlNet生成失败: {str(e)}")
            raise
    
    async def _generate_fallback_image(
        self,
        original_image: Image.Image,
        prompt: str
    ) -> Image.Image:
        """使用备用方案生成图像"""
        try:
            # 这里可以实现备用的图像生成方案
            # 比如调用外部API或使用其他模型
            
            # 暂时返回原图的修改版本
            img_array = np.array(original_image)
            
            # 简单的图像处理作为示例
            # 调整亮度、对比度等
            img_array = cv2.convertScaleAbs(img_array, alpha=1.2, beta=10)
            
            return Image.fromarray(img_array)
            
        except Exception as e:
            logger.error(f"备用图像生成失败: {str(e)}")
            return original_image
    
    async def _generate_step_image(
        self,
        original_image: Image.Image,
        step: Dict[str, Any],
        base_features: List[str],
        step_index: int
    ) -> Image.Image:
        """生成单个步骤图像"""
        try:
            # 获取步骤的图像提示词
            step_prompt = step.get('image_prompt', '')
            if not step_prompt:
                step_prompt = f"step {step_index + 1}: {step.get('title', '改造步骤')}"
            
            # 添加环保风格
            eco_prompt = settings.eco_style_prompt
            full_prompt = f"{step_prompt}, {eco_prompt}, detailed, step by step process"
            
            # 生成图像
            if self.pipeline:
                # 使用ControlNet生成
                control_image = self._extract_control_structure(original_image)
                result = await self._generate_with_controlnet(
                    control_image, full_prompt, original_image
                )
            else:
                # 使用备用方案
                result = await self._generate_fallback_image(original_image, full_prompt)
            
            return result
            
        except Exception as e:
            logger.error(f"步骤图像生成失败: {str(e)}")
            return original_image
    
    def _post_process_image(
        self,
        generated_image: Image.Image,
        original_image: Image.Image
    ) -> Image.Image:
        """后处理生成的图像"""
        try:
            # 调整图像大小以匹配原图
            if generated_image.size != original_image.size:
                generated_image = generated_image.resize(
                    original_image.size, Image.Resampling.LANCZOS
                )
            
            # 应用一些后处理效果
            # 比如锐化、色彩调整等
            img_array = np.array(generated_image)
            
            # 轻微锐化
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            img_array = cv2.filter2D(img_array, -1, kernel)
            
            # 确保像素值在有效范围内
            img_array = np.clip(img_array, 0, 255).astype(np.uint8)
            
            return Image.fromarray(img_array)
            
        except Exception as e:
            logger.error(f"图像后处理失败: {str(e)}")
            return generated_image
    
    def save_image(self, image: Image.Image, filename: str) -> str:
        """保存图像到文件"""
        try:
            # 确保用户输出目录存在
            output_dir = "static/users/user1/output"
            os.makedirs(output_dir, exist_ok=True)
            
            # 构建完整路径
            filepath = os.path.join(output_dir, filename)
            
            # 保存图像
            image.save(filepath, "JPEG", quality=settings.image_quality)
            
            logger.info(f"图像已保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"图像保存失败: {str(e)}")
            raise Exception(f"图像保存失败: {str(e)}")
    
    def image_to_base64(self, image: Image.Image) -> str:
        """将图像转换为base64字符串"""
        try:
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=settings.image_quality)
            img_bytes = buffer.getvalue()
            return base64.b64encode(img_bytes).decode()
        except Exception as e:
            logger.error(f"图像转base64失败: {str(e)}")
            raise Exception(f"图像转base64失败: {str(e)}")
    
    def validate_generation_requirements(self) -> bool:
        """验证图像生成环境要求"""
        try:
            # 如果使用通义千问API，直接返回True
            if self.use_tongyi:
                return True
            
            # 检查CUDA可用性
            if self.device == "cuda":
                if not torch.cuda.is_available():
                    logger.warning("CUDA不可用，将使用CPU")
                    return False
            
            # 检查模型是否加载
            if not self.pipeline:
                logger.warning("图像生成模型未加载")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"环境验证失败: {str(e)}")
            return False
