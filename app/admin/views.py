




from fastapi import FastAPI
from sqladmin import Admin, ModelView

from app.auth.models import UserModel, ProfileModel
from app.finance.models import CurrencyModel, ExpenseModel, ExpenseTypeModel, IncomeModel, IncomeTypeModel
from app.utils.database.database import engine
from app.admin.auth import authentication_backend

class BaseAdmin(ModelView):
    can_delete = False
    page_size = 25
    page_size_options = [25, 50, 100, 200]

class UsersAdmin(BaseAdmin, model=UserModel):
    column_list = [
        UserModel.email,
        UserModel.profile,
        UserModel.incomes,
        UserModel.expencies,
        UserModel.income_types,
        UserModel.expense_types
    ]
    column_details_exclude_list = [UserModel.hashed_password]
    column_searchable_list = [UserModel.email]
    name = "user"
    name_plural = "users"
    icon = "fa-solid fa-user fa-xl"
    #column_default_sort = [(UserModel.registered_at, True)]

class ProfileAdmin(BaseAdmin, model=ProfileModel):
    column_list = [c.name for c in ProfileModel.__table__.c]
    column_searchable_list = [ProfileModel.username]
    name = "profile"
    name_plural = "profiles"
    icon = "fa-solid fa-id-card fa-xl"
    #column_default_sort = [(UserModel.registered_at, True)]


class CurrencyAdmin(BaseAdmin, model=CurrencyModel):
    column_list = [c.name for c in CurrencyModel.__table__.c]
    column_searchable_list = [CurrencyModel.currency_code]
    name = "currency"
    name_plural = "currencies"
    icon = "fa-solid fa-dollar-sign fa-2xl"


class IncomeTypeAdmin(BaseAdmin, model=IncomeTypeModel):
    #column_list = [IncomeTypeModel.user, IncomeTypeModel.categories]
    #column_searchable_list = [IncomeTypeModel.user_id]
    name = "income category"
    name_plural = "income categories"
    icon = "fa-solid fa-arrow-up-wide-short fa-xl"

class ExpenseTypeAdmin(BaseAdmin, model=ExpenseTypeModel):
    column_list = [ExpenseTypeModel.user, ExpenseTypeModel.categories]
    column_searchable_list = [ExpenseTypeModel.user_id]
    name = "expense category"
    name_plural = "expense categories"
    icon = "fa-solid fa-arrow-down-wide-short fa-xl"

class IncomeAdmin(BaseAdmin, model=IncomeModel):
    name = "income item"
    name_plural = "incomes"
    icon = "fa-solid fa-hand-holding-dollar fa-xl"

class ExpenseAdmin(BaseAdmin, model=ExpenseModel):
    
    name = "expense item"
    name_plural = "expencies"
    icon = "fa-solid fa-credit-card fa-xl"

admin_views = [
    UsersAdmin, 
    ProfileAdmin, 
    IncomeAdmin,
    ExpenseAdmin,
    IncomeTypeAdmin,
    ExpenseTypeAdmin,
    CurrencyAdmin,
]

def adding_views(app: FastAPI) -> None:
    admin = Admin(
        app=app,
        engine=engine,
        authentication_backend=authentication_backend
    )
    for admin_view in admin_views:
        admin.add_view(admin_view)