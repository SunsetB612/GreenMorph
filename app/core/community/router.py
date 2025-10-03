"""
社区功能API路由
"""

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

        # 关键修改：将SQLAlchemy对象转换为字典，并添加图片信息
        posts_with_images = []
        for post in posts:
            # 获取该帖子的图片
            images = db.query(CommunityImage).filter(
                CommunityImage.target_id == post.id,
                CommunityImage.image_type == ImageType.POST
            ).all()

            post_data = {
                "id": post.id,
                "user_id": post.user_id,
                "title": post.title,
                "content": post.content,
                "likes_count": post.likes_count,
                "comments_count": post.comments_count,
                "created_at": post.created_at.isoformat(),  # 转换为字符串
                "updated_at": post.updated_at.isoformat(),  # 转换为字符串
                "images": [img.file_path for img in images]  # 添加图片
            }
            posts_with_images.append(post_data)

        return {
            "total": total,
            "page": page,
            "size": size,
            "items": posts_with_images  # 返回处理后的数据
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
        # current_user: User = Depends(get_current_user)  # TODO: 添加用户认证
        # db: Session = Depends(get_db)  # TODO: 添加数据库依赖
):
    """创建新帖子"""
    from fastapi import HTTPException

    db: Session = SessionLocal()
    try:
        # TODO: 从认证中获取真实用户ID
        fake_user_id = 1

        # 创建帖子对象
        db_post = Post(
            title=post.title,
            content=post.content,
            user_id=fake_user_id
        )

        # 保存到数据库
        db.add(db_post)
        db.commit()
        db.refresh(db_post)

        return db_post

    except Exception as e:
        # 发生错误时回滚
        if db:
            db.rollback()
        raise HTTPException(status_code=500, detail=f"创建帖子失败: {str(e)}")
    finally:
        db.close()


from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.shared.utils.file_manager import FileManager
from app.core.community.image_models import CommunityImage, ImageType
from typing import Dict


@router.post("/posts/{post_id}/images")
async def upload_post_image(
        post_id: int,
        file: UploadFile = File(...),
        # current_user: User = Depends(get_current_user)  # TODO: 添加用户认证
        # db: Session = Depends(get_db)  # 不使用依赖注入，手动管理
):
    """上传帖子图片"""
    from app.shared.utils.file_manager import FileManager
    from app.core.community.image_models import CommunityImage, ImageType
    from fastapi import HTTPException

    db: Session = SessionLocal()  # 手动创建数据库会话
    try:
        # 验证文件类型
        if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
            raise HTTPException(status_code=400, detail="不支持的图片格式")

        # 读取文件内容
        content = await file.read()

        # 保存文件
        file_manager = FileManager()
        userid = "user1"  # TODO: 从认证中获取真实用户ID

        file_path, public_url = file_manager.save_uploaded_file(
            content=content,
            filename=file.filename,
            userid=userid,
            category="posts",
            post_id=str(post_id)
        )

        # 保存到数据库
        community_image = CommunityImage(
            uploader_id=1,  # TODO: 从认证中获取真实用户ID
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(content),
            mime_type=file.content_type,
            image_type=ImageType.POST.value,
            target_id=post_id
        )
        db.add(community_image)
        db.commit()  # 提交到数据库
        db.refresh(community_image)  # 刷新获取ID

        print(f"图片已保存到数据库，ID: {community_image.id}")  # 调试信息

        return {
            "message": "帖子图片上传成功",
            "file_path": file_path,
            "public_url": public_url,
            "filename": file.filename,
            "size": len(content),
            "image_id": community_image.id  # 返回数据库ID
        }

    except Exception as e:
        db.rollback()  # 出错时回滚
        print(f"上传图片失败: {str(e)}")  # 打印错误信息
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")
    finally:
        db.close()  # 关闭数据库连接


@router.post("/comments/{comment_id}/images")
async def upload_comment_image(
    comment_id: int,
    file: UploadFile = File(...),
    # current_user: User = Depends(get_current_user)  # TODO: 添加用户认证
    # db: Session = Depends(get_db)  # TODO: 添加数据库依赖
):
    """上传评论图片"""
    from app.shared.utils.file_manager import FileManager
    from app.core.community.image_models import CommunityImage, ImageType
    from fastapi import HTTPException
    
    # 验证文件类型
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="不支持的图片格式")
    
    # 读取文件内容
    content = await file.read()
    
    # 保存文件
    file_manager = FileManager()
    userid = "user1"  # TODO: 从认证中获取真实用户ID
    
    file_path, public_url = file_manager.save_uploaded_file(
        content=content,
        filename=file.filename,
        userid=userid,
        category="comments",
        post_id=str(comment_id)  # 这里用comment_id作为目录名
    )
    
    # TODO: 保存到数据库
    # community_image = CommunityImage(
    #     uploader_id=1,  # TODO: 从认证中获取真实用户ID
    #     original_filename=file.filename,
    #     file_path=file_path,
    #     file_size=len(content),
    #     mime_type=file.content_type,
    #     image_type=ImageType.COMMENT,
    #     target_id=comment_id
    # )
    # db.add(community_image)
    # db.commit()
    
    return {
        "message": "评论图片上传成功",
        "file_path": file_path,
        "public_url": public_url,
        "filename": file.filename,
        "size": len(content)
    }


@router.get("/posts/{post_id}")
async def get_post(post_id: int, db: Session = Depends(get_db)):
    """获取单个帖子详情"""
    pass


@router.put("/posts/{post_id}")
async def update_post(post_id: int):
    """更新帖子"""
    pass


@router.delete("/posts/{post_id}")
async def delete_post(post_id: int):
    """删除帖子"""
    pass


# 评论相关
@router.get("/posts/{post_id}/comments")
async def get_comments(post_id: int):
    """获取帖子的评论列表"""
    pass


@router.post("/posts/{post_id}/comments")
async def create_comment(post_id: int):
    """创建评论"""
    pass


@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: int):
    """删除评论"""
    pass


# 点赞相关
@router.post("/posts/{post_id}/like")
async def like_post(post_id: int):
    """点赞帖子"""
    pass


@router.delete("/posts/{post_id}/like")
async def unlike_post(post_id: int):
    """取消点赞帖子"""
    pass


@router.post("/comments/{comment_id}/like")
async def like_comment(comment_id: int):
    """点赞评论"""
    pass


@router.delete("/comments/{comment_id}/like")
async def unlike_comment(comment_id: int):
    """取消点赞评论"""
    pass
