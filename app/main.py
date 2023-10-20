from app.auth.router import auth_router, user_router
from .data.config import settings
from app.finance.router import finance_router

from app.finance.utils import lifespan
from app.admin.views import adding_views

from fastapi import FastAPI
import sentry_sdk

sentry_sdk.init(
    dsn=settings.SENTRY_URL,
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

app = FastAPI(title="Finance App", lifespan=lifespan)

app.include_router(router=auth_router)
app.include_router(router=user_router)
app.include_router(router=finance_router)

adding_views(app)
