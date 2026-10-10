from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends
from app.common.response import Response
from app.schemas.auth import LoginRequest
from app.schemas.auth import RegisterRequest
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["权限验证"])


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """登录"""
    result = auth_service.login(db, data)
    # 返回信息
    return Response.success(
        message="登录成功",
        data=result,
    )

@router.post("/token", summary="Swagger 授权登录（表单，仅供文档页使用）")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """给 Swagger 的 Authorize 按钮用：入参是表单，出参必须是 access_token"""
    result = auth_service.login(
        db, LoginRequest(username=form_data.username, password=form_data.password)
    )
    # 这里不能用 Response.success 包装，Swagger 只认顶层的 access_token 字段
    return {"access_token": result.token, "token_type": "bearer"}


@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """注册"""
    auth_service.register(db, data)
    # 返回信息
    return Response.success(message="注册成功")
