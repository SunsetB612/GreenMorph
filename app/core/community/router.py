"""
社区功能API路由
"""
from app.core.security import get_current_active_user
API_BASE_URL = "http://localhost:8000"
from fastapi import Depends,Query,HTTPException
from app.database import get_db,SessionLocal
from datetime import datetime
from fastapi import APIRouter, UploadFile, File
from app.core.community.image_models import CommunityImage, ImageType
from pydantic import BaseModel
from app.core.user.models import User
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.community.models import Comment,Post, Like,TargetType
router = APIRouter()

class PostCreate(BaseModel):
    title: str
    content: str

class PostOut(BaseModel):
    id: int
    user_id: int
    user_name: str
    title: str
    content: str
    likes_count: int = 0
    comments_count: int = 0
    created_at: datetime
    updated_at: datetime

class CommentCreate(BaseModel):
    content: str

@router.get("/posts")
async def get_posts(
    category: str = Query("latest", regex="^(latest|popular|following)$"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
):
    db: Session = SessionLocal()
    try:
        # 基础查询
        query = db.query(Post)

        # 分类排序规则
        order_by_map = {
            "latest": Post.created_at.desc(),
            "popular": (Post.likes_count.desc(), Post.comments_count.desc()),
            "following": Post.created_at.desc()
        }
        query = query.order_by(*order_by_map[category]) if isinstance(order_by_map[category], tuple) \
                else query.order_by(order_by_map[category])

        # 分页
        total = query.count()
        posts = query.offset((page - 1) * size).limit(size).all()

        # 构建返回数据
        items = []
        for post in posts:
            images = (
                db.query(CommunityImage.file_path)
                .filter(
                    CommunityImage.target_id == post.id,
                    CommunityImage.image_type == ImageType.POST
                )
                .all()
            )
            user = db.query(User.username).filter(User.id == post.user_id).first()

            items.append({
                "id": post.id,
                "user_id": post.user_id,
                "user_name": user.username if user else f"用户{post.user_id}",
                "title": post.title,
                "content": post.content,
                "likes_count": post.likes_count,
                "comments_count": post.comments_count,
                "created_at": post.created_at.isoformat(),
                "updated_at": post.updated_at.isoformat(),
                "images": [img.file_path for img in images]
            })

        return {"total": total, "page": page, "size": size, "items": items}

    finally:
        db.close()

@router.post("/posts", response_model=PostOut)
async def create_post(
    post: PostCreate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建新帖子"""
    try:
        # 新建帖子
        db_post = Post(
            title=post.title,
            content=post.content,
            user_id=current_user["id"]
        )
        db.add(db_post)
        db.commit()
        db.refresh(db_post)

        # 返回结果
        return {
            "id": db_post.id,
            "user_id": db_post.user_id,
            "user_name": current_user["username"],
            "title": db_post.title,
            "content": db_post.content,
            "likes_count": db_post.likes_count or 0,
            "comments_count": db_post.comments_count or 0,
            "created_at": db_post.created_at.isoformat(),
            "updated_at": db_post.updated_at.isoformat(),
            "images": [],
            "is_liked": False
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建帖子失败: {e}")

@router.post("/posts/{post_id}/images")
async def upload_post_image(
    post_id: int,
    file: UploadFile = File(...),
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """上传帖子图片"""
    from app.shared.utils.file_manager import FileManager
    from app.core.community.image_models import CommunityImage, ImageType

    try:
        user_id = current_user["id"]

        # 校验文件类型
        if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise HTTPException(status_code=400, detail="不支持的图片格式")

        content = await file.read()

        # 保存文件
        file_manager = FileManager()
        file_path, public_url = file_manager.save_uploaded_file(
            content=content,
            filename=file.filename,
            userid=str(user_id),
            category="posts",
            post_id=str(post_id),
        )

        # 写入数据库
        community_image = CommunityImage(
            uploader_id=user_id,
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(content),
            mime_type=file.content_type,
            image_type=ImageType.POST.value,
            target_id=post_id,
        )
        db.add(community_image)
        db.commit()
        db.refresh(community_image)

        return {
            "message": "帖子图片上传成功",
            "file_path": file_path,
            "public_url": public_url,
            "filename": file.filename,
            "size": len(content),
            "image_id": community_image.id,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"上传失败: {e}")

@router.post("/comments/{comment_id}/images")
async def upload_comment_image(
    comment_id: int,
    file: UploadFile = File(...),
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """上传评论图片"""
    from app.shared.utils.file_manager import FileManager
    from app.core.community.image_models import CommunityImage, ImageType

    try:
        user_id = current_user["id"]

        # 检查评论是否存在
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")

        # 检查文件类型
        if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise HTTPException(status_code=400, detail="不支持的图片格式")

        # 检查文件大小（限制 5MB）
        content = await file.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="图片大小不能超过 5MB")

        # 保存文件
        file_manager = FileManager()
        file_path, public_url = file_manager.save_uploaded_file(
            content=content,
            filename=file.filename,
            userid=str(user_id),
            category="comments",
            post_id=str(comment_id),
        )

        # 保存数据库记录
        community_image = CommunityImage(
            uploader_id=user_id,
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(content),
            mime_type=file.content_type,
            image_type=ImageType.COMMENT,
            target_id=comment_id,
        )
        db.add(community_image)
        db.commit()
        db.refresh(community_image)

        return {
            "message": "评论图片上传成功",
            "image_id": community_image.id,
            "file_path": file_path,
            "public_url": public_url,
            "filename": file.filename,
            "size": len(content),
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"上传评论图片失败: {e}")

@router.get("/posts/{post_id}")
async def get_post(post_id: int, db: Session = Depends(get_db)):
    """
    获取单个帖子详情，用于更新/删除操作。
    返回标题、内容、图片列表。
    """
    # 获取帖子
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    # 获取图片
    images = (
        db.query(CommunityImage.id, CommunityImage.file_path)
        .filter(
            CommunityImage.target_id == post.id,
            CommunityImage.image_type == ImageType.POST,
        )
        .all()
    )

    # 返回结果
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "updated_at": post.updated_at.isoformat() if post.updated_at else None,
        "user_id": post.user_id,
        "images": [{"id": img.id, "file_path": img.file_path} for img in images],
    }





@router.put("/posts/{post_id}", response_model=PostOut)
async def update_post(
    post_id: int,
    post_update: PostCreate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """更新帖子"""
    try:
        user_id = current_user["id"]
        username = current_user["username"]

        # 获取帖子
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")

        # 权限校验
        if post.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权修改他人帖子")

        # 更新内容
        post.title = post_update.title
        post.content = post_update.content
        post.updated_at = func.now()

        db.commit()
        db.refresh(post)

        # 返回结果
        return {
            "id": post.id,
            "user_id": post.user_id,
            "user_name": username,
            "title": post.title,
            "content": post.content,
            "likes_count": post.likes_count or 0,
            "comments_count": post.comments_count or 0,
            "created_at": post.created_at.isoformat() if post.created_at else None,
            "updated_at": post.updated_at.isoformat() if post.updated_at else None,
            "images": [],
            "is_liked": False,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新帖子失败: {e}")



@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: int,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """删除帖子及其关联的评论和图片"""
    from app.shared.utils.file_manager import FileManager

    try:
        user_id = current_user["id"]

        # 查找帖子
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")

        # 权限校验
        if post.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权删除他人帖子")

        file_manager = FileManager()

        # 删除帖子图片
        post_images = (
            db.query(CommunityImage)
            .filter(
                CommunityImage.target_id == post_id,
                CommunityImage.image_type == ImageType.POST,
            )
            .all()
        )
        for image in post_images:
            try:
                file_manager.delete_file(image.file_path)
            except Exception as e:
                print(f"删除帖子图片失败: {e}")
            db.delete(image)

        # 删除评论及图片
        comments = db.query(Comment).filter(Comment.post_id == post_id).all()
        deleted_comments_count = 0

        for comment in comments:
            comment_images = (
                db.query(CommunityImage)
                .filter(
                    CommunityImage.target_id == comment.id,
                    CommunityImage.image_type == ImageType.COMMENT,
                )
                .all()
            )
            for image in comment_images:
                try:
                    file_manager.delete_file(image.file_path)
                except Exception as e:
                    print(f"删除评论图片失败: {e}")
                db.delete(image)

            db.delete(comment)
            deleted_comments_count += 1

        # 删除帖子本身
        db.delete(post)
        db.commit()

        return {
            "message": "帖子、评论及所有关联图片删除成功",
            "post_id": post_id,
            "deleted_comments_count": deleted_comments_count,
            "deleted_post_images_count": len(post_images),
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除帖子失败: {e}")



@router.get("/posts/{post_id}/comments")
async def get_comments(
    post_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """获取评论列表（包含用户信息和图片）"""
    try:
        # 查询总数
        query = db.query(Comment).filter(Comment.post_id == post_id)
        total = query.count()

        # 分页获取评论
        comments = (
            query.order_by(Comment.created_at.asc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        results = []
        for c in comments:
            # 获取用户信息
            user = db.query(User).filter(User.id == c.user_id).first()

            # 获取评论图片
            images = (
                db.query(CommunityImage)
                .filter(
                    CommunityImage.target_id == c.id,
                    CommunityImage.image_type == "comment"
                )
                .all()
            )
            image_urls = [f"{API_BASE_URL}/{img.file_path}" for img in images]

            results.append({
                "id": c.id,
                "post_id": c.post_id,
                "user_id": c.user_id,
                "content": c.content,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "user_name": user.username if user else f"用户{c.user_id}",
                "user_avatar": f"https://api.dicebear.com/7.x/miniavs/svg?seed={c.user_id}",
                "images": image_urls
            })

        return {
            "total": total,
            "page": page,
            "size": size,
            "items": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取评论失败: {str(e)}")






@router.post("/posts/{post_id}/comments")
async def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    current_user = Depends(get_current_active_user),  # 用户认证
    db: Session = Depends(get_db)
):
    """创建评论"""
    try:
        user_id = current_user["id"]
        username = current_user["username"]

        # 1. 验证帖子是否存在
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")

        # 2. 创建评论
        comment = Comment(
            post_id=post_id,
            user_id=user_id,
            content=comment_data.content
        )
        db.add(comment)

        # 3. 更新帖子评论数
        post.comments_count = Post.comments_count + 1

        db.commit()
        db.refresh(comment)

        # 4. 返回结果
        return {
            "id": comment.id,
            "user_id": user_id,
            "user_name": username,
            "content": comment_data.content,
            "created_at": comment.created_at.isoformat(),
            "user_avatar": f"https://api.dicebear.com/7.x/miniavs/svg?seed={user_id}"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建评论失败: {str(e)}")

@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除评论（自动删除关联的所有图片）"""
    try:
        user_id = current_user["id"]

        # 1. 验证评论是否存在
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")

        # 2. 权限验证
        if comment.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权删除他人评论")

        # 3. 获取所属帖子 ID（用于计数更新）
        post_id = comment.post_id

        # 4. 删除评论关联图片
        images = db.query(CommunityImage).filter(
            CommunityImage.target_id == comment_id,
            CommunityImage.image_type == ImageType.COMMENT
        ).all()

        deleted_images_count = 0
        for image in images:
            try:
                from app.shared.utils.file_manager import FileManager
                FileManager().delete_file(image.file_path)
                deleted_images_count += 1
                print(f"🗑️ 已删除评论图片文件: {image.file_path}")
            except Exception as err:
                print(f"⚠️ 删除评论图片失败 {image.file_path}: {err}")
            db.delete(image)

        # 5. 删除评论本身
        db.delete(comment)

        # 6. 更新帖子评论数
        post = db.query(Post).filter(Post.id == post_id).first()
        if post and post.comments_count > 0:
            post.comments_count -= 1

        db.commit()

        return {
            "message": "评论及关联图片删除成功",
            "comment_id": comment_id,
            "post_id": post_id,
            "deleted_images_count": deleted_images_count
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除评论失败: {str(e)}")

@router.post("/posts/{post_id}/like")
async def like_post(
    post_id: int,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """点赞帖子"""
    try:
        user_id = current_user["id"]

        # 1. 验证帖子是否存在
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")

        # 2. 检查是否已点赞
        liked = db.query(Like).filter(
            Like.user_id == user_id,
            Like.target_type == TargetType.POST,
            Like.target_id == post_id
        ).first()
        if liked:
            raise HTTPException(status_code=400, detail="已经点赞过该帖子")

        # 3. 添加点赞记录
        db.add(Like(
            user_id=user_id,
            target_type=TargetType.POST,
            target_id=post_id
        ))
        post.likes_count += 1

        db.commit()

        return {
            "message": "点赞成功",
            "post_id": post_id,
            "likes_count": post.likes_count,
            "user_id": user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"点赞失败: {str(e)}")

@router.delete("/posts/{post_id}/like")
async def unlike_post(
    post_id: int,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """取消点赞帖子"""
    try:
        user_id = current_user["id"]

        # 1. 验证帖子是否存在
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")

        # 2. 检查是否已点赞
        like = db.query(Like).filter(
            Like.user_id == user_id,
            Like.target_type == TargetType.POST,
            Like.target_id == post_id
        ).first()
        if not like:
            raise HTTPException(status_code=400, detail="尚未点赞该帖子")

        # 3. 删除点赞记录
        db.delete(like)
        if post.likes_count > 0:  # 防止出现负数
            post.likes_count -= 1

        db.commit()

        return {
            "message": "取消点赞成功",
            "post_id": post_id,
            "likes_count": post.likes_count,
            "user_id": user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"取消点赞失败: {str(e)}")

@router.get("/posts/{post_id}/like/status")
async def get_like_status(
    post_id: int,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取当前用户对帖子的点赞状态"""
    try:
        user_id = current_user["id"]

        like = db.query(Like).filter(
            Like.user_id == user_id,
            Like.target_type == TargetType.POST,
            Like.target_id == post_id
        ).first()

        return {
            "is_liked": like is not None,
            "post_id": post_id,
            "user_id": user_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询点赞状态失败: {str(e)}")

@router.post("/comments/{comment_id}/like")
async def like_comment(
    comment_id: int,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """点赞评论"""
    try:
        user_id = current_user["id"]

        # 1. 验证评论是否存在
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")

        # 2. 检查是否已点赞
        like = db.query(Like).filter(
            Like.user_id == user_id,
            Like.target_type == TargetType.COMMENT,
            Like.target_id == comment_id
        ).first()
        if like:
            raise HTTPException(status_code=400, detail="已经点赞过该评论")

        # 3. 创建点赞记录
        new_like = Like(
            user_id=user_id,
            target_type=TargetType.COMMENT,
            target_id=comment_id
        )
        db.add(new_like)
        db.commit()

        # 4. 查询当前点赞总数
        likes_count = db.query(Like).filter(
            Like.target_type == TargetType.COMMENT,
            Like.target_id == comment_id
        ).count()

        return {
            "message": "评论点赞成功",
            "comment_id": comment_id,
            "user_id": user_id,
            "likes_count": likes_count
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"评论点赞失败: {str(e)}")

@router.delete("/comments/{comment_id}/like")
async def unlike_comment(
    comment_id: int,
    current_user = Depends(get_current_active_user),  # 用户认证
    db: Session = Depends(get_db)
):
    """取消点赞评论"""
    try:
        current_user_id = current_user["id"]

        # 1. 验证评论是否存在
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")

        # 2. 检查是否已经点赞
        existing_like = (
            db.query(Like)
            .filter(
                Like.user_id == current_user_id,
                Like.target_type == TargetType.COMMENT,
                Like.target_id == comment_id
            )
            .first()
        )
        if not existing_like:
            raise HTTPException(status_code=400, detail="尚未点赞该评论")

        # 3. 执行取消点赞
        db.delete(existing_like)
        db.commit()

        # 4. 查询取消后点赞总数
        like_count = (
            db.query(Like)
            .filter(
                Like.target_type == TargetType.COMMENT,
                Like.target_id == comment_id
            )
            .count()
        )

        return {
            "message": "取消评论点赞成功",
            "comment_id": comment_id,
            "user_id": current_user_id,
            "likes_count": like_count
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"取消评论点赞失败: {str(e)}")



@router.get("/comments/like/status/batch")
async def get_batch_comment_like_status(
    comment_ids: str = Query(..., description="评论ID列表，用逗号分隔"),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """批量获取当前用户对多个评论的点赞状态和点赞数"""
    try:
        user_id = current_user["id"]

        # 解析评论ID列表
        comment_id_list = [int(cid) for cid in comment_ids.split(",") if cid]

        # 查询当前用户对这些评论的点赞状态
        likes = db.query(Like).filter(
            Like.user_id == user_id,
            Like.target_type == TargetType.COMMENT,
            Like.target_id.in_(comment_id_list)
        ).all()
        status_map = {like.target_id: True for like in likes}

        # 查询每条评论的点赞总数
        likes_count_map = {
            comment_id: db.query(Like).filter(
                Like.target_type == TargetType.COMMENT,
                Like.target_id == comment_id
            ).count()
            for comment_id in comment_id_list
        }

        return {
            "status_map": status_map,
            "likes_count_map": likes_count_map,
            "user_id": user_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量查询评论点赞状态失败: {str(e)}")

@router.delete("/posts/{post_id}/images/{image_id}")
async def delete_post_image(
    post_id: int,
    image_id: int,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除帖子中的单张图片（编辑帖子时使用）"""
    try:
        user_id = current_user["id"]

        # 1. 验证帖子是否存在
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")

        # 2. 权限验证（只有作者可删除图片）
        if post.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权删除他人帖子的图片")

        # 3. 查找图片记录
        image = db.query(CommunityImage).filter(
            CommunityImage.id == image_id,
            CommunityImage.target_id == post_id,
            CommunityImage.image_type == ImageType.POST
        ).first()
        if not image:
            raise HTTPException(status_code=404, detail="图片不存在")

        # 4. 删除实际文件（失败也不影响数据库删除）
        try:
            from app.shared.utils.file_manager import FileManager
            file_manager = FileManager()
            file_manager.delete_file(image.file_path)
        except Exception:
            pass

        # 5. 删除数据库记录
        db.delete(image)
        db.commit()

        return {
            "message": "帖子图片删除成功",
            "post_id": post_id,
            "image_id": image_id,
            "deleted_file_path": image.file_path
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除帖子图片失败: {str(e)}")


@router.get("/users/{user_id}/stats")
async def get_user_stats(
        user_id: int,
        db: Session = Depends(get_db)
):
    """获取用户帖子统计（发布作品数和总点赞数）"""
    try:
        # 获取用户发布的帖子数量
        posts_count = db.query(Post).filter(Post.user_id == user_id).count()

        # 获取用户所有帖子的总点赞数
        total_likes = db.query(func.coalesce(func.sum(Post.likes_count), 0)).filter(
            Post.user_id == user_id
        ).scalar()

        return {
            "code": 200,
            "message": "获取用户统计成功",
            "data": {
                "user_id": user_id,
                "posts_count": posts_count,
                "total_likes": total_likes
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户统计失败: {str(e)}")


@router.get("/users/{user_id}/posts")
async def get_user_posts(
        user_id: int,
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1, le=50),
        db: Session = Depends(get_db)
):
    """获取指定用户的帖子"""
    try:
        # 查询用户的帖子
        query = db.query(Post).filter(Post.user_id == user_id)
        total = query.count()

        posts = query.order_by(Post.created_at.desc()) \
            .offset((page - 1) * size) \
            .limit(size) \
            .all()

        items = []
        for post in posts:
            images = db.query(CommunityImage.file_path) \
                .filter(
                CommunityImage.target_id == post.id,
                CommunityImage.image_type == ImageType.POST
            ) \
                .all()

            user = db.query(User.username).filter(User.id == post.user_id).first()

            items.append({
                "id": post.id,
                "user_id": post.user_id,
                "user_name": user.username if user else f"用户{post.user_id}",
                "title": post.title,
                "content": post.content,
                "likes_count": post.likes_count,
                "comments_count": post.comments_count,
                "created_at": post.created_at.isoformat(),
                "updated_at": post.updated_at.isoformat(),
                "images": [img.file_path for img in images]
            })

        return {"total": total, "page": page, "size": size, "items": items}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户帖子失败: {str(e)}")


@router.get("/users/{user_id}/liked-posts")
async def get_user_liked_posts(
        user_id: int,
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1, le=50),
        db: Session = Depends(get_db)
):
    """获取用户点赞过的帖子"""
    try:
        # 查询用户点赞的帖子ID
        liked_post_ids = db.query(Like.target_id).filter(
            Like.user_id == user_id,
            Like.target_type == TargetType.POST
        ).all()
        liked_post_ids = [post_id[0] for post_id in liked_post_ids]

        if not liked_post_ids:
            return {"total": 0, "page": page, "size": size, "items": []}

        # 查询这些帖子的详细信息
        query = db.query(Post).filter(Post.id.in_(liked_post_ids))
        total = query.count()

        posts = query.order_by(Post.created_at.desc()) \
            .offset((page - 1) * size) \
            .limit(size) \
            .all()

        items = []
        for post in posts:
            images = db.query(CommunityImage.file_path) \
                .filter(
                CommunityImage.target_id == post.id,
                CommunityImage.image_type == ImageType.POST
            ) \
                .all()

            user = db.query(User.username).filter(User.id == post.user_id).first()

            items.append({
                "id": post.id,
                "user_id": post.user_id,
                "user_name": user.username if user else f"用户{post.user_id}",
                "title": post.title,
                "content": post.content,
                "likes_count": post.likes_count,
                "comments_count": post.comments_count,
                "created_at": post.created_at.isoformat(),
                "updated_at": post.updated_at.isoformat(),
                "images": [img.file_path for img in images]
            })

        return {"total": total, "page": page, "size": size, "items": items}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户点赞帖子失败: {str(e)}")