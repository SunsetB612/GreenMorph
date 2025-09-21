"""
改造步骤可视化生成模块
生成每个改造步骤的详细示意图和说明
"""

import base64
import io
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
from loguru import logger

from config import settings


class StepVisualizer:
    """步骤可视化生成器"""
    
    def __init__(self):
        self.font_size = 24
        self.title_font_size = 32
        self.step_font_size = 20
        self.margin = 40
        self.line_height = 30
        
    async def create_step_visualization(
        self,
        original_image: Image.Image,
        step: Dict[str, Any],
        step_number: int,
        total_steps: int,
        base_features: List[str]
    ) -> Image.Image:
        """
        创建单个步骤的可视化图像
        
        Args:
            original_image: 原始图片
            step: 步骤信息
            step_number: 步骤编号
            total_steps: 总步骤数
            base_features: 原图特征
            
        Returns:
            Image.Image: 步骤可视化图像
        """
        try:
            # 创建画布
            canvas_width = 800
            canvas_height = 600
            canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
            draw = ImageDraw.Draw(canvas)
            
            # 绘制标题区域
            self._draw_title_section(draw, step, step_number, total_steps, canvas_width)
            
            # 绘制原图区域
            original_section = self._draw_original_section(
                draw, original_image, canvas_width, canvas_height
            )
            
            # 绘制步骤说明区域
            self._draw_step_description(
                draw, step, original_section[1], canvas_width, canvas_height
            )
            
            # 绘制材料工具区域
            self._draw_materials_tools_section(
                draw, step, canvas_width, canvas_height
            )
            
            # 绘制进度指示器
            self._draw_progress_indicator(
                draw, step_number, total_steps, canvas_width, canvas_height
            )
            
            logger.info(f"步骤 {step_number} 可视化图像创建完成")
            return canvas
            
        except Exception as e:
            logger.error(f"步骤可视化创建失败: {str(e)}")
            return self._create_fallback_visualization(step, step_number)
    
    def _draw_title_section(
        self,
        draw: ImageDraw.Draw,
        step: Dict[str, Any],
        step_number: int,
        total_steps: int,
        canvas_width: int
    ) -> int:
        """绘制标题区域"""
        try:
            # 标题背景
            title_height = 80
            draw.rectangle(
                [(0, 0), (canvas_width, title_height)],
                fill='#2E8B57'  # 环保绿色
            )
            
            # 步骤标题
            title_text = f"步骤 {step_number}/{total_steps}: {step.get('title', '改造步骤')}"
            title_font = self._get_font(self.title_font_size, bold=True)
            
            # 计算文本位置（居中）
            bbox = draw.textbbox((0, 0), title_text, font=title_font)
            text_width = bbox[2] - bbox[0]
            text_x = (canvas_width - text_width) // 2
            text_y = (title_height - self.title_font_size) // 2
            
            draw.text((text_x, text_y), title_text, fill='white', font=title_font)
            
            return title_height
            
        except Exception as e:
            logger.error(f"标题区域绘制失败: {str(e)}")
            return 80
    
    def _draw_original_section(
        self,
        draw: ImageDraw.Draw,
        original_image: Image.Image,
        canvas_width: int,
        canvas_height: int
    ) -> Tuple[int, int]:
        """绘制原图区域"""
        try:
            # 原图区域位置
            section_y = 100
            section_width = 300
            section_height = 200
            
            # 调整原图大小
            resized_image = original_image.resize(
                (section_width, section_height), Image.Resampling.LANCZOS
            )
            
            # 粘贴原图
            paste_x = (canvas_width - section_width) // 2
            draw.rectangle(
                [(paste_x - 5, section_y - 5), 
                 (paste_x + section_width + 5, section_y + section_height + 5)],
                outline='#2E8B57',
                width=3
            )
            
            # 在原图上添加标注
            annotated_image = self._annotate_original_image(resized_image)
            
            return section_y, section_y + section_height
            
        except Exception as e:
            logger.error(f"原图区域绘制失败: {str(e)}")
            return 100, 300
    
    def _annotate_original_image(self, image: Image.Image) -> Image.Image:
        """在原图上添加标注"""
        try:
            # 转换为numpy数组
            img_array = np.array(image)
            
            # 添加一些标注线条和文字
            # 这里可以根据具体需求添加更复杂的标注
            
            return Image.fromarray(img_array)
            
        except Exception as e:
            logger.error(f"原图标注失败: {str(e)}")
            return image
    
    def _draw_step_description(
        self,
        draw: ImageDraw.Draw,
        step: Dict[str, Any],
        start_y: int,
        canvas_width: int,
        canvas_height: int
    ) -> None:
        """绘制步骤说明区域"""
        try:
            # 说明区域位置
            desc_x = 20
            desc_y = start_y + 20
            desc_width = canvas_width - 40
            
            # 步骤描述
            description = step.get('description', '暂无描述')
            desc_font = self._get_font(self.step_font_size)
            
            # 绘制描述文本（支持换行）
            self._draw_multiline_text(
                draw, description, (desc_x, desc_y), desc_width, desc_font, 'black'
            )
            
            # 预估时间
            time_text = f"预估时间: {step.get('estimated_time', '未知')}"
            time_y = desc_y + 100
            draw.text((desc_x, time_y), time_text, fill='#666666', font=desc_font)
            
            # 难度等级
            difficulty = step.get('difficulty', '未知')
            difficulty_color = self._get_difficulty_color(difficulty)
            diff_text = f"难度: {difficulty}"
            diff_y = time_y + 30
            draw.text((desc_x, diff_y), diff_text, fill=difficulty_color, font=desc_font)
            
        except Exception as e:
            logger.error(f"步骤说明绘制失败: {str(e)}")
    
    def _draw_materials_tools_section(
        self,
        draw: ImageDraw.Draw,
        step: Dict[str, Any],
        canvas_width: int,
        canvas_height: int
    ) -> None:
        """绘制材料和工具区域"""
        try:
            # 材料和工具区域
            section_y = canvas_height - 150
            section_height = 130
            
            # 背景
            draw.rectangle(
                [(0, section_y), (canvas_width, canvas_height)],
                fill='#F0F8F0'  # 浅绿色背景
            )
            
            # 材料列表
            materials = step.get('materials_needed', [])
            if materials:
                materials_text = "所需材料: " + ", ".join(materials)
                materials_font = self._get_font(self.step_font_size)
                draw.text((20, section_y + 10), materials_text, fill='black', font=materials_font)
            
            # 工具列表
            tools = step.get('tools_needed', [])
            if tools:
                tools_text = "所需工具: " + ", ".join(tools)
                tools_y = section_y + 40
                draw.text((20, tools_y), tools_text, fill='black', font=materials_font)
            
            # 安全注意事项
            safety_notes = step.get('safety_notes', '')
            if safety_notes:
                safety_text = f"安全提示: {safety_notes}"
                safety_y = section_y + 70
                safety_font = self._get_font(16)
                draw.text((20, safety_y), safety_text, fill='#CC0000', font=safety_font)
            
        except Exception as e:
            logger.error(f"材料工具区域绘制失败: {str(e)}")
    
    def _draw_progress_indicator(
        self,
        draw: ImageDraw.Draw,
        step_number: int,
        total_steps: int,
        canvas_width: int,
        canvas_height: int
    ) -> None:
        """绘制进度指示器"""
        try:
            # 进度条位置
            progress_y = canvas_height - 20
            progress_width = canvas_width - 40
            progress_height = 10
            
            # 进度条背景
            draw.rectangle(
                [(20, progress_y), (20 + progress_width, progress_y + progress_height)],
                fill='#E0E0E0'
            )
            
            # 当前进度
            progress = step_number / total_steps
            current_width = int(progress_width * progress)
            draw.rectangle(
                [(20, progress_y), (20 + current_width, progress_y + progress_height)],
                fill='#2E8B57'
            )
            
            # 进度文字
            progress_text = f"{step_number}/{total_steps}"
            progress_font = self._get_font(14)
            text_x = 20 + progress_width + 10
            draw.text((text_x, progress_y - 5), progress_text, fill='black', font=progress_font)
            
        except Exception as e:
            logger.error(f"进度指示器绘制失败: {str(e)}")
    
    def _draw_multiline_text(
        self,
        draw: ImageDraw.Draw,
        text: str,
        position: Tuple[int, int],
        max_width: int,
        font: Any,
        fill: str
    ) -> None:
        """绘制多行文本"""
        try:
            x, y = position
            words = text.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font)
                text_width = bbox[2] - bbox[0]
                
                if text_width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        lines.append(word)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            for line in lines:
                draw.text((x, y), line, fill=fill, font=font)
                y += self.line_height
                
        except Exception as e:
            logger.error(f"多行文本绘制失败: {str(e)}")
    
    def _get_font(self, size: int, bold: bool = False) -> Any:
        """获取字体"""
        try:
            # 尝试使用系统字体
            if bold:
                font_path = "arialbd.ttf"  # Windows Arial Bold
            else:
                font_path = "arial.ttf"    # Windows Arial
            
            return ImageFont.truetype(font_path, size)
        except:
            # 使用默认字体
            return ImageFont.load_default()
    
    def _get_difficulty_color(self, difficulty: str) -> str:
        """根据难度获取颜色"""
        difficulty_lower = difficulty.lower()
        if '简单' in difficulty_lower or 'easy' in difficulty_lower:
            return '#00AA00'  # 绿色
        elif '中等' in difficulty_lower or 'medium' in difficulty_lower:
            return '#FF8800'  # 橙色
        elif '困难' in difficulty_lower or 'hard' in difficulty_lower:
            return '#CC0000'  # 红色
        else:
            return '#666666'  # 灰色
    
    def _create_fallback_visualization(
        self,
        step: Dict[str, Any],
        step_number: int
    ) -> Image.Image:
        """创建备用可视化图像"""
        try:
            # 创建简单的备用图像
            canvas = Image.new('RGB', (400, 300), 'white')
            draw = ImageDraw.Draw(canvas)
            
            # 绘制简单文本
            title = f"步骤 {step_number}: {step.get('title', '改造步骤')}"
            draw.text((20, 20), title, fill='black')
            
            description = step.get('description', '暂无描述')
            draw.text((20, 60), description, fill='black')
            
            return canvas
            
        except Exception as e:
            logger.error(f"备用可视化创建失败: {str(e)}")
            # 返回空白图像
            return Image.new('RGB', (400, 300), 'white')
    
    async def create_comparison_visualization(
        self,
        original_image: Image.Image,
        final_image: Image.Image,
        steps: List[Dict[str, Any]]
    ) -> Image.Image:
        """
        创建改造前后对比可视化
        
        Args:
            original_image: 原始图片
            final_image: 最终效果图
            steps: 改造步骤列表
            
        Returns:
            Image.Image: 对比可视化图像
        """
        try:
            # 创建对比画布
            canvas_width = 1000
            canvas_height = 600
            canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
            draw = ImageDraw.Draw(canvas)
            
            # 标题
            title = "改造前后对比"
            title_font = self._get_font(36, bold=True)
            bbox = draw.textbbox((0, 0), title, font=title_font)
            text_width = bbox[2] - bbox[0]
            text_x = (canvas_width - text_width) // 2
            draw.text((text_x, 20), title, fill='#2E8B57', font=title_font)
            
            # 原图区域
            original_section = self._draw_comparison_section(
                draw, original_image, "改造前", 50, canvas_width, canvas_height
            )
            
            # 最终效果图区域
            final_section = self._draw_comparison_section(
                draw, final_image, "改造后", canvas_width // 2 + 50, canvas_width, canvas_height
            )
            
            # 添加步骤概览
            self._draw_steps_overview(draw, steps, canvas_width, canvas_height)
            
            logger.info("对比可视化图像创建完成")
            return canvas
            
        except Exception as e:
            logger.error(f"对比可视化创建失败: {str(e)}")
            return self._create_fallback_visualization({}, 0)
    
    def _draw_comparison_section(
        self,
        draw: ImageDraw.Draw,
        image: Image.Image,
        label: str,
        start_x: int,
        canvas_width: int,
        canvas_height: int
    ) -> None:
        """绘制对比区域"""
        try:
            # 图像尺寸
            img_width = 300
            img_height = 200
            
            # 调整图像大小
            resized_image = image.resize((img_width, img_height), Image.Resampling.LANCZOS)
            
            # 绘制标签
            label_font = self._get_font(24, bold=True)
            bbox = draw.textbbox((0, 0), label, font=label_font)
            text_width = bbox[2] - bbox[0]
            label_x = start_x + (img_width - text_width) // 2
            draw.text((label_x, 80), label, fill='black', font=label_font)
            
            # 绘制图像边框
            draw.rectangle(
                [(start_x, 120), (start_x + img_width, 120 + img_height)],
                outline='#2E8B57',
                width=3
            )
            
        except Exception as e:
            logger.error(f"对比区域绘制失败: {str(e)}")
    
    def _draw_steps_overview(
        self,
        draw: ImageDraw.Draw,
        steps: List[Dict[str, Any]],
        canvas_width: int,
        canvas_height: int
    ) -> None:
        """绘制步骤概览"""
        try:
            # 步骤概览区域
            overview_y = 400
            overview_height = 180
            
            # 背景
            draw.rectangle(
                [(0, overview_y), (canvas_width, canvas_height)],
                fill='#F8F8F8'
            )
            
            # 标题
            overview_title = "改造步骤概览"
            title_font = self._get_font(20, bold=True)
            draw.text((20, overview_y + 10), overview_title, fill='black', font=title_font)
            
            # 绘制步骤列表
            step_y = overview_y + 40
            step_font = self._get_font(16)
            
            for i, step in enumerate(steps[:5]):  # 最多显示5个步骤
                step_text = f"{i+1}. {step.get('title', '未知步骤')}"
                draw.text((20, step_y), step_text, fill='black', font=step_font)
                step_y += 25
                
        except Exception as e:
            logger.error(f"步骤概览绘制失败: {str(e)}")
    
    def save_visualization(self, image: Image.Image, filename: str) -> str:
        """保存可视化图像"""
        try:
            import os
            os.makedirs(settings.output_dir, exist_ok=True)
            filepath = os.path.join(settings.output_dir, filename)
            image.save(filepath, "JPEG", quality=settings.image_quality)
            logger.info(f"可视化图像已保存: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"可视化图像保存失败: {str(e)}")
            raise Exception(f"可视化图像保存失败: {str(e)}")
