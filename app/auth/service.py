import uuid
from datetime import datetime, timedelta, timezone
import smtplib
from email.message import EmailMessage
from app.tasks.celery import celery_app


from app.data.config import settings
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
import pyotp


class AuthService:
    @staticmethod
    async def create_token(user_id: uuid.UUID) -> Token:
        access_token = AuthService._create_jwt_token(user_id=user_id)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = AuthService._create_refresh_token()
        async with async_session_maker() as session:
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
            access_token=access_token, 
            refresh_token=refresh_token, 
            token_type="bearer"
        )

    @staticmethod
    async def logout(token: uuid.UUID) -> None:
        async with async_session_maker() as session:
            refresh_session = await RefreshSessionDAO.find_one_or_none(
                session, RefreshSessionModel.refresh_token == token
            )
            if refresh_session:
                await RefreshSessionDAO.delete(session, id=refresh_session.id)
            await session.commit()

    @staticmethod
    async def refresh_token(token: uuid.UUID) -> Token:
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

            access_token = AuthService._create_jwt_token(user_id=user.id)
            refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            refresh_token = AuthService._create_refresh_token()

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

    @staticmethod
    async def authenticate_user(email: str, password: str) -> UserModel | None:
        async with async_session_maker() as session:
            db_user = await UserDAO.find_one_or_none(session, email=email)
        if db_user and is_valid_password(password, db_user.hashed_password):
            return db_user
        return None

    @staticmethod
    async def abort_all_sessions(user_id: uuid.UUID):
        async with async_session_maker() as session:
            await RefreshSessionDAO.delete(
                session, RefreshSessionModel.user_id == user_id
            )
            await session.commit()

    @staticmethod
    def _create_jwt_token(user_id: uuid.UUID = None, email: str = None) -> str:
        if user_id:
            to_encode = {
                "sub": str(user_id),
                "exp": datetime.utcnow()
                + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            }
        else:
            to_encode = {
                "email": email,
                "exp": datetime.utcnow()
                + timedelta(days=settings.EMAIL_VERIFY_TOKEN_EXPIRE_DAYS),
            }
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_AUTH, algorithm=settings.ALGORITHM
        )
        if user_id:
            return f"Bearer {encoded_jwt}"
        return encoded_jwt

    @staticmethod
    def _create_refresh_token() -> str:
        return uuid.uuid4()
    
    @staticmethod
    def _create_verify_mail(token: str):
        msg = EmailMessage()
        msg['Subject'] = 'Verify your email address'
        msg['From'] = settings.SMTP_USER
        msg['To'] = settings.SMTP_USER

        msg.set_content(
            '<div>'
            '<h1>verify account</h1>'
            f'http://localhost:8000/auth/verify/{token}'
            '</div>',
            subtype='html'
        )
        return msg
    
    
    @celery_app.task
    def send_verify_email(token: str):
        msg = AuthService._create_verify_mail(token)
        with smtplib.SMTP_SSL(
            settings.SMTP_HOST, 
            settings.SMTP_PORT
        ) as server:
            server.login(
                settings.SMTP_USER, 
                settings.SMTP_PASSWORD
            )
            server.send_message(msg)
    
    @staticmethod
    async def send_verification_token(user: UserModel):
        if user.is_verified:
            raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, 
                    detail="User already verified"
                )
        token = AuthService._create_jwt_token(email=user.email)
        AuthService.send_verify_email.delay(token)
        return True
        
    # @staticmethod
    # async def create_otp_for_verify():
    #     code_generator = pyotp.TOTP(settings.OTP_SECRET_KEY)
    #     return code_generator.now()

    @staticmethod
    async def verify_user(token: str):
        async with async_session_maker() as session:
            try:
                payload = jwt.decode(token, settings.SECRET_AUTH, algorithms=[settings.ALGORITHM])
                email = payload.get("email")
                if not email:
                    raise InvalidTokenException
            except Exception:
                raise InvalidTokenException
            db_user = await UserDAO.find_one_or_none(session, email=email)
            if db_user.is_verified:
                return {
                    "status": "error",
                    "data": None,
                    "details": "User already verified"
                }
            await UserDAO.update(
                session, 
                UserModel.email == email, 
                obj_in={"is_verified": True}
            )
            await session.commit()
            return {
                "status": "success",
                "data": None,
                "details": "Verification is success"
            }
            

class UserService:
    @staticmethod
    async def register_new_user(user: UserCreate) -> UserModel:
        async with async_session_maker() as session:
            user_exist = await UserDAO.find_one_or_none(session, email=user.email)
            if user_exist:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, 
                    detail="User already exists"
                )

            db_user = await UserDAO.add(
                session,
                UserCreateDB(
                    **user.model_dump(),
                    hashed_password=get_password_hash(user.password),
                ),
            )
            await session.commit()
        return db_user

    @staticmethod
    async def get_user(user_id: uuid.UUID) -> UserModel:
        async with async_session_maker() as session:
            db_user = await UserDAO.find_one_or_none(session, id=user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return db_user

    @staticmethod
    async def update_user(
        user_id: uuid.UUID,
        *, 
        password: str | None = None, 
        is_verified: bool | None = None
    ) -> UserModel:
        async with async_session_maker() as session:
            db_user = await UserDAO.find_one_or_none(session, UserModel.id == user_id)
            if not db_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            # if user.password:
            #     user_in = UserUpdateDB(
            #         **user.model_dump(
            #             exclude={"is_active", "is_verified", "is_superuser"},
            #             exclude_unset=True,
            #         ),
            #         hashed_password=get_password_hash(user.password),
            #     )
            # else:
            #     user_in = UserUpdateDB(**user.model_dump())
            user_in = {}
            if password:
                user_in.update(hashed_password=get_password_hash(password))    

            if isinstance(is_verified, bool):
                user_in.update(hashed_password=get_password_hash(password))
            
            user_update = await UserDAO.update(
                session, UserModel.id == user_id, obj_in=user_in
            )
            await session.commit()
            return user_update

    @staticmethod
    async def delete_user(user_id: uuid.UUID):
        async with async_session_maker() as session:
            db_user = await UserDAO.find_one_or_none(session, id=user_id)
            if not db_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )
            await UserDAO.update(session, UserModel.id == user_id, obj_in={"is_active": False})
            await session.commit()

    @staticmethod
    async def get_users_list(
        *filter, offset: int = 0, limit: int = 100, **filter_by
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

    @staticmethod
    async def update_user_from_superuser(
        user_id: uuid.UUID, user: UserUpdate
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

    @staticmethod
    async def delete_user_from_superuser(user_id: uuid.UUID):
        async with async_session_maker() as session:
            await UserDAO.delete(session, UserModel.id == user_id)
            await session.commit()

    @staticmethod
    async def create_profile( 
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
        
    @staticmethod
    async def update_profile(
        new_profile: BaseProfile,
        user_id: uuid.UUID
    ) -> ProfileModel:
        async with async_session_maker() as session:
            db_profile = await ProfileDAO.find_one_or_none(
                session, 
                user_id == user_id
            )
            if not db_profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail="Profile not found"
                )
            profile_update = await ProfileDAO.update(
                session, 
                user_id == user_id, 
                obj_in=new_profile
            )
            await session.commit()
            return profile_update
        
    @staticmethod
    async def delete_profile(user_id: uuid.UUID) -> ProfileModel:
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