import uuid

from app.data.config import settings
from app.utils.exceptions import InvalidTokenException
from .models import UserModel
from .utils import OAuth2PasswordBearerWithCookie
from .service import UserService

from jose import jwt
from fastapi import Depends, HTTPException, status

oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/api/auth/login")

async def get_not_verified_user(token: str = Depends(oauth2_scheme)) -> UserModel | None:
    try:
        payload = jwt.decode(token, settings.SECRET, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenException
    except Exception:
        raise InvalidTokenException
    return await UserService.get_user(uuid.UUID(user_id))

async def get_current_verified_user(
        current_user: UserModel = Depends(get_not_verified_user)
    ) -> UserModel | None:
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Verify email"
        )
    return current_user


async def get_current_superuser(
    current_user: UserModel = Depends(get_current_verified_user),
) -> UserModel:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges"
        )
    return current_user


async def get_current_active_user(
    current_user: UserModel = Depends(get_current_verified_user),
) -> UserModel:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User is not active"
        )
    return current_user
