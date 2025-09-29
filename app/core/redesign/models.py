"""
改造项目数据模型
"""

from sqlalchemy import Column, BigInteger, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class RedesignProject(Base):
    """改造项目模型"""
    __tablename__ = "redesign_projects"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    original_image_filename = Column(String(255))
    final_image_filename = Column(String(255))
    target_style = Column(String(50))
    
    # 关系
    user = relationship("User", back_populates="redesign_projects")
