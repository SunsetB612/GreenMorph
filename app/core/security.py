"""
认证安全模块
"""
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
# 移除循环导入，User模型将在运行时动态获取

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# JWT认证方案
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        import bcrypt
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        print(f"密码验证失败: {e}")
        return False

def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    # 调试信息：打印密码长度
    password_bytes = len(password.encode('utf-8'))
    print(f"密码长度: {len(password)} 字符, {password_bytes} 字节")
    print(f"密码内容: {repr(password)}")
    
    # 确保密码长度不超过72字节（bcrypt限制）
    if password_bytes > 72:
        print(f"密码过长，截断到72字节")
        password = password[:72]
    
    try:
        # 使用更简单的bcrypt配置
        import bcrypt
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        print(f"密码哈希失败: {e}")
        print(f"密码内容: {repr(password)}")
        raise

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """验证JWT令牌"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = verify_token(token)
        if payload is None:
            raise credentials_exception
        
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # 从数据库获取用户信息
    from sqlalchemy import text
    user = db.execute(
        text("SELECT * FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    ).fetchone()
    
    if user is None:
        raise credentials_exception
    
    # 返回用户数据字典，避免循环导入
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "password_hash": user.password_hash,
        "bio": user.bio,
        "skill_level": user.skill_level,
        "points": user.points,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }

def get_current_active_user(current_user = Depends(get_current_user)):
    """获取当前活跃用户"""
    return current_user
