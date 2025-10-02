"""
社区功能API路由
"""

from fastapi import APIRouter, UploadFile, File

router = APIRouter()


# 帖子相关
@router.get("/posts")
async def get_posts():
    """获取帖子列表"""
    pass


@router.post("/posts")
async def create_post():
    """创建帖子"""
    pass


@router.post("/posts/{post_id}/images")
async def upload_post_image(
    post_id: int,
    file: UploadFile = File(...),
    # current_user: User = Depends(get_current_user)  # TODO: 添加用户认证
    # db: Session = Depends(get_db)  # TODO: 添加数据库依赖
):
    """上传帖子图片"""
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
        category="posts",
        post_id=str(post_id)
    )
    
    # TODO: 保存到数据库
    # community_image = CommunityImage(
    #     uploader_id=1,  # TODO: 从认证中获取真实用户ID
    #     original_filename=file.filename,
    #     file_path=file_path,
    #     file_size=len(content),
    #     mime_type=file.content_type,
    #     image_type=ImageType.POST,
    #     target_id=post_id
    # )
    # db.add(community_image)
    # db.commit()
    
    return {
        "message": "帖子图片上传成功",
        "file_path": file_path,
        "public_url": public_url,
        "filename": file.filename,
        "size": len(content)
    }


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
async def get_post(post_id: int):
    """获取单个帖子"""
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
