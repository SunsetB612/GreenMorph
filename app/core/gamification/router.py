"""
激励系统API路由
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/achievements")
async def get_achievements():
    """获取所有成就列表"""
    pass


@router.get("/achievements/user/{user_id}")
async def get_user_achievements(user_id: int):
    """获取用户的成就列表"""
    pass


@router.post("/achievements/check")
async def check_achievements():
    """检查并发放成就"""
    pass


@router.get("/leaderboard")
async def get_leaderboard():
    """获取积分排行榜"""
    pass
