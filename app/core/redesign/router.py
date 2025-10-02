"""
改造项目API路由
"""

import uuid
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from loguru import logger

from app.shared.models import (
    ImageAnalysisResponse,
    RedesignRequest, RedesignResponse
)
from app.core.redesign.redesign_service import RedesignService
from app.core.redesign.models import InputImage
from app.database import get_db
from app.config import settings

router = APIRouter()

def get_redesign_service() -> RedesignService:
    """获取再设计服务实例"""
    # 这里需要从主应用获取服务实例
    try:
        from app.main import redesign_service
        if redesign_service is None:
            raise HTTPException(status_code=503, detail="服务未初始化")
        return redesign_service
    except ImportError:
        # 如果无法导入，创建一个新的服务实例
        from app.core.redesign.redesign_service import RedesignService
        return RedesignService()


# ==================== 图片分析API ====================

@router.post("/analyze/image", response_model=ImageAnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    service: RedesignService = Depends(get_redesign_service),
    db: Session = Depends(get_db)
):
    """
    分析上传的旧物图片
    - 识别物品类型、材质、状态
    - 评估改造潜力
    - 提供改造建议
    - 保存图片到文件夹和数据库
    """
    try:
        logger.info(f"开始分析图片: {file.filename}")
        
        # 验证文件类型
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="只支持图片文件")
        
        # 验证文件大小
        content = await file.read()
        if len(content) > settings.max_file_size:
            raise HTTPException(status_code=400, detail=f"文件过大，最大支持 {settings.max_file_size} 字节")
        
        # 调用分析服务
        result = await service.analyze_image_direct(content)
        
        # 保存上传的图片到用户专属目录
        # 注意：这里暂时使用userid="user1"，实际应用中应该从认证中获取用户ID
        userid = "user1"  # TODO: 从认证中获取真实用户ID
        
        # 根据分析结果生成有意义的文件名前缀
        main_objects = result.main_objects
        if main_objects:
            # 使用识别到的主要物体作为前缀
            prefix = main_objects[0].replace(" ", "_").lower()
        else:
            prefix = "unknown_item"
        
        file_path, public_url = service.file_manager.save_uploaded_file(
            content, file.filename, userid, prefix=prefix, category="input"
        )
        
        # 保存图片信息到数据库
        input_image = InputImage(
            user_id=1,  # TODO: 从认证中获取真实用户ID
            original_filename=file.filename,
            input_image_path=file_path,
            input_image_size=len(content),
            mime_type=file.content_type
        )
        
        db.add(input_image)
        db.commit()
        db.refresh(input_image)
        
        logger.info(f"图片信息已保存到数据库，ID: {input_image.id}")
        
        # 更新结果中的文件信息
        result.uploaded_file = file.filename
        result.file_path = file_path
        result.input_number = input_image.id  # 使用数据库ID作为输入编号
        
        logger.info(f"图片分析完成: {file.filename}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"图片分析失败: {str(e)}")
        # 如果数据库操作失败，回滚事务
        db.rollback()
        raise HTTPException(status_code=500, detail=f"图片分析失败: {str(e)}")


# ==================== 再设计API ====================

@router.post("/generate", response_model=RedesignResponse)
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
        logger.info(f"开始生成再设计方案")
        
        # 调用再设计服务
        result = await service.redesign_item(request)
        
        # 后台任务：保存结果到数据库
        background_tasks.add_task(service.save_redesign_result, result)
        
        logger.info(f"再设计方案生成完成")
        return result
        
    except Exception as e:
        logger.error(f"再设计方案生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"再设计方案生成失败: {str(e)}")


# ==================== 图片管理API ====================

@router.get("/images")
async def get_uploaded_images(
    db: Session = Depends(get_db),
    limit: int = 10,
    offset: int = 0
):
    """获取上传的图片列表"""
    try:
        images = db.query(InputImage).offset(offset).limit(limit).all()
        
        result = []
        for image in images:
            result.append({
                "id": image.id,
                "user_id": image.user_id,
                "original_filename": image.original_filename,
                "input_image_path": image.input_image_path,
                "input_image_size": image.input_image_size,
                "mime_type": image.mime_type,
                "created_at": image.created_at.isoformat() if image.created_at else None
            })
        
        return {
            "images": result,
            "total": len(result),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"获取图片列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取图片列表失败: {str(e)}")


@router.get("/images/{image_id}")
async def get_image_info(
    image_id: int,
    db: Session = Depends(get_db)
):
    """获取单个图片信息"""
    try:
        image = db.query(InputImage).filter(InputImage.id == image_id).first()
        
        if not image:
            raise HTTPException(status_code=404, detail="图片不存在")
        
        return {
            "id": image.id,
            "user_id": image.user_id,
            "original_filename": image.original_filename,
            "input_image_path": image.input_image_path,
            "input_image_size": image.input_image_size,
            "mime_type": image.mime_type,
            "created_at": image.created_at.isoformat() if image.created_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取图片信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取图片信息失败: {str(e)}")


# ==================== 项目管理API ====================

@router.get("/projects")
async def get_projects():
    """获取用户的改造项目列表"""
    pass


@router.post("/projects")
async def create_project():
    """创建改造项目"""
    pass


@router.get("/projects/{project_id}")
async def get_project(project_id: int):
    """获取单个改造项目"""
    pass


@router.put("/projects/{project_id}")
async def update_project(project_id: int):
    """更新改造项目"""
    pass


@router.delete("/projects/{project_id}")
async def delete_project(project_id: int):
    """删除改造项目"""
    pass


@router.post("/projects/{project_id}/analyze")
async def analyze_project(project_id: int):
    """分析改造项目"""
    pass


@router.post("/projects/{project_id}/generate")
async def generate_redesign_by_project(project_id: int):
    """生成改造方案"""
    pass
