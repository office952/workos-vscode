import hashlib
import logging
import os
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from core.config import resolve_dev_auth_impersonation_user_id
from core.auth import AccessTokenError, JWTConfigurationError, decode_access_token
from core.database import get_db
from core.environment import dev_auth_allowed
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from models.auth import User
from schemas.auth import UserResponse
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)

DEV_BYPASS_TOKEN = "__DEV_BYPASS_TOKEN__"
SYNTHETIC_DEV_ADMIN_USER_ID = "dev-admin-user-00000000"

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
CSRF_EXCLUDED_PATHS = {"/api/v1/auth/token/exchange"}
_DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]


def _allowed_origins() -> list[str]:
    env_origins = os.environ.get("ALLOWED_ORIGINS", "")
    if not env_origins.strip():
        return _DEFAULT_ALLOWED_ORIGINS
    return [o.strip() for o in env_origins.split(",") if o.strip()]


def _normalize_origin_from_header(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"


def _origin_allowed(request: Request) -> bool:
    origin_header = request.headers.get("origin")
    referer_header = request.headers.get("referer")
    origin = _normalize_origin_from_header(origin_header)
    if not origin:
        origin = _normalize_origin_from_header(referer_header)
    if not origin:
        return False

    allowed = {o.lower() for o in _allowed_origins()}
    return origin in allowed


def evaluate_csrf_report_only(request: Request) -> tuple[str, list[str]]:
    """Evaluate CSRF report-only state for cookie-authenticated mutating requests."""
    method = request.method.upper()
    if method not in MUTATING_METHODS:
        return "skipped", ["method_not_mutating"]

    if request.url.path in CSRF_EXCLUDED_PATHS:
        return "skipped_excluded", ["path_excluded"]

    reasons: list[str] = []
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("x-csrf-token")

    if not csrf_cookie:
        reasons.append("csrf_cookie_missing")
    if not csrf_header:
        reasons.append("csrf_header_missing")

    if csrf_cookie and csrf_header and csrf_cookie != csrf_header:
        reasons.append("csrf_mismatch")

    if not _origin_allowed(request):
        reasons.append("origin_invalid_or_missing")

    if not reasons:
        return "passed", []

    has_missing = any(reason.endswith("_missing") for reason in reasons)
    return ("missing" if has_missing else "invalid"), reasons


async def get_bearer_token(
    request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> str:
    """Extract bearer token from Authorization header."""
    if credentials and credentials.scheme.lower() == "bearer":
        request.state.auth_source = "bearer"
        request.state.csrf_report_only = "skipped_bearer"
        request.state.csrf_report_only_reasons = ["auth_source_bearer"]
        return credentials.credentials

    # Callback flow may store token in an HttpOnly cookie; prefer this
    # over exposing tokens in URL/query parameters.
    cookie_token = request.cookies.get("app_token")
    if cookie_token:
        request.state.auth_source = "cookie"
        status_value, reasons = evaluate_csrf_report_only(request)
        request.state.csrf_report_only = status_value
        request.state.csrf_report_only_reasons = reasons
        if status_value in {"missing", "invalid"}:
            logger.warning(
                "CSRF report-only: status=%s method=%s path=%s reasons=%s",
                status_value,
                request.method,
                request.url.path,
                ",".join(reasons),
            )
        return cookie_token

    # DEV AUTH BYPASS: In development/local/test environments, allow unauthenticated
    # requests by returning a synthetic dev token. This enables frontend development
    # without requiring a full OIDC login flow.
    if dev_auth_allowed():
        logger.info(
            "Dev auth bypass: no credentials for %s %s — returning synthetic dev token",
            request.method,
            request.url.path,
        )
        request.state.auth_source = "dev_bypass"
        request.state.csrf_report_only = "skipped_dev"
        request.state.csrf_report_only_reasons = ["dev_auth_bypass"]
        return DEV_BYPASS_TOKEN

    logger.debug("Authentication required for request %s %s", request.method, request.url.path)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication credentials were not provided")


def _synthetic_dev_admin_user() -> UserResponse:
    return UserResponse(
        id=SYNTHETIC_DEV_ADMIN_USER_ID,
        email="dev@localhost",
        name="Dev Admin",
        role="admin",
        last_login=datetime.now(),
    )


async def _resolve_dev_bypass_user(db: AsyncSession) -> UserResponse:
    impersonation_id = resolve_dev_auth_impersonation_user_id()
    if not impersonation_id:
        logger.debug("Dev auth bypass: no WORKOS_DEV_AUTH_USER_ID — synthetic Dev Admin")
        return _synthetic_dev_admin_user()

    user = await db.get(User, impersonation_id)
    if user is None:
        logger.error(
            "Dev auth impersonation failed: WORKOS_DEV_AUTH_USER_ID=%s not found in users",
            impersonation_id,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "dev_auth_user_not_found",
                "message": (
                    f"WORKOS_DEV_AUTH_USER_ID={impersonation_id!r} was not found in the users table. "
                    "Seed the user first or unset WORKOS_DEV_AUTH_USER_ID."
                ),
            },
        )

    logger.info(
        "Dev auth bypass: impersonating user id=%s email=%s role=%s",
        user.id,
        user.email,
        user.role,
    )
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        last_login=user.last_login,
    )


async def get_current_user(
    token: str = Depends(get_bearer_token),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Dependency to get current authenticated user via JWT token."""
    if token == DEV_BYPASS_TOKEN and dev_auth_allowed():
        return await _resolve_dev_bypass_user(db)

    try:
        payload = decode_access_token(token)
    except AccessTokenError as exc:
        # Log error type only, not the full exception which may contain sensitive token data
        logger.warning("Token validation failed: %s", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message)
    except JWTConfigurationError as exc:
        logger.warning("JWT configuration missing: %s", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")

    last_login_raw = payload.get("last_login")
    last_login = None
    if isinstance(last_login_raw, str):
        try:
            last_login = datetime.fromisoformat(last_login_raw)
        except ValueError:
            # Log user hash instead of actual user ID to avoid exposing sensitive information
            user_hash = hashlib.sha256(str(user_id).encode()).hexdigest()[:8] if user_id else "unknown"
            logger.debug("Failed to parse last_login for user hash: %s", user_hash)

    return UserResponse(
        id=user_id,
        email=payload.get("email", ""),
        name=payload.get("name"),
        role=payload.get("role", "user"),
        last_login=last_login,
    )


async def get_admin_user(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Dependency to ensure current user has admin role."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
