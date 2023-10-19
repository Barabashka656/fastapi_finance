from decimal import Decimal
import uuid
from pydantic import BaseModel, Field


class Currency(BaseModel):
    currency_code: str = Field(examples=['USD'], max_length=3)
    symbol: str = Field(examples=['$'])
    name: str = Field(examples=['United States dollar'])


class BaseFinanceType(BaseModel):
    user_id: str | None
    categories: list | None = Field(None)

    class Config:
        from_attributes = True


class FinanceItemCreate(BaseModel):
    currency_code: str = Field(examples=['USD'], max_length=3)
    category: str
    value: Decimal
    comment: str
    
class FinanceItemCreateDB(FinanceItemCreate):
    user_id: uuid.UUID

class FinanceItem(FinanceItemCreateDB):
    id: uuid.UUID
    

class FinanceType(BaseFinanceType):
    id: uuid.UUID
