"""
激励系统数据模型
"""

from sqlalchemy import Column, BigInteger, String, Text, ForeignKey, Integer, Enum, DateTime
from sqlalchemy.sql import func
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserAchievement(Base):
    """用户成就模型"""
    __tablename__ = "user_achievements"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(BigInteger, ForeignKey("achievements.id"), nullable=False)
    earned_at = Column(DateTime(timezone=True), server_default=func.now())
