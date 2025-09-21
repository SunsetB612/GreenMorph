"""
GreenMorph FastAPI 主应用
提供旧物再设计的REST API接口
"""

import os
import time
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger

from models import (
    ImageAnalysisRequest, ImageAnalysisResponse,
    RedesignRequest, RedesignResponse,
    ErrorResponse, HealthResponse
)
from redesign_service import RedesignService
from config import settings


# 全局服务实例
redesign_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global redesign_service
    
    # 启动时初始化
    logger.info("启动 GreenMorph 服务...")
    redesign_service = RedesignService()
    logger.info("GreenMorph 服务启动完成")
    
    yield
    
    # 关闭时清理
    logger.info("关闭 GreenMorph 服务...")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI驱动的旧物再设计平台 - 多模态大模型API调用模块",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/outputs", StaticFiles(directory=settings.output_dir), name="outputs")


def get_redesign_service() -> RedesignService:
    """获取再设计服务实例"""
    if redesign_service is None:
        raise HTTPException(status_code=503, detail="服务未初始化")
    return redesign_service


@app.get("/", response_model=dict)
async def root():
    """根路径"""
    return {
        "message": "欢迎使用 GreenMorph - AI驱动的旧物再设计平台",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check(service: RedesignService = Depends(get_redesign_service)):
    """健康检查"""
    return await service.get_health_status()


@app.get("/info", response_model=dict)
async def service_info(service: RedesignService = Depends(get_redesign_service)):
    """获取服务信息"""
    return service.get_service_info()


@app.post("/analyze", response_model=ImageAnalysisResponse)
async def analyze_image(
    request: ImageAnalysisRequest,
    service: RedesignService = Depends(get_redesign_service)
):
    """
    分析旧物图片
    
    提取旧物的主要结构和特征，识别材料类型、颜色、状态等信息
    """
    try:
        return await service.analyze_image(request)
    except Exception as e:
        logger.error(f"图片分析API调用失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/upload", response_model=ImageAnalysisResponse)
async def analyze_uploaded_image(
    file: UploadFile = File(...),
    service: RedesignService = Depends(get_redesign_service)
):
    """
    分析上传的旧物图片
    
    支持直接上传图片文件进行分析
    """
    try:
        # 验证文件类型
        if file.content_type not in settings.allowed_image_types:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件类型: {file.content_type}"
            )
        
        # 验证文件大小
        content = await file.read()
        if len(content) > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"文件过大，最大支持 {settings.max_file_size} 字节"
            )
        
        # 创建分析请求
        request = ImageAnalysisRequest(image_base64=content.hex())
        return await service.analyze_image(request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传图片分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/redesign", response_model=RedesignResponse)
async def redesign_item(
    request: RedesignRequest,
    background_tasks: BackgroundTasks,
    service: RedesignService = Depends(get_redesign_service)
):
    """
    生成旧物再设计方案
    
    基于用户需求和图片分析结果，生成完整的改造方案，包括：
    - 最终效果图
    - 各步骤示意图
    - 详细改造说明书
    - 材料工具清单
    - 成本估算
    """
    try:
        # 添加后台任务：清理旧文件
        background_tasks.add_task(service.cleanup_old_files)
        
        return await service.redesign_item(request)
    except Exception as e:
        logger.error(f"再设计API调用失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/redesign/upload", response_model=RedesignResponse)
async def redesign_uploaded_item(
    file: UploadFile = File(...),
    user_requirements: str = "",
    target_style: str = "modern",
    target_materials: Optional[str] = None,
    budget_range: Optional[str] = None,
    skill_level: str = "beginner",
    background_tasks: BackgroundTasks = None,
    service: RedesignService = Depends(get_redesign_service)
):
    """
    基于上传图片生成再设计方案
    
    支持直接上传图片文件进行再设计
    """
    try:
        # 验证文件
        if file.content_type not in settings.allowed_image_types:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file.content_type}"
            )
        
        content = await file.read()
        if len(content) > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"文件过大，最大支持 {settings.max_file_size} 字节"
            )
        
        # 解析目标材料
        materials = None
        if target_materials:
            materials = [m.strip() for m in target_materials.split(",")]
        
        # 创建再设计请求
        from models import StyleType, MaterialType
        request = RedesignRequest(
            image_base64=content.hex(),
            user_requirements=user_requirements,
            target_style=StyleType(target_style),
            target_materials=[MaterialType(m) for m in (materials or [])],
            budget_range=budget_range,
            skill_level=skill_level
        )
        
        # 添加后台任务
        if background_tasks:
            background_tasks.add_task(service.cleanup_old_files)
        
        return await service.redesign_item(request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传图片再设计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/outputs/{filename}")
async def get_output_file(filename: str):
    """获取输出文件"""
    try:
        file_path = os.path.join(settings.output_dir, filename)
        if os.path.exists(file_path):
            return FileResponse(file_path)
        else:
            raise HTTPException(status_code=404, detail="文件不存在")
    except Exception as e:
        logger.error(f"获取文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/outputs/{filename}")
async def delete_output_file(filename: str):
    """删除输出文件"""
    try:
        file_path = os.path.join(settings.output_dir, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return {"message": "文件删除成功"}
        else:
            raise HTTPException(status_code=404, detail="文件不存在")
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/styles", response_model=List[str])
async def get_available_styles():
    """获取可用的改造风格"""
    from models import StyleType
    return [style.value for style in StyleType]


@app.get("/materials", response_model=List[str])
async def get_available_materials():
    """获取可用的材料类型"""
    from models import MaterialType
    return [material.value for material in MaterialType]


# 错误处理
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "接口不存在", "detail": str(exc)}


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"内部服务器错误: {str(exc)}")
    return {"error": "内部服务器错误", "detail": "请稍后重试"}


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"启动 GreenMorph 服务在 {settings.host}:{settings.port}")
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
