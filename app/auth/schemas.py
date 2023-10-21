import uuid
from pydantic import BaseModel, EmailStr, Field

######################
#    User SCHEMAS    #
######################

class UserBase(BaseModel):
    email: str | None = Field(None)
    is_active: bool = Field(True)
    is_verified: bool = Field(False)
    is_superuser: bool = Field(False)


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(UserBase):
    password: str | None = None


class User(UserBase):
    id: uuid.UUID
    email: EmailStr
    is_active: bool
    is_verified: bool
    is_superuser: bool

    class Config:
        from_attributes = True


class UserCreateDB(UserBase):
    hashed_password: str | None = None


class UserUpdateDB(UserBase):
    hashed_password: str


#######################
#   Refresh SCHEMAS   #
#######################

class RefreshSessionCreate(BaseModel):
    refresh_token: uuid.UUID
    expires_in: int
    user_id: uuid.UUID


class RefreshSessionUpdate(RefreshSessionCreate):
    user_id: uuid.UUID | None = Field(None)


class Token(BaseModel):
    access_token: str
    refresh_token: uuid.UUID
    token_type: str

#######################
#   Profile SCHEMAS   #
#######################

class BaseProfile(BaseModel):
    username: str = Field(examples=['John'])
    currency_code: str = Field(max_length=3, examples=['USD'])

class Profile(BaseProfile):
    user_id: uuid.UUID
