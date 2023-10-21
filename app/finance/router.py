from fastapi import APIRouter, Depends
from fastapi_cache.decorator import cache
from app.auth.dependencies import get_current_active_user, get_current_superuser, get_current_verified_user

from app.auth.models import UserModel
from app.finance.schemas import Currency, BaseFinanceType, FinanceItem, FinanceItemCreate, FinanceType
from app.finance.service import FinanceService


finance_router = APIRouter(
    prefix="/finance", 
    tags=["finance"]
)

@finance_router.get("")
@cache(expire=3600)
async def get_currencies() -> list[Currency]:
    return await FinanceService.get_currencies_list()


@finance_router.get("/income/category")
async def get_income_types(
    current_user: UserModel = Depends(get_current_verified_user)
) -> list[str]:
    return await FinanceService.get_categories_list(
        finance_type=FinanceService.INCOME, 
        user_id=current_user.id
    )


@finance_router.get("/expense/category")
async def get_expense_types(
    current_user: UserModel = Depends(get_current_verified_user)
) -> list[str]:
    return await FinanceService.get_categories_list(
        finance_type=FinanceService.EXPENSE, 
        user_id=current_user.id
    )


@finance_router.post("/income/category")
async def adding_new_income_category(
    new_category = str,
    current_user: UserModel = Depends(get_current_verified_user),
) -> list[str]:
    return await FinanceService.adding_finance_category(
        finance_type=FinanceService.INCOME,
        user_id=current_user.id,
        new_category=new_category
    )


@finance_router.post("/expense/category")
async def adding_new_expense_category(
    new_category = str,
    current_user: UserModel = Depends(get_current_verified_user),
) -> list[str]:
    return await FinanceService.adding_finance_category(
        finance_type=FinanceService.EXPENSE,
        user_id=current_user.id,
        new_category=new_category
    )


@finance_router.post("/income")
async def create_income(
    finance_item: FinanceItemCreate, 
    current_user: UserModel = Depends(get_current_active_user)
) -> FinanceItem:
    return await FinanceService.adding_finance_item(
        finance_type=FinanceService.EXPENSE,
        user_id=current_user.id,
        finance=finance_item
    )


@finance_router.post("/expense")
async def create_expense(
    finance_item: FinanceItemCreate, 
    current_user: UserModel = Depends(get_current_active_user)
) -> FinanceItem:
    return await FinanceService.adding_finance_item(
        finance_type=FinanceService.EXPENSE,
        user_id=current_user.id,
        finance=finance_item
    )
