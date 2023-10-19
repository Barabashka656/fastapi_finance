import json
import os
import uuid
from fastapi import HTTPException, status
from app.auth.dao import UserDAO
from app.auth.models import UserModel

from app.auth.schemas import User
from app.finance.schemas import BaseFinanceType, FinanceItem, FinanceItemCreate, FinanceItemCreateDB

from .models import CurrencyModel, ExpenseModel, ExpenseTypeModel, IncomeModel, IncomeTypeModel
from .dao import ExpenseDAO, ExpenseTypeDAO, IncomeDAO, IncomeTypeDAO, CurrencyDAO
from app.utils.database.database import async_session_maker


class FinanceService:
    EXPENSE = 'expense'
    INCOME = 'income'
    _base_incomes = [
        "Salary", "Investment", 
        "Pocket Money", "Pension", 
        "Gift", "Other"
    ]
    _base_expencies = [
        "Food",
        "Health",
        "Transport",
        "Beauty",
        "Apparel",
        "Education",
        "Household",
        "Pets",
        "Gift",
        "Other",
    ]

    @classmethod
    async def init_currencies(cls):
        async with async_session_maker() as session:
            currencies = await CurrencyDAO.find_all(session, limit=1)
            if not currencies:
                path = os.path.join("app", "finance", "currencies.json")
                with open(path, "r") as f:
                    data = json.loads(f.read())
                await CurrencyDAO.add_all(session, data)
                await session.commit()


    @classmethod
    async def adding_base_categories(cls, db_user_id: User):
        async with async_session_maker() as session:
            await IncomeTypeDAO.add(
                session, 
                {
                    "user_id": db_user_id, 
                    "categories": cls._base_incomes
                }
            )
            await ExpenseTypeDAO.add(
                session, 
                {
                    "user_id": db_user_id, 
                    "categories": cls._base_expencies
                }
            )
            await UserDAO.find_all_with_joinedload_option(
                session,
                load=UserModel.expense_types
            )
            await session.commit()


    @classmethod
    async def adding_finance_category(
        cls, 
        finance_type: str,
        user_id: uuid.UUID, 
        new_category: str
    ):
        async with async_session_maker() as session:
            if finance_type == cls.INCOME:
                dao = IncomeTypeDAO
                model = IncomeTypeModel
            elif finance_type == cls.EXPENSE:
                dao = ExpenseTypeDAO
                model = ExpenseTypeModel
            finance_type_instance: ExpenseTypeModel | IncomeTypeModel = \
                await dao.find_one_or_none(session, user_id=user_id)
            categories = finance_type_instance.categories
            categories.append(new_category)
            db_instance: IncomeTypeModel | ExpenseTypeModel = \
            await dao.update(
                session,
                model.user_id == user_id,
                obj_in=BaseFinanceType(
                    categories=categories
                )
            )
            await session.commit()
        return db_instance.categories
    
    @classmethod
    async def adding_finance_item(
        cls, 
        finance_type: str,
        user_id: uuid.UUID, 
        finance: FinanceItemCreate
    ) -> IncomeModel | ExpenseModel:
        async with async_session_maker() as session:
            if finance_type == cls.INCOME:
                dao = IncomeDAO
            elif finance_type == cls.EXPENSE:
                dao = ExpenseDAO
            print('123412341432')
            db_instance: IncomeModel | ExpenseModel = \
                await dao.add(
                    session,
                    obj_in=FinanceItemCreateDB(
                        **finance.model_dump(),
                        user_id=user_id
                    )
                )
            print('123412341432233')
            await session.commit()
            print('12341234143fdsfddfaf2')
            print(db_instance)
        return db_instance

    @classmethod
    async def get_currencies_list(cls, *filter, **filter_by) -> list[CurrencyModel]:
        async with async_session_maker() as session:
            currencies = await CurrencyDAO.find_all(session, *filter, **filter_by)
        if not currencies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Currencies not found"
            )
        return currencies

    @classmethod
    async def get_categories_list(
        cls, 
        finance_type: str, 
        user_id: uuid.UUID, 
    ) -> list[str]:
        async with async_session_maker() as session:
            if finance_type == 'income':
                dao = IncomeTypeDAO
            elif finance_type == 'expense':
                dao = ExpenseTypeDAO
            result: ExpenseTypeModel | IncomeTypeModel = \
                await dao.find_one_or_none(
                    session,
                    user_id=user_id
                )
            return result.categories
