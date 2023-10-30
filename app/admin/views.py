




from fastapi import FastAPI
from sqladmin import Admin, ModelView

from app.auth.models import RefreshSessionModel, UserModel, ProfileModel
from app.finance.models import BaseTypeModel, CurrencyModel, ExpenseModel, ExpenseTypeModel, IncomeModel, IncomeTypeModel
from app.utils.database.database import engine
from app.admin.auth import authentication_backend

class BaseAdmin(ModelView):
    page_size = 25
    page_size_options = [25, 50, 100, 200]

class UsersAdmin(BaseAdmin, model=UserModel):
    column_list = [
        UserModel.email,
        UserModel.profiles,
        UserModel.incomes,
        UserModel.expencies,
        UserModel.income_types,
        UserModel.expense_types,
        UserModel.refresh_sessions
    ]
    column_details_exclude_list = [UserModel.hashed_password]
    column_searchable_list = [UserModel.email]
    name = "user"
    name_plural = "users"
    icon = "fa-solid fa-user fa-xl"
    can_delete = False
    column_default_sort = [(UserModel.email, True)]

class ProfileAdmin(BaseAdmin, model=ProfileModel):
    column_list = [
        ProfileModel.username,
        ProfileModel.user,
        ProfileModel.currency
    ]
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


class BaseTypeAdmin(BaseAdmin):
    column_list = [
        ExpenseTypeModel.user, 
        ExpenseTypeModel.categories,
        ExpenseTypeModel.user_id
    ]
    column_searchable_list = [ExpenseTypeModel.user_id]

class IncomeTypeAdmin(BaseTypeAdmin, model=IncomeTypeModel):
    
    name = "income category"
    name_plural = "income categories"
    icon = "fa-solid fa-arrow-up-wide-short fa-xl"

class ExpenseTypeAdmin(BaseTypeAdmin, model=ExpenseTypeModel):
    
    name = "expense category"
    name_plural = "expense categories"
    icon = "fa-solid fa-arrow-down-wide-short fa-xl"

class IncomeAdmin(BaseAdmin, model=IncomeModel):
    column_list = [
        IncomeModel.user,
        IncomeModel.currency_code,
        IncomeModel.value,
        IncomeModel.category,
        IncomeModel.comment
    ]
    name = "income item"
    name_plural = "incomes"
    icon = "fa-solid fa-hand-holding-dollar fa-xl"

class ExpenseAdmin(BaseAdmin, model=ExpenseModel):
    column_list = [
        ExpenseModel.user,
        ExpenseModel.currency_code,
        ExpenseModel.value,
        ExpenseModel.category,
        ExpenseModel.comment
    ]
    name = "expense item"
    name_plural = "expencies"
    icon = "fa-solid fa-credit-card fa-xl"

class RefreshSessionAdmin(BaseAdmin, model=RefreshSessionModel):
    column_exclude_list = [RefreshSessionModel.expires_in, RefreshSessionModel.user_id]
    name = "refresh session"
    name_plural = "refresh sessions"
    icon = "fa-solid fa-arrows-rotate fa-xl"

admin_views = [
    UsersAdmin,
    ProfileAdmin, 
    IncomeAdmin,
    ExpenseAdmin,
    IncomeTypeAdmin,
    ExpenseTypeAdmin,
    CurrencyAdmin,
    RefreshSessionAdmin
]

def init_views(app: FastAPI) -> None:
    admin = Admin(
        app=app,
        engine=engine,
        authentication_backend=authentication_backend
    )
    for admin_view in admin_views:
        admin.add_view(admin_view)