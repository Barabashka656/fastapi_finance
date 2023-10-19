from typing import AsyncGenerator
import uuid

from sqlalchemy import UUID

from app.data.config import settings
from sqlalchemy.orm import Mapped, mapped_column

from sqlalchemy.orm import DeclarativeBase 
from sqlalchemy.ext.asyncio import (
    AsyncSession, 
    async_sessionmaker, 
    create_async_engine
)


engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class BaseUUID(Base):
    __abstract__ = True
    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, index=True, default=uuid.uuid4
    )
    
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
