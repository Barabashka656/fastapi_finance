from app.dao.base import BaseDAO
from app.finance.models import (
    CurrencyModel,
    ExpenseModel, 
    ExpenseTypeModel,
    IncomeModel, 
    IncomeTypeModel
)

class CurrencyDAO(BaseDAO):
    model = CurrencyModel

class ExpenseTypeDAO(BaseDAO):
    model = ExpenseTypeModel

class IncomeTypeDAO(BaseDAO):
    model = IncomeTypeModel

class IncomeDAO(BaseDAO):
    model = IncomeModel

class ExpenseDAO(BaseDAO):
    model = ExpenseModel
