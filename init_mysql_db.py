#!/usr/bin/env python3
"""
MySQL数据库初始化脚本
创建数据库和用户，并初始化表结构
"""

import os
import sys
import pymysql
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings


def create_database_and_user():
    """创建数据库和用户"""
    try:
        # 连接到MySQL服务器（不指定数据库）
        connection = pymysql.connect(
            host=settings.mysql_host,
            port=settings.mysql_port,
            user='root',  # 使用root用户创建数据库
            password=input("请输入MySQL root密码: "),
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # 创建数据库
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{settings.mysql_database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            logger.info(f"数据库 '{settings.mysql_database}' 创建成功")
            
            # 创建用户（如果不存在）
            cursor.execute(f"CREATE USER IF NOT EXISTS '{settings.mysql_username}'@'%' IDENTIFIED BY '{settings.mysql_password}'")
            logger.info(f"用户 '{settings.mysql_username}' 创建成功")
            
            # 授权
            cursor.execute(f"GRANT ALL PRIVILEGES ON `{settings.mysql_database}`.* TO '{settings.mysql_username}'@'%'")
            cursor.execute("FLUSH PRIVILEGES")
            logger.info("用户权限设置成功")
            
        connection.close()
        return True
        
    except Exception as e:
        logger.error(f"创建数据库和用户失败: {str(e)}")
        return False


def test_connection():
    """测试数据库连接"""
    try:
        engine = create_engine(settings.database_url)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("数据库连接测试成功")
            return True
    except Exception as e:
        logger.error(f"数据库连接测试失败: {str(e)}")
        return False


def create_tables():
    """创建所有表"""
    try:
        from app.database import engine, Base
        from app.core.user.models import User
        from app.core.redesign.models import RedesignProject
        from app.core.community.models import Post, Comment, Like
        from app.core.gamification.models import Achievement, UserAchievement
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
        return True
        
    except Exception as e:
        logger.error(f"创建表失败: {str(e)}")
        return False


def insert_initial_data():
    """插入初始数据"""
    try:
        from app.database import SessionLocal
        from app.core.gamification.models import Achievement, ConditionType
        
        db = SessionLocal()
        
        # 创建初始成就数据
        achievements = [
            Achievement(
                name="新手改造师",
                description="完成第一个改造项目",
                condition_type=ConditionType.PROJECT_COUNT,
                condition_value=1,
                points=10
            ),
            Achievement(
                name="社区活跃者",
                description="发布第一个帖子",
                condition_type=ConditionType.POST_COUNT,
                condition_value=1,
                points=5
            ),
            Achievement(
                name="改造达人",
                description="完成10个改造项目",
                condition_type=ConditionType.PROJECT_COUNT,
                condition_value=10,
                points=50
            ),
            Achievement(
                name="社区明星",
                description="获得100个点赞",
                condition_type=ConditionType.LIKES_RECEIVED,
                condition_value=100,
                points=100
            )
        ]
        
        for achievement in achievements:
            db.add(achievement)
        
        db.commit()
        logger.info("初始数据插入成功")
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"插入初始数据失败: {str(e)}")
        return False


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🚀 开始初始化MySQL数据库")
    logger.info("=" * 60)
    
    # 步骤1: 创建数据库和用户
    logger.info("步骤1: 创建数据库和用户...")
    if not create_database_and_user():
        logger.error("数据库初始化失败")
        sys.exit(1)
    
    # 步骤2: 测试连接
    logger.info("步骤2: 测试数据库连接...")
    if not test_connection():
        logger.error("数据库连接失败")
        sys.exit(1)
    
    # 步骤3: 创建表
    logger.info("步骤3: 创建数据库表...")
    if not create_tables():
        logger.error("创建表失败")
        sys.exit(1)
    
    # 步骤4: 插入初始数据
    logger.info("步骤4: 插入初始数据...")
    if not insert_initial_data():
        logger.error("插入初始数据失败")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("✅ MySQL数据库初始化完成！")
    logger.info("=" * 60)
    logger.info(f"数据库: {settings.mysql_database}")
    logger.info(f"用户: {settings.mysql_username}")
    logger.info(f"主机: {settings.mysql_host}:{settings.mysql_port}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
