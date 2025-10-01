#!/usr/bin/env python3
"""
MySQL数据库初始化脚本 v3.0
根据最新的数据库设计创建数据库和表结构
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
        # 获取用户输入的密码
        password = input("请输入MySQL root密码: ")
        
        # 连接到MySQL服务器（不指定数据库）
        connection = pymysql.connect(
            host=settings.mysql_host,
            port=settings.mysql_port,
            user='root',  # 使用root用户创建数据库
            password=password,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # 创建数据库
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{settings.mysql_database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            logger.info(f"数据库 '{settings.mysql_database}' 创建成功")
            
            # 使用root用户，不需要创建新用户
            logger.info("使用root用户，跳过用户创建步骤")
            
        connection.close()
        return True
        
    except Exception as e:
        logger.error(f"创建数据库和用户失败: {str(e)}")
        return False


def test_connection():
    """测试数据库连接"""
    try:
        # 使用用户输入的密码构建连接URL
        password = input("请再次输入MySQL root密码进行连接测试: ")
        test_url = f"mysql+pymysql://root:{password}@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}?charset={settings.mysql_charset}"
        
        engine = create_engine(test_url)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("数据库连接测试成功")
            return True
    except Exception as e:
        logger.error(f"数据库连接测试失败: {str(e)}")
        return False


def create_tables():
    """根据新的数据库设计创建所有表"""
    try:
        # 使用用户输入的密码构建连接URL
        password = input("请再次输入MySQL root密码创建表: ")
        database_url = f"mysql+pymysql://root:{password}@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}?charset={settings.mysql_charset}"
        engine = create_engine(database_url)
        
        # 创建所有表的SQL语句
        create_tables_sql = """
        -- 1. 用户表
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            avatar_path VARCHAR(255),
            bio TEXT,
            skill_level ENUM('beginner', 'intermediate', 'advanced') DEFAULT 'beginner',
            points INT DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );

        -- 2. 用户输入图片表
        CREATE TABLE IF NOT EXISTS input_images (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            user_id BIGINT NOT NULL,
            original_filename VARCHAR(255),
            input_image_path VARCHAR(500) NOT NULL,
            input_image_size INT,
            mime_type VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        -- 3. 用户输入需求表
        CREATE TABLE IF NOT EXISTS input_demand (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            user_id BIGINT NOT NULL,
            demand TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        -- 4. 改造项目表
        CREATE TABLE IF NOT EXISTS redesign_projects (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            user_id BIGINT NOT NULL,
            project_name VARCHAR(200) NOT NULL,
            input_image_id BIGINT,
            input_demand_id BIGINT,
            output_image_path VARCHAR(500),
            output_pdf_path VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (input_image_id) REFERENCES input_images(id) ON DELETE SET NULL,
            FOREIGN KEY (input_demand_id) REFERENCES input_demand(id) ON DELETE SET NULL
        );

        -- 5. 改造步骤表
        CREATE TABLE IF NOT EXISTS redesign_steps (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            project_id BIGINT NOT NULL,
            step_number INT NOT NULL,
            description TEXT NOT NULL,
            step_image_path VARCHAR(500),
            FOREIGN KEY (project_id) REFERENCES redesign_projects(id) ON DELETE CASCADE,
            INDEX idx_project_step (project_id, step_number)
        );

        -- 6. 项目详情表
        CREATE TABLE IF NOT EXISTS project_details (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            project_id BIGINT NOT NULL,
            total_cost_estimate TEXT,
            total_time_estimate TEXT,
            difficulty_level VARCHAR(20),
            materials_and_tools TEXT,
            safety_notes TEXT,
            tips TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES redesign_projects(id) ON DELETE CASCADE
        );

        -- 7. 社区帖子表
        CREATE TABLE IF NOT EXISTS posts (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            user_id BIGINT NOT NULL,
            title VARCHAR(200) NOT NULL,
            content TEXT NOT NULL,
            images JSON,
            likes_count INT DEFAULT 0,
            comments_count INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        -- 8. 评论表
        CREATE TABLE IF NOT EXISTS comments (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            post_id BIGINT NOT NULL,
            user_id BIGINT NOT NULL,
            content TEXT NOT NULL,
            images JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        -- 9. 点赞表
        CREATE TABLE IF NOT EXISTS likes (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            user_id BIGINT NOT NULL,
            target_type ENUM('post', 'comment') NOT NULL,
            target_id BIGINT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_like (user_id, target_type, target_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        -- 10. 成就表
        CREATE TABLE IF NOT EXISTS achievements (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            icon_filename VARCHAR(255),
            condition_type ENUM('project_count', 'post_count', 'likes_received') NOT NULL,
            condition_value INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- 11. 用户成就表
        CREATE TABLE IF NOT EXISTS user_achievements (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            user_id BIGINT NOT NULL,
            achievement_id BIGINT NOT NULL,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_user_achievement (user_id, achievement_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (achievement_id) REFERENCES achievements(id) ON DELETE CASCADE
        );
        """
        
        with engine.connect() as connection:
            # 执行创建表的SQL
            for statement in create_tables_sql.split(';'):
                if statement.strip():
                    connection.execute(text(statement))
                    connection.commit()
        
        logger.info("数据库表创建成功")
        return True
        
    except Exception as e:
        logger.error(f"创建表失败: {str(e)}")
        return False


def insert_initial_data():
    """插入初始数据"""
    try:
        # 使用用户输入的密码构建连接URL
        password = input("请再次输入MySQL root密码插入数据: ")
        database_url = f"mysql+pymysql://root:{password}@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}?charset={settings.mysql_charset}"
        engine = create_engine(database_url)
        
        # 插入初始成就数据
        insert_achievements_sql = """
        INSERT INTO achievements (name, description, condition_type, condition_value) VALUES
        ('新手改造师', '完成第一个改造项目', 'project_count', 1),
        ('社区活跃者', '发布第一个帖子', 'post_count', 1),
        ('改造达人', '完成10个改造项目', 'project_count', 10),
        ('社区明星', '获得100个点赞', 'likes_received', 100);
        """
        
        with engine.connect() as connection:
            connection.execute(text(insert_achievements_sql))
            connection.commit()
        
        logger.info("初始数据插入成功")
        return True
        
    except Exception as e:
        logger.error(f"插入初始数据失败: {str(e)}")
        return False


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🚀 开始初始化MySQL数据库 v3.0")
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
