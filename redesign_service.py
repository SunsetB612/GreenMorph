"""
GreenMorph 主服务类
整合图片分析、多模态API调用、图像生成和步骤可视化功能
"""

import base64
import io
import os
import uuid
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
from loguru import logger

from models import (
    ImageAnalysisRequest, ImageAnalysisResponse,
    RedesignRequest, RedesignResponse, RedesignStep,
    ErrorResponse, HealthResponse
)
from image_analyzer import ImageAnalyzer
from multimodal_api import MultimodalAPI
from image_generator import ImageGenerator
from step_visualizer import StepVisualizer
from file_manager import FileManager
from config import settings


class RedesignService:
    """旧物再设计主服务"""
    
    def __init__(self):
        self.image_analyzer = ImageAnalyzer()
        self.multimodal_api = MultimodalAPI()
        self.image_generator = ImageGenerator()
        self.step_visualizer = StepVisualizer()
        self.file_manager = FileManager()
        
        logger.info("GreenMorph 服务初始化完成")
    
    async def analyze_image(self, request: ImageAnalysisRequest) -> ImageAnalysisResponse:
        """
        分析旧物图片
        
        Args:
            request: 图片分析请求
            
        Returns:
            ImageAnalysisResponse: 分析结果
        """
        try:
            # 获取图片数据
            image_data = await self._get_image_data(request)
            
            # 验证图片
            if not self.image_analyzer.validate_image(image_data):
                raise ValueError("图片格式不支持或文件过大")
            
            # 分析图片
            analysis_result = await self.image_analyzer.analyze_image(image_data)
            
            logger.info(f"图片分析完成: {len(analysis_result.main_objects)} 个物体")
            return analysis_result
            
        except Exception as e:
            logger.error(f"图片分析失败: {str(e)}")
            raise Exception(f"图片分析失败: {str(e)}")
    
    async def analyze_image_direct(self, image_data: bytes) -> ImageAnalysisResponse:
        """
        直接分析图片字节数据
        
        Args:
            image_data: 图片二进制数据
            
        Returns:
            ImageAnalysisResponse: 分析结果
        """
        try:
            # 验证图片
            if not self.image_analyzer.validate_image(image_data):
                raise ValueError("图片格式不支持或文件过大")
            
            # 分析图片
            analysis_result = await self.image_analyzer.analyze_image(image_data)
            
            logger.info(f"图片分析完成: {len(analysis_result.main_objects)} 个物体")
            return analysis_result
            
        except Exception as e:
            logger.error(f"图片分析失败: {str(e)}")
            raise Exception(f"图片分析失败: {str(e)}")
    
    async def redesign_item(self, request: RedesignRequest) -> RedesignResponse:
        """
        生成旧物再设计方案
        
        Args:
            request: 再设计请求
            
        Returns:
            RedesignResponse: 再设计结果
        """
        try:
            # 生成唯一任务ID
            task_id = str(uuid.uuid4())
            logger.info(f"开始处理再设计任务: {task_id}")
            
            # 1. 获取并分析原始图片
            image_data = await self._get_image_data(request)
            if not self.image_analyzer.validate_image(image_data):
                raise ValueError("图片格式不支持或文件过大")
            
            original_image = Image.open(io.BytesIO(image_data))
            image_analysis = await self.image_analyzer.analyze_image(image_data)
            
            # 2. 生成改造计划
            redesign_plan = await self.multimodal_api.generate_redesign_plan(
                image_analysis=image_analysis.dict(),
                user_requirements=request.user_requirements,
                target_style=request.target_style.value,
                target_materials=[m.value for m in (request.target_materials or [])]
            )
            
            # 3. 生成最终效果图
            final_image = await self.image_generator.generate_final_effect_image(
                original_image=original_image,
                redesign_plan=redesign_plan,
                user_requirements=request.user_requirements,
                target_style=request.target_style.value
            )
            
            # 4. 生成步骤图像
            steps_data = redesign_plan.get('steps', [])
            step_images = await self.image_generator.generate_step_images(
                original_image=original_image,
                steps=steps_data,
                base_features=image_analysis.features
            )
            
            # 5. 生成步骤可视化
            step_visualizations = []
            for i, step in enumerate(steps_data):
                visualization = await self.step_visualizer.create_step_visualization(
                    original_image=original_image,
                    step=step,
                    step_number=i + 1,
                    total_steps=len(steps_data),
                    base_features=image_analysis.features
                )
                step_visualizations.append(visualization)
            
            # 6. 保存所有图像
            saved_images = await self._save_all_images(
                task_id, final_image, step_images, step_visualizations
            )
            
            # 7. 构建响应
            response = self._build_redesign_response(
                saved_images, redesign_plan, image_analysis
            )
            
            logger.info(f"再设计任务完成: {task_id}")
            return response
            
        except Exception as e:
            logger.error(f"再设计任务失败: {str(e)}")
            raise Exception(f"再设计任务失败: {str(e)}")
    
    async def _get_image_data(self, request) -> bytes:
        """获取图片数据"""
        try:
            if request.image_url:
                # 从URL下载图片
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(request.image_url) as response:
                        if response.status == 200:
                            return await response.read()
                        else:
                            raise ValueError(f"图片下载失败: HTTP {response.status}")
            
            elif request.image_base64:
                # 从Base64解码图片
                return base64.b64decode(request.image_base64)
            
            else:
                raise ValueError("未提供图片数据")
                
        except Exception as e:
            logger.error(f"获取图片数据失败: {str(e)}")
            raise Exception(f"获取图片数据失败: {str(e)}")
    
    async def _save_all_images(
        self,
        task_id: str,
        final_image: Image.Image,
        step_images: List[Image.Image],
        step_visualizations: List[Image.Image]
    ) -> Dict[str, str]:
        """保存所有生成的图像"""
        try:
            saved_images = {}
            
            # 保存最终效果图
            final_bytes = self._image_to_bytes(final_image)
            final_path = self.file_manager.save_output_file(final_bytes, task_id, "final")
            saved_images['final_image'] = final_path
            
            # 保存步骤图像
            step_image_paths = []
            for i, step_image in enumerate(step_images):
                step_bytes = self._image_to_bytes(step_image)
                step_path = self.file_manager.save_output_file(step_bytes, task_id, "step", i+1)
                step_image_paths.append(step_path)
            saved_images['step_images'] = step_image_paths
            
            # 保存步骤可视化
            step_viz_paths = []
            for i, viz_image in enumerate(step_visualizations):
                viz_bytes = self._image_to_bytes(viz_image)
                viz_path = self.file_manager.save_output_file(viz_bytes, task_id, "visualization", i+1)
                step_viz_paths.append(viz_path)
            saved_images['step_visualizations'] = step_viz_paths
            
            logger.info(f"所有图像已保存: {task_id}")
            return saved_images
            
        except Exception as e:
            logger.error(f"图像保存失败: {str(e)}")
            raise Exception(f"图像保存失败: {str(e)}")
    
    def _image_to_bytes(self, image: Image.Image) -> bytes:
        """将PIL图像转换为字节"""
        import io
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=95)
        return buffer.getvalue()
    
    def _build_redesign_response(
        self,
        saved_images: Dict[str, str],
        redesign_plan: Dict[str, Any],
        image_analysis: ImageAnalysisResponse
    ) -> RedesignResponse:
        """构建再设计响应"""
        try:
            # 转换步骤数据
            steps = []
            for step_data in redesign_plan.get('steps', []):
                step = RedesignStep(
                    step_number=step_data.get('step_number', 0),
                    title=step_data.get('title', ''),
                    description=step_data.get('description', ''),
                    materials_needed=step_data.get('materials_needed', []),
                    tools_needed=step_data.get('tools_needed', []),
                    estimated_time=step_data.get('estimated_time', ''),
                    difficulty=step_data.get('difficulty', ''),
                    image_prompt=step_data.get('image_prompt', ''),
                    safety_notes=step_data.get('safety_notes')
                )
                steps.append(step)
            
            # 构建响应
            response = RedesignResponse(
                final_image_url=self._get_public_url(saved_images['final_image']),
                step_images=[self._get_public_url(path) for path in saved_images['step_images']],
                redesign_guide=steps,
                total_estimated_time=redesign_plan.get('total_estimated_time', '待评估'),
                total_cost_estimate=redesign_plan.get('total_cost_estimate', '待评估'),
                sustainability_score=redesign_plan.get('sustainability_score', 7),
                difficulty_rating=redesign_plan.get('difficulty_rating', '中等'),
                tips=redesign_plan.get('tips', [])
            )
            
            return response
            
        except Exception as e:
            logger.error(f"响应构建失败: {str(e)}")
            raise Exception(f"响应构建失败: {str(e)}")
    
    def _get_public_url(self, file_path: str) -> str:
        """获取公开访问URL"""
        # 这里应该根据实际部署情况生成公开URL
        # 暂时返回相对路径
        filename = os.path.basename(file_path)
        return f"/output/{filename}"
    
    async def get_health_status(self) -> HealthResponse:
        """获取服务健康状态"""
        try:
            # 检查各个组件的状态
            components_status = {
                'image_analyzer': True,
                'multimodal_api': (self.multimodal_api.tongyi_client is not None or 
                                 self.multimodal_api.openai_client is not None or 
                                 self.multimodal_api.anthropic_client is not None),
                'image_generator': self.image_generator.validate_generation_requirements(),
                'step_visualizer': True
            }
            
            # 添加调试信息
            logger.info(f"健康检查组件状态: {components_status}")
            
            # 计算整体状态
            all_healthy = all(components_status.values())
            status = "healthy" if all_healthy else "degraded"
            
            logger.info(f"整体健康状态: {status}")
            
            return HealthResponse(
                status=status,
                version=settings.app_version,
                timestamp=str(int(__import__('time').time()))
            )
            
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return HealthResponse(
                status="unhealthy",
                version=settings.app_version,
                timestamp=str(int(__import__('time').time()))
            )
    
    async def cleanup_old_files(self, max_age_hours: int = 24):
        """清理旧文件"""
        try:
            import time
            import glob
            
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            # 清理输出目录中的旧文件
            output_pattern = os.path.join(settings.output_dir, "*")
            for file_path in glob.glob(output_pattern):
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        logger.info(f"已删除旧文件: {file_path}")
            
            logger.info("文件清理完成")
            
        except Exception as e:
            logger.error(f"文件清理失败: {str(e)}")
    
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "service_name": "GreenMorph Redesign Service",
            "version": settings.app_version,
            "description": "AI驱动的旧物再设计平台核心服务",
            "features": [
                "图片特征分析",
                "多模态大模型调用",
                "结构控制图像生成",
                "改造步骤可视化",
                "环保设计优化"
            ],
            "supported_formats": settings.allowed_image_types,
            "max_file_size": settings.max_file_size,
            "output_quality": settings.image_quality
        }
