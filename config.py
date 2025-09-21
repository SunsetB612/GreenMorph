"""
GreenMorph 配置文件
多模态大模型API调用模块配置
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    app_name: str = "GreenMorph API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    
    # 文件上传配置
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_image_types: list = ["image/jpeg", "image/png", "image/webp"]
    input_dir: str = "input"
    output_dir: str = "output"
    
    # 多模态大模型API配置
    # 通义千问配置
    tongyi_api_key: Optional[str] = None
    tongyi_model: str = "qwen-vl-plus"
    tongyi_base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    
    # OpenAI配置（保留作为备用）
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4-vision-preview"
    
    # Anthropic配置（保留作为备用）
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-opus-20240229"
    
    # Replicate配置（保留作为备用）
    replicate_api_token: Optional[str] = None
    
    # 图像生成配置
    image_generation_model: str = "stabilityai/stable-diffusion-xl-base-1.0"
    controlnet_model: str = "lllyasviel/sd-controlnet-canny"
    
    # 图像处理配置
    max_image_size: tuple = (1024, 1024)
    image_quality: int = 95
    
    @field_validator('max_image_size', mode='before')
    @classmethod
    def parse_max_image_size(cls, v):
        if isinstance(v, str):
            # 解析 "1024,1024" 格式
            try:
                parts = v.split(',')
                return (int(parts[0]), int(parts[1]))
            except:
                return (1024, 1024)
        return v
    
    # 环保风格提示词
    eco_style_prompt: str = (
        "eco-friendly, sustainable, natural materials, "
        "recycled, upcycled, green design, organic textures, "
        "earth tones, minimalist, clean lines"
    )
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"  # 忽略额外的字段
    }


# 全局配置实例
settings = Settings()

# 确保必要的目录存在
os.makedirs(settings.input_dir, exist_ok=True)
os.makedirs(settings.output_dir, exist_ok=True)
