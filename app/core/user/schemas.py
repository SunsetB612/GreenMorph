"""
用户认证相关的Pydantic模型
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from app.shared.models import UserBase, UserCreate, UserLogin, UserResponse, Token, UserUpdate

# 重新定义带验证的模型
class UserCreateWithValidation(UserCreate):
    """用户注册模型（带验证）"""
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少6位')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('用户名长度至少3位')
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v

class UserLoginWithValidation(UserLogin):
    """用户登录模型（带验证）"""
    email: EmailStr

class UserUpdateWithValidation(UserUpdate):
    """用户更新模型（带验证）"""
    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            if len(v) < 3:
                raise ValueError('用户名长度至少3位')
            if not v.isalnum():
                raise ValueError('用户名只能包含字母和数字')
        return v

class TokenData(BaseModel):
    """令牌数据模型"""
    user_id: Optional[int] = None
