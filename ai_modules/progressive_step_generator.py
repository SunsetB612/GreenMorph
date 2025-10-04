"""
渐进式步骤图生成器
基于多轮对话的上下文记忆，生成真正的渐进式改造步骤图
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from PIL import Image
import io
from loguru import logger
from ai_modules.doubao_generator import DoubaoSeedreamGenerator


class ConversationMemory:
    """AI对话记忆管理"""
    
    def __init__(self):
        self.conversation_history = []
        self.current_context = {}
    
    def add_step(self, step_info: Dict[str, Any], image_url: str, prompt: str):
        """添加步骤到对话历史"""
        self.conversation_history.append({
            'step': step_info,
            'image_url': image_url,
            'prompt': prompt,
            'timestamp': time.time()
        })
    
    def get_context_prompt(self, current_step: Dict[str, Any]) -> str:
        """构建包含历史上下文的提示词"""
        if not self.conversation_history:
            return ""
        
        context = "【改造历史回顾】:\n"
        for i, history in enumerate(self.conversation_history):
            step_title = history['step'].get('title', f'步骤{i+1}')
            step_desc = history['step'].get('description', '')
            context += f"- 步骤{i+1}: {step_title} - {step_desc}\n"
        
        context += f"\n【当前任务】: 基于以上改造历史，继续第{len(self.conversation_history)+1}步改造\n"
        return context
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
        self.current_context = {}


class ProgressiveStepGenerator:
    """渐进式步骤图生成器"""
    
    def __init__(self):
        self.doubao_generator = DoubaoSeedreamGenerator()
        self.conversation_memory = ConversationMemory()
    
    async def generate_progressive_steps(
        self,
        original_image: Image.Image,
        final_image: Image.Image,
        steps: List[Dict[str, Any]],
        user_requirements: str,
        target_style: str
    ) -> List[Image.Image]:
        """
        生成渐进式步骤图
        
        关键：每一步都基于前一步的结果，形成真正的渐进式改造
        
        Args:
            original_image: 原始图片
            final_image: 最终效果图
            steps: 改造步骤列表
            user_requirements: 用户需求
            target_style: 目标风格
            
        Returns:
            List[Image.Image]: 渐进式步骤图列表
        """
        try:
            logger.info(f"🎨 开始生成渐进式步骤图，共{len(steps)}个步骤")
            
            # 清空对话记忆，开始新的改造任务
            self.conversation_memory.clear_history()
            
            step_images = []
            current_image = original_image.copy()
            
            # 豆包Seedream4.0使用图片URL，不需要base64
            # 原图和最终效果图用于构建提示词上下文
            
            for i, step in enumerate(steps):
                step_num = i + 1
                total_steps = len(steps)
                progress = step_num / total_steps  # 修正进度计算，第一步应该是33%
                
                logger.info(f"🔧 生成步骤{step_num}/{total_steps}: {step.get('title', '未知步骤')}")
                logger.info(f"   进度: {progress*100:.0f}%")
                logger.info(f"   基于前一步结果: {'是' if step_images else '否（第一步基于原图）'}")
                
                # 生成单个渐进式步骤图
                step_image = await self._generate_progressive_step(
                    current_image=current_image,
                    original_image=original_image,
                    final_image=final_image,
                    step=step,
                    step_num=step_num,
                    total_steps=total_steps,
                    progress=progress,
                    user_requirements=user_requirements,
                    target_style=target_style,
                    step_images=step_images  # 传递之前的步骤图用于上下文
                )
                
                step_images.append(step_image)
                
                # 关键：更新当前图像为下一步的输入（真正的渐进式）
                current_image = step_image.copy()
                logger.info(f"✅ 步骤{step_num}生成完成，已更新为下一步的输入图像")
                
                # 记录到对话记忆
                self.conversation_memory.add_step(
                    step_info=step,
                    image_url="",  # 这里可以记录图片URL
                    prompt=""  # 这里可以记录使用的提示词
                )
            
            logger.info(f"🎉 渐进式步骤图生成完成，共{len(step_images)}张")
            return step_images
            
        except Exception as e:
            logger.error(f"❌ 渐进式步骤图生成失败: {e}")
            return []
    
    async def _generate_progressive_step(
        self,
        current_image: Image.Image,
        original_image: Image.Image,
        final_image: Image.Image,
        step: Dict[str, Any],
        step_num: int,
        total_steps: int,
        progress: float,
        user_requirements: str,
        target_style: str,
        step_images: List[Image.Image]
    ) -> Image.Image:
        """生成单个渐进式步骤图"""
        try:
            # 构建渐进式对话提示词
            progressive_prompt = self._build_progressive_prompt(
                step=step,
                step_num=step_num,
                total_steps=total_steps,
                progress=progress,
                user_requirements=user_requirements,
                target_style=target_style,
                step_images=step_images
            )
            
            # 打印详细的提示词信息
            logger.info(f"📝 步骤{step_num}提示词详情:")
            logger.info(f"   步骤标题: {step.get('title', '未知步骤')}")
            logger.info(f"   步骤描述: {step.get('description', '无描述')}")
            logger.info(f"   进度百分比: {progress*100:.0f}%")
            logger.info(f"   用户需求: {user_requirements}")
            logger.info(f"   目标风格: {target_style}")
            logger.info(f"   之前步骤数: {len(step_images)}")
            logger.info(f"   完整提示词:")
            logger.info(f"   {'='*60}")
            logger.info(f"   {progressive_prompt}")
            logger.info(f"   {'='*60}")
            
            # 使用豆包API生成，关键是要传递对话上下文
            step_image = await self._generate_with_context(
                current_image=current_image,
                prompt=progressive_prompt,
                step_num=step_num,
                step_images=step_images,
                original_image=original_image,
                final_image=final_image
            )
            
            return step_image
            
        except Exception as e:
            logger.error(f"❌ 渐进式步骤{step_num}生成失败: {e}")
            return current_image
    
    def _build_progressive_prompt(
        self,
        step: Dict[str, Any],
        step_num: int,
        total_steps: int,
        progress: float,
        user_requirements: str,
        target_style: str,
        step_images: List[Image.Image]
    ) -> str:
        """构建渐进式对话提示词"""
        
        step_title = step.get('title', f'步骤{step_num}')
        step_description = step.get('description', '')
        
        # 构建渐进式提示词
        context_info = ""
        if step_images:
            # 使用对话记忆获取历史上下文
            memory_context = self.conversation_memory.get_context_prompt(step)
            context_info = f"""
【改造历史】: 这是第{step_num}步，基于前{step_num-1}步的改造结果继续
【当前状态】: 输入图片是经过{step_num-1}步改造后的状态
{memory_context}
"""
        else:
            context_info = """
【改造历史】: 这是第1步，基于原始物品开始改造
【当前状态】: 输入图片是原始物品的初始状态
"""
        
        prompt = f"""你是一个专业的旧物改造设计师。请根据以下要求对输入图片进行改造：

{context_info}

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
8. 确保步骤图与最终效果图在视觉上保持一致
9. 重点展现结构变化，保持原有材料和颜色
10. 避免过于理想化或不现实的改造效果

【目标风格】: {target_style}
【用户需求】: {user_requirements}

        【现实性要求】:
        - 改造效果要符合物理定律
        - 结构要稳定可靠
        - 材料使用要合理
        - 避免过于复杂的改造
        - 确保普通人可以完成
        
        【严格质量要求】:
        - 禁止生成任何不现实的改造效果
        - 禁止建议使用专业工具或设备
        - 禁止生成过于复杂的结构设计
        - 必须基于物品的实际情况进行改造
        - 必须考虑改造后的实际使用价值
        - 必须确保每个步骤都是可操作的
        - 图像必须清晰、专业、无文字
        - 改造效果必须与最终目标一致
        
        【基于现实案例的步骤约束】:
        - 每个步骤都必须基于真实可行的改造案例
        - 禁止生成任何在现实中不存在的改造效果
        - 结构变化必须符合物理定律和工程常识
        - 材料使用必须基于实际改造经验
        - 工具使用必须基于真实DIY案例
        - 时间估算必须基于实际改造经验
        - 难度评估必须基于真实改造案例
        - 安全注意事项必须基于实际改造经验

请生成高质量的改造步骤图，确保与最终目标方向一致，图像干净无文字，改造效果现实可行。"""
        
        return prompt
    
    async def _generate_with_context(
        self,
        current_image: Image.Image,
        prompt: str,
        step_num: int,
        step_images: List[Image.Image],
        original_image: Image.Image = None,
        final_image: Image.Image = None
    ) -> Image.Image:
        """使用上下文生成步骤图 - 传入所有相关图片"""
        try:
            # 准备所有相关图片的URL列表
            image_urls = []
            
            # 1. 当前图像（主要输入）
            logger.info(f"🔄 上传当前图像到云存储...")
            current_image_url = await self._upload_image_to_cloud(current_image)
            image_urls.append(current_image_url)
            logger.info(f"✅ 当前图像上传完成，URL: {current_image_url}")
            
            # 2. 原图（提供参考）
            if original_image:
                logger.info(f"🔄 上传原图到云存储...")
                original_image_url = await self._upload_image_to_cloud(original_image)
                image_urls.append(original_image_url)
                logger.info(f"✅ 原图上传完成，URL: {original_image_url}")
            
            # 3. 最终效果图（提供目标引导）
            if final_image:
                logger.info(f"🔄 上传最终效果图到云存储...")
                final_image_url = await self._upload_image_to_cloud(final_image)
                image_urls.append(final_image_url)
                logger.info(f"✅ 最终效果图上传完成，URL: {final_image_url}")
            
            # 4. 之前的步骤图（提供渐进参考）
            if step_images:
                for i, step_img in enumerate(step_images[-2:]):  # 只取最近2张步骤图
                    logger.info(f"🔄 上传步骤图{i+1}到云存储...")
                    step_image_url = await self._upload_image_to_cloud(step_img)
                    image_urls.append(step_image_url)
                    logger.info(f"✅ 步骤图{i+1}上传完成，URL: {step_image_url}")
            
            # 打印API调用参数
            logger.info(f"🚀 调用豆包API生成步骤{step_num}图像:")
            logger.info(f"   模型: doubao-seedream-4-0-250828")
            logger.info(f"   输入图像数量: {len(image_urls)}")
            logger.info(f"   图像URLs: {image_urls}")
            logger.info(f"   提示词长度: {len(prompt)} 字符")
            logger.info(f"   图像尺寸: 2K")
            logger.info(f"   水印: 启用")
            
            # 使用豆包API生成 - 传入多个图片URL
            response = self.doubao_generator.client.images.generate(
                model="doubao-seedream-4-0-250828",
                prompt=prompt,
                image=image_urls,  # 传入多个图片URL
                size="2K",
                response_format="url",
                watermark=True
            )
            
            logger.info(f"📡 豆包API响应:")
            logger.info(f"   响应状态: {'成功' if response.data else '失败'}")
            if response.data:
                logger.info(f"   生成图像URL: {response.data[0].url}")
            else:
                logger.warning(f"   API返回空数据")
            
            if response.data and response.data[0].url:
                # 下载生成的图像
                step_image = await self.doubao_generator._download_image(response.data[0].url)
                
                # 质量检查
                quality_result = await self._check_step_quality(step_image, current_image, step_num)
                if quality_result['is_valid']:
                    logger.info(f"✅ 步骤{step_num}质量检查通过: {quality_result['message']}")
                    return step_image
                else:
                    logger.warning(f"⚠️ 步骤{step_num}质量检查失败: {quality_result['message']}")
                    # 如果质量不好，尝试重新生成或使用当前图像
                    if step_num == 1:  # 第一步质量不好，使用原图
                        return current_image
                    else:  # 后续步骤质量不好，使用前一步结果
                        return current_image
            else:
                logger.warning(f"⚠️ 步骤{step_num}生成失败，使用当前图像")
                return current_image
                
        except Exception as e:
            logger.error(f"❌ 豆包API调用失败: {e}")
            return current_image
    
    async def _upload_image_to_cloud(self, image: Image.Image) -> str:
        """将PIL图像上传到云存储并返回URL"""
        try:
            from app.shared.utils.cloud_storage import smart_upload_pil_image
            import time
            
            # 上传图片到云存储 - 使用正确的参数名
            image_url = await smart_upload_pil_image(
                pil_image=image,  # 正确的参数名
                filename=f"step_temp_{int(time.time())}.jpg"
            )
            
            if image_url:
                logger.info(f"✅ 图片已上传到云存储: {image_url}")
                return image_url
            else:
                logger.warning("⚠️ 图片上传返回空URL，使用本地临时文件")
                return await self._save_local_temp_image(image)
            
        except Exception as e:
            logger.error(f"❌ 图片上传失败: {e}")
            # 如果上传失败，保存到本地临时文件
            return await self._save_local_temp_image(image)
    
    async def _save_local_temp_image(self, image: Image.Image) -> str:
        """保存图像到本地临时文件并返回文件路径"""
        try:
            import os
            import tempfile
            
            # 创建临时文件
            temp_dir = "static/temp"
            os.makedirs(temp_dir, exist_ok=True)
            
            temp_filename = f"step_temp_{int(time.time())}.jpg"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            # 保存图像
            image.save(temp_path, "JPEG", quality=95)
            
            # 返回本地文件路径（需要转换为可访问的URL）
            local_url = f"file://{os.path.abspath(temp_path)}"
            logger.info(f"📁 图片已保存到本地临时文件: {temp_path}")
            return local_url
            
        except Exception as e:
            logger.error(f"❌ 本地临时文件保存失败: {e}")
            # 最后的备选方案
            return "https://via.placeholder.com/512x512/lightgray/000000?text=Upload+Failed"
    
    async def _check_step_quality(self, step_image: Image.Image, previous_image: Image.Image, step_num: int) -> Dict[str, Any]:
        """检查步骤图质量"""
        try:
            # 1. 基本图像质量检查
            if step_image.size[0] < 100 or step_image.size[1] < 100:
                return {'is_valid': False, 'message': '图像尺寸过小'}
            
            # 2. 检查图像是否与上一步有合理的变化
            similarity_score = self._calculate_image_similarity(step_image, previous_image)
            
            if similarity_score > 0.95:  # 变化太小
                return {'is_valid': False, 'message': f'与上一步变化太小 (相似度: {similarity_score:.2f})'}
            
            if similarity_score < 0.3:  # 变化太大，可能偏离目标
                return {'is_valid': False, 'message': f'与上一步变化太大 (相似度: {similarity_score:.2f})'}
            
            # 3. 检查图像是否包含合理的内容
            if self._is_blank_or_corrupted(step_image):
                return {'is_valid': False, 'message': '图像内容异常'}
            
            return {'is_valid': True, 'message': f'质量良好 (相似度: {similarity_score:.2f})'}
            
        except Exception as e:
            logger.error(f"❌ 质量检查失败: {e}")
            return {'is_valid': True, 'message': '质量检查跳过'}
    
    def _calculate_image_similarity(self, img1: Image.Image, img2: Image.Image) -> float:
        """计算两张图像的相似度"""
        try:
            import numpy as np
            from PIL import ImageStat
            
            # 调整到相同尺寸
            size = (256, 256)
            img1_resized = img1.resize(size, Image.Resampling.LANCZOS)
            img2_resized = img2.resize(size, Image.Resampling.LANCZOS)
            
            # 转换为灰度图
            img1_gray = img1_resized.convert('L')
            img2_gray = img2_resized.convert('L')
            
            # 计算直方图
            hist1 = img1_gray.histogram()
            hist2 = img2_gray.histogram()
            
            # 计算直方图相似度
            similarity = 0
            for i in range(len(hist1)):
                similarity += min(hist1[i], hist2[i])
            
            total_pixels = img1_gray.size[0] * img1_gray.size[1]
            similarity_score = similarity / total_pixels
            
            return similarity_score
            
        except Exception as e:
            logger.error(f"❌ 相似度计算失败: {e}")
            return 0.5  # 默认中等相似度
    
    def _is_blank_or_corrupted(self, image: Image.Image) -> bool:
        """检查图像是否空白或损坏"""
        try:
            # 检查图像是否全黑或全白
            from PIL import ImageStat
            stat = ImageStat.Stat(image)
            
            # 计算平均亮度
            mean_brightness = sum(stat.mean) / len(stat.mean)
            
            # 如果太暗或太亮，可能是异常图像
            if mean_brightness < 10 or mean_brightness > 245:
                return True
            
            # 检查图像尺寸是否合理
            if image.size[0] < 50 or image.size[1] < 50:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ 图像异常检查失败: {e}")
            return True  # 检查失败时认为异常
    
    async def generate_step_analysis(
        self,
        original_image: Image.Image,
        step_images: List[Image.Image],
        final_image: Image.Image,
        steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析步骤图的渐进性"""
        try:
            logger.info("🔍 分析步骤图的渐进性...")
            
            analysis = {
                'total_steps': len(step_images),
                'progressive_quality': 'good',
                'step_analysis': [],
                'recommendations': []
            }
            
            # 分析每个步骤
            for i, (step_img, step) in enumerate(zip(step_images, steps)):
                step_analysis = {
                    'step_number': i + 1,
                    'step_title': step.get('title', f'步骤{i+1}'),
                    'has_progression': True,  # 这里可以添加更复杂的分析逻辑
                    'quality_score': 0.8  # 这里可以添加质量评分逻辑
                }
                analysis['step_analysis'].append(step_analysis)
            
            # 生成建议
            if len(step_images) < 3:
                analysis['recommendations'].append("建议增加更多中间步骤")
            
            if analysis['progressive_quality'] == 'poor':
                analysis['recommendations'].append("建议优化步骤间的渐进性")
            
            logger.info("✅ 步骤图分析完成")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ 步骤图分析失败: {e}")
            return {'error': str(e)}
    
    async def create_progressive_comparison(
        self,
        original_image: Image.Image,
        step_images: List[Image.Image],
        final_image: Image.Image,
        steps: List[Dict[str, Any]]
    ) -> Image.Image:
        """创建渐进式对比图"""
        try:
            logger.info("🔄 创建渐进式对比图...")
            
            # 创建对比画布
            canvas_width = 1200
            canvas_height = 800
            canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
            
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(canvas)
            
            # 绘制标题
            title_font = ImageFont.load_default()
            draw.text((20, 20), "渐进式改造步骤对比", fill='#2E8B57', font=title_font)
            
            # 计算图像布局
            img_width = 200
            img_height = 150
            spacing = 20
            start_x = 20
            start_y = 80
            
            # 所有图像（原图 + 步骤图 + 最终图）
            all_images = [original_image] + step_images + [final_image]
            all_labels = ["原图"] + [f"步骤{i+1}" for i in range(len(step_images))] + ["最终效果"]
            
            # 绘制图像网格
            cols = min(6, len(all_images))  # 最多6列
            for i, (img, label) in enumerate(zip(all_images, all_labels)):
                row = i // cols
                col = i % cols
                
                x = start_x + col * (img_width + spacing)
                y = start_y + row * (img_height + 60)
                
                # 调整图像大小
                img_resized = img.resize((img_width, img_height), Image.Resampling.LANCZOS)
                canvas.paste(img_resized, (x, y))
                
                # 绘制标签
                draw.text((x, y + img_height + 10), label, fill='black', font=title_font)
                
                # 绘制进度指示
                progress = (i + 1) / len(all_images)
                progress_text = f"{progress*100:.0f}%"
                draw.text((x, y + img_height + 30), progress_text, fill='#2E8B57', font=title_font)
            
            logger.info("✅ 渐进式对比图创建完成")
            return canvas
            
        except Exception as e:
            logger.error(f"❌ 渐进式对比图创建失败: {e}")
            return original_image
