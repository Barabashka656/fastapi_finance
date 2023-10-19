import uuid

from datetime import datetime, timedelta, timezone

from app.finance.dao import IncomeTypeDAO


from .schemas import (
    BaseProfile,
    Profile,
    Profile,
    RefreshSessionUpdate,
    UserCreate,
    User,
    Token,
    UserCreateDB,
    RefreshSessionCreate,
    UserUpdate,
    UserUpdateDB,
)
from .utils import get_password_hash, is_valid_password
from .models import ProfileModel, UserModel, RefreshSessionModel
from .dao import ProfileDAO, UserDAO, RefreshSessionDAO
from app.utils.exceptions import InvalidTokenException, TokenExpiredException
from app.utils.database.database import async_session_maker
from app.data.config import settings

from fastapi import HTTPException, status
from jose import jwt


class AuthService:
    @classmethod
    async def create_token(cls, user_id: uuid.UUID) -> Token:
        access_token = cls._create_access_token(user_id)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = cls._create_refresh_token()

        async with async_session_maker() as session:
            a = RefreshSessionCreate(
                user_id=user_id,
                refresh_token=refresh_token,
                expires_in=refresh_token_expires.total_seconds(),
            )
            await RefreshSessionDAO.add(
                session,
                RefreshSessionCreate(
                    user_id=user_id,
                    refresh_token=refresh_token,
                    expires_in=refresh_token_expires.total_seconds(),
                ),
            )
            await session.commit()
        return Token(
            access_token=access_token, refresh_token=refresh_token, token_type="bearer"
        )

    @classmethod
    async def logout(cls, token: uuid.UUID) -> None:
        async with async_session_maker() as session:
            refresh_session = await RefreshSessionDAO.find_one_or_none(
                session, RefreshSessionModel.refresh_token == token
            )
            if refresh_session:
                await RefreshSessionDAO.delete(session, id=refresh_session.id)
            await session.commit()

    @classmethod
    async def refresh_token(cls, token: uuid.UUID) -> Token:
        async with async_session_maker() as session:
            refresh_session = await RefreshSessionDAO.find_one_or_none(
                session, RefreshSessionModel.refresh_token == token
            )
            if not refresh_session:
                raise InvalidTokenException
            if datetime.now(timezone.utc) >= refresh_session.created_at + timedelta(
                seconds=refresh_session.expires_in
            ):
                await RefreshSessionDAO.delete(id=refresh_session.id)
                raise TokenExpiredException

            user = await UserDAO.find_one_or_none(session, id=refresh_session.user_id)
            if not user:
                raise InvalidTokenException

            access_token = cls._create_access_token(user.id)
            refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            refresh_token = cls._create_refresh_token()

            await RefreshSessionDAO.update(
                session,
                RefreshSessionModel.id == refresh_session.id,
                obj_in=RefreshSessionUpdate(
                    refresh_token=refresh_token,
                    expires_in=refresh_token_expires.total_seconds(),
                ),
            )
            await session.commit()
        return Token(
            access_token=access_token, refresh_token=refresh_token, token_type="bearer"
        )

    @classmethod
    async def authenticate_user(cls, email: str, password: str) -> UserModel | None:
        async with async_session_maker() as session:
            db_user = await UserDAO.find_one_or_none(session, email=email)
        if db_user and is_valid_password(password, db_user.hashed_password):
            return db_user
        return None

    @classmethod
    async def abort_all_sessions(cls, user_id: uuid.UUID):
        async with async_session_maker() as session:
            await RefreshSessionDAO.delete(
                session, RefreshSessionModel.user_id == user_id
            )
            await session.commit()

    @classmethod
    def _create_access_token(cls, user_id: uuid.UUID) -> str:
        to_encode = {
            "sub": str(user_id),
            "exp": datetime.utcnow()
            + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        }
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET, algorithm=settings.ALGORITHM
        )
        return f"Bearer {encoded_jwt}"

    @classmethod
    def _create_refresh_token(cls) -> str:
        return uuid.uuid4()


class UserService:
    @classmethod
    async def register_new_user(cls, user: UserCreate) -> UserModel:
        async with async_session_maker() as session:
            user_exist = await UserDAO.find_one_or_none(session, email=user.email)
            if user_exist:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail="User already exists"
                )

            user.is_superuser = False
            user.is_verified = False
            db_user = await UserDAO.add(
                session,
                UserCreateDB(
                    **user.model_dump(),
                    hashed_password=get_password_hash(user.password),
                ),
            )
            await session.commit()
        return db_user

    @classmethod
    async def get_user(cls, user_id: uuid.UUID) -> UserModel:
        async with async_session_maker() as session:
            db_user = await UserDAO.find_one_or_none(session, id=user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return db_user

    @classmethod
    async def update_user(cls, user_id: uuid.UUID, user: UserUpdate) -> UserModel:
        async with async_session_maker() as session:
            db_user = await UserDAO.find_one_or_none(session, UserModel.id == user_id)
            if not db_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            if user.password:
                user_in = UserUpdateDB(
                    **user.model_dump(
                        exclude={"is_active", "is_verified", "is_superuser"},
                        exclude_unset=True,
                    ),
                    hashed_password=get_password_hash(user.password),
                )
            else:
                user_in = UserUpdateDB(**user.model_dump())

            user_update = await UserDAO.update(
                session, UserModel.id == user_id, obj_in=user_in
            )
            await session.commit()
            return user_update

    @classmethod
    async def delete_user(cls, user_id: uuid.UUID):
        async with async_session_maker() as session:
            db_user = await UserDAO.find_one_or_none(session, id=user_id)
            if not db_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )
            await UserDAO.update(session, UserModel.id == user_id, {"is_active": False})
            await session.commit()

    @classmethod
    async def get_users_list(
        cls, *filter, offset: int = 0, limit: int = 100, **filter_by
    ) -> list[UserModel]:
        async with async_session_maker() as session:
            users = await UserDAO.find_all(
                session, *filter, offset=offset, limit=limit, **filter_by
            )
        if not users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Users not found"
            )
        return users
        return [
            User(
                id=str(db_user.id),
                email=db_user.email,
                fio=db_user.fio,
                is_active=db_user.is_active,
                is_superuser=db_user.is_superuser,
            )
            for db_user in users
        ]

    @classmethod
    async def update_user_from_superuser(
        cls, user_id: uuid.UUID, user: UserUpdate
    ) -> User:
        async with async_session_maker() as session:
            db_user = await UserDAO.find_one_or_none(session, UserModel.id == user_id)
            if not db_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            user_in = UserUpdateDB(**user.model_dump(exclude_unset=True))
            user_update = await UserDAO.update(
                session, UserModel.id == user_id, obj_in=user_in
            )
            await session.commit()
            return user_update

    @classmethod
    async def delete_user_from_superuser(cls, user_id: uuid.UUID):
        async with async_session_maker() as session:
            await UserDAO.delete(session, UserModel.id == user_id)
            await session.commit()

    @classmethod
    async def create_profile(
        cls, 
        profile: BaseProfile, 
        user_id: uuid.UUID
    ) -> ProfileModel:
        async with async_session_maker() as session:
            profile_exist = await ProfileDAO.find_one_or_none(session, user_id=user_id)
            if profile_exist:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, 
                    detail="Profile already exists"
                )
            new_profile = await ProfileDAO.add(
                session,
                Profile(
                    **profile.model_dump(),
                    user_id=user_id
                )
            )
            await session.commit()
            return new_profile
        
    @classmethod
    async def update_profile(
        cls, 
        new_profile: BaseProfile,
        user_id: uuid.UUID
    ) -> ProfileModel:
        async with async_session_maker() as session:
            db_profile = await ProfileDAO.find_one_or_none(
                session, 
                ProfileModel.user_id == user_id
            )
            if not db_profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail="Profile not found"
                )
            profile_update = await ProfileDAO.update(
                session, 
                ProfileModel.user_id == user_id, 
                obj_in=new_profile
            )
            await session.commit()
            return profile_update
        
    @classmethod
    async def delete_profile(
        cls, 
        user_id: uuid.UUID
    ) -> ProfileModel:
        async with async_session_maker() as session:
            db_profile = await ProfileDAO.find_one_or_none(
                session, 
                ProfileModel.user_id == user_id
            )
            if not db_profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail="Profile not found"
                )
            await ProfileDAO.delete(
                session,
                user_id=user_id
            )
            await session.commit()
        return {"message": "Profile has been deleted"}