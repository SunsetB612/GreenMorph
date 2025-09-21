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

from config import settings


class ImageGenerator:
    """图像生成器"""
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipeline = None
        self.controlnet = None
        self.canny_detector = None
        self.openpose_detector = None
        self.use_tongyi = True  # 使用通义千问API
        self._initialize_models()
    
    def _initialize_models(self):
        """初始化图像生成模型"""
        try:
            logger.info("初始化通义千问图像生成API")
            # 使用通义千问API，无需加载本地模型
            self.pipeline = None
            self.controlnet = None
            self.canny_detector = None
            self.openpose_detector = None
            logger.info("通义千问图像生成API初始化完成")
            
        except Exception as e:
            logger.error(f"通义千问API初始化失败: {str(e)}")
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
            
            # 调用通义千问图像生成API
            # 确保prompt是字符串格式
            if not isinstance(prompt, str):
                prompt = str(prompt)
            
            response = ImageSynthesis.call(
                model='wanx-v1',
                prompt=prompt,
                n=1,
                size='1024*1024'
            )
            
            if response.status_code == 200:
                # 下载生成的图像
                import requests
                from io import BytesIO
                
                image_url = response.output.results[0].url
                img_response = requests.get(image_url)
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
            
            # 使用通义千问生成图像
            if self.use_tongyi:
                result_image = await self._generate_with_tongyi(prompt, original_image)
            else:
                # 使用备用方案
                result_image = await self._generate_fallback_image(
                    original_image, prompt
                )
            
            # 后处理
            result_image = self._post_process_image(result_image, original_image)
            
            logger.info("最终效果图生成完成")
            return result_image
            
        except Exception as e:
            logger.error(f"最终效果图生成失败: {str(e)}")
            raise Exception(f"效果图生成失败: {str(e)}")
    
    async def generate_step_images(
        self,
        original_image: Image.Image,
        steps: List[Dict[str, Any]],
        base_features: List[str]
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
                
                # 为每个步骤生成图像
                if self.use_tongyi:
                    step_prompt = step.get('image_prompt', f"step {i+1}: {step.get('title', '改造步骤')}")
                    step_image = await self._generate_with_tongyi(step_prompt, original_image)
                else:
                    step_image = await self._generate_step_image(
                        original_image, step, base_features, i
                    )
                
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
        
        # 基础提示词
        base_prompt = f"upcycled furniture, {target_style} style, {user_requirements}"
        
        # 添加环保元素
        eco_elements = settings.eco_style_prompt
        
        # 添加质量描述
        quality_prompt = "high quality, detailed, professional photography, studio lighting"
        
        # 组合提示词
        full_prompt = f"{base_prompt}, {eco_elements}, {quality_prompt}"
        
        # 负面提示词
        negative_prompt = "low quality, blurry, distorted, unrealistic, unsafe, harmful materials"
        
        return full_prompt, negative_prompt
    
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
            # 确保输出目录存在
            os.makedirs(settings.output_dir, exist_ok=True)
            
            # 构建完整路径
            filepath = os.path.join(settings.output_dir, filename)
            
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
