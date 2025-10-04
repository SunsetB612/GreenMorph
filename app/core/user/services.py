"""
用户认证业务逻辑
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException, status
from typing import Optional
from datetime import datetime
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.user.models import User
from .schemas import UserCreateWithValidation, UserLoginWithValidation, UserUpdateWithValidation
from app.shared.models import UserResponse

def create_user(db: Session, user: UserCreateWithValidation) -> UserResponse:
    """创建新用户"""
    # 检查邮箱是否已存在
    existing_user = db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": user.email}
    ).fetchone()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册"
        )
    
    # 检查用户名是否已存在
    existing_username = db.execute(
        text("SELECT id FROM users WHERE username = :username"),
        {"username": user.username}
    ).fetchone()
    
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该用户名已被使用"
        )
    
    # 创建新用户
    hashed_password = get_password_hash(user.password)
    
    result = db.execute(
        text("""
            INSERT INTO users (username, email, password_hash, created_at)
            VALUES (:username, :email, :password_hash, :created_at)
        """),
        {
            "username": user.username,
            "email": user.email,
            "password_hash": hashed_password,
            "created_at": datetime.utcnow()
        }
    )
    
    db.commit()
    
    # 获取新创建的用户
    new_user = db.execute(
        text("SELECT * FROM users WHERE id = :user_id"),
        {"user_id": result.lastrowid}
    ).fetchone()
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        bio=new_user.bio,
        skill_level=new_user.skill_level,
        points=new_user.points,
        is_active=new_user.is_active,
        created_at=new_user.created_at
    )

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """验证用户凭据"""
    user = db.execute(
        text("SELECT * FROM users WHERE email = :email"),
        {"email": email}
    ).fetchone()
    
    if not user:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    return User(
        id=user.id,
        username=user.username,
        email=user.email,
        password_hash=user.password_hash,
        bio=user.bio,
        skill_level=user.skill_level,
        points=user.points,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

def login_user(db: Session, user_login: UserLoginWithValidation) -> dict:
    """用户登录"""
    user = authenticate_user(db, user_login.email, user_login.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            bio=user.bio,
            skill_level=user.skill_level,
            points=user.points,
            is_active=user.is_active,
            created_at=user.created_at
        )
    }

def get_user_by_id(db: Session, user_id: int) -> Optional[UserResponse]:
    """根据ID获取用户信息"""
    user = db.execute(
        text("SELECT * FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    ).fetchone()
    
    if not user:
        return None
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        bio=user.bio,
        skill_level=user.skill_level,
        points=user.points,
        is_active=user.is_active,
        created_at=user.created_at
    )

def update_user(db: Session, user_id: int, user_update: UserUpdateWithValidation) -> Optional[UserResponse]:
    """更新用户信息"""
    # 检查用户是否存在
    existing_user = db.execute(
        text("SELECT * FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    ).fetchone()
    
    if not existing_user:
        return None
    
    # 构建更新字段
    update_fields = {}
    if user_update.username is not None:
        # 检查新用户名是否已被使用
        if user_update.username != existing_user.username:
            existing_username = db.execute(
                text("SELECT id FROM users WHERE username = :username AND id != :user_id"),
                {"username": user_update.username, "user_id": user_id}
            ).fetchone()
            if existing_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该用户名已被使用"
                )
        update_fields["username"] = user_update.username
    
    if user_update.bio is not None:
        update_fields["bio"] = user_update.bio
    
    if user_update.skill_level is not None:
        update_fields["skill_level"] = user_update.skill_level
    
    if not update_fields:
        return get_user_by_id(db, user_id)
    
    # 执行更新
    set_clause = ", ".join([f"{key} = :{key}" for key in update_fields.keys()])
    update_fields["user_id"] = user_id
    update_fields["updated_at"] = datetime.utcnow()
    
    db.execute(
        text(f"UPDATE users SET {set_clause}, updated_at = :updated_at WHERE id = :user_id"),
        update_fields
    )
    
    db.commit()
    
    return get_user_by_id(db, user_id)

def delete_user(db: Session, user_id: int) -> bool:
    """删除用户"""
    result = db.execute(
        text("DELETE FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    )
    
    db.commit()
    
    return result.rowcount > 0
