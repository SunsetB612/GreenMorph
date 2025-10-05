"""
激励系统API路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.gamification.models import Achievement

router = APIRouter()


@router.get("/achievements")
async def get_achievements(db: Session = Depends(get_db)):
    """获取所有成就列表"""
    try:
        # 从数据库获取所有成就
        achievements = db.query(Achievement).all()

        # 转换为前端需要的格式
        achievements_list = []
        for achievement in achievements:
            achievements_list.append({
                "id": achievement.id,
                "name": achievement.name,
                "description": achievement.description,
                "condition_type": achievement.condition_type,
                "condition_value": achievement.condition_value,
                "created_at": achievement.created_at.isoformat() if achievement.created_at else None
            })

        return {
            "code": 200,
            "message": "获取成就列表成功",
            "data": achievements_list
        }

    except Exception as e:
        return {
            "code": 500,
            "message": f"获取成就列表失败: {str(e)}",
            "data": []
        }


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
