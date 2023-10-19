from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from app.finance.models import ExpenseTypeModel, IncomeTypeModel
from app.utils.database.database import Base, BaseUUID
from app.finance.mixins import CurrencyRelationMixin, UserRelationMixin 

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import TIMESTAMP, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

if TYPE_CHECKING:
    from app.finance.models import ExpenseModel, IncomeModel, CurrencyModel


class UserModel(BaseUUID):
    __tablename__ = "user"
    user_relations = {"back_populates": __tablename__, "uselist": True}
    
    email: Mapped[str] = mapped_column(index=True)
    hashed_password: Mapped[str]

    profile: Mapped["ProfileModel"] = relationship(back_populates=__tablename__)

    expencies: Mapped[list["ExpenseModel"]] = relationship(**user_relations)
    incomes: Mapped[list["IncomeModel"]] = relationship(**user_relations)
    expense_types: Mapped["ExpenseTypeModel"] = relationship(**user_relations)
    income_types: Mapped["IncomeTypeModel"] = relationship(**user_relations)

    is_active: Mapped[bool] = mapped_column(default=True)
    is_verified: Mapped[bool] = mapped_column(default=False)
    is_superuser: Mapped[bool] = mapped_column(default=False)

    def __str__(self):
        return 'User: ' + self.email


class ProfileModel(Base, UserRelationMixin, CurrencyRelationMixin):
    __tablename__ = "profile"
    _user_back_populates = __tablename__
    _currenecy_back_populates = __tablename__
    _user_primary_key = True
    username: Mapped[str | None]

    def __str__(self):
        return 'Profile: ' + self.username


class RefreshSessionModel(Base):
    __tablename__ = "refresh_session"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    refresh_token: Mapped[uuid.UUID] = mapped_column(UUID, index=True)
    expires_in: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.now()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID, 
        ForeignKey("user.id", ondelete="CASCADE")
    )
