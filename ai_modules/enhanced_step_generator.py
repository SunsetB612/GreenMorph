"""
增强版步骤图生成器
解决步骤图质量差和数量少的问题
"""

import asyncio
from typing import List, Dict, Any, Optional
from PIL import Image
import io
import base64
from loguru import logger
from ai_modules.doubao_generator import DoubaoSeedreamGenerator
from ai_modules.image_generator import ImageGenerator


class EnhancedStepGenerator:
    """增强版步骤图生成器"""
    
    def __init__(self):
        self.doubao_generator = DoubaoSeedreamGenerator()
        self.image_generator = ImageGenerator()
    
    async def generate_enhanced_step_images(
        self,
        original_image: Image.Image,
        final_image: Image.Image,
        steps: List[Dict[str, Any]],
        user_requirements: str,
        target_style: str
    ) -> List[Image.Image]:
        """
        生成增强版步骤图
        
        Args:
            original_image: 原始图片
            final_image: 最终效果图
            steps: 改造步骤列表
            user_requirements: 用户需求
            target_style: 目标风格
            
        Returns:
            List[Image.Image]: 步骤图列表
        """
        try:
            logger.info(f"🎨 开始生成增强版步骤图，共{len(steps)}个步骤")
            
            step_images = []
            current_image = original_image.copy()
            
            for i, step in enumerate(steps):
                step_num = i + 1
                total_steps = len(steps)
                progress = step_num / total_steps
                
                logger.info(f"🔧 生成步骤{step_num}/{total_steps}: {step.get('title', '未知步骤')}")
                
                # 生成单个步骤图
                step_image = await self._generate_single_step_image(
                    current_image=current_image,
                    final_image=final_image,
                    step=step,
                    step_num=step_num,
                    total_steps=total_steps,
                    progress=progress,
                    user_requirements=user_requirements,
                    target_style=target_style
                )
                
                step_images.append(step_image)
                
                # 更新当前图像为下一步的输入
                current_image = step_image.copy()
                
                logger.info(f"✅ 步骤{step_num}生成完成")
            
            logger.info(f"🎉 所有步骤图生成完成，共{len(step_images)}张")
            return step_images
            
        except Exception as e:
            logger.error(f"❌ 增强版步骤图生成失败: {e}")
            return []
    
    async def _generate_single_step_image(
        self,
        current_image: Image.Image,
        final_image: Image.Image,
        step: Dict[str, Any],
        step_num: int,
        total_steps: int,
        progress: float,
        user_requirements: str,
        target_style: str
    ) -> Image.Image:
        """生成单个步骤图"""
        try:
            # 构建详细的步骤提示词
            step_prompt = self._build_enhanced_step_prompt(
                step=step,
                step_num=step_num,
                total_steps=total_steps,
                progress=progress,
                user_requirements=user_requirements,
                target_style=target_style
            )
            
            # 使用豆包Seedream4.0生成步骤图
            step_image = await self._generate_with_doubao(
                current_image=current_image,
                prompt=step_prompt,
                step_num=step_num
            )
            
            return step_image
            
        except Exception as e:
            logger.error(f"❌ 步骤{step_num}生成失败: {e}")
            # 返回当前图像作为备用
            return current_image
    
    def _build_enhanced_step_prompt(
        self,
        step: Dict[str, Any],
        step_num: int,
        total_steps: int,
        progress: float,
        user_requirements: str,
        target_style: str
    ) -> str:
        """构建增强版步骤提示词"""
        
        step_title = step.get('title', f'步骤{step_num}')
        step_description = step.get('description', '')
        materials = step.get('materials_needed', [])
        tools = step.get('tools_needed', [])
        
        # 简化的提示词，与渐进式生成器保持一致
        prompt = f"""你是一个专业的旧物改造设计师。请根据以下要求进行改造：

【当前任务】: {step_title}
【任务描述】: {step_description}
【改造进度】: {step_num}/{total_steps} ({progress*100:.0f}%)

【改造要求】:
1. 基于输入图片的当前状态进行改造
2. 只对当前步骤指定的部分进行改造
3. 保持物品的基本结构不变
4. 确保改造结果与目标风格一致
5. 保持改造的连贯性和逻辑性
6. 不要包含任何文字、标签、水印或文本元素
7. 生成纯图像内容，无文字覆盖

【目标风格】: {target_style}
【用户需求】: {user_requirements}

【所需材料】: {', '.join(materials) if materials else '基础材料'}
【所需工具】: {', '.join(tools) if tools else '基础工具'}

请生成高质量的改造步骤图，确保与最终目标方向一致，图像干净无文字。"""
        
        return prompt
    
    async def _generate_with_doubao(
        self,
        current_image: Image.Image,
        prompt: str,
        step_num: int
    ) -> Image.Image:
        """使用豆包Seedream4.0生成步骤图"""
        try:
            # 将图像转换为base64
            img_buffer = io.BytesIO()
            current_image.save(img_buffer, format='JPEG', quality=95)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            # 使用豆包API生成
            response = self.doubao_generator.client.images.generate(
                model="doubao-seedream-4-0-250828",
                prompt=prompt,
                image=img_base64,
                size="2K",
                response_format="url",
                watermark=True
            )
            
            if response.data and response.data[0].url:
                # 下载生成的图像
                step_image = await self.doubao_generator._download_image(response.data[0].url)
                return step_image
            else:
                logger.warning(f"⚠️ 步骤{step_num}生成失败，使用当前图像")
                return current_image
                
        except Exception as e:
            logger.error(f"❌ 豆包API调用失败: {e}")
            return current_image
    
    async def generate_step_comparison(
        self,
        original_image: Image.Image,
        step_images: List[Image.Image],
        final_image: Image.Image,
        steps: List[Dict[str, Any]]
    ) -> Image.Image:
        """生成步骤对比图"""
        try:
            logger.info("🔄 生成步骤对比图")
            
            # 创建对比画布
            canvas_width = 1200
            canvas_height = 800
            canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
            
            # 计算每个图像的尺寸
            img_width = 200
            img_height = 150
            spacing = 20
            
            # 绘制标题
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(canvas)
            title_font = ImageFont.load_default()
            draw.text((20, 20), "改造步骤对比图", fill='black', font=title_font)
            
            # 绘制原图
            original_resized = original_image.resize((img_width, img_height), Image.Resampling.LANCZOS)
            canvas.paste(original_resized, (20, 60))
            draw.text((20, 220), "原图", fill='black', font=title_font)
            
            # 绘制步骤图
            for i, (step_img, step) in enumerate(zip(step_images, steps)):
                x = 20 + (i + 1) * (img_width + spacing)
                y = 60
                
                step_resized = step_img.resize((img_width, img_height), Image.Resampling.LANCZOS)
                canvas.paste(step_resized, (x, y))
                
                # 步骤标题
                step_title = step.get('title', f'步骤{i+1}')
                draw.text((x, 220), step_title, fill='black', font=title_font)
            
            # 绘制最终效果图
            final_x = 20 + (len(step_images) + 1) * (img_width + spacing)
            final_resized = final_image.resize((img_width, img_height), Image.Resampling.LANCZOS)
            canvas.paste(final_resized, (final_x, 60))
            draw.text((final_x, 220), "最终效果", fill='black', font=title_font)
            
            logger.info("✅ 步骤对比图生成完成")
            return canvas
            
        except Exception as e:
            logger.error(f"❌ 步骤对比图生成失败: {e}")
            return original_image
    
    async def generate_enhanced_visualization(
        self,
        original_image: Image.Image,
        step_images: List[Image.Image],
        final_image: Image.Image,
        steps: List[Dict[str, Any]]
    ) -> Image.Image:
        """生成增强版可视化图"""
        try:
            logger.info("🎨 生成增强版可视化图")
            
            # 创建大画布
            canvas_width = 1600
            canvas_height = 1000
            canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
            
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(canvas)
            
            # 绘制标题
            title_font = ImageFont.load_default()
            draw.text((20, 20), "GreenMorph 改造步骤详解", fill='#2E8B57', font=title_font)
            
            # 绘制步骤网格
            cols = 4  # 每行4个图像
            img_width = 300
            img_height = 200
            spacing = 20
            
            all_images = [original_image] + step_images + [final_image]
            all_labels = ["原图"] + [f"步骤{i+1}" for i in range(len(step_images))] + ["最终效果"]
            
            for i, (img, label) in enumerate(zip(all_images, all_labels)):
                row = i // cols
                col = i % cols
                
                x = 20 + col * (img_width + spacing)
                y = 80 + row * (img_height + 60)
                
                # 调整图像大小
                img_resized = img.resize((img_width, img_height), Image.Resampling.LANCZOS)
                canvas.paste(img_resized, (x, y))
                
                # 绘制标签
                draw.text((x, y + img_height + 10), label, fill='black', font=title_font)
                
                # 绘制步骤信息
                if i > 0 and i <= len(step_images):
                    step = steps[i-1]
                    step_title = step.get('title', f'步骤{i}')
                    step_desc = step.get('description', '')[:50] + '...' if len(step.get('description', '')) > 50 else step.get('description', '')
                    
                    # 绘制步骤标题
                    draw.text((x, y + img_height + 30), step_title, fill='#2E8B57', font=title_font)
                    
                    # 绘制步骤描述
                    if step_desc:
                        draw.text((x, y + img_height + 50), step_desc, fill='#666666', font=title_font)
            
            logger.info("✅ 增强版可视化图生成完成")
            return canvas
            
        except Exception as e:
            logger.error(f"❌ 增强版可视化图生成失败: {e}")
            return original_image
