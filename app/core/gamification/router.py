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
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter()
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
async def get_user_achievements(user_id: int, db: Session = Depends(get_db)):
    """获取用户的成就进度"""
    try:
        # 1. 验证用户是否存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {
                "code": 404,
                "message": "用户不存在",
                "data": []
            }

        # 2. 获取所有成就定义
        all_achievements = db.query(Achievement).all()

        # 3. 获取用户已获得的成就
        earned_achievements = db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id
        ).all()
        earned_achievement_ids = {ua.achievement_id for ua in earned_achievements}
        earned_achievement_map = {ua.achievement_id: ua.earned_at for ua in earned_achievements}

        # 4. 计算用户在各条件下的进度
        user_progress = calculate_user_progress(user_id, db)

        # 5. 构建响应数据
        user_achievements = []
        for achievement in all_achievements:
            current_progress = user_progress.get(achievement.condition_type, 0)
            is_earned = achievement.id in earned_achievement_ids

            # 计算进度百分比
            progress_percentage = 0
            if achievement.condition_value > 0:
                progress_percentage = min(100, int((current_progress / achievement.condition_value) * 100))

            user_achievements.append({
                "id": achievement.id,
                "name": achievement.name,
                "description": achievement.description,
                "icon": achievement.icon_filename,
                "condition_type": achievement.condition_type,
                "condition_value": achievement.condition_value,
                "status": "achieved" if is_earned else "locked",
                "progress": current_progress,
                "target": achievement.condition_value,
                "progress_percentage": progress_percentage,
                "earned_at": earned_achievement_map.get(achievement.id).isoformat()
                if is_earned and earned_achievement_map.get(achievement.id) else None,
                "is_completed": current_progress >= achievement.condition_value
            })

        return {
            "code": 200,
            "message": "获取用户成就成功",
            "data": {
                "user_id": user_id,
                "username": user.username,
                "total_achievements": len(all_achievements),
                "earned_count": len(earned_achievement_ids),
                "achievements": user_achievements
            }
        }

    except Exception as e:
        logger.error(f"获取用户成就失败: {str(e)}")
        return {
            "code": 500,
            "message": f"获取用户成就失败: {str(e)}",
            "data": []
        }


def calculate_user_progress(user_id: int, db: Session) -> dict:
    """计算用户在各条件下的进度"""
    from sqlalchemy import and_

    progress = {}

    try:
        # 计算帖子数量
        post_count = db.query(Post).filter(Post.user_id == user_id).count()
        progress['post_count'] = post_count

        # 计算评论数量
        comment_count = db.query(Comment).filter(Comment.user_id == user_id).count()
        progress['comment_count'] = comment_count

        # 计算获得的点赞数 - 使用子查询避免复杂关联
        # 先获取用户的所有帖子ID
        user_post_ids = [post.id for post in db.query(Post.id).filter(Post.user_id == user_id).all()]

        if user_post_ids:
            post_likes = db.query(Like).filter(
                and_(
                    Like.target_type == 'post',
                    Like.target_id.in_(user_post_ids)
                )
            ).count()
        else:
            post_likes = 0

        progress['likes_received'] = post_likes

        # 计算项目数量
        project_count = db.query(RedesignProject).filter(
            RedesignProject.user_id == user_id
        ).count()
        progress['project_count'] = project_count

        logger.info(f"用户 {user_id} 进度统计: {progress}")

    except Exception as e:
        logger.error(f"计算用户进度失败: {e}")
        progress.setdefault('post_count', 0)
        progress.setdefault('comment_count', 0)
        progress.setdefault('likes_received', 0)
        progress.setdefault('project_count', 0)

    return progress


@router.post("/achievements/check/{user_id}")
async def check_achievements(user_id: int, db: Session = Depends(get_db)):
    """检查并发放成就"""
    try:
        # 1. 验证用户是否存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {
                "code": 404,
                "message": "用户不存在",
                "data": []
            }

        # 2. 计算用户当前进度
        user_progress = calculate_user_progress(user_id, db)

        # 3. 获取所有成就定义
        all_achievements = db.query(Achievement).all()

        # 4. 获取用户已获得的成就
        earned_achievements = db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id
        ).all()
        earned_achievement_ids = {ua.achievement_id for ua in earned_achievements}

        # 5. 检查并发放新成就
        new_achievements = []

        for achievement in all_achievements:
            # 如果用户还没有获得这个成就
            if achievement.id not in earned_achievement_ids:
                current_progress = user_progress.get(achievement.condition_type, 0)

                # 检查是否满足成就条件
                if current_progress >= achievement.condition_value:
                    # 发放成就
                    user_achievement = UserAchievement(
                        user_id=user_id,
                        achievement_id=achievement.id
                    )
                    db.add(user_achievement)
                    new_achievements.append({
                        "id": achievement.id,
                        "name": achievement.name,
                        "description": achievement.description,
                        "icon": achievement.icon_filename,
                        "condition_type": achievement.condition_type,
                        "condition_value": achievement.condition_value,
                        "current_progress": current_progress
                    })

        # 6. 提交事务
        if new_achievements:
            db.commit()
            logger.info(f"用户 {user_id}({user.username}) 获得了 {len(new_achievements)} 个新成就")

        # 7. 返回结果
        return {
            "code": 200,
            "message": f"成就检查完成，获得了 {len(new_achievements)} 个新成就" if new_achievements else "没有新成就",
            "data": {
                "user_id": user_id,
                "username": user.username,
                "new_achievements": new_achievements,
                "total_earned": len(earned_achievements) + len(new_achievements),
                "user_progress": user_progress
            }
        }

    except Exception as e:
        db.rollback()
        logger.error(f"检查成就失败: {str(e)}")
        return {
            "code": 500,
            "message": f"检查成就失败: {str(e)}",
            "data": []
        }


@router.get("/leaderboard")
async def get_leaderboard():
    """获取积分排行榜"""
    pass
