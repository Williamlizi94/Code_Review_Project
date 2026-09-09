"""Authentication endpoints — register, login, profile, and Google OAuth."""

import hashlib
import hmac
import secrets
from html import escape
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import (
    authenticate_user,
    create_access_token,
    create_user,
    get_current_user,
    hash_password,
)
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import LoginRequest, Token, UserCreate, UserOut

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])
settings = get_settings()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> UserOut:
    """Register a new user."""
    user = await create_user(payload.email, payload.password, payload.full_name, db)
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/login", response_model=Token)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> Token:
    """Authenticate and return a JWT access token."""
    user = await authenticate_user(payload.email, payload.password, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user.id, user.email)
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)) -> UserOut:
    """Get the currently authenticated user's profile."""
    return UserOut.model_validate(current_user)


@router.get("/google/login", include_in_schema=False)
async def google_login() -> RedirectResponse:
    """Begin an authorization-code flow with Google."""
    if not settings.google_oauth_client_id or not settings.google_oauth_client_secret:
        raise HTTPException(status_code=503, detail="Google login is not configured")
    state = secrets.token_urlsafe(32)
    params = urlencode(
        {
            "client_id": settings.google_oauth_client_id,
            "redirect_uri": settings.google_oauth_redirect_url,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "prompt": "select_account",
        }
    )
    response = RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")
    response.set_cookie(
        "codeguardian_google_state", state, max_age=600, httponly=True, secure=True, samesite="lax"
    )
    return response


@router.get("/google/callback", include_in_schema=False)
async def google_callback(request: Request, code: str, state: str, db: AsyncSession = Depends(get_db)) -> HTMLResponse:
    """Exchange the Google code, create/link a user, then populate the existing browser session."""
    expected_state = request.cookies.get("codeguardian_google_state", "")
    if not expected_state or not hmac.compare_digest(state, expected_state):
        raise HTTPException(status_code=400, detail="Invalid Google login state")

    async with httpx.AsyncClient(timeout=15) as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "redirect_uri": settings.google_oauth_redirect_url,
                "grant_type": "authorization_code",
            },
        )
        if token_response.is_error:
            raise HTTPException(status_code=401, detail="Google authorization failed")
        access_token = token_response.json().get("access_token")
        profile_response = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if profile_response.is_error:
        raise HTTPException(status_code=401, detail="Could not read Google profile")
    profile = profile_response.json()
    email = str(profile.get("email", "")).strip().lower()
    if not email or profile.get("email_verified") is not True:
        raise HTTPException(status_code=401, detail="Google email is not verified")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            email=email,
            full_name=profile.get("name") or None,
            hashed_password=hash_password(secrets.token_urlsafe(48)),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif not user.is_active:
        raise HTTPException(status_code=403, detail="User account is disabled")

    app_token = create_access_token(user.id, user.email)
    user_name = escape(user.full_name or user.email)
    page = f"""<!doctype html><meta charset=\"utf-8\"><title>Signing in…</title>
<script>
localStorage.setItem('codeguardian_access_token', {app_token!r});
localStorage.setItem('codeguardian_user', JSON.stringify({{email: {user.email!r}, full_name: {user_name!r}}}));
location.replace('/02-dashboard.html');
</script>"""
    response = HTMLResponse(page)
    response.delete_cookie("codeguardian_google_state", secure=True, samesite="lax")
    return response
