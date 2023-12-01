from app.auth.router import auth_router, user_router
from .data.config import settings
from app.finance.router import finance_router

from app.utils.lifespan_init import lifespan
from app.admin.views import init_views

import sentry_sdk
from fastapi import FastAPI


sentry_sdk.init(
    dsn=settings.SENTRY_URL,
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)


app = FastAPI(title="Finance App", lifespan=lifespan)

from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator(
    should_group_status_codes=False, excluded_handlers=[".*admin*.", "/metrics"]
).instrument(app).expose(app)

app.include_router(router=auth_router)
app.include_router(router=user_router)
app.include_router(router=finance_router)

init_views(app)
