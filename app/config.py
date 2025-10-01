"""
GreenMorph 配置文件
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    app_name: str = "GreenMorph API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    
    # MySQL数据库配置
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_username: str = "greenmorph"
    mysql_password: str = "greenmorph123"
    mysql_database: str = "greenmorph"
    mysql_charset: str = "utf8mb4"
    
    # 数据库连接URL（自动生成）
    database_url: str = ""
    
    # JWT配置
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # 文件上传配置
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_image_types: list = ["image/jpeg", "image/png", "image/webp"]
    
    # 文件存储路径
    static_dir: str = "app/static"
    input_dir: str = "app/static/input"
    output_dir: str = "app/static/output"
    
    # AI模型配置
    tongyi_api_key: Optional[str] = None
    tongyi_model: str = "qwen-vl-plus"
    tongyi_base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    
    # 其他AI服务配置（备用）
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4-vision-preview"
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-opus-20240229"
    replicate_api_token: Optional[str] = None
    
    # 图像生成配置
    image_generation_model: str = "stabilityai/stable-diffusion-xl-base-1.0"
    controlnet_model: str = "lllyasviel/sd-controlnet-canny"
    
    # 图像处理配置
    max_image_size: tuple = (1024, 1024)
    image_quality: int = 95
    
    # 环保风格提示词
    eco_style_prompt: str = (
        "eco-friendly, sustainable, natural materials, "
        "recycled, upcycled, green design, organic textures, "
        "earth tones, minimalist, clean lines"
    )
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }


# 全局配置实例
settings = Settings()

# 自动生成MySQL连接URL
settings.database_url = (
    f"mysql+pymysql://{settings.mysql_username}:{settings.mysql_password}"
    f"@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}"
    f"?charset={settings.mysql_charset}"
)

# 确保必要的目录存在
os.makedirs(settings.input_dir, exist_ok=True)
os.makedirs(settings.output_dir, exist_ok=True)
os.makedirs(f"{settings.input_dir}/avatars", exist_ok=True)
os.makedirs(f"{settings.input_dir}/redesign_projects", exist_ok=True)
os.makedirs(f"{settings.input_dir}/posts", exist_ok=True)
os.makedirs(f"{settings.output_dir}/redesign_projects", exist_ok=True)
os.makedirs(f"{settings.output_dir}/steps", exist_ok=True)
