from fastapi import Depends, Response
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from app.auth.dependencies import get_current_superuser
from app.auth.service import AuthService

from app.auth.service import AuthService
from app.data.config import settings
from app.auth.models import UserModel


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        email, password = form["username"], form["password"]
        user = await AuthService.authenticate_user(email, password)
        if user and user.is_superuser:
            token = await AuthService.create_token(user.id)
            request.session.update({"token": token.access_token})
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return RedirectResponse(request.url_for("admin:login"), status_code=302)
        user: UserModel = Depends(get_current_superuser)
        if not user:
            return RedirectResponse(request.url_for("admin:login"), status_code=302)
        return True

authentication_backend = AdminAuth(secret_key=settings.SECRET)
