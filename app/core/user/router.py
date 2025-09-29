"""
用户管理API路由
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/profile")
async def get_profile():
    """获取用户资料"""
    pass


@router.put("/profile")
async def update_profile():
    """更新用户资料"""
    pass


@router.post("/upload-avatar")
async def upload_avatar():
    """上传头像"""
    pass
