"""
社区功能API路由
"""

from fastapi import APIRouter

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
