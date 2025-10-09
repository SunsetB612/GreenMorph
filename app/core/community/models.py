"""
社区数据模型
"""

from sqlalchemy import Column, BigInteger, String, Text, ForeignKey, Integer, JSON, Enum, DateTime
from sqlalchemy.sql import func
from app.database import Base
import enum
from sqlalchemy.orm import relationship

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
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Comment(Base):
    """评论模型"""
    __tablename__ = "comments"
    
    id = Column(BigInteger, primary_key=True, index=True)
    post_id = Column(BigInteger, ForeignKey("posts.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Like(Base):
    """点赞模型"""
    __tablename__ = "likes"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    target_type = Column(Enum("post","comment",name="targettype"), nullable=False)
    target_id = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
