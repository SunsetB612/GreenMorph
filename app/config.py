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
    mysql_username: str = "root"
    mysql_password: str = ""  # 从环境变量获取
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
    static_dir: str = "static"
    # 注意：不再使用固定的input_dir和output_dir，改为按用户分目录
    # input_dir: str = "static/input"  # 已废弃
    # output_dir: str = "static/output"  # 已废弃
    
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
    
    # Hugging Face API配置
    huggingface_api_token: Optional[str] = None
    
    # 云存储配置
    imgbb_api_key: Optional[str] = "ff3d6b661dc2c1035dd5bf3754499f8d"  # ImgBB API密钥
    enable_cloud_storage: bool = True  # 是否启用云存储功能
    
    # Web搜索配置
    google_search_api_key: Optional[str] = None  # Google Search API密钥
    google_search_engine_id: Optional[str] = None  # Google自定义搜索引擎ID
    serpapi_key: Optional[str] = None  # SerpAPI密钥（备选方案）
    enable_web_search: bool = True  # 是否启用网页搜索功能
    
    # 国内搜索API配置
    baidu_search_api_key: Optional[str] = None  # 百度搜索API密钥
    baidu_search_secret_key: Optional[str] = None  # 百度搜索API密钥
    bing_search_api_key: Optional[str] = None  # 必应搜索API密钥
    sogou_search_api_key: Optional[str] = None  # 搜狗搜索API密钥
    search_priority: str = "baidu,bing,google,serpapi"  # 搜索API优先级
    
    # Seedream4(APIYI) 图生图HTTP接口配置
    seedream_api_base: str = "https://api.apiyi.com"
    seedream_api_key: Optional[str] = None  # 环境变量SEEDREAM_API_KEY

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

# 确保必要的目录存在（只创建static根目录，用户目录按需创建）
os.makedirs(settings.static_dir, exist_ok=True)
