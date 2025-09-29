"""
GreenMorph FastAPI 主应用
提供旧物再设计的REST API接口
"""

import os
import time
import base64
from contextlib import asynccontextmanager
from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger

from app.config import settings
from app.database import init_db
from app.shared.models import (
    ImageAnalysisRequest, ImageAnalysisResponse,
    RedesignRequest, RedesignResponse,
    ErrorResponse, HealthResponse
)
from app.core.redesign.redesign_service import RedesignService


# 全局服务实例
redesign_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global redesign_service
    
    # 启动时初始化
    logger.info("启动 GreenMorph 服务...")
    await init_db()
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
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/output", StaticFiles(directory=settings.output_dir), name="output")


def get_redesign_service() -> RedesignService:
    """获取再设计服务实例"""
    if redesign_service is None:
        raise HTTPException(status_code=503, detail="服务未初始化")
    return redesign_service

# 导入路由
from app.core.auth import router as auth_router
from app.core.user import router as user_router
from app.core.redesign import router as redesign_router
from app.core.community import router as community_router
from app.core.gamification import router as gamification_router

# 注册路由
app.include_router(auth_router, prefix="/api/auth", tags=["认证"])
app.include_router(user_router, prefix="/api/users", tags=["用户"])
app.include_router(redesign_router, prefix="/api/redesign", tags=["改造项目"])
app.include_router(community_router, prefix="/api/community", tags=["社区"])
app.include_router(gamification_router, prefix="/api/gamification", tags=["激励系统"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用 GreenMorph - AI驱动的旧物再设计平台",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=int(time.time())
    )


# ==================== 图片分析API ====================

@app.post("/api/analyze/image", response_model=ImageAnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    service: RedesignService = Depends(get_redesign_service)
):
    """
    分析上传的旧物图片
    - 识别物品类型、材质、状态
    - 评估改造潜力
    - 提供改造建议
    """
    try:
        logger.info(f"开始分析图片: {file.filename}")
        
        # 验证文件类型
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="只支持图片文件")
        
        # 读取文件内容
        content = await file.read()
        
        # 调用分析服务
        result = await service.analyze_image(content, file.filename)
        
        logger.info(f"图片分析完成: {file.filename}")
        return result
        
    except Exception as e:
        logger.error(f"图片分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"图片分析失败: {str(e)}")


@app.post("/api/analyze/image/base64", response_model=ImageAnalysisResponse)
async def analyze_image_base64(
    request: ImageAnalysisRequest,
    service: RedesignService = Depends(get_redesign_service)
):
    """
    分析Base64编码的图片
    """
    try:
        logger.info("开始分析Base64图片")
        
        # 解码Base64图片
        try:
            image_data = base64.b64decode(request.image_base64)
        except Exception as e:
            raise HTTPException(status_code=400, detail="无效的Base64编码")
        
        # 调用分析服务
        result = await service.analyze_image(image_data, request.filename or "image.jpg")
        
        logger.info("Base64图片分析完成")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Base64图片分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"图片分析失败: {str(e)}")


# ==================== 再设计API ====================

@app.post("/api/redesign/generate", response_model=RedesignResponse)
async def generate_redesign(
    request: RedesignRequest,
    background_tasks: BackgroundTasks,
    service: RedesignService = Depends(get_redesign_service)
):
    """
    生成再设计方案
    - 基于图片分析和用户需求
    - 生成多种改造方案
    - 提供详细的设计说明和步骤
    """
    try:
        logger.info(f"开始生成再设计方案: {request.project_name}")
        
        # 调用再设计服务
        result = await service.generate_redesign(request)
        
        # 后台任务：保存结果到数据库
        background_tasks.add_task(service.save_redesign_result, result)
        
        logger.info(f"再设计方案生成完成: {request.project_name}")
        return result
        
    except Exception as e:
        logger.error(f"再设计方案生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"再设计方案生成失败: {str(e)}")


@app.get("/api/redesign/{project_id}")
async def get_redesign_result(
    project_id: str,
    service: RedesignService = Depends(get_redesign_service)
):
    """
    获取再设计结果
    """
    try:
        result = await service.get_redesign_result(project_id)
        if not result:
            raise HTTPException(status_code=404, detail="项目不存在")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取再设计结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取结果失败: {str(e)}")


@app.get("/api/redesign/{project_id}/download/{image_type}")
async def download_redesign_image(
    project_id: str,
    image_type: str,
    service: RedesignService = Depends(get_redesign_service)
):
    """
    下载再设计图片
    - image_type: original, result, step_1, step_2, step_3
    """
    try:
        # 验证图片类型
        valid_types = ["original", "result", "step_1", "step_2", "step_3"]
        if image_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"无效的图片类型，支持的类型: {valid_types}")
        
        # 获取图片路径
        image_path = await service.get_redesign_image_path(project_id, image_type)
        if not image_path or not Path(image_path).exists():
            raise HTTPException(status_code=404, detail="图片不存在")
        
        return FileResponse(
            path=image_path,
            media_type="image/jpeg",
            filename=f"{project_id}_{image_type}.jpg"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载图片失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载图片失败: {str(e)}")


# ==================== 项目管理API ====================

@app.get("/api/projects")
async def list_projects(
    limit: int = 10,
    offset: int = 0,
    service: RedesignService = Depends(get_redesign_service)
):
    """
    获取项目列表
    """
    try:
        projects = await service.list_projects(limit=limit, offset=offset)
        return {
            "projects": projects,
            "total": len(projects),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"获取项目列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")


@app.delete("/api/projects/{project_id}")
async def delete_project(
    project_id: str,
    service: RedesignService = Depends(get_redesign_service)
):
    """
    删除项目
    """
    try:
        success = await service.delete_project(project_id)
        if not success:
            raise HTTPException(status_code=404, detail="项目不存在")
        return {"message": "项目删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除项目失败: {str(e)}")


# ==================== 系统信息API ====================

@app.get("/api/system/info")
async def get_system_info():
    """
    获取系统信息
    """
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "debug": settings.debug,
        "output_dir": settings.output_dir,
        "max_file_size": settings.max_file_size,
        "supported_formats": settings.supported_formats
    }


@app.get("/api/system/stats")
async def get_system_stats(
    service: RedesignService = Depends(get_redesign_service)
):
    """
    获取系统统计信息
    """
    try:
        stats = await service.get_system_stats()
        return stats
    except Exception as e:
        logger.error(f"获取系统统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取系统统计失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"启动 GreenMorph 服务在 {settings.host}:{settings.port}")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
