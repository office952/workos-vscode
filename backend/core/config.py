import logging
import os
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_ROOT.parent

_DATABASE_URL_ENV = "DATABASE_URL"


def load_backend_env() -> None:
    """Load backend/.env and repo-root .env for CLI scripts and Alembic.

    Existing shell environment variables are not overridden.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        logger.debug("python-dotenv not installed; skipping .env load")
        return

    for env_path in (_BACKEND_ROOT / ".env", _REPO_ROOT / ".env"):
        if env_path.is_file():
            load_dotenv(env_path, override=False)
            logger.debug("Loaded environment from %s", env_path)


def resolve_database_url() -> str:
    """Return DATABASE_URL after loading .env files; fail with a clear message if missing."""
    load_backend_env()
    url = os.environ.get(_DATABASE_URL_ENV, "").strip()
    if not url:
        raise ValueError(
            f"{_DATABASE_URL_ENV} environment variable is required.\n"
            "Local dev options:\n"
            "  1. Copy backend/.env.example to backend/.env\n"
            "  2. From repo root: npm run dev:backend (sets DATABASE_URL automatically)\n"
            "  3. Export DATABASE_URL in your shell before running scripts or Alembic\n"
            "See docs/operations/OWNER_EMPLOYEE_MOBILE_READINESS.md"
        )
    return url


_DEV_AUTH_USER_ID_ENV = "WORKOS_DEV_AUTH_USER_ID"


def resolve_dev_auth_impersonation_user_id() -> str | None:
    """Return WORKOS_DEV_AUTH_USER_ID only when dev auth bypass is permitted.

    In staging/production the env var is ignored (returns None).
    """
    from core.environment import dev_auth_allowed

    if not dev_auth_allowed():
        return None
    raw = os.environ.get(_DEV_AUTH_USER_ID_ENV, "").strip()
    return raw or None


class Settings(BaseSettings):
    # Application
    app_name: str = "FastAPI Modular Template"
    debug: bool = False
    version: str = "1.0.0"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # AWS Lambda Configuration
    is_lambda: bool = False
    lambda_function_name: str = "fastapi-backend"
    aws_region: str = "us-east-1"

    @property
    def backend_url(self) -> str:
        """Generate backend URL from host and port."""
        if self.is_lambda:
            # In Lambda environment, return the API Gateway URL
            return os.environ.get(
                "PYTHON_BACKEND_URL", f"https://{self.lambda_function_name}.execute-api.{self.aws_region}.amazonaws.com"
            )
        else:
            # Use localhost for external callbacks instead of 0.0.0.0
            display_host = "127.0.0.1" if self.host == "0.0.0.0" else self.host
            return os.environ.get("PYTHON_BACKEND_URL", f"http://{display_host}:{self.port}")

    # Phase 4 — Registry Linkage Validation config flags (S27)
    registry_materials_live: bool = True
    registry_machines_live: bool = False

    # Phase 6 — Execution Output Model config flag (S27)
    # When true, gate calls ProductSystem preview and promotes WRN-01 to BLK-*
    registry_productsystem_live: bool = True

    # Phase 8 — Execution Plan Generation Gate Writer Strict Mode
    # When true, POST /plan/from-order/{order_id} runs full gate pre-flight
    # and returns 412 on non-structural blockers. When false (legacy), writer
    # only enforces structural checks (201/409/422).
    # Activated: 2026-05-09 Phase 8 Controlled Activation.
    gate_writer_strict: bool = True

    # Intake V6 — sold scope dependency validation strict mode (env OFFER_SCOPE_DEPENDENCY_STRICT).
    # Default permissive: save allowed with confirmation-required warnings visible.
    offer_scope_dependency_strict: bool = False

    class Config:
        case_sensitive = False
        extra = "ignore"

    def __getattr__(self, name: str) -> Any:
        """
        Dynamically read attributes from environment variables.
        For example: settings.opapi_key reads from OPAPI_KEY environment variable.

        Args:
            name: Attribute name (e.g., 'opapi_key')

        Returns:
            Value from environment variable

        Raises:
            AttributeError: If attribute doesn't exist and not found in environment variables
        """
        # Convert attribute name to environment variable name (snake_case -> UPPER_CASE)
        env_var_name = name.upper()

        # Check if environment variable exists
        if env_var_name in os.environ:
            value = os.environ[env_var_name]
            # Cache the value in instance dict to avoid repeated lookups
            self.__dict__[name] = value
            logger.debug(f"Read dynamic attribute {name} from environment variable {env_var_name}")
            return value

        # If not found, raise AttributeError to maintain normal Python behavior
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


# Global settings instance
settings = Settings()
