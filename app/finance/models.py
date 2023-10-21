from datetime import datetime
from typing import TYPE_CHECKING
from decimal import Decimal
import uuid
from currency_converter import CurrencyConverter

from sqlalchemy import ARRAY, ForeignKey, String, Text
from .mixins import CurrencyRelationMixin, UserRelationMixin

from app.utils.database.database import Base, BaseUUID

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

if TYPE_CHECKING:
    from app.auth.models import ProfileModel


class CurrencyModel(Base):
    __tablename__ = "currencies"
    currency_code: Mapped[str] = mapped_column(String(3), index=True, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(18), index=True)
    name: Mapped[str]
    income: Mapped["IncomeModel"] = relationship(back_populates="currency")
    expense: Mapped["ExpenseModel"] = relationship(back_populates="currency")
    profiles: Mapped["ProfileModel"] = relationship(back_populates="currency")
    
    def __str__(self):
        return 'Profile currency code: ' + self.currency_code
    

class FinanceEntityModel(CurrencyRelationMixin, UserRelationMixin, BaseUUID):
    __abstract__ = True
    comment: Mapped[str] = mapped_column(Text)
    value: Mapped[Decimal]
    category: Mapped[str]


class ExpenseModel(FinanceEntityModel):
    __tablename__ = "expencies"
    _user_back_populates = __tablename__
    _finance_type_back_populates = __tablename__
    _currenecy_back_populates = "expense"
    

class IncomeModel(FinanceEntityModel):
    __tablename__ = "incomes"
    _user_back_populates = __tablename__
    _finance_type_back_populates = __tablename__
    _currenecy_back_populates = "income"
    

class BaseTypeModel(Base, UserRelationMixin):
    __abstract__ = True
    categories: Mapped[list[str]] = mapped_column(ARRAY(String))

#$cash account
class IncomeTypeModel(BaseTypeModel):
    __tablename__ = "income_types"
    _user_back_populates = __tablename__
    _user_primary_key = True
    def __str__(self):
        return 'income_type'

class ExpenseTypeModel(BaseTypeModel):
    __tablename__ = "expense_types"
    _user_back_populates = __tablename__
    _user_primary_key = True
    def __str__(self):
        return 'expense_type'



