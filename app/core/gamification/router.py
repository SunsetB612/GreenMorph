"""
激励系统API路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.gamification.models import Achievement,UserAchievement
from app.core.redesign.models import RedesignProject
from app.core.user.models import User
from app.core.community.models import Post, Comment, Like
from loguru import logger
from datetime import datetime
router = APIRouter()
def calculate_user_progress(user_id: int, db: Session) -> dict:
    """计算用户在各条件下的进度"""
    from sqlalchemy import and_

    progress = {}

    try:
        # 用户发帖数
        progress["post_count"] = db.query(Post).filter(Post.user_id == user_id).count()

        # 用户评论数
        progress["comment_count"] = db.query(Comment).filter(Comment.user_id == user_id).count()

        # 用户收到的点赞数（基于帖子）
        user_post_ids = [
            post.id for post in db.query(Post.id).filter(Post.user_id == user_id).all()
        ]
        if user_post_ids:
            progress["likes_received"] = db.query(Like).filter(
                and_(
                    Like.target_type == "post",
                    Like.target_id.in_(user_post_ids)
                )
            ).count()
        else:
            progress["likes_received"] = 0

        # 用户发起的改造项目数
        progress["project_count"] = db.query(RedesignProject).filter(
            RedesignProject.user_id == user_id
        ).count()

        logger.info(f"用户 {user_id} 进度统计: {progress}")

    except Exception as e:
        logger.error(f"计算用户进度失败: {e}")
        # 保证返回结构完整
        progress.update({
            "post_count": progress.get("post_count", 0),
            "comment_count": progress.get("comment_count", 0),
            "likes_received": progress.get("likes_received", 0),
            "project_count": progress.get("project_count", 0),
        })

    return progress

@router.get("/achievements")
async def get_achievements(db: Session = Depends(get_db)):
    """获取所有成就列表"""
    try:
        achievements = db.query(Achievement).all()

        achievements_list = [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "condition_type": a.condition_type,
                "condition_value": a.condition_value,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in achievements
        ]

        return {
            "code": 200,
            "message": "获取成就列表成功",
            "data": achievements_list
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取成就列表失败: {e}",
            "data": []
        }

@router.get("/achievements/user/{user_id}")
async def get_user_achievements(user_id: int, db: Session = Depends(get_db)):
    """获取用户的成就进度"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"code": 404, "message": "用户不存在", "data": []}

        all_achievements = db.query(Achievement).all()
        earned = db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id
        ).all()

        earned_ids = {ua.achievement_id for ua in earned}
        earned_map = {ua.achievement_id: ua.earned_at for ua in earned}
        user_progress = calculate_user_progress(user_id, db)

        def build_item(a: Achievement):
            current = user_progress.get(a.condition_type, 0)
            is_earned = a.id in earned_ids
            percentage = (
                min(100, int(current / a.condition_value * 100))
                if a.condition_value > 0 else 0
            )
            return {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "icon": a.icon_filename,
                "condition_type": a.condition_type,
                "condition_value": a.condition_value,
                "status": "achieved" if is_earned else "locked",
                "progress": current,
                "target": a.condition_value,
                "progress_percentage": percentage,
                "earned_at": (
                    earned_map[a.id].isoformat()
                    if is_earned and earned_map.get(a.id) else None
                ),
                "is_completed": current >= a.condition_value,
            }

        achievements = [build_item(a) for a in all_achievements]

        return {
            "code": 200,
            "message": "获取用户成就成功",
            "data": {
                "user_id": user_id,
                "username": user.username,
                "total_achievements": len(all_achievements),
                "earned_count": len(earned_ids),
                "achievements": achievements,
            },
        }
    except Exception as e:
        logger.error(f"获取用户成就失败: {e}")
        return {"code": 500, "message": f"获取用户成就失败: {e}", "data": []}

@router.post("/achievements/check/{user_id}")
async def check_achievements(user_id: int, db: Session = Depends(get_db)):
    """检查并发放成就"""
    try:
        # 验证用户是否存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"code": 404, "message": "用户不存在", "data": []}

        # 计算用户进度
        user_progress = calculate_user_progress(user_id, db)

        # 获取所有成就定义
        all_achievements = db.query(Achievement).all()

        # 获取用户已获得的成就
        earned = db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id
        ).all()
        earned_ids = {ua.achievement_id for ua in earned}

        # 检查并发放新成就
        new_achievements = []
        for achievement in all_achievements:
            if achievement.id not in earned_ids:
                current_progress = user_progress.get(achievement.condition_type, 0)
                if current_progress >= achievement.condition_value:
                    db.add(UserAchievement(user_id=user_id, achievement_id=achievement.id))
                    new_achievements.append({
                        "id": achievement.id,
                        "name": achievement.name,
                        "description": achievement.description,
                        "icon": achievement.icon_filename,
                        "condition_type": achievement.condition_type,
                        "condition_value": achievement.condition_value,
                        "current_progress": current_progress,
                    })

        if new_achievements:
            db.commit()
            logger.info(f"用户 {user_id}({user.username}) 新增成就 {len(new_achievements)} 个")

        return {
            "code": 200,
            "message": (
                f"成就检查完成，获得 {len(new_achievements)} 个新成就"
                if new_achievements else "没有新成就"
            ),
            "data": {
                "user_id": user_id,
                "username": user.username,
                "new_achievements": new_achievements,
                "total_earned": len(earned) + len(new_achievements),
                "user_progress": user_progress,
            },
        }

    except Exception as e:
        db.rollback()
        logger.error(f"检查成就失败: {e}")
        return {"code": 500, "message": f"检查成就失败: {e}", "data": []}

@router.get("/leaderboard")
async def get_leaderboard(
    db: Session = Depends(get_db),
    limit: int = 50
):
    """获取积分排行榜"""
    try:
        # 查询活跃用户并按积分排序
        leaderboard_data = (
            db.query(User.id, User.username, User.points, User.skill_level)
            .filter(User.is_active == True)
            .order_by(User.points.desc())
            .limit(limit)
            .all()
        )

        leaderboard = []
        current_rank = 1
        previous_points = None
        skip_rank = 0

        for _, (user_id, username, points, _) in enumerate(leaderboard_data):
            # 并列排名处理
            if previous_points is not None and points == previous_points:
                skip_rank += 1
            else:
                current_rank += skip_rank
                skip_rank = 0

            # 实时计算等级（覆盖数据库中的 skill_level）
            if points >= 200:
                level = "advanced"
            elif points >= 100:
                level = "intermediate"
            else:
                level = "beginner"

            leaderboard.append({
                "rank": current_rank,
                "user_id": user_id,
                "username": username,
                "points": points or 0,
                "skill_level": level,
            })

            previous_points = points
            current_rank += 1

        return {
            "code": 200,
            "message": "获取积分排行榜成功",
            "data": {
                "leaderboard": leaderboard,
                "total_users": len(leaderboard),
                "type": "points",
                "updated_at": datetime.now().isoformat(),
            },
        }

    except Exception as e:
        logger.error(f"获取积分排行榜失败: {e}")
        return {"code": 500, "message": f"获取积分排行榜失败: {e}", "data": []}

@router.get("/leaderboard/user/{user_id}")
async def get_user_ranking(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取指定用户在积分排行榜中的排名"""
    try:
        # 查询用户信息
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"code": 404, "message": "用户不存在", "data": None}

        # 计算排名（比当前用户积分高的人数 + 1）
        higher_score_count = (
            db.query(User)
            .filter(User.points > user.points, User.is_active == True)
            .count()
        )
        rank = higher_score_count + 1

        # 统计总活跃用户数
        total_users = db.query(User).filter(User.is_active == True).count()

        # 实时计算等级
        points = user.points or 0
        if points >= 200:
            level = "advanced"
        elif points >= 100:
            level = "intermediate"
        else:
            level = "beginner"

        # 计算百分位
        percentile = (
            round((total_users - rank) / total_users * 100, 1)
            if total_users > 0 else 0
        )

        return {
            "code": 200,
            "message": "获取用户排名成功",
            "data": {
                "user_id": user_id,
                "username": user.username,
                "points": points,
                "skill_level": level,
                "rank": rank,
                "total_users": total_users,
                "percentile": percentile,
            },
        }

    except Exception as e:
        logger.error(f"获取用户排名失败: {e}")
        return {"code": 500, "message": f"获取用户排名失败: {e}", "data": None}
