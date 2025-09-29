"""
数据库连接和模型定义
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from loguru import logger

from app.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

# 元数据
metadata = MetaData()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """初始化数据库"""
    try:
        # 导入所有模型以确保它们被注册
        from app.core.user.models import User
        from app.core.redesign.models import RedesignProject
        from app.core.community.models import Post, Comment, Like
        from app.core.gamification.models import Achievement, UserAchievement
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise
