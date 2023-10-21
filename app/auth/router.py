import uuid

from app.finance.service import FinanceService
from .dependencies import (
    get_current_active_user,
    get_current_superuser,
    get_current_verified_user,
    get_not_verified_user
)
from .models import UserModel
from .service import (
    AuthService,
    UserService
)
from .schemas import (
    BaseProfile,
    Token,
    UserCreate,
    User,
    UserUpdate,
    Profile
)
from app.utils.exceptions import (
    InvalidCredentialsException,
    IncorrectEmailOrPassswordException, 
    UserAlreadyExistsException
)
from app.data.config import settings

from fastapi import (
    APIRouter,
    Request,
    Response,
    status,
    Depends
)
from fastapi.security import OAuth2PasswordRequestForm


auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)
user_router = APIRouter(
    prefix="/users", 
    tags=["user"]
)

    #################
    #  Auth Router  #
    #################
 
@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate) -> User:
    db_user = await UserService.register_new_user(user)
    await FinanceService.adding_base_categories(db_user.id)
    return db_user

@auth_router.post("/login")
async def login(
    response: Response,
    credentials: OAuth2PasswordRequestForm = Depends()
) -> Token:
    user = await AuthService.authenticate_user(credentials.username, credentials.password)
    if not user:
        raise InvalidCredentialsException
    token = await AuthService.create_token(user.id)
    response.set_cookie(
        'access_token',
        token.access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True
    )
    response.set_cookie(
        'refresh_token',
        token.refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 30 * 24 * 60,
        httponly=True
    )
    return token

@auth_router.get("/request_for_verify")
async def request_for_verify(
    user: UserModel = Depends(get_not_verified_user),
) -> bool:
    return await AuthService.send_verification_token(user)


@auth_router.post("/verify/{token}")
async def verify(
    token: str
):
    return await AuthService.verify_user(token)
    

@auth_router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    user: UserModel = Depends(get_current_active_user),
):
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')

    await AuthService.logout(request.cookies.get('refresh_token'))
    return {"message": "Logged out successfully"}


@auth_router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response
) -> Token:
    new_token = await AuthService.refresh_token(
        uuid.UUID(request.cookies.get("refresh_token"))
    )
    response.set_cookie(
        'access_token',
        new_token.access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
    )
    response.set_cookie(
        'refresh_token',
        new_token.refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 30 * 24 * 60,
        httponly=True,
    )
    return new_token


@auth_router.post("/abort")
async def abort_all_sessions(
    response: Response,
    user: UserModel = Depends(get_current_verified_user)
):
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')

    await AuthService.abort_all_sessions(user.id)
    return {"message": "All sessions was aborted"}


    #################
    #  User Router  #
    #################


@user_router.get("")
async def get_users_list(
    offset: int | None = 0,
    limit: int | None = 100,
    current_user: UserModel = Depends(get_current_superuser)
) -> list[User]:
    return await UserService.get_users_list(offset=offset, limit=limit)


@user_router.get("/me")
async def get_current_verified_user(
    current_user: UserModel = Depends(get_current_active_user)
) -> User:
    return await UserService.get_user(current_user.id)


@user_router.patch("/me")
async def update_current_user(
    new_password: str,
    current_user: UserModel = Depends(get_current_verified_user)
) -> User:
    return await UserService.update_user(current_user.id, password=new_password)


@user_router.delete("/me")
async def delete_current_user(
    request: Request,
    response: Response,
    current_user: UserModel = Depends(get_current_verified_user)
):
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')

    await AuthService.logout(request.cookies.get('refresh_token'))
    await UserService.delete_user(current_user.id)
    return {"message": "User status is not active already"}


@user_router.get("/{user_id}")
async def get_user(
    user_id: str,
    current_user: UserModel = Depends(get_current_superuser)
) -> User:
    return await UserService.get_user(user_id)


@user_router.put("/{user_id}")
async def update_user(
    user_id: str,
    user: User,
    current_user: UserModel = Depends(get_current_superuser)
) -> User:
    return await UserService.update_user_from_superuser(user_id, user)


@user_router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: UserModel = Depends(get_current_superuser)
):
    await UserService.delete_user_from_superuser(user_id)
    return {"message": "User was deleted"}


    ####################
    #  Profile Router  #
    ####################

@user_router.post("/me/profile", status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile: BaseProfile,
    current_user: UserModel = Depends(get_current_active_user)
) -> Profile:
    return await UserService.create_profile(profile, current_user.id)

@user_router.put("/me/profile")
async def update_profile(
    profile: BaseProfile,
    current_user: UserModel = Depends(get_current_verified_user)
) -> Profile:
    return await UserService.update_profile(profile, current_user.id)

@user_router.delete("/me/profile")
async def delete_profile(
    current_user: UserModel = Depends(get_current_verified_user)
):
    return await UserService.delete_profile(current_user.id)
     