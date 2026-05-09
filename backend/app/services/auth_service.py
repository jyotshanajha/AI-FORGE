import uuid
from datetime import timezone, datetime
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.services.fallback_store import get_store, update_store


def _load_users_from_store() -> dict[str, dict]:
    store = get_store()
    users = store.get("users", {})
    if isinstance(users, dict):
        return users
    return {}


# In-memory cache backed by local JSON store for development/testing when DB is unavailable
_in_memory_users: dict[str, dict] = _load_users_from_store()


def _persist_users_to_store() -> None:
    def _mutator(store: dict) -> None:
        store["users"] = _in_memory_users

    update_store(_mutator)


class AuthService:
    @staticmethod
    async def register(db: AsyncSession, email: str, password: str) -> User:
        try:
            existing = await db.execute(select(User).where(User.email == email.lower()))
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=409, detail={"error": "conflict", "message": "Email already registered"})

            user = User(email=email.lower(), hashed_password=hash_password(password))
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except HTTPException:
            raise
        except Exception as e:
            # Database unavailable - use in-memory store for development/testing
            print(f"Database error during registration: {e}. Using in-memory store.")
            
            email_lower = email.lower()
            if email_lower in _in_memory_users:
                raise HTTPException(status_code=409, detail={"error": "conflict", "message": "Email already registered"})
            
            user_id = str(uuid.uuid4())
            created_at = datetime.now(timezone.utc)
            _in_memory_users[email_lower] = {
                "id": user_id,
                "email": email_lower,
                "hashed_password": hash_password(password),
                "created_at": created_at.isoformat(),
            }
            _persist_users_to_store()
            user = User(id=uuid.UUID(user_id), email=email_lower, hashed_password=hash_password(password), created_at=created_at)
            return user

    @staticmethod
    async def login(db: AsyncSession, email: str, password: str) -> User:
        try:
            result = await db.execute(select(User).where(User.email == email.lower()))
            user = result.scalar_one_or_none()
            if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
                raise HTTPException(status_code=401, detail={"error": "invalid_credentials", "message": "Invalid email/password"})
            return user
        except HTTPException:
            raise
        except Exception as e:
            # Database unavailable - use in-memory store for development/testing
            print(f"Database error during login: {e}. Using in-memory store.")
            
            email_lower = email.lower()
            if email_lower not in _in_memory_users:
                raise HTTPException(status_code=401, detail={"error": "invalid_credentials", "message": "Invalid email/password"})
            
            stored_user = _in_memory_users[email_lower]
            if not verify_password(password, stored_user["hashed_password"]):
                raise HTTPException(status_code=401, detail={"error": "invalid_credentials", "message": "Invalid email/password"})
            
            user = User(id=uuid.UUID(stored_user["id"]), email=email_lower, hashed_password=stored_user["hashed_password"], created_at=datetime.fromisoformat(stored_user["created_at"]))
            return user

    @staticmethod
    def create_token(user: User) -> str:
        from app.core.security import create_access_token
        return create_access_token(str(user.id), user.email)

    @staticmethod
    def build_google_login_url(state: str) -> str:
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_REDIRECT_URI:
            raise HTTPException(status_code=400, detail={"error": "google_not_configured", "message": "Google OAuth not configured"})

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    @staticmethod
    async def login_with_google_code(db: AsyncSession, code: str) -> User:
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET or not settings.GOOGLE_REDIRECT_URI:
            raise HTTPException(status_code=400, detail={"error": "google_not_configured", "message": "Google OAuth not configured"})

        async with httpx.AsyncClient(timeout=30) as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            token_response.raise_for_status()
            token_json = token_response.json()

            userinfo_response = await client.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {token_json['access_token']}"},
            )
            userinfo_response.raise_for_status()
            profile = userinfo_response.json()

        email = profile.get("email", "").lower()
        google_id = profile.get("sub")
        if not email or not google_id:
            raise HTTPException(status_code=400, detail={"error": "google_profile_invalid", "message": "Google profile missing email/sub"})

        try:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

            if user:
                if not user.google_id:
                    user.google_id = google_id
                    await db.commit()
                    await db.refresh(user)
                return user

            user = User(email=email, google_id=google_id, hashed_password=None)
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except Exception as e:
            # Database unavailable - use in-memory store for development/testing
            print(f"Database error during Google login: {e}. Using in-memory store.")
            
            if email in _in_memory_users:
                stored_user = _in_memory_users[email]
                if not stored_user.get("google_id"):
                    stored_user["google_id"] = google_id
                    _persist_users_to_store()
                # Create a User-like object from stored data
                created_at = datetime.fromisoformat(stored_user["created_at"])
                user = User(id=uuid.UUID(stored_user["id"]), email=email, google_id=google_id, hashed_password=None, created_at=created_at)
                return user
            
            # Create new in-memory user
            user_id = str(uuid.uuid4())
            created_at = datetime.now(timezone.utc)
            _in_memory_users[email] = {
                "id": user_id,
                "email": email,
                "google_id": google_id,
                "created_at": created_at.isoformat(),
            }
            _persist_users_to_store()
            user = User(id=uuid.UUID(user_id), email=email, google_id=google_id, hashed_password=None, created_at=created_at)
            return user


def build_state() -> str:
    return f"state-{uuid.uuid4()}-{int(datetime.now(timezone.utc).timestamp())}"
