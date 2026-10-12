from app.database import SessionLocal
from app.models import User
from fastapi import status
from app.utils.jwt import decode_access_token
from app.common.exceptions import BusinessException


def user_id_from_authorization(authorization: str | None) -> int:
    """解析token 拿到用户ID"""
    if not authorization:
        raise BusinessException(message="缺少authorization", code=401)
    token = authorization
    if authorization.lower().startswith('bearer '):
        token = authorization.split(' ', 1)[1].strip()
    if not token :
        raise BusinessException(message="缺少登录凭证", code=401)
    """JWT token 鉴权验证合法性"""
    try:
        payload = decode_access_token(token)
    except Exception:
        raise BusinessException(
            code=status.HTTP_401_UNAUTHORIZED, message="登录已失效，请重新登录"
        )
    # 获取到用户ID
    user_id = payload.get("user_id")
    if not user_id:
        raise BusinessException(
            code=status.HTTP_401_UNAUTHORIZED, message="无效的登录凭证"
        )
    # 从数据库根据用户ID查询用户信息
    db=SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id, User.status == 1).first()
        if not user:
            raise BusinessException(
                code=status.HTTP_401_UNAUTHORIZED,
                message="登录已失效或用户已被禁用",
        )
        return user_id
    finally:
        db.close()