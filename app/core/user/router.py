"""
用户认证API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import get_current_active_user
# 移除User模型导入，避免循环导入
from .schemas import UserCreateWithValidation, UserLoginWithValidation, UserUpdateWithValidation
from app.shared.models import UserResponse, Token
from .services import create_user, login_user, get_user_by_id, update_user, delete_user

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreateWithValidation, db: Session = Depends(get_db)):
    """用户注册"""
    try:
        return create_user(db, user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )

@router.post("/login", response_model=dict)
async def login(user_login: UserLoginWithValidation, db: Session = Depends(get_db)):
    """用户登录"""
    try:
        return login_user(db, user_login)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        bio=current_user["bio"],
        skill_level=current_user["skill_level"],
        points=current_user["points"],
        is_active=current_user["is_active"],
        created_at=current_user["created_at"]
    )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """根据ID获取用户信息"""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdateWithValidation,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新当前用户信息"""
    try:
        updated_user = update_user(db, current_user["id"], user_update)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新失败: {str(e)}"
        )

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除当前用户"""
    try:
        success = delete_user(db, current_user["id"])
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}"
        )