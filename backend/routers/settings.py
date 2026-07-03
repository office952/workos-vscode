import re
from pathlib import Path
from typing import Dict, Set

from dependencies.auth import get_admin_user
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from schemas.auth import UserResponse

router = APIRouter(prefix="/api/v1/admin/settings", tags=["admin-settings"])

# AUDIT FIX (Task 13): Secret patterns that MUST be masked at read time.
# These keys are NEVER returned in cleartext regardless of auth level.
_SECRET_PATTERNS: tuple[str, ...] = (
    "SECRET",
    "TOKEN",
    "KEY",
    "PASSWORD",
    "CREDENTIAL",
)

# Keys that are explicitly forbidden from being edited via the UI.
_IMMUTABLE_KEYS: Set[str] = {
    "DATABASE_URL",
    "JWT_SECRET_KEY",
    "OIDC_CLIENT_SECRET",
    "STRIPE_SECRET_KEY",
}

# Allowlist of keys that CAN be edited via the settings UI.
# Any key not in this list is read-only from the UI.
_EDITABLE_KEYS: Set[str] = {
    "HOST",
    "PORT",
    "FRONTEND_URL",
    "ALLOWED_DOMAINS",
    "ALLOWED_ORIGINS",
    "OIDC_ISSUER_URL",
    "OIDC_CLIENT_ID",
    "OIDC_SCOPE",
    "JWT_ALGORITHM",
    "JWT_EXPIRE_MINUTES",
    "ADMIN_USER_ID",
    "ADMIN_USER_EMAIL",
    "STRIPE_SUCCESS_URL",
    "STRIPE_CANCEL_URL",
    "VITE_API_BASE_URL",
    "VITE_FRONTEND_URL",
    "ENABLE_MOCK_DATA",
    "ENVIRONMENT",
}


def _is_secret_key(key: str) -> bool:
    """Check if a key matches secret patterns."""
    upper = key.upper()
    for pattern in _SECRET_PATTERNS:
        if pattern in upper:
            return True
    return False


def _mask_value(key: str, value: str) -> str:
    """Mask secret values. Returns masked string for secrets, original for safe keys."""
    if _is_secret_key(key):
        if len(value) <= 4:
            return "****"
        return value[:2] + "*" * (len(value) - 4) + value[-2:]
    return value


class EnvVariable(BaseModel):
    key: str
    value: str
    description: str = ""


class EnvConfig(BaseModel):
    backend_vars: Dict[str, EnvVariable]
    frontend_vars: Dict[str, EnvVariable]


class EnvVariableUpdate(BaseModel):
    value: str


def get_env_file_path(env_type: str) -> Path:
    """Get the path to the environment variable file."""
    base_path = Path(__file__).parent.parent
    if env_type == "backend":
        return base_path / ".env"
    elif env_type == "frontend":
        return base_path.parent / "frontend" / ".env"
    else:
        raise ValueError("Invalid env_type")


def read_env_file(env_type: str) -> Dict[str, str]:
    """Read an environment variable file."""
    env_file = get_env_file_path(env_type)
    if not env_file.exists():
        return {}

    env_vars = {}
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
    return env_vars


def write_env_file(env_type: str, env_vars: Dict[str, str]):
    """Write to an environment variable file."""
    env_file = get_env_file_path(env_type)

    # Ensure the directory exists
    env_file.parent.mkdir(parents=True, exist_ok=True)

    with open(env_file, "w", encoding="utf-8") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")


@router.get("", response_model=EnvConfig)
async def get_settings(current_user: UserResponse = Depends(get_admin_user)):
    """Retrieve environment variable configuration.

    AUDIT FIX (Task 13): Secret values are ALWAYS masked at read time.
    Critical secrets (DATABASE_URL, JWT_SECRET_KEY, etc.) are never
    returned in cleartext even to admin users.
    """
    try:
        backend_vars = read_env_file("backend")
        frontend_vars = read_env_file("frontend")

        # Define descriptions for configuration items
        backend_descriptions = {
            "DATABASE_URL": "Database connection string (masked)",
            "STRIPE_SECRET_KEY": "Stripe secret key (masked)",
            "STRIPE_SUCCESS_URL": "Payment success callback URL",
            "STRIPE_CANCEL_URL": "Payment cancellation callback URL",
            "ALLOWED_DOMAINS": "Allowed domains",
            "ALLOWED_ORIGINS": "CORS allowed origins",
            "OIDC_ISSUER_URL": "OIDC issuer URL",
            "OIDC_CLIENT_ID": "OIDC client ID",
            "OIDC_CLIENT_SECRET": "OIDC client secret (masked)",
            "OIDC_SCOPE": "OIDC scopes",
            "HOST": "Server host address",
            "PORT": "Server port",
            "FRONTEND_URL": "Frontend URL",
            "JWT_SECRET_KEY": "JWT signing secret key (masked)",
            "JWT_ALGORITHM": "JWT signing algorithm",
            "JWT_EXPIRE_MINUTES": "JWT expiration time (minutes)",
            "ADMIN_USER_ID": "Admin user ID",
            "ADMIN_USER_EMAIL": "Admin user email",
            "ENABLE_MOCK_DATA": "Enable mock data seeding (true/false)",
            "ENVIRONMENT": "Runtime environment (dev/prod)",
        }

        frontend_descriptions = {"VITE_API_BASE_URL": "Base API URL", "VITE_FRONTEND_URL": "Frontend URL"}

        # Build response data — MASK secret values
        backend_config = {}
        for key, value in backend_vars.items():
            masked_value = _mask_value(key, value)
            backend_config[key] = EnvVariable(
                key=key, value=masked_value, description=backend_descriptions.get(key, "")
            )

        frontend_config = {}
        for key, value in frontend_vars.items():
            masked_value = _mask_value(key, value)
            frontend_config[key] = EnvVariable(
                key=key, value=masked_value, description=frontend_descriptions.get(key, "")
            )

        return EnvConfig(backend_vars=backend_config, frontend_vars=frontend_config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read configuration: {str(e)}")


def _validate_editable(key: str) -> None:
    """Raise 403 if the key is immutable or not in the editable allowlist."""
    if key.upper() in _IMMUTABLE_KEYS:
        raise HTTPException(
            status_code=403,
            detail=f"Key '{key}' is a critical secret and cannot be edited via UI.",
        )
    if _is_secret_key(key):
        raise HTTPException(
            status_code=403,
            detail=f"Key '{key}' matches a secret pattern and cannot be edited via UI.",
        )
    if key.upper() not in _EDITABLE_KEYS and key not in _EDITABLE_KEYS:
        raise HTTPException(
            status_code=403,
            detail=f"Key '{key}' is not in the editable allowlist.",
        )


@router.put("/backend/{key}")
async def update_backend_setting(
    key: str, update: EnvVariableUpdate, current_user: UserResponse = Depends(get_admin_user)
):
    """Update a backend environment variable. Enforces editable allowlist."""
    _validate_editable(key)
    try:
        env_vars = read_env_file("backend")
        env_vars[key] = update.value
        write_env_file("backend", env_vars)
        return {"message": f"Backend configuration '{key}' updated successfully; restart required to take effect."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")


@router.put("/frontend/{key}")
async def update_frontend_setting(
    key: str, update: EnvVariableUpdate, current_user: UserResponse = Depends(get_admin_user)
):
    """Update a frontend environment variable. Enforces editable allowlist."""
    _validate_editable(key)
    try:
        env_vars = read_env_file("frontend")
        env_vars[key] = update.value
        write_env_file("frontend", env_vars)
        return {"message": f"Frontend configuration '{key}' updated successfully; restart required to take effect."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")


@router.post("/backend/{key}")
async def add_backend_setting(
    key: str, update: EnvVariableUpdate, current_user: UserResponse = Depends(get_admin_user)
):
    """Add a backend environment variable. Enforces editable allowlist."""
    _validate_editable(key)
    try:
        env_vars = read_env_file("backend")
        env_vars[key] = update.value
        write_env_file("backend", env_vars)
        return {"message": f"Backend configuration '{key}' added successfully; restart required to take effect."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add configuration: {str(e)}")


@router.post("/frontend/{key}")
async def add_frontend_setting(
    key: str, update: EnvVariableUpdate, current_user: UserResponse = Depends(get_admin_user)
):
    """Add a frontend environment variable. Enforces editable allowlist."""
    _validate_editable(key)
    try:
        env_vars = read_env_file("frontend")
        env_vars[key] = update.value
        write_env_file("frontend", env_vars)
        return {"message": f"Frontend configuration '{key}' added successfully; restart required to take effect."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add configuration: {str(e)}")


@router.delete("/backend/{key}")
async def delete_backend_setting(key: str, current_user: UserResponse = Depends(get_admin_user)):
    """Delete a backend environment variable."""
    try:
        env_vars = read_env_file("backend")
        if key in env_vars:
            del env_vars[key]
            write_env_file("backend", env_vars)
            return {"message": f"Backend configuration '{key}' deleted successfully; restart required to take effect."}
        else:
            raise HTTPException(status_code=404, detail=f"Configuration item '{key}' does not exist")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete configuration: {str(e)}")


@router.delete("/frontend/{key}")
async def delete_frontend_setting(key: str, current_user: UserResponse = Depends(get_admin_user)):
    """Delete a frontend environment variable."""
    try:
        env_vars = read_env_file("frontend")
        if key in env_vars:
            del env_vars[key]
            write_env_file("frontend", env_vars)
            return {"message": f"Frontend configuration '{key}' deleted successfully; restart required to take effect."}
        else:
            raise HTTPException(status_code=404, detail=f"Configuration item '{key}' does not exist")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete configuration: {str(e)}")
