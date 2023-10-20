import os

from dotenv import (
    load_dotenv
)

path = os.path.join('app', 'data', '.env')
load_dotenv(path)

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import (
    RedisDsn,
    PostgresDsn,
    EmailStr,
    HttpUrl
)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra='forbid', env_file=path, env_file_encoding='utf-8')
    
    # auth fields
    SECRET: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # pg database fields
    DB_NAME: str
    DB_USER: str
    DB_PASS: str
    DB_HOST: str
    DB_PORT: int

    @property
    def DATABASE_URL(self) -> PostgresDsn:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # redis database fields
    REDIS_HOST: str
    REDIS_PORT: int
    
    @property
    def REDIS_URL(self) -> RedisDsn:
        return f'redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0'

    # sentry fields
    SENTRY_URL: HttpUrl

settings = Settings(_env_file=path, _env_file_encoding='utf-8')
