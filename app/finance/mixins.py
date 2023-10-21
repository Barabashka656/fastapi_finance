from typing import TYPE_CHECKING
import uuid
from sqlalchemy import ForeignKey
from sqlalchemy.orm import declared_attr

from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.auth.models import UserModel
    from app.finance.models import CurrencyModel


class UserRelationMixin:
    _user_id_unique: bool = False
    _user_back_populates: str | None = None
    _user_primary_key: bool = False
    _user_fk_ondelete: str | None = "CASCADE"
    
    @declared_attr
    def user_id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(ForeignKey('user.id', ondelete=cls._user_fk_ondelete), unique=cls._user_id_unique, primary_key=cls._user_primary_key)
    
    @declared_attr
    def user(cls) -> Mapped["UserModel"]:
        return relationship("UserModel", back_populates=cls._user_back_populates)
    

class CurrencyRelationMixin:
    _currenecy_back_populates: str | None = None

    @declared_attr
    def currency_code(cls) -> Mapped[str]:
        return mapped_column(
            ForeignKey('currencies.currency_code')
        )
    
    @declared_attr
    def currency(cls) -> Mapped["CurrencyModel"]:
        return relationship(
            "CurrencyModel", 
            back_populates=cls._currenecy_back_populates
        )