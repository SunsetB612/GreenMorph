"""
GreenMorph 数据模型
定义API请求和响应的数据结构
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class StyleType(str, Enum):
    """改造风格类型"""
    MODERN = "modern"
    VINTAGE = "vintage"
    MINIMALIST = "minimalist"
    INDUSTRIAL = "industrial"
    SCANDINAVIAN = "scandinavian"
    BOHEMIAN = "bohemian"
    RUSTIC = "rustic"
    CONTEMPORARY = "contemporary"


class MaterialType(str, Enum):
    """材料类型"""
    WOOD = "wood"
    METAL = "metal"
    FABRIC = "fabric"
    GLASS = "glass"
    CERAMIC = "ceramic"
    PLASTIC = "plastic"
    LEATHER = "leather"
    PAPER = "paper"




class ImageAnalysisResponse(BaseModel):
    """图片分析响应"""
    main_objects: List[str] = Field(description="主要物体识别结果")
    materials: List[MaterialType] = Field(description="识别出的材料类型")
    colors: List[str] = Field(description="主要颜色")
    condition: str = Field(description="物品状态描述")
    dimensions: Optional[Dict[str, float]] = Field(None, description="预估尺寸")
    features: List[str] = Field(description="关键特征")
    confidence: float = Field(description="分析置信度")
    appearance: Optional[str] = Field(None, description="外观特征描述")
    structure: Optional[str] = Field(None, description="结构特征描述")
    status: Optional[str] = Field(None, description="状态评估")
    uploaded_file: Optional[str] = Field(None, description="上传的文件名")
    file_path: Optional[str] = Field(None, description="文件保存路径")
    cloud_url: Optional[str] = Field(None, description="云存储URL")
    input_number: Optional[int] = Field(None, description="输入图片编号")


class RedesignRequest(BaseModel):
    """旧物再设计请求"""
    image_url: Optional[str] = Field(None, description="旧物图片URL")
    input_image_id: Optional[int] = Field(None, description="已上传图片的ID")
    user_requirements: str = Field(description="用户改造需求描述")
    target_style: StyleType = Field(description="目标风格")
    target_materials: Optional[List[MaterialType]] = Field(None, description="目标材料")
    budget_range: Optional[str] = Field(None, description="预算范围")
    skill_level: Optional[str] = Field("beginner", description="技能水平")
    
    class Config:
        schema_extra = {
            "example": {
                "user_requirements": "将旧木椅改造成现代简约风格的书桌",
                "target_style": "modern",
                "target_materials": ["wood"],
                "budget_range": "100-300元",
                "skill_level": "intermediate"
            }
        }


class RedesignStep(BaseModel):
    """改造步骤"""
    step_number: int = Field(description="步骤编号")
    title: str = Field(description="步骤标题")
    description: str = Field(description="步骤描述")
    materials_needed: List[str] = Field(description="所需材料")
    tools_needed: List[str] = Field(description="所需工具")
    estimated_time: str = Field(description="预估时间")
    difficulty: str = Field(description="难度等级")
    image_prompt: str = Field(description="图像生成提示词")
    safety_notes: Optional[str] = Field(None, description="安全注意事项")


class RedesignResponse(BaseModel):
    """旧物再设计响应"""
    final_image_url: str = Field(description="最终效果图URL")
    step_images: List[str] = Field(description="各步骤示意图URL列表")
    redesign_guide: List[RedesignStep] = Field(description="改造说明书")
    total_estimated_time: str = Field(description="总预估时间")
    total_cost_estimate: str = Field(description="总成本估算")
    sustainability_score: int = Field(description="可持续性评分(1-10)")
    difficulty_rating: str = Field(description="整体难度评级")
    tips: List[str] = Field(description="改造小贴士")


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(description="错误信息")
    detail: Optional[str] = Field(None, description="详细错误信息")
    code: int = Field(description="错误代码")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(description="服务状态")
    version: str = Field(description="版本号")
    timestamp: str = Field(description="时间戳")


# 用户认证相关模型
class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: str


class UserCreate(UserBase):
    """用户注册模型"""
    password: str


class UserLogin(BaseModel):
    """用户登录模型"""
    email: str
    password: str


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    bio: Optional[str] = None
    skill_level: str = 'beginner'
    points: int = 0
    is_active: bool = True
    created_at: datetime


class Token(BaseModel):
    """令牌响应模型"""
    access_token: str
    token_type: str = "bearer"


class UserUpdate(BaseModel):
    """用户更新模型"""
    username: Optional[str] = None
    bio: Optional[str] = None
    skill_level: Optional[str] = None
