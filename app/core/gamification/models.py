"""
激励系统数据模型
"""

from sqlalchemy import Column, BigInteger, String, Text, ForeignKey, Integer, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ConditionType(str, enum.Enum):
    PROJECT_COUNT = "project_count"
    POST_COUNT = "post_count"
    LIKES_RECEIVED = "likes_received"


class Achievement(Base):
    """成就模型"""
    __tablename__ = "achievements"
    
    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon_filename = Column(String(255))
    condition_type = Column(Enum(ConditionType), nullable=False)
    condition_value = Column(Integer, nullable=False)
    points = Column(Integer, default=10)
    
    # 关系
    user_achievements = relationship("UserAchievement", back_populates="achievement")


class UserAchievement(Base):
    """用户成就模型"""
    __tablename__ = "user_achievements"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(BigInteger, ForeignKey("achievements.id"), nullable=False)
    
    # 关系
    user = relationship("User", back_populates="user_achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")
