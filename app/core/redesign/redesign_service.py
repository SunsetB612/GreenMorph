"""
GreenMorph 主服务类
整合图片分析、多模态API调用、图像生成和步骤可视化功能
"""

import io
import os
import uuid
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
from loguru import logger

from app.shared.models import (
    ImageAnalysisResponse,
    RedesignRequest, RedesignResponse, RedesignStep,
    ErrorResponse, HealthResponse
)
from ai_modules.image_analyzer import ImageAnalyzer
from ai_modules.multimodal_api import MultimodalAPI
from ai_modules.image_generator import ImageGenerator
from ai_modules.step_visualizer import StepVisualizer
from app.shared.utils.file_manager import FileManager
from app.config import settings


class RedesignService:
    """旧物再设计主服务"""
    
    def __init__(self):
        self.image_analyzer = ImageAnalyzer()
        self.multimodal_api = MultimodalAPI()
        self.image_generator = ImageGenerator()
        self.step_visualizer = StepVisualizer()
        self.file_manager = FileManager()
        
        logger.info("GreenMorph 服务初始化完成")
    
    async def analyze_image(self, image_data: bytes, filename: str = "image.jpg") -> ImageAnalysisResponse:
        """
        分析旧物图片
        
        Args:
            image_data: 图片二进制数据
            filename: 文件名
            
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
    
    async def analyze_image(self, image_data: bytes, filename: str = "image.jpg") -> ImageAnalysisResponse:
        """
        分析图片（兼容旧接口）
        
        Args:
            image_data: 图片二进制数据
            filename: 文件名
            
        Returns:
            ImageAnalysisResponse: 分析结果
        """
        return await self.analyze_image_direct(image_data)
    
    async def redesign_item(self, request: RedesignRequest, db=None) -> RedesignResponse:
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
            logger.info("🎨 开始生成最终效果图...")
            try:
                final_image = await self.image_generator.generate_final_effect_image(
                    original_image=original_image,
                    redesign_plan=redesign_plan,
                    user_requirements=request.user_requirements,
                    target_style=request.target_style.value
                )
                logger.info("✅ 最终效果图生成完成")
            except Exception as e:
                logger.error(f"❌ 最终效果图生成失败: {str(e)}")
                raise
            
            # 4. 生成步骤图像
            steps_data = redesign_plan.get('steps', [])
            logger.info(f"🔧 开始生成 {len(steps_data)} 个步骤图像...")
            step_images = await self.image_generator.generate_step_images(
                original_image=original_image,
                steps=steps_data,
                base_features=image_analysis.features
            )
            logger.info("✅ 步骤图像生成完成")
            
            # 5. 生成步骤可视化
            logger.info("📊 开始生成步骤可视化...")
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
            logger.info("✅ 步骤可视化生成完成")
            
            # 6. 保存所有图像
            logger.info("💾 保存生成的图像...")
            try:
                saved_images = await self._save_all_images(
                    task_id, final_image, step_images, step_visualizations
                )
                logger.info("✅ 图像保存完成")
                logger.info(f"🔍 保存的图像路径: {saved_images}")
            except Exception as e:
                logger.error(f"❌ 图像保存失败: {str(e)}")
                raise
            
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
                # 检查是否是本地文件路径
                if request.image_url.startswith(('http://', 'https://')):
                    # 从URL下载图片
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.get(request.image_url) as response:
                            if response.status == 200:
                                return await response.read()
                            else:
                                raise ValueError(f"图片下载失败: HTTP {response.status}")
                else:
                    # 读取本地文件
                    import os
                    if os.path.exists(request.image_url):
                        with open(request.image_url, 'rb') as f:
                            return f.read()
                    else:
                        raise ValueError(f"本地图片文件不存在: {request.image_url}")
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
            final_path = self.file_manager.save_output_file(final_bytes, task_id, "final", userid="user1")
            saved_images['final_image'] = final_path
            
            # 保存步骤图像
            step_image_paths = []
            for i, step_image in enumerate(step_images):
                step_bytes = self._image_to_bytes(step_image)
                step_path = self.file_manager.save_output_file(step_bytes, task_id, "step", i+1, userid="user1")
                step_image_paths.append(step_path)
            saved_images['step_images'] = step_image_paths
            
            # 保存步骤可视化
            step_viz_paths = []
            for i, viz_image in enumerate(step_visualizations):
                viz_bytes = self._image_to_bytes(viz_image)
                viz_path = self.file_manager.save_output_file(viz_bytes, task_id, "visualization", i+1, userid="user1")
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
            logger.info(f"🔍 构建响应，saved_images键: {list(saved_images.keys())}")
            logger.info(f"🔍 saved_images内容: {saved_images}")
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
        # 将文件系统路径转换为公开访问URL
        # 例如: static/user1/output/results/xxx.jpg -> /static/user1/output/results/xxx.jpg
        if file_path.startswith("static/"):
            return f"/{file_path}"
        else:
            # 兼容旧路径格式
            filename = os.path.basename(file_path)
            return f"/static/user1/output/result/{filename}"
    
    async def _create_placeholder_images(self, task_id: str, step_count: int) -> Dict[str, Any]:
        """创建占位符图像文件（用于快速测试）"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import os
            from pathlib import Path
            
            # 确保输出目录存在
            output_dir = Path("static/output")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            saved_images = {}
            
            # 创建最终效果图占位符
            final_image = Image.new('RGB', (800, 600), color='lightblue')
            draw = ImageDraw.Draw(final_image)
            
            # 添加文字
            try:
                # 尝试使用系统字体
                font = ImageFont.truetype("arial.ttf", 40)
            except:
                # 如果没有找到字体，使用默认字体
                font = ImageFont.load_default()
            
            draw.text((50, 250), "改造效果图", fill='darkblue', font=font)
            draw.text((50, 300), f"任务ID: {task_id[:8]}...", fill='darkblue', font=font)
            
            # 保存最终效果图
            final_filename = f"project_{task_id}_final.jpg"
            final_path = output_dir / final_filename
            final_image.save(final_path, 'JPEG', quality=95)
            
            saved_images['final_image_url'] = f"/static/output/{final_filename}"
            
            # 创建步骤图像占位符
            step_image_urls = []
            for i in range(step_count):
                step_image = Image.new('RGB', (600, 400), color='lightgreen')
                step_draw = ImageDraw.Draw(step_image)
                
                step_draw.text((50, 150), f"步骤 {i+1}", fill='darkgreen', font=font)
                step_draw.text((50, 200), f"任务: {task_id[:8]}...", fill='darkgreen', font=font)
                
                step_filename = f"project_{task_id}_step_{i+1}.jpg"
                step_path = output_dir / step_filename
                step_image.save(step_path, 'JPEG', quality=95)
                
                step_image_urls.append(f"/static/output/{step_filename}")
            
            saved_images['step_images'] = step_image_urls
            
            logger.info(f"✅ 创建了 {1 + step_count} 个占位符图像文件")
            return saved_images
            
        except Exception as e:
            logger.error(f"❌ 创建占位符图像失败: {str(e)}")
            # 如果创建失败，返回默认URL
            return {
                'final_image_url': '/static/placeholder/default_final.jpg',
                'step_images': [f'/static/placeholder/default_step_{i+1}.jpg' for i in range(step_count)]
            }
    
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
    
    async def save_redesign_result(self, result: RedesignResponse, db=None):
        """保存再设计结果到数据库"""
        try:
            if db is None:
                logger.warning("未提供数据库会话，跳过保存")
                return
            
            from app.core.redesign.models import RedesignProject, RedesignStep, ProjectDetail
            
            # 创建改造项目记录
            project = RedesignProject(
                user_id=1,  # TODO: 从认证中获取真实用户ID
                project_name=f"改造项目_{int(__import__('time').time())}",
                output_image_path=result.final_image_url,
                # input_image_id 和 input_demand_id 可以后续关联
            )
            
            db.add(project)
            db.commit()
            db.refresh(project)
            
            # 保存改造步骤
            for step_data in result.redesign_guide:
                step = RedesignStep(
                    project_id=project.id,
                    step_number=step_data.step_number,
                    description=step_data.description,
                    # step_image_path 可以从 step_images 中获取对应的图片
                )
                db.add(step)
            
            # 保存项目详情
            project_detail = ProjectDetail(
                project_id=project.id,
                total_cost_estimate=result.total_cost_estimate,
                total_time_estimate=result.total_estimated_time,
                difficulty_level=result.difficulty_rating,
                materials_and_tools=", ".join([
                    f"步骤{step.step_number}: {', '.join(step.materials_needed + step.tools_needed)}"
                    for step in result.redesign_guide
                ]),
                tips=", ".join(result.tips)
            )
            db.add(project_detail)
            
            db.commit()
            logger.info(f"再设计结果已保存到数据库，项目ID: {project.id}")
            
        except Exception as e:
            logger.error(f"保存再设计结果失败: {str(e)}")
            if db:
                db.rollback()
    
    async def get_redesign_result(self, project_id: str):
        """获取再设计结果"""
        try:
            # 这里可以添加从数据库获取结果的逻辑
            logger.info(f"获取项目结果: {project_id}")
            return None
        except Exception as e:
            logger.error(f"获取再设计结果失败: {str(e)}")
            return None
    
    async def get_redesign_image_path(self, project_id: str, image_type: str):
        """获取再设计图片路径"""
        try:
            # 构建图片路径
            if image_type == "original":
                filename = f"{project_id}_original.jpg"
            elif image_type == "result":
                filename = f"{project_id}_final.jpg"
            elif image_type.startswith("step_"):
                step_num = image_type.split("_")[1]
                filename = f"{project_id}_step_{step_num}.jpg"
            else:
                filename = f"{project_id}_{image_type}.jpg"
            
            # 确定目录
            if image_type.startswith("step_"):
                file_path = os.path.join(settings.output_dir, "steps", filename)
            else:
                file_path = os.path.join(settings.output_dir, "redesign_projects", filename)
            
            return file_path
        except Exception as e:
            logger.error(f"获取图片路径失败: {str(e)}")
            return None
    
    async def list_projects(self, limit: int = 10, offset: int = 0):
        """获取项目列表"""
        try:
            # 这里可以添加从数据库获取项目列表的逻辑
            logger.info(f"获取项目列表: limit={limit}, offset={offset}")
            return []
        except Exception as e:
            logger.error(f"获取项目列表失败: {str(e)}")
            return []
    
    async def delete_project(self, project_id: str):
        """删除项目"""
        try:
            # 这里可以添加删除项目的逻辑
            logger.info(f"删除项目: {project_id}")
            return True
        except Exception as e:
            logger.error(f"删除项目失败: {str(e)}")
            return False
    
    async def get_system_stats(self):
        """获取系统统计信息"""
        try:
            return {
                "total_projects": 0,
                "total_images_processed": 0,
                "average_processing_time": 0,
                "system_status": "healthy"
            }
        except Exception as e:
            logger.error(f"获取系统统计失败: {str(e)}")
            return {}
