import base64
import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import httpx
from core.config import settings
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError, JWSSignatureError, JWTClaimsError

logger = logging.getLogger(__name__)


class OIDCConfigurationError(RuntimeError):
    """Raised when required OIDC configuration is missing."""


class JWTConfigurationError(RuntimeError):
    """Raised when required JWT configuration is missing."""


def _require_oidc_value(attr_name: str) -> str:
    """Read a required OIDC setting and fail with a controlled error if missing."""
    try:
        value = getattr(settings, attr_name)
    except AttributeError as exc:
        raise OIDCConfigurationError(f"Missing required OIDC setting: {attr_name.upper()}") from exc

    if value is None or (isinstance(value, str) and not value.strip()):
        raise OIDCConfigurationError(f"Missing required OIDC setting: {attr_name.upper()}")
    return value


def _optional_oidc_value(attr_name: str) -> Optional[str]:
    """Read an optional OIDC setting, returning None if missing or empty."""
    try:
        value = getattr(settings, attr_name)
    except AttributeError:
        return None
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    return value


def _require_jwt_value(attr_name: str) -> str:
    """Read a required JWT setting and fail with a controlled error if missing."""
    try:
        value = getattr(settings, attr_name)
    except AttributeError as exc:
        raise JWTConfigurationError(f"Missing required JWT setting: {attr_name.upper()}") from exc

    if value is None or (isinstance(value, str) and not value.strip()):
        raise JWTConfigurationError(f"Missing required JWT setting: {attr_name.upper()}")
    return value


def generate_state() -> str:
    """Generate a secure state parameter for OIDC."""
    return secrets.token_urlsafe(32)


def generate_nonce() -> str:
    """Generate a secure nonce parameter for OIDC."""
    return secrets.token_urlsafe(32)


def generate_code_verifier() -> str:
    """Generate PKCE code verifier."""
    return secrets.token_urlsafe(96)  # 128 bytes base64url encoded


def generate_code_challenge(code_verifier: str) -> str:
    """Generate PKCE code challenge from verifier using SHA256."""
    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


def _resolve_jwks_url() -> str:
    """Resolve JWKS URL: use OIDC_JWKS_URL if configured, else issuer + /.well-known/jwks.json."""
    override = _optional_oidc_value("oidc_jwks_url")
    if override:
        return override
    oidc_issuer_url = _require_oidc_value("oidc_issuer_url")
    return f"{oidc_issuer_url}/.well-known/jwks.json"


def _resolve_authorization_endpoint() -> str:
    """Resolve authorization endpoint: use OIDC_AUTHORIZATION_ENDPOINT if configured, else issuer + /authorize."""
    override = _optional_oidc_value("oidc_authorization_endpoint")
    if override:
        return override
    oidc_issuer_url = _require_oidc_value("oidc_issuer_url")
    return f"{oidc_issuer_url}/authorize"


def _resolve_token_endpoint() -> str:
    """Resolve token endpoint: use OIDC_TOKEN_ENDPOINT if configured, else issuer + /token."""
    override = _optional_oidc_value("oidc_token_endpoint")
    if override:
        return override
    oidc_issuer_url = _require_oidc_value("oidc_issuer_url")
    return f"{oidc_issuer_url}/token"


async def get_jwks() -> Dict[str, Any]:
    """Get JWKS (JSON Web Key Set) from OIDC provider."""
    jwks_url = _resolve_jwks_url()
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info(f"Fetching JWKS from: {jwks_url}")
            response = await client.get(jwks_url)
            response.raise_for_status()
            jwks_data = response.json()
            logger.info(f"Successfully fetched JWKS with {len(jwks_data.get('keys', []))} keys")
            return jwks_data
    except httpx.TimeoutException as e:
        logger.error(f"Timeout while fetching JWKS from {jwks_url}: {e}")
        raise Exception("Unable to retrieve authentication keys")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error {e.response.status_code} while fetching JWKS from {jwks_url}: {e.response.text}")
        raise Exception("Unable to retrieve authentication keys")
    except Exception as e:
        logger.error(f"Failed to fetch JWKS from {jwks_url}: {e}")
        raise Exception("Unable to retrieve authentication keys")


class IDTokenValidationError(Exception):
    """Custom exception for ID token validation errors."""

    def __init__(self, message: str, error_type: str = "validation_error"):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)


class AccessTokenError(Exception):
    """Custom exception for application JWT access token errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def create_access_token(claims: Dict[str, Any], expires_minutes: Optional[int] = None) -> str:
    """Create signed JWT access token from provided claims."""
    jwt_secret_key = _require_jwt_value("jwt_secret_key")
    jwt_algorithm = _require_jwt_value("jwt_algorithm")

    now = datetime.now(timezone.utc)
    token_claims = claims.copy()

    expiry_minutes = expires_minutes if expires_minutes is not None else int(_require_jwt_value("jwt_expire_minutes"))
    expire_at = now + timedelta(minutes=expiry_minutes)

    token_claims.update(
        {
            "exp": expire_at,
            "iat": now,
            "nbf": now,
        }
    )

    token = jwt.encode(token_claims, jwt_secret_key, algorithm=jwt_algorithm)
    # Log user hash instead of actual user ID to avoid exposing sensitive information
    user_id = token_claims.get("sub", "unknown")
    user_hash = hashlib.sha256(str(user_id).encode()).hexdigest()[:8] if user_id != "unknown" else "unknown"
    logger.debug("Authentication token created for user hash: %s", user_hash)
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT access token."""
    jwt_secret_key = _require_jwt_value("jwt_secret_key")
    jwt_algorithm = _require_jwt_value("jwt_algorithm")

    try:
        payload = jwt.decode(token, jwt_secret_key, algorithms=[jwt_algorithm])
        # Log user hash instead of actual user ID to avoid exposing sensitive information
        user_id = payload.get("sub", "unknown")
        user_hash = hashlib.sha256(str(user_id).encode()).hexdigest()[:8] if user_id != "unknown" else "unknown"
        logger.debug("Authentication token validated for user hash: %s", user_hash)
        return payload
    except ExpiredSignatureError as exc:
        logger.info("Authentication token has expired")
        raise AccessTokenError("Token has expired") from exc
    except JWTError as exc:
        # Log error type only, not the full exception which may contain sensitive token data
        logger.warning("Token validation failed: %s", type(exc).__name__)
        raise AccessTokenError("Invalid authentication token") from exc


async def validate_id_token(id_token: str, access_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Validate ID token with proper JWT signature verification using JWKS.

    Args:
        id_token: The OIDC ID token to validate.
        access_token: Optional access token for at_hash claim validation.
            Google ID tokens include at_hash; passing the access_token allows
            the JWT library to verify it without weakening other validations.
    """
    oidc_issuer_url = _require_oidc_value("oidc_issuer_url")

    try:
        # Get the header to find the key ID
        header = jwt.get_unverified_header(id_token)
        kid = header.get("kid")

        if not kid:
            logger.error("ID token validation failed: No key ID found in JWT header")
            raise IDTokenValidationError("Token format is invalid", "missing_kid")

        # Get JWKS from the provider
        try:
            jwks = await get_jwks()
        except Exception as e:
            logger.error(f"ID token validation failed: Failed to fetch JWKS from issuer {oidc_issuer_url}: {e}")
            raise IDTokenValidationError("Unable to retrieve authentication keys", "jwks_fetch_error")

        # Find the matching key
        key = None
        for jwk in jwks.get("keys", []):
            if jwk.get("kid") == kid:
                key = jwk
                break

        if not key:
            logger.error(f"ID token validation failed: No key found for kid: {kid} in JWKS from {oidc_issuer_url}")
            raise IDTokenValidationError("Authentication key validation failed", "key_not_found")

        # Convert JWK to PEM format for jose library
        import base64

        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        def base64url_decode(inp):
            """Decode base64url-encoded string."""
            padding = 4 - (len(inp) % 4)
            if padding != 4:
                inp += "=" * padding
            return base64.urlsafe_b64decode(inp)

        try:
            # Extract RSA components
            n = int.from_bytes(base64url_decode(key["n"]), "big")
            e = int.from_bytes(base64url_decode(key["e"]), "big")

            # Construct RSA public key
            public_numbers = rsa.RSAPublicNumbers(e, n)
            public_key = public_numbers.public_key()

            # Convert to PEM format
            pem_key = public_key.public_bytes(
                encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        except Exception as e:
            logger.error(f"ID token validation failed: Failed to convert JWK to PEM format: {e}")
            raise IDTokenValidationError("Authentication key processing failed", "key_conversion_error")

        # Verify and decode the JWT
        # Build decode options — pass access_token for at_hash validation if provided
        decode_kwargs: Dict[str, Any] = {
            "algorithms": ["RS256"],
            "issuer": oidc_issuer_url,
            "audience": _require_oidc_value("oidc_client_id"),
        }
        if access_token:
            decode_kwargs["access_token"] = access_token

        try:
            payload = jwt.decode(
                id_token,
                pem_key,
                **decode_kwargs,
            )
            # Log user hash instead of actual user ID to avoid exposing sensitive information
            user_id = payload.get("sub", "unknown")
            user_hash = hashlib.sha256(str(user_id).encode()).hexdigest()[:8] if user_id != "unknown" else "unknown"
            logger.info("ID token successfully validated for user hash: %s", user_hash)
            return payload
        except ExpiredSignatureError:
            logger.error("JWT validation failed: ID token has expired")
            raise IDTokenValidationError("Token has expired", "token_expired")
        except JWSSignatureError:
            logger.error("JWT validation failed: Invalid JWT signature")
            raise IDTokenValidationError("Token signature verification failed", "invalid_signature")
        except JWTClaimsError as e:
            # JWTClaimsError covers issuer, audience, and other claims validation
            logger.error(f"JWT validation failed: Claims validation error: {e}")
            if "iss" in str(e).lower() or "issuer" in str(e).lower():
                raise IDTokenValidationError("Token issuer validation failed", "invalid_issuer")
            elif "aud" in str(e).lower() or "audience" in str(e).lower():
                raise IDTokenValidationError("Token audience validation failed", "invalid_audience")
            else:
                raise IDTokenValidationError("Token claims validation failed", "invalid_claims")

    except IDTokenValidationError:
        # Re-raise our custom exceptions
        raise
    except JWTError as e:
        logger.error(f"JWT validation failed: {e}")
        raise IDTokenValidationError("Token validation failed", "jwt_error")
    except Exception as e:
        logger.error(f"Unexpected error during ID token validation: {e}")
        raise IDTokenValidationError("Authentication processing failed", "unexpected_error")


def build_authorization_url(
    state: str,
    nonce: str,
    code_challenge: Optional[str] = None,
    redirect_uri: Optional[str] = None,
) -> str:
    """Build OIDC authorization URL with optional PKCE support."""
    import urllib.parse

    oidc_client_id = _require_oidc_value("oidc_client_id")
    oidc_scope = _require_oidc_value("oidc_scope")

    params = {
        "client_id": oidc_client_id,
        "response_type": "code",
        "scope": oidc_scope,
        "redirect_uri": redirect_uri or f"{settings.backend_url}/api/v1/auth/callback",
        "state": state,
        "nonce": nonce,
    }

    # Add PKCE parameters if provided
    if code_challenge:
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = "S256"

    authorization_endpoint = _resolve_authorization_endpoint()
    auth_url = f"{authorization_endpoint}?" + urllib.parse.urlencode(params)
    return auth_url


def build_logout_url(id_token: Optional[str] = None) -> str:
    """Build OIDC logout URL."""
    import urllib.parse

    oidc_issuer_url = _require_oidc_value("oidc_issuer_url")
    frontend_url = _require_oidc_value("frontend_url")

    params = {"post_logout_redirect_uri": f"{frontend_url}/auth/logout"}

    if id_token:
        params["id_token_hint"] = id_token

    logout_url = f"{oidc_issuer_url}/logout?" + urllib.parse.urlencode(params)
    return logout_url