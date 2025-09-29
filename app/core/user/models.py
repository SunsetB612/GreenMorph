"""
用户数据模型
"""

from sqlalchemy import Column, BigInteger, String, Text, Enum, Integer, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class SkillLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    avatar_filename = Column(String(255))
    bio = Column(Text)
    skill_level = Column(Enum(SkillLevel), default=SkillLevel.BEGINNER)
    points = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # 关系
    redesign_projects = relationship("RedesignProject", back_populates="user")
    posts = relationship("Post", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    likes = relationship("Like", back_populates="user")
    user_achievements = relationship("UserAchievement", back_populates="user")
