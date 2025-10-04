"""
社区功能API路由
"""
from app.core.security import get_current_active_user
API_BASE_URL = "http://localhost:8000"
from fastapi import APIRouter, UploadFile, File
from app.database import SessionLocal
from app.core.community.models import Post
router = APIRouter()
from  app.core.community.image_models import CommunityImage,ImageType
from pydantic import BaseModel
from fastapi import HTTPException
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db

# 帖子相关
from fastapi import APIRouter, Query
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.core.community.models import Post

router = APIRouter()


@router.get("/posts")
async def get_posts(
    category: str = Query("latest", regex="^(latest|popular|following)$"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
):
    db: Session = SessionLocal()
    try:
        query = db.query(Post)

        if category == "latest":
            query = query.order_by(Post.created_at.desc())
        elif category == "popular":
            query = query.order_by(Post.likes_count.desc(), Post.comments_count.desc())
        elif category == "following":
            query = query.order_by(Post.created_at.desc())

        total = query.count()
        posts = query.offset((page - 1) * size).limit(size).all()

        # 关键修改：将SQLAlchemy对象转换为字典，并添加图片信息和用户名
        posts_with_images = []
        for post in posts:
            # 获取该帖子的图片
            images = db.query(CommunityImage).filter(
                CommunityImage.target_id == post.id,
                CommunityImage.image_type == ImageType.POST
            ).all()

            # 获取帖子作者的用户名
            user = db.query(User).filter(User.id == post.user_id).first()
            user_name = user.username if user else f"用户{post.user_id}"

            post_data = {
                "id": post.id,
                "user_id": post.user_id,
                "user_name": user_name,  # 添加用户名
                "title": post.title,
                "content": post.content,
                "likes_count": post.likes_count,
                "comments_count": post.comments_count,
                "created_at": post.created_at.isoformat(),
                "updated_at": post.updated_at.isoformat(),
                "images": [img.file_path for img in images]
            }
            posts_with_images.append(post_data)

        return {
            "total": total,
            "page": page,
            "size": size,
            "items": posts_with_images
        }
    finally:
        db.close()



from datetime import datetime
from pydantic import BaseModel

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
    created_at: datetime  # 使用 datetime 而不是 str
    updated_at: datetime  # 使用 datetime 而不是 str

    class Config:
        orm_mode = True
        from_attributes = True


@router.post("/posts", response_model=PostOut)
async def create_post(
    post: PostCreate,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建新帖子"""
    try:
        current_user_id = current_user["id"]
        current_username = current_user["username"]  # 获取用户名

        # 创建帖子对象
        db_post = Post(
            title=post.title,
            content=post.content,
            user_id=current_user_id
        )

        db.add(db_post)
        db.commit()
        db.refresh(db_post)

        # 返回包含用户名的数据
        return {
            **db_post.__dict__,
            "user_name": current_username,  # 添加用户名
            "likes_count": 0,
            "comments_count": 0,
            "images": [],
            "is_liked": False
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建帖子失败: {str(e)}")


from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.shared.utils.file_manager import FileManager
from app.core.community.image_models import CommunityImage, ImageType
from typing import Dict


@router.post("/posts/{post_id}/images")
async def upload_post_image(
    post_id: int,
    file: UploadFile = File(...),
    current_user = Depends(get_current_active_user),  # 添加认证依赖
    db: Session = Depends(get_db)  # 使用依赖注入，统一风格
):
    """上传帖子图片"""
    from app.shared.utils.file_manager import FileManager
    from app.core.community.image_models import CommunityImage, ImageType
    from fastapi import HTTPException

    try:
        # 使用真实用户ID，替换假数据
        current_user_id = current_user["id"]

        # 验证文件类型
        if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
            raise HTTPException(status_code=400, detail="不支持的图片格式")

        # 读取文件内容
        content = await file.read()

        # 保存文件
        file_manager = FileManager()
        userid = str(current_user_id)  # 使用真实用户ID

        file_path, public_url = file_manager.save_uploaded_file(
            content=content,
            filename=file.filename,
            userid=userid,
            category="posts",
            post_id=str(post_id)
        )

        # 保存到数据库
        community_image = CommunityImage(
            uploader_id=current_user_id,  # 使用真实用户ID
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(content),
            mime_type=file.content_type,
            image_type=ImageType.POST.value,
            target_id=post_id
        )
        db.add(community_image)
        db.commit()
        db.refresh(community_image)

        print(f"图片已保存到数据库，ID: {community_image.id}")

        return {
            "message": "帖子图片上传成功",
            "file_path": file_path,
            "public_url": public_url,
            "filename": file.filename,
            "size": len(content),
            "image_id": community_image.id
        }

    except Exception as e:
        db.rollback()
        print(f"上传图片失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/comments/{comment_id}/images")
async def upload_comment_image(
    comment_id: int,
    file: UploadFile = File(...),
    current_user = Depends(get_current_active_user),  # 添加认证依赖
    db: Session = Depends(get_db)  # 使用依赖注入
):
    """上传评论图片"""
    try:
        from app.shared.utils.file_manager import FileManager
        from app.core.community.image_models import CommunityImage, ImageType

        # 使用真实用户ID，替换假数据
        current_user_id = current_user["id"]

        # 验证评论是否存在
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")

        # 验证文件类型
        if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
            raise HTTPException(status_code=400, detail="不支持的图片格式")

        # 验证文件大小（限制5MB）
        content = await file.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="图片大小不能超过5MB")

        # 保存文件
        file_manager = FileManager()
        file_path, public_url = file_manager.save_uploaded_file(
            content=content,
            filename=file.filename,
            userid=str(current_user_id),  # 使用真实用户ID
            category="comments",
            post_id=str(comment_id)
        )

        # 保存到数据库
        community_image = CommunityImage(
            uploader_id=current_user_id,  # 使用真实用户ID
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(content),
            mime_type=file.content_type,
            image_type=ImageType.COMMENT,
            target_id=comment_id
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
            "size": len(content)
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"上传评论图片失败: {str(e)}")


from app.core.user.models import User

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.community.models import Post
from app.core.community.image_models import CommunityImage, ImageType



@router.get("/posts/{post_id}")
async def get_post(post_id: int, db: Session = Depends(get_db)):
    """
    获取单个帖子详情，用于更新/删除操作。
    返回帖子标题、内容、图片列表。
    """
    # 1. 获取帖子
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    # 2. 获取帖子关联图片
    images = db.query(CommunityImage).filter(
        CommunityImage.target_id == post.id,
        CommunityImage.image_type == ImageType.POST
    ).all()

    # 3. 返回可编辑信息给前端
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "images": [img.file_path for img in images],  # 只返回 file_path，前端可拼接完整 URL
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "updated_at": post.updated_at.isoformat() if post.updated_at else None,
        "user_id": post.user_id
    }

from sqlalchemy import func


@router.put("/posts/{post_id}", response_model=PostOut)
async def update_post(
        post_id: int,
        post_update: PostCreate,
        current_user=Depends(get_current_active_user),  # 添加认证
        db: Session = Depends(get_db)
):
    try:
        # 使用真实用户ID，替换假数据
        current_user_id = current_user["id"]
        current_username = current_user["username"]  # 获取用户名

        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")

        # 权限验证：只有作者能编辑
        if post.user_id != current_user_id:  # 使用真实用户ID
            raise HTTPException(status_code=403, detail="无权修改他人帖子")

        post.title = post_update.title
        post.content = post_update.content
        post.updated_at = func.now()

        db.commit()
        db.refresh(post)

        # 返回包含用户名的数据 - 仿照你的create_post返回格式
        return {
            **post.__dict__,
            "user_name": current_username,  # 添加用户名
            "likes_count": post.likes_count,
            "comments_count": post.comments_count,
            "images": [],
            "is_liked": False
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新帖子失败: {str(e)}")


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: int,
    current_user = Depends(get_current_active_user),  # 添加认证依赖
    db: Session = Depends(get_db)
):
    """删除帖子"""
    try:
        # 使用真实用户ID，替换假数据
        current_user_id = current_user["id"]

        # 1. 查找帖子
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")

        # 2. 权限验证：只有作者能删除
        if post.user_id != current_user_id:  # 使用真实用户ID
            raise HTTPException(status_code=403, detail="无权删除他人帖子")

        # 3. 删除关联的图片记录
        images = db.query(CommunityImage).filter(
            CommunityImage.target_id == post_id,
            CommunityImage.image_type == ImageType.POST
        ).all()

        for image in images:
            # TODO: 删除实际图片文件
            # file_manager.delete_file(image.file_path)
            db.delete(image)

        # 4. 删除帖子
        db.delete(post)
        db.commit()

        return {"message": "帖子删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除帖子失败: {str(e)}")

from  app.core.community.models import Comment
# 评论相关
from sqlalchemy import text

@router.get("/posts/{post_id}/comments")
async def get_comments(
        post_id: int,
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1, le=50),
        db: Session = Depends(get_db)
):
    """获取评论列表（包含图片）"""
    try:
        # 查询评论（分页）
        comments_query = db.query(Comment).filter(Comment.post_id == post_id)
        total = comments_query.count()

        comments = comments_query.order_by(Comment.created_at.asc()) \
            .offset((page - 1) * size) \
            .limit(size) \
            .all()

        comments_data = []
        for comment in comments:
            # 查询用户信息
            user = db.query(User).filter(User.id == comment.user_id).first()

            # 查询评论的图片
            images = db.query(CommunityImage).filter(
                CommunityImage.target_id == comment.id,
                CommunityImage.image_type == "comment"
            ).all()

            image_urls = [f"{API_BASE_URL}/{img.file_path}" for img in images]

            comment_data = {
                "id": comment.id,
                "post_id": comment.post_id,
                "user_id": comment.user_id,
                "content": comment.content,
                "created_at": comment.created_at.isoformat() if comment.created_at else None,
                "user_name": user.username if user else f"用户{comment.user_id}",
                "user_avatar": f"https://api.dicebear.com/7.x/miniavs/svg?seed={comment.user_id}",
                "images": image_urls  # 添加图片URL列表
            }
            comments_data.append(comment_data)

        return {
            "total": total,
            "page": page,
            "size": size,
            "items": comments_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取评论失败: {str(e)}")


from sqlalchemy.orm import Session
from app.core.community.models import Post, Comment
from pydantic import BaseModel
from app.core.user.models import User

class CommentCreate(BaseModel):
    content: str
@router.post("/posts/{post_id}/comments")
async def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    current_user = Depends(get_current_active_user),  # 添加认证依赖
    db: Session = Depends(get_db)
):
    """创建评论"""
    try:
        # 使用真实用户ID，替换假数据
        current_user_id = current_user["id"]
        current_username = current_user["username"]  # 获取用户名

        # 1. 验证帖子是否存在
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")

        # 2. 创建评论
        new_comment = Comment(
            post_id=post_id,
            user_id=current_user_id,
            content=comment_data.content
        )

        db.add(new_comment)

        # 3. 更新帖子评论计数
        post.comments_count = Post.comments_count + 1

        db.commit()
        db.refresh(new_comment)

        return {
            "id": new_comment.id,
            "user_id": current_user_id,
            "user_name": current_username,  # 使用认证中的用户名
            "content": comment_data.content,
            "created_at": new_comment.created_at.isoformat(),
            "user_avatar": f"https://api.dicebear.com/7.x/miniavs/svg?seed={current_user_id}"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建评论失败: {str(e)}")


from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db  # 根据你的实际路径调整
from app.core.community.models import Comment, Post


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user = Depends(get_current_active_user),  # 添加认证依赖
    db: Session = Depends(get_db)
):
    """删除评论"""
    try:
        # 使用真实用户ID，替换假数据
        current_user_id = current_user["id"]

        # 1. 验证评论是否存在
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")

        # 2. 验证用户权限（只能删除自己的评论）
        if comment.user_id != current_user_id:
            raise HTTPException(status_code=403, detail="无权删除他人评论")

        # 3. 获取评论所属的帖子ID（用于更新计数）
        post_id = comment.post_id

        # 4. 删除评论
        db.delete(comment)

        # 5. 更新帖子的评论计数
        post = db.query(Post).filter(Post.id == post_id).first()
        if post and post.comments_count > 0:
            post.comments_count = Post.comments_count - 1

        db.commit()

        return {
            "message": "评论删除成功",
            "comment_id": comment_id,
            "post_id": post_id
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除评论失败: {str(e)}")


from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.community.models import Post, Like,TargetType

# 点赞相关
@router.post("/posts/{post_id}/like")
async def like_post(
    post_id: int,
    current_user = Depends(get_current_active_user),  # 添加认证依赖
    db: Session = Depends(get_db)
):
    """点赞帖子"""
    try:
        # 使用真实用户ID，替换假数据
        current_user_id = current_user["id"]

        # 1. 验证帖子是否存在
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")

        # 2. 检查是否已经点赞
        existing_like = db.query(Like).filter(
            Like.user_id == current_user_id,
            Like.target_type == TargetType.POST,
            Like.target_id == post_id
        ).first()

        if existing_like:
            raise HTTPException(status_code=400, detail="已经点赞过该帖子")

        # 3. 执行点赞
        new_like = Like(
            user_id=current_user_id,
            target_type=TargetType.POST,
            target_id=post_id
        )
        db.add(new_like)
        post.likes_count = Post.likes_count + 1

        db.commit()

        return {
            "message": "点赞成功",
            "post_id": post_id,
            "likes_count": post.likes_count,
            "user_id": current_user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"点赞失败: {str(e)}")

from app.core.community.models import Post, Like,TargetType
@router.delete("/posts/{post_id}/like")
async def unlike_post(
    post_id: int,
    current_user = Depends(get_current_active_user),  # 添加认证依赖
    db: Session = Depends(get_db)
):
    """取消点赞帖子"""
    try:
        # 使用真实用户ID，替换假数据
        current_user_id = current_user["id"]

        # 1. 验证帖子是否存在
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")

        # 2. 检查是否已经点赞
        existing_like = db.query(Like).filter(
            Like.user_id == current_user_id,
            Like.target_type == TargetType.POST,
            Like.target_id == post_id
        ).first()

        if not existing_like:
            raise HTTPException(status_code=400, detail="尚未点赞该帖子")

        # 3. 执行取消点赞
        db.delete(existing_like)
        post.likes_count = post.likes_count - 1

        db.commit()

        return {
            "message": "取消点赞成功",
            "post_id": post_id,
            "likes_count": post.likes_count,
            "user_id": current_user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"取消点赞失败: {str(e)}")


@router.get("/posts/{post_id}/like/status")
async def get_like_status(
    post_id: int,
    current_user = Depends(get_current_active_user),  # 添加认证依赖
    db: Session = Depends(get_db)
):
    """获取当前用户对帖子的点赞状态"""
    try:
        # 使用真实用户ID，替换假数据
        current_user_id = current_user["id"]

        existing_like = db.query(Like).filter(
            Like.user_id == current_user_id,
            Like.target_type == "POST",
            Like.target_id == post_id
        ).first()

        return {
            "is_liked": existing_like is not None,
            "post_id": post_id,
            "user_id": current_user_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询点赞状态失败: {str(e)}")




@router.post("/comments/{comment_id}/like")
async def like_comment(
    comment_id: int,
    current_user = Depends(get_current_active_user),  # 添加认证依赖
    db: Session = Depends(get_db)
):
    """点赞评论"""
    try:
        # 使用真实用户ID，替换假数据
        current_user_id = current_user["id"]

        # 1. 验证评论是否存在
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")

        # 2. 检查是否已经点赞
        existing_like = db.query(Like).filter(
            Like.user_id == current_user_id,
            Like.target_type == TargetType.COMMENT,
            Like.target_id == comment_id
        ).first()

        if existing_like:
            raise HTTPException(status_code=400, detail="已经点赞过该评论")

        # 3. 执行点赞
        new_like = Like(
            user_id=current_user_id,
            target_type=TargetType.COMMENT,
            target_id=comment_id
        )
        db.add(new_like)
        db.commit()

        # 4. 查询当前评论的总点赞数（点赞后总数）
        like_count = db.query(Like).filter(
            Like.target_type == TargetType.COMMENT,
            Like.target_id == comment_id
        ).count()

        print(f"✅ 点赞成功，评论 {comment_id} 当前点赞数: {like_count}")  # 调试信息

        return {
            "message": "评论点赞成功",
            "comment_id": comment_id,
            "user_id": current_user_id,
            "likes_count": like_count
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"评论点赞失败: {str(e)}")

@router.delete("/comments/{comment_id}/like")
async def unlike_comment(
    comment_id: int,
    current_user = Depends(get_current_active_user),  # 添加认证依赖
    db: Session = Depends(get_db)
):
    """取消点赞评论"""
    try:
        # 使用真实用户ID，替换假数据
        current_user_id = current_user["id"]

        # 1. 验证评论是否存在
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")

        # 2. 检查是否已经点赞
        existing_like = db.query(Like).filter(
            Like.user_id == current_user_id,
            Like.target_type == TargetType.COMMENT,
            Like.target_id == comment_id
        ).first()

        if not existing_like:
            raise HTTPException(status_code=400, detail="尚未点赞该评论")

        # 3. 执行取消点赞
        db.delete(existing_like)
        db.commit()

        # 4. 查询当前评论的总点赞数（取消点赞后总数）
        like_count = db.query(Like).filter(
            Like.target_type == TargetType.COMMENT,
            Like.target_id == comment_id
        ).count()

        print(f"✅ 取消点赞成功，评论 {comment_id} 当前点赞数: {like_count}")  # 调试信息

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
    current_user = Depends(get_current_active_user),  # 添加认证依赖
    db: Session = Depends(get_db)
):
    """批量获取当前用户对多个评论的点赞状态和点赞数"""
    try:
        # 使用真实用户ID，替换假数据
        current_user_id = current_user["id"]

        comment_id_list = [int(cid) for cid in comment_ids.split(",") if cid]

        print(f"🔍 查询评论ID: {comment_id_list}")

        # 查询点赞状态
        likes = db.query(Like).filter(
            Like.user_id == current_user_id,
            Like.target_type == TargetType.COMMENT,
            Like.target_id.in_(comment_id_list)
        ).all()
        status_map = {like.target_id: True for like in likes}

        # 查询点赞数
        likes_count_map = {}
        for comment_id in comment_id_list:
            count = db.query(Like).filter(
                Like.target_type == TargetType.COMMENT,
                Like.target_id == comment_id
            ).count()
            likes_count_map[comment_id] = count

        print(f"✅ 最终返回: status_map={status_map}, likes_count_map={likes_count_map}")

        return {
            "status_map": status_map,
            "likes_count_map": likes_count_map,
            "user_id": current_user_id
        }

    except Exception as e:
        print(f"❌ 批量查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量查询评论点赞状态失败: {str(e)}")