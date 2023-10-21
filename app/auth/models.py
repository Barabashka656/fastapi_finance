from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from app.finance.models import ExpenseTypeModel, IncomeTypeModel
from app.utils.database.database import Base, BaseUUID
from app.finance.mixins import CurrencyRelationMixin, UserRelationMixin 

from sqlalchemy import TIMESTAMP, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

if TYPE_CHECKING:
    from app.finance.models import ExpenseModel, IncomeModel


class UserModel(BaseUUID):
    __tablename__ = "user"
    user_relations = {"back_populates": __tablename__}
    
    email: Mapped[str] = mapped_column(index=True)
    hashed_password: Mapped[str]

    profiles: Mapped["ProfileModel"] = relationship(**user_relations)
    refresh_sessions: Mapped["RefreshSessionModel"] = relationship(**user_relations)

    expencies: Mapped[list["ExpenseModel"]] = relationship(**user_relations)
    incomes: Mapped[list["IncomeModel"]] = relationship(**user_relations)
    
    user_relations.update(uselist=True)
    expense_types: Mapped["ExpenseTypeModel"] = relationship(**user_relations)
    income_types: Mapped["IncomeTypeModel"] = relationship(**user_relations)

    is_active: Mapped[bool] = mapped_column(default=True)
    is_verified: Mapped[bool] = mapped_column(default=False)
    is_superuser: Mapped[bool] = mapped_column(default=False)

    def __str__(self):
        return 'User: ' + self.email


class ProfileModel(Base, UserRelationMixin, CurrencyRelationMixin):
    __tablename__ = "profiles"
    _user_back_populates = __tablename__
    _currenecy_back_populates = __tablename__
    _user_primary_key = True
    username: Mapped[str | None] = mapped_column(String(32))

    def __str__(self):
        return 'Profile: ' + self.username


class RefreshSessionModel(BaseUUID, UserRelationMixin):
    __tablename__ = "refresh_sessions"
    _user_back_populates = __tablename__

    refresh_token: Mapped[uuid.UUID] = mapped_column(index=True)
    expires_in: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.now()
    )
