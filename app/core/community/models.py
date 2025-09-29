"""
社区数据模型
"""

from sqlalchemy import Column, BigInteger, String, Text, ForeignKey, Integer, JSON, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class TargetType(str, enum.Enum):
    POST = "post"
    COMMENT = "comment"


class Post(Base):
    """帖子模型"""
    __tablename__ = "posts"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    images = Column(JSON)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    
    # 关系
    user = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")
    likes = relationship("Like", back_populates="target_post")


class Comment(Base):
    """评论模型"""
    __tablename__ = "comments"
    
    id = Column(BigInteger, primary_key=True, index=True)
    post_id = Column(BigInteger, ForeignKey("posts.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    
    # 关系
    post = relationship("Post", back_populates="comments")
    user = relationship("User", back_populates="comments")
    likes = relationship("Like", back_populates="target_comment")


class Like(Base):
    """点赞模型"""
    __tablename__ = "likes"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    target_type = Column(Enum(TargetType), nullable=False)
    target_id = Column(BigInteger, nullable=False)
    
    # 关系
    user = relationship("User", back_populates="likes")
    target_post = relationship("Post", back_populates="likes", foreign_keys=[target_id])
    target_comment = relationship("Comment", back_populates="likes", foreign_keys=[target_id])
