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
from ai_modules.enhanced_step_generator import EnhancedStepGenerator
from ai_modules.progressive_step_generator import ProgressiveStepGenerator
from app.shared.utils.file_manager import FileManager
from app.config import settings
from app.core.redesign.style_models import RedesignStyle, get_style_description


class RedesignService:
    """旧物再设计主服务"""
    
    def __init__(self):
        self.image_analyzer = ImageAnalyzer()
        self.multimodal_api = MultimodalAPI()
        self.image_generator = ImageGenerator()
        self.step_visualizer = StepVisualizer()
        self.enhanced_step_generator = EnhancedStepGenerator()
        self.progressive_step_generator = ProgressiveStepGenerator()
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
    
    async def _get_cached_analysis(self, request: RedesignRequest, db) -> Optional[ImageAnalysisResponse]:
        """
        从数据库获取缓存的图片分析结果
        
        Args:
            request: 再设计请求
            db: 数据库会话
            
        Returns:
            ImageAnalysisResponse: 缓存的分析结果，如果没有则返回None
        """
        try:
            if not db or not request.input_image_id:
                return None
            
            from app.core.redesign.models import InputImage
            from app.shared.models import ImageAnalysisResponse
            import json
            
            # 从数据库查询图片记录
            input_image = db.query(InputImage).filter(
                InputImage.id == request.input_image_id
            ).first()
            
            if not input_image or not input_image.analysis_result:
                return None
            
            # 解析JSON格式的分析结果
            analysis_data = json.loads(input_image.analysis_result)
            
            # 转换为ImageAnalysisResponse对象
            return ImageAnalysisResponse(**analysis_data)
            
        except Exception as e:
            logger.error(f"获取缓存分析结果失败: {str(e)}")
            return None
    
    async def redesign_item(self, request: RedesignRequest, db=None, user_id: str = "user1") -> RedesignResponse:
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
            
            # 1. 获取图片来源（优先云端URL用于图生图）
            source_image_url = await self._get_source_image_url(request, db)
            
            # 尝试从数据库获取缓存的分析结果
            image_analysis = await self._get_cached_analysis(request, db)
            
            # 如果没有缓存结果，则进行分析
            if image_analysis is None:
                logger.info("未找到缓存的分析结果，开始重新分析...")
                image_analysis = await self.image_analyzer.analyze_image(image_data)
            else:
                logger.info("使用缓存的图片分析结果")
            
            # 2. 生成改造计划（包含网页搜索灵感）
            redesign_plan = await self.multimodal_api.generate_redesign_plan(
                image_analysis=image_analysis.dict(),
                user_requirements=request.user_requirements,
                target_style=request.target_style.value,
                target_materials=[m.value for m in (request.target_materials or [])],
                web_search_func=self._web_search_wrapper
            )
            
            # 将原图分析信息和源图URL添加到改造计划中，供图像生成使用
            redesign_plan['original_analysis'] = image_analysis.dict()
            redesign_plan['source_image_url'] = source_image_url  # 添加源图URL供步骤图生成使用
            
            # 调试：打印改造计划内容
            logger.info(f"🔍 改造计划内容:")
            logger.info(f"   改造计划键: {list(redesign_plan.keys())}")
            logger.info(f"   步骤数据: {redesign_plan.get('steps', [])}")
            logger.info(f"   步骤数量: {len(redesign_plan.get('steps', []))}")
            if redesign_plan.get('steps'):
                logger.info(f"   第一个步骤: {redesign_plan['steps'][0] if redesign_plan['steps'] else 'None'}")
            
            # 如果步骤数量不足，尝试生成完备方案
            if len(redesign_plan.get('steps', [])) < 6:
                logger.warning(f"⚠️ 步骤数量不足({len(redesign_plan.get('steps', []))}个)，尝试生成完备方案...")
                # 获取搜索灵感数据
                inspiration_data = await self._get_inspiration_data(
                    image_analysis=image_analysis,
                    user_requirements=request.user_requirements
                )
                redesign_plan = await self._generate_comprehensive_plan(
                    image_analysis=image_analysis,
                    user_requirements=request.user_requirements,
                    target_style=request.target_style,
                    inspiration_data=inspiration_data
                )
                logger.info(f"✅ 完备方案生成完成，步骤数量: {len(redesign_plan.get('steps', []))}")
            
            # 3. 尝试同会话生成所有图像（推荐模式）
            logger.info("🎨 尝试同会话生成最终效果图和步骤图...")
            conversation_result = None
            
            if source_image_url:
                try:
                    steps_data = redesign_plan.get('steps', [])
                    conversation_result = await self.image_generator.generate_all_images_in_conversation(
                        source_image_url=source_image_url,
                        redesign_plan=redesign_plan,
                        user_requirements=request.user_requirements,
                        target_style=request.target_style.value,
                        steps=steps_data
                    )
                    logger.info("✅ 同会话生成模式成功")
                except Exception as ce:
                    logger.warning(f"同会话生成失败，降级到分离模式: {ce}")
            
            # 如果同会话生成成功，直接使用结果
            if conversation_result:
                final_image = conversation_result['final_image']
                step_images = conversation_result['step_images']
                logger.info(f"✅ 同会话模式完成：最终效果图 + {len(step_images)} 张步骤图")
                logger.info(f"🔍 同会话模式获取的step_images数量: {len(step_images)}")
            else:
                # 降级到原有的分离生成模式
                logger.info("🔄 降级到分离生成模式...")
                
                final_image = None
                # 3.1 若存在云端URL，优先尝试图生图
                if source_image_url:
                    logger.info(f"尝试图生图模式，源图URL: {source_image_url}")
                    try:
                        final_image = await self.image_generator.generate_final_effect_image_from_url(
                            source_image_url=source_image_url,
                            redesign_plan=redesign_plan,
                            user_requirements=request.user_requirements,
                            target_style=request.target_style.value
                        )
                        logger.info("✅ 图生图模式成功")
                    except Exception as ie:
                        logger.warning(f"图生图失败，准备降级为文生图: {ie}")
                        final_image = None
                # 3.2 降级：使用本地原图+文生图策略（此时才加载本地图片，避免不必要IO）
                if final_image is None:
                    image_data = await self._get_image_data(request)
                    if not self.image_analyzer.validate_image(image_data):
                        raise ValueError("图片格式不支持或文件过大")
                    original_image = Image.open(io.BytesIO(image_data))
                    final_image = await self.image_generator.generate_final_effect_image(
                        original_image=original_image,
                        redesign_plan=redesign_plan,
                        user_requirements=request.user_requirements,
                        target_style=request.target_style.value
                    )
                if final_image is None:
                    raise Exception("最终效果图生成失败")
                logger.info("✅ 最终效果图生成完成")
            
            # 4. 生成步骤图像（仅在分离模式时需要）
            if not conversation_result:  # 只有在分离模式时才需要单独生成步骤图
                step_images = []  # 初始化步骤图像列表
                steps_data = redesign_plan.get('steps', [])
                logger.info(f"🔧 开始生成 {len(steps_data)} 个步骤图像...")
                original_image_for_steps = None
                try:
                    if source_image_url:
                        logger.info(f"尝试从URL下载原图用于步骤生成: {source_image_url}")
                        original_image_for_steps = await self.image_generator._download_image_to_pil(source_image_url)
                        if original_image_for_steps:
                            logger.info("✅ 从URL成功下载原图")
                except Exception as e:
                    logger.warning(f"⚠️ 从URL下载原图失败: {e}")
                    original_image_for_steps = None
                if original_image_for_steps is None:
                    # 若降级时已加载original_image，则复用；否则按需加载一次
                    try:
                        original_image_for_steps = original_image
                    except NameError:
                        img_bytes = await self._get_image_data(request)
                        original_image_for_steps = Image.open(io.BytesIO(img_bytes))
                step_images = await self.image_generator.generate_step_images(
                    original_image=original_image_for_steps,
                    steps=steps_data,
                    base_features=image_analysis.features,
                    redesign_plan=redesign_plan,  # 传递redesign_plan，包含source_image_url
                    final_result_image=final_image  # 传递最终效果图作为目标引导
                )
                logger.info("✅ 步骤图像生成完成")
            else:
                logger.info("✅ 步骤图像已在同会话模式中生成")
            
            # 5. 生成增强版步骤图（如果还没有步骤图）
            if not step_images:
                logger.info("🎨 开始生成增强版步骤图...")
                
                # 确保有原图用于步骤生成
                if 'original_image_for_steps' not in locals():
                    try:
                        if source_image_url:
                            original_image_for_steps = await self.image_generator._download_image_to_pil(source_image_url)
                        else:
                            img_bytes = await self._get_image_data(request)
                            original_image_for_steps = Image.open(io.BytesIO(img_bytes))
                    except Exception as e:
                        logger.warning(f"⚠️ 获取原图失败，使用占位图: {e}")
                        original_image_for_steps = Image.new('RGB', (512, 512), 'lightgray')
                
                # 使用渐进式步骤生成器（真正的渐进式改造）
                step_images = await self.progressive_step_generator.generate_progressive_steps(
                    original_image=original_image_for_steps,
                    final_image=final_image,
                    steps=steps_data,
                    user_requirements=request.user_requirements,
                    target_style=request.target_style
                )
                logger.info(f"✅ 渐进式步骤图生成完成，共{len(step_images)}张")
            
            # 生成渐进式对比图
            progressive_comparison = await self.progressive_step_generator.create_progressive_comparison(
                original_image=original_image_for_steps if 'original_image_for_steps' in locals() else Image.new('RGB', (512, 512), 'lightgray'),
                step_images=step_images,
                final_image=final_image,
                steps=steps_data
            )
            
            # 分析步骤图的渐进性
            step_analysis = await self.progressive_step_generator.generate_step_analysis(
                original_image=original_image_for_steps if 'original_image_for_steps' in locals() else Image.new('RGB', (512, 512), 'lightgray'),
                step_images=step_images,
                final_image=final_image,
                steps=steps_data
            )
            
            # 合并所有可视化图像（只包含对比图，不重复步骤图）
            step_visualizations = [progressive_comparison]
            
            logger.info(f"✅ 增强版步骤图生成完成，共{len(step_visualizations)}张图像")
            
            # 6. 保存所有图像
            logger.info("💾 保存生成的图像...")
            logger.info(f"🔍 准备保存的step_images数量: {len(step_images)}")
            try:
                saved_images = await self._save_all_images(
                    task_id, final_image, step_images, step_visualizations, user_id
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

    async def _get_source_image_url(self, request, db) -> Optional[str]:
        """从数据库优先获取云端URL，若无则返回None"""
        try:
            if not db:
                logger.info("🔍 数据库连接为空，无法获取源图URL")
                return None
            
            input_image_id = getattr(request, 'input_image_id', None)
            logger.info(f"🔍 请求中的input_image_id: {input_image_id}")
            
            if input_image_id:
                from app.core.redesign.models import InputImage
                record = db.query(InputImage).filter(InputImage.id == input_image_id).first()
                
                if record:
                    logger.info(f"🔍 找到数据库记录，cloud_url: {record.cloud_url}")
                    if record.cloud_url:
                        logger.info(f"✅ 获取到OSS URL: {record.cloud_url}")
                        return record.cloud_url
                    else:
                        logger.warning("⚠️ 数据库记录中cloud_url为空")
                else:
                    logger.warning(f"⚠️ 未找到ID为{input_image_id}的图片记录")
            else:
                logger.info("🔍 请求中没有input_image_id，尝试查找最新的图片记录")
                # 备用方案：查找最新的有cloud_url的记录
                from app.core.redesign.models import InputImage
                latest_record = db.query(InputImage).filter(
                    InputImage.cloud_url.isnot(None)
                ).order_by(InputImage.created_at.desc()).first()
                
                if latest_record and latest_record.cloud_url:
                    logger.info(f"✅ 使用最新记录的OSS URL: {latest_record.cloud_url}")
                    return latest_record.cloud_url
                else:
                    logger.warning("⚠️ 没有找到任何有效的cloud_url记录")
                    
        except Exception as e:
            logger.error(f"❌ 获取源图URL异常: {e}")
        
        logger.info("🔍 未获取到OSS URL，返回None")
        return None

    async def _is_url_accessible(self, url: str) -> bool:
        """检测URL是否可访问（HEAD优先，失败则GET小范围）"""
        try:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=10)  # 增加超时时间
            async with aiohttp.ClientSession(timeout=timeout) as session:
                try:
                    logger.info(f"🔍 检测URL可达性: {url}")
                    async with session.head(url, allow_redirects=True) as resp:
                        logger.info(f"✅ HEAD请求成功，状态码: {resp.status}")
                        return 200 <= resp.status < 400
                except Exception as head_error:
                    logger.warning(f"⚠️ HEAD请求失败: {head_error}，尝试GET请求")
                    try:
                        async with session.get(url, allow_redirects=True) as resp:
                            logger.info(f"✅ GET请求成功，状态码: {resp.status}")
                            return 200 <= resp.status < 400
                    except Exception as get_error:
                        logger.warning(f"⚠️ GET请求也失败: {get_error}")
                        return False
        except Exception as e:
            logger.warning(f"❌ URL可达性检测异常: {e}")
            return False
    
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
        step_visualizations: List[Image.Image],
        user_id: str = "user1"
    ) -> Dict[str, str]:
        """保存所有生成的图像"""
        try:
            saved_images = {}
            
            # 保存最终效果图
            final_bytes = self._image_to_bytes(final_image)
            final_path = self.file_manager.save_output_file(final_bytes, task_id, "final", userid=user_id)
            saved_images['final_image'] = final_path
            
            # 保存步骤图像
            step_image_paths = []
            for i, step_image in enumerate(step_images):
                step_bytes = self._image_to_bytes(step_image)
                step_path = self.file_manager.save_output_file(step_bytes, task_id, "step", i+1, userid=user_id)
                step_image_paths.append(step_path)
            saved_images['step_images'] = step_image_paths
            
            # 保存步骤可视化
            step_viz_paths = []
            for i, viz_image in enumerate(step_visualizations):
                viz_bytes = self._image_to_bytes(viz_image)
                viz_path = self.file_manager.save_output_file(viz_bytes, task_id, "visualization", i+1, userid=user_id)
                step_viz_paths.append(viz_path)
            saved_images['step_visualizations'] = step_viz_paths
            
            logger.info(f"所有图像已保存: {task_id}")
            return saved_images
            
        except Exception as e:
            logger.error(f"图像保存失败: {str(e)}")
            raise Exception(f"图像保存失败: {str(e)}")
    
    def _image_to_bytes(self, image: Image.Image) -> bytes:
        """将PIL图像转换为字节"""
        try:
            import io
            
            # 验证图像对象
            if not isinstance(image, Image.Image):
                raise ValueError(f"输入不是有效的PIL图像对象: {type(image)}")
            
            # 确保图像是RGB格式
            if image.mode != 'RGB':
                logger.info(f"转换图像模式从 {image.mode} 到 RGB")
                image = image.convert('RGB')
            
            # 验证图像尺寸
            if image.size[0] == 0 or image.size[1] == 0:
                raise ValueError(f"图像尺寸无效: {image.size}")
            
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=95, optimize=True)
            
            # 验证生成的字节数据
            image_bytes = buffer.getvalue()
            if len(image_bytes) == 0:
                raise ValueError("图像转换后字节数据为空")
            
            logger.info(f"✅ 图像转换成功，大小: {len(image_bytes)} bytes")
            return image_bytes
            
        except Exception as e:
            logger.error(f"❌ 图像转换为字节失败: {str(e)}")
            logger.error(f"❌ 图像信息: 模式={getattr(image, 'mode', 'unknown')}, 尺寸={getattr(image, 'size', 'unknown')}")
            raise Exception(f"图像转换失败: {str(e)}")
    
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
        # 处理Windows路径分隔符
        normalized_path = file_path.replace("\\", "/")
        
        if normalized_path.startswith("static/"):
            return f"/{normalized_path}"
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
            
            # 确保输出目录存在（使用用户分目录结构）
            output_dir = Path("static/users/user1/output")
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
            
            saved_images['final_image_url'] = f"/static/users/user1/output/{final_filename}"
            
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
                
                step_image_urls.append(f"/static/users/user1/output/{step_filename}")
            
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
            
            # 清理用户输出目录中的旧文件
            output_pattern = os.path.join("static/users", "*", "output", "*")
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
    
    async def save_redesign_result(self, result: RedesignResponse, db=None, request: Optional[RedesignRequest]=None, user_id: int = 1):
        """保存再设计结果到数据库"""
        try:
            if db is None:
                logger.warning("未提供数据库会话，跳过保存")
                return
            
            from app.core.redesign.models import RedesignProject, RedesignStep, ProjectDetail, InputDemand
            
            # 创建改造项目记录
            project = RedesignProject(
                user_id=user_id,
                project_name=f"改造项目_{int(__import__('time').time())}",
                output_image_path=result.final_image_url,
                input_image_id=getattr(request, 'input_image_id', None) if request else None,
            )
            
            db.add(project)
            db.commit()
            db.refresh(project)
            
            # 如有用户需求，保存到 InputDemand 并关联到项目
            if request and getattr(request, 'user_requirements', None):
                demand = InputDemand(
                    user_id=user_id,
                    demand=request.user_requirements
                )
                db.add(demand)
                db.commit()
                db.refresh(demand)
                project.input_demand_id = demand.id
                db.add(project)
                db.commit()
            
            # 保存改造步骤
            # 将生成的步骤图片URL（如果有）写入步骤记录
            step_image_urls = getattr(result, 'step_images', []) or []
            for idx, step_data in enumerate(result.redesign_guide):
                step = RedesignStep(
                    project_id=project.id,
                    step_number=step_data.step_number,
                    description=step_data.description,
                    step_image_path= step_image_urls[idx] if idx < len(step_image_urls) else None
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
            
            # 确定目录（使用用户分目录结构）
            if image_type.startswith("step_"):
                file_path = os.path.join("static/users/user1/output/steps", filename)
            else:
                file_path = os.path.join("static/users/user1/output/result", filename)
            
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
    
    async def _web_search_wrapper(self, search_term: str, explanation: str = "") -> str:
        """
        网页搜索包装函数
        
        Args:
            search_term: 搜索关键词
            explanation: 搜索说明
            
        Returns:
            搜索结果文本
        """
        try:
            # 尝试使用真实的web_search API
            try:
                from ai_modules.web_search import web_search
                from app.config import settings
                
                # 检查是否配置了搜索API
                if (settings.google_search_api_key and settings.google_search_engine_id) or settings.serpapi_key:
                    logger.info(f"🔍 使用真实网页搜索: {search_term}")
                    print(f"🔍 搜索关键词: {search_term}")
                    print(f"📝 搜索说明: {explanation}")
                    print(f"   🌐 搜索关键词: {search_term}")
                    print(f"   🚀 使用真实搜索API")
                    
                    result = await web_search(search_term, explanation)
                    
                    if result:
                        print(f"   ✅ 真实搜索完成，获取到内容长度: {len(result)} 字符")
                        return result
                    else:
                        print(f"   ⚠️ 真实搜索无结果，降级到模拟数据")
                        raise Exception("搜索无结果")
                else:
                    print(f"   ⚠️ 未配置搜索API密钥，使用模拟数据")
                    raise Exception("未配置搜索API")
                    
            except Exception as search_error:
                # 降级到模拟搜索结果
                logger.warning(f"真实搜索失败，使用模拟数据: {search_error}")
                print(f"   🔄 降级到模拟搜索结果")
                
                mock_results = self._get_mock_search_results(search_term)
                print(f"   ✅ 模拟搜索完成，获取到 {len(mock_results.split('。'))} 条相关信息")
                
                return mock_results
            
        except Exception as e:
            logger.error(f"网页搜索失败: {e}")
            return ""
    
    def _get_mock_search_results(self, search_term: str) -> str:
        """获取模拟的搜索结果"""
        # 根据搜索词返回相关的模拟结果
        if "椅子" in search_term or "chair" in search_term:
            return """
            小红书用户分享：旧椅子改造成小书架，在座位下方增加储物格，既保持了椅子的外观又增加了实用性。
            Pinterest DIY: 将老式木椅重新打磨上漆，保持原有颜色，只在扶手处增加杯托功能。
            宜家改造案例：椅子靠背改造成小型展示架，可以放置装饰品或小植物。
            豆瓣小组分享：椅子改造技巧 - 保持原有木材质感，重点改变结构比例。
            YouTube教程：如何给旧椅子增加储物功能而不改变外观。
            """
        elif "桌子" in search_term or "table" in search_term:
            return """
            小红书改造：旧桌子改造成工作台，在桌面下方增加抽屉，保持原有木色。
            Pinterest创意：桌子改造成移动工作站，增加轮子和侧面储物。
            知乎分享：桌子翻新技巧 - 保持表面纹理，重点改造功能结构。
            """
        else:
            return """
            旧物改造通用技巧：保持原有材质和颜色，重点改变结构和功能。
            DIY社区分享：改造时注意尺寸限制，避免过度改变原有比例。
            改造平台推荐：使用环保材料，保持物品的实用性。
            """
    
    async def _generate_comprehensive_plan(
        self,
        image_analysis: Dict[str, Any],
        user_requirements: str,
        target_style: str,
        inspiration_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成完备的改造方案 - 专门用于生成详细计划"""
        logger.info("🔧 开始生成完备改造方案...")
        
        try:
            # 使用增强的提示词生成完备方案
            comprehensive_plan = await self.multimodal_api.generate_comprehensive_plan(
                image_analysis=image_analysis,
                user_requirements=user_requirements,
                target_style=target_style,
                inspiration_data=inspiration_data
            )
            
            logger.info(f"✅ 完备方案生成成功，包含 {len(comprehensive_plan.get('steps', []))} 个步骤")
            return comprehensive_plan
            
        except Exception as e:
            logger.error(f"❌ 生成完备方案失败: {e}")
            # 返回基础方案作为备选
            return {
                'title': '基础改造方案',
                'description': '基于物品特征的改造计划',
                'steps': [
                    {
                        'title': '准备工作',
                        'description': '清洁和检查物品状态',
                        'materials_needed': ['清洁剂', '抹布'],
                        'tools_needed': ['手套'],
                        'estimated_time': '30分钟',
                        'difficulty': '简单',
                        'safety_notes': '注意清洁剂使用安全'
                    }
                ],
                'total_cost': '50元',
                'sustainability_score': 8,
                'tips': ['保持原有材料特色', '注重实用性']
            }
    
    async def _get_inspiration_data(
        self,
        image_analysis: Dict[str, Any],
        user_requirements: str
    ) -> Dict[str, Any]:
        """获取搜索灵感数据"""
        try:
            main_objects = image_analysis.get('main_objects', ['furniture'])
            item_type = main_objects[0] if main_objects else 'furniture'
            materials = [str(m).replace('MaterialType.', '') for m in image_analysis.get('materials', [])]
            
            logger.info(f"🔍 获取 {item_type} 的搜索灵感...")
            
            inspiration_data = await self.inspiration_engine.get_renovation_inspiration(
                item_type=item_type,
                materials=materials,
                user_requirements=user_requirements,
                web_search_func=self._web_search_wrapper
            )
            
            if not inspiration_data or not inspiration_data.get('ideas'):
                logger.warning("⚠️ 搜索结果为空，使用严格约束模式")
                inspiration_data = {'ideas': [], 'constraints': ['strict_reality_mode']}
            
            return inspiration_data
            
        except Exception as e:
            logger.error(f"❌ 获取搜索灵感失败: {e}")
            return {'ideas': [], 'constraints': ['strict_reality_mode']}
