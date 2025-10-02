"""
社区图片数据模型
"""

from sqlalchemy import Column, BigInteger, String, ForeignKey, Integer, Enum, DateTime
from sqlalchemy.sql import func
from app.database import Base
import enum


class ImageType(str, enum.Enum):
    """图片类型枚举"""
    POST = "post"
    COMMENT = "comment"


class CommunityImage(Base):
    """社区图片模型"""
    __tablename__ = "community_images"
    
    id = Column(BigInteger, primary_key=True, index=True)
    uploader_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String(255))
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    image_type = Column(Enum(ImageType), nullable=False)
    target_id = Column(BigInteger, nullable=False)  # 帖子ID或评论ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
