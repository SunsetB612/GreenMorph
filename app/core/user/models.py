"""
用户数据模型
"""

from sqlalchemy import Column, BigInteger, String, Text, Enum, Integer, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class SkillLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate" 
    advanced = "advanced"


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    bio = Column(Text)
    skill_level = Column(Enum(SkillLevel), default=SkillLevel.beginner)
    points = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系定义暂时注释掉，避免循环导入问题
    # redesign_projects = relationship("RedesignProject", back_populates="user", lazy="dynamic")
    # posts = relationship("Post", back_populates="user", lazy="dynamic")
    # comments = relationship("Comment", back_populates="user", lazy="dynamic")
    # likes = relationship("Like", back_populates="user", lazy="dynamic")
    # user_achievements = relationship("UserAchievement", back_populates="user", lazy="dynamic")
