
from app.dao.base import BaseDAO
from app.auth.models import UserModel
from .models import ProfileModel, RefreshSessionModel
from .schemas import (
    UserCreateDB,
    UserUpdateDB,
    RefreshSessionCreate,
    RefreshSessionUpdate
)

class UsersDAO(BaseDAO):
    model = UserModel

class UserDAO(BaseDAO[UserModel, UserCreateDB, UserUpdateDB]):
    model = UserModel


class RefreshSessionDAO(BaseDAO[RefreshSessionModel, RefreshSessionCreate, RefreshSessionUpdate]):
    model = RefreshSessionModel

class ProfileDAO(BaseDAO):
    model = ProfileModel