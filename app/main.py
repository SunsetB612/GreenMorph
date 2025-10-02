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
    ImageAnalysisResponse,
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
from app.core.redesign import router as redesign_router

# 注册路由
app.include_router(redesign_router, prefix="/api/redesign", tags=["改造项目"])


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
        "debug": settings.debug,
        "output_dir": settings.output_dir,
        "max_file_size": settings.max_file_size,
        "supported_formats": settings.allowed_image_types
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
