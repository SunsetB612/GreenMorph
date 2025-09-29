"""
认证相关API路由
"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/register")
async def register():
    """用户注册"""
    pass


@router.post("/login")
async def login():
    """用户登录"""
    pass


@router.post("/logout")
async def logout():
    """用户登出"""
    pass


@router.post("/refresh")
async def refresh_token():
    """刷新令牌"""
    pass
