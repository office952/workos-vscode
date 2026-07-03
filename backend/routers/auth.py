import logging
import os
import secrets
from typing import Optional
from urllib.parse import urlencode
from urllib.parse import urlparse

import httpx
from core.auth import (
    IDTokenValidationError,
    OIDCConfigurationError,
    _resolve_token_endpoint,
    build_authorization_url,
    build_logout_url,
    generate_code_challenge,
    generate_code_verifier,
    generate_nonce,
    generate_state,
    validate_id_token,
)
from core.config import settings
from core.database import get_db
from dependencies.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from models.auth import User
from schemas.auth import (
    PlatformTokenExchangeRequest,
    TokenExchangeResponse,
    UserResponse,
)
from services.auth import AuthService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
logger = logging.getLogger(__name__)


def _should_use_secure_cookie(request: Request) -> bool:
    """Set Secure cookies only when request scheme is effectively HTTPS."""
    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    if forwarded_proto:
        proto = forwarded_proto.split(",", 1)[0].strip().lower()
        return proto == "https"
    return request.url.scheme == "https"


def _strip_port(host: str) -> str:
    """Return hostname without port, preserving IPv4/hostname semantics."""
    host = (host or "").strip().lower()
    if not host:
        return ""
    if ":" in host and host.count(":") == 1:
        return host.split(":", 1)[0]
    return host


def _extract_hostname(url: str) -> str:
    """Extract lowercase hostname from URL-like string."""
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def _trusted_hosts() -> set[str]:
    """Build trusted host set from explicit env + configured frontend/backend URLs."""
    hosts: set[str] = {"localhost", "127.0.0.1"}

    env_allowed = os.getenv("ALLOWED_DOMAINS", "")
    if env_allowed.strip():
        for item in env_allowed.split(","):
            host = _strip_port(item)
            if host:
                hosts.add(host)

    for url in (settings.backend_url, getattr(settings, "frontend_url", "")):
        host = _extract_hostname(url)
        if host:
            hosts.add(host)

    return hosts


def _is_trusted_host(host: str) -> bool:
    """Validate host against trusted host allowlist."""
    candidate = _strip_port(host)
    if not candidate:
        return False
    trusted = _trusted_hosts()
    return candidate in trusted


def _local_patch(url: str) -> str:
    """Patch URL for local development."""
    if os.getenv("LOCAL_PATCH", "").lower() not in ("true", "1"):
        return url

    patched_url = url.replace("https://", "http://").replace(":8000", ":3000")
    logger.debug("[get_dynamic_backend_url] patching URL from %s to %s", url, patched_url)
    return patched_url


def get_dynamic_backend_url(request: Request) -> str:
    """Get backend URL dynamically from request headers.

    Priority: mgx-external-domain > x-forwarded-host > host > settings.backend_url
    """
    mgx_external_domain = request.headers.get("mgx-external-domain")
    x_forwarded_host = request.headers.get("x-forwarded-host")
    host = request.headers.get("host")
    forwarded_proto = request.headers.get("x-forwarded-proto")
    if forwarded_proto:
        scheme = forwarded_proto.split(",", 1)[0].strip().lower() or request.url.scheme
    else:
        scheme = request.url.scheme

    effective_host = mgx_external_domain or x_forwarded_host or host
    if not effective_host:
        logger.warning("[get_dynamic_backend_url] No host found, fallback to %s", settings.backend_url)
        return settings.backend_url

    if not _is_trusted_host(effective_host):
        logger.warning(
            "[get_dynamic_backend_url] Untrusted host '%s', fallback to settings.backend_url",
            effective_host,
        )
        return settings.backend_url

    dynamic_url = _local_patch(f"{scheme}://{effective_host}")
    logger.debug(
        "[get_dynamic_backend_url] mgx-external-domain=%s, x-forwarded-host=%s, host=%s, scheme=%s, dynamic_url=%s",
        mgx_external_domain,
        x_forwarded_host,
        host,
        scheme,
        dynamic_url,
    )
    return dynamic_url


def _resolve_frontend_url(backend_url_fallback: str) -> str:
    """Resolve the frontend URL for post-auth redirects.

    Uses FRONTEND_URL env/config if available; otherwise falls back to backend_url
    (legacy behavior for local dev where frontend and backend share the same origin).
    """
    try:
        frontend_url = getattr(settings, "frontend_url")
        if frontend_url and isinstance(frontend_url, str) and frontend_url.strip():
            return frontend_url.rstrip("/")
    except AttributeError:
        pass
    return backend_url_fallback


def derive_name_from_email(email: str) -> str:
    return email.split("@", 1)[0] if email else ""


@router.get("/login")
async def login(request: Request, db: AsyncSession = Depends(get_db)):
    """Start OIDC login flow with PKCE."""
    state = generate_state()
    nonce = generate_nonce()
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)

    # Store state, nonce, and code verifier in database
    auth_service = AuthService(db)
    await auth_service.store_oidc_state(state, nonce, code_verifier)

    # Build redirect_uri dynamically from request
    backend_url = get_dynamic_backend_url(request)
    redirect_uri = f"{backend_url}/api/v1/auth/callback"
    logger.info("[login] Starting OIDC flow with redirect_uri=%s", redirect_uri)

    try:
        auth_url = build_authorization_url(state, nonce, code_challenge, redirect_uri=redirect_uri)
    except OIDCConfigurationError as exc:
        logger.warning("[login] OIDC configuration missing: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": str(exc)},
        )

    return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND, headers={"X-Request-ID": state})


@router.get("/callback")
async def callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle OIDC callback."""
    backend_url = get_dynamic_backend_url(request)
    frontend_url = _resolve_frontend_url(backend_url)

    def redirect_with_error(message: str) -> RedirectResponse:
        fragment = urlencode({"msg": message})
        return RedirectResponse(
            url=f"{frontend_url}/auth/error?{fragment}",
            status_code=status.HTTP_302_FOUND,
        )

    if error:
        return redirect_with_error(f"OIDC error: {error}")

    if not code or not state:
        return redirect_with_error("Missing code or state parameter")

    # Validate state using database
    auth_service = AuthService(db)
    temp_data = await auth_service.get_and_delete_oidc_state(state)
    if not temp_data:
        return redirect_with_error("Invalid or expired state parameter")

    nonce = temp_data["nonce"]
    code_verifier = temp_data.get("code_verifier")

    try:
        # Build redirect_uri dynamically from request
        redirect_uri = f"{backend_url}/api/v1/auth/callback"
        logger.info("[callback] Exchanging code for tokens with redirect_uri=%s", redirect_uri)

        # Exchange authorization code for tokens with PKCE
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": settings.oidc_client_id,
            "client_secret": settings.oidc_client_secret,
        }

        # Add PKCE code verifier if available
        if code_verifier:
            token_data["code_verifier"] = code_verifier

        token_url = _resolve_token_endpoint()
        try:
            async with httpx.AsyncClient() as client:
                token_response = await client.post(
                    token_url,
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded", "X-Request-ID": state},
                )
        except httpx.HTTPError as e:
            logger.error(
                "[callback] Token exchange HTTP error: url=%s, error=%s",
                token_url,
                str(e),
                exc_info=True,
            )
            return redirect_with_error(f"Token exchange failed: {e}")

        if token_response.status_code != 200:
            logger.error(
                "[callback] Token exchange failed: url=%s, status_code=%s, response=%s",
                token_url,
                token_response.status_code,
                token_response.text,
            )
            return redirect_with_error(f"Token exchange failed: {token_response.text}")

        tokens = token_response.json()

        # Validate ID token — pass access_token for at_hash validation (required by Google)
        id_token = tokens.get("id_token")
        if not id_token:
            return redirect_with_error("No ID token received")

        id_claims = await validate_id_token(id_token, access_token=tokens.get("access_token"))

        # Validate nonce
        if id_claims.get("nonce") != nonce:
            return redirect_with_error("Invalid nonce")

        # Get or create user
        email = id_claims.get("email", "")
        name = id_claims.get("name") or derive_name_from_email(email)
        user = await auth_service.get_or_create_user(platform_sub=id_claims["sub"], email=email, name=name)

        # Issue application JWT token encapsulating user information
        app_token, expires_at, _ = await auth_service.issue_app_token(user=user)

        # Redirect to FRONTEND callback page, not API domain
        redirect_url = f"{frontend_url}/auth/callback"
        logger.info("[callback] OIDC callback successful, redirecting to frontend callback page")
        redirect_response = RedirectResponse(
            url=redirect_url,
            status_code=status.HTTP_302_FOUND,
        )
        # Store app token in HttpOnly cookie to avoid URL/query token leakage.
        # Cookie is read server-side by auth dependency fallback.
        try:
            cookie_max_age = int(getattr(settings, "jwt_expire_minutes", 60)) * 60
        except (TypeError, ValueError):
            cookie_max_age = 3600
        secure_cookie = _should_use_secure_cookie(request)
        redirect_response.set_cookie(
            key="app_token",
            value=app_token,
            httponly=True,
            secure=secure_cookie,
            samesite="lax",
            max_age=max(1, cookie_max_age),
            path="/",
        )
        # Double-submit token cookie must be JS-readable so frontend can mirror it in X-CSRF-Token.
        csrf_token = secrets.token_urlsafe(32)
        redirect_response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            httponly=False,
            secure=secure_cookie,
            samesite="lax",
            max_age=max(1, cookie_max_age),
            path="/",
        )
        return redirect_response

    except IDTokenValidationError as e:
        # Redirect to error page with validation details
        return redirect_with_error(f"Authentication failed: {e.message}")
    except HTTPException as e:
        # Redirect to error page with the original detail message
        return redirect_with_error(str(e.detail))
    except Exception as e:
        logger.exception(f"Unexpected error in OIDC callback: {e}")
        return redirect_with_error(
            "Authentication processing failed. Please try again or contact support if the issue persists."
        )


@router.post("/token/exchange", response_model=TokenExchangeResponse)
async def exchange_platform_token(
    payload: PlatformTokenExchangeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Exchange Platform token for app token. Admin gets admin role, team members get user role."""
    logger.info("[token/exchange] Received platform token exchange request")

    try:
        _ = (
            settings.oidc_issuer_url,
            settings.oidc_client_id,
            settings.oidc_client_secret,
        )
    except AttributeError as exc:
        logger.warning("[token/exchange] OIDC configuration missing")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Missing required OIDC configuration"},
        )

    verify_url = f"{settings.oidc_issuer_url}/platform/tokens/verify"
    logger.debug(f"[token/exchange] Verifying token with issuer: {verify_url}")

    try:
        async with httpx.AsyncClient() as client:
            verify_response = await client.post(
                verify_url,
                json={"platform_token": payload.platform_token},
                headers={"Content-Type": "application/json"},
            )
        logger.debug(f"[token/exchange] Issuer response status: {verify_response.status_code}")
    except httpx.HTTPError as exc:
        logger.error(f"[token/exchange] HTTP error verifying platform token: {exc}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unable to verify platform token") from exc

    try:
        verify_body = verify_response.json()
        logger.debug(f"[token/exchange] Issuer response body: {verify_body}")
    except ValueError:
        logger.error(f"[token/exchange] Failed to parse issuer response as JSON: {verify_response.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid response from platform token verification service",
        )

    if not isinstance(verify_body, dict):
        logger.error(f"[token/exchange] Unexpected response type: {type(verify_body)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response from platform token verification service",
        )

    if verify_response.status_code != status.HTTP_200_OK or not verify_body.get("success"):
        message = verify_body.get("message", "") if isinstance(verify_body, dict) else ""
        logger.warning(
            f"[token/exchange] Token verification failed: status={verify_response.status_code}, message={message}"
        )
        raise HTTPException(
            status_code=verify_response.status_code,
            detail=message or "Platform token verification failed",
        )

    payload_data = verify_body.get("data") or {}
    raw_user_id = payload_data.get("user_id")
    logger.info(f"[token/exchange] Token verified, platform_user_id={raw_user_id}, email={payload_data.get('email')}")

    if not raw_user_id:
        logger.error("[token/exchange] Platform token payload missing user_id")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Platform token payload missing user_id")

    platform_user_id = str(raw_user_id)
    is_admin = platform_user_id == str(settings.admin_user_id)
    role = "admin" if is_admin else "user"

    logger.info(f"[token/exchange] User verified: platform_user_id={platform_user_id}, role={role}")
    auth_service = AuthService(db)

    user_email = payload_data.get("email", "") or (getattr(settings, "admin_user_email", "") if is_admin else "")
    user_name = payload_data.get("name") or payload_data.get("username")
    if not user_name:
        user_name = derive_name_from_email(user_email)

    user = User(id=platform_user_id, email=user_email, name=user_name, role=role)
    logger.debug(
        f"[token/exchange] User object for token issuance: id={user.id}, email={user.email}, role={user.role}"
    )

    app_token, expires_at, _ = await auth_service.issue_app_token(user=user)
    logger.info(f"[token/exchange] Token issued successfully for user_id={user.id}, expires_at={expires_at}")

    return TokenExchangeResponse(
        token=app_token,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """Get current user info."""
    return current_user


@router.get("/permissions")
async def get_current_user_permissions(current_user: UserResponse = Depends(get_current_user)):
    """Get current user's effective role and permissions."""
    from dependencies.permissions import (
        get_role_permissions,
        resolve_effective_role,
    )

    effective_role = resolve_effective_role(current_user.role)
    permissions = get_role_permissions(effective_role)
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "raw_role": current_user.role,
        "effective_role": effective_role,
        "permissions": permissions,
    }


@router.get("/logout")
async def logout(request: Request):
    """Logout user."""
    try:
        logout_url = build_logout_url()
    except OIDCConfigurationError as exc:
        logger.warning("[logout] OIDC configuration missing: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": str(exc)},
        )
    response = JSONResponse({"redirect_url": logout_url})
    secure_cookie = _should_use_secure_cookie(request)
    response.delete_cookie(
        key="app_token",
        path="/",
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
    )
    response.delete_cookie(
        key="csrf_token",
        path="/",
        secure=secure_cookie,
        samesite="lax",
    )
    return response