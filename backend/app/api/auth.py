from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from app.services.auth_service import AuthService, build_state


router = APIRouter()


@router.post("/register", response_model=AuthResponse)
async def register(payload: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    user = await AuthService.register(db, payload.email, payload.password)
    token = AuthService.create_token(user)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
    )
    return AuthResponse(user=UserResponse(id=user.id, email=user.email, created_at=user.created_at))


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    user = await AuthService.login(db, payload.email, payload.password)
    token = AuthService.create_token(user)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
    )
    return AuthResponse(user=UserResponse(id=user.id, email=user.email, created_at=user.created_at))


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(
        key="access_token",
        path="/",
        samesite="lax",
        secure=False,
    )
    return {"status": "ok"}


@router.get("/me", response_model=AuthResponse)
async def me(current_user: User = Depends(get_current_user)) -> AuthResponse:
    return AuthResponse(user=UserResponse(id=current_user.id, email=current_user.email, created_at=current_user.created_at))


@router.get("/google/login")
async def google_login() -> dict[str, str]:
    state = build_state()
    return {"url": AuthService.build_google_login_url(state), "state": state}


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    try:
        user = await AuthService.login_with_google_code(db, code)
    except Exception as exc:
        error_msg = str(exc).replace('"', '').replace("'", "")
        return RedirectResponse(
            url=f"http://localhost:5173?error=google_auth_failed&message={error_msg}"
        )

    token = AuthService.create_token(user)
    frontend_url = "http://localhost:5173"
    response = RedirectResponse(url=frontend_url)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
    )
    return response
