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
    # likes关系通过多态设计，不需要直接关系


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
    # likes关系通过多态设计，不需要直接关系


class Like(Base):
    """点赞模型"""
    __tablename__ = "likes"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    target_type = Column(Enum(TargetType), nullable=False)
    target_id = Column(BigInteger, nullable=False)
    
    # 关系
    user = relationship("User", back_populates="likes")
    # 多态关系不需要直接的外键关系
