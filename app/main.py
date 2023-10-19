from app.auth.router import auth_router, user_router
from app.finance.router import finance_router

from app.finance.utils import lifespan
from app.utils.database.database import engine
from app.admin.auth import authentication_backend
from app.admin.views import (
    
    adding_views
)

from fastapi import FastAPI
from sqladmin import Admin



app = FastAPI(title="Finance App", lifespan=lifespan)
app.include_router(router=auth_router)
app.include_router(router=user_router)
app.include_router(router=finance_router)



# admin = Admin(
#     app=app,
#     engine=engine,
#     authentication_backend=authentication_backend
# )

adding_views(app)
