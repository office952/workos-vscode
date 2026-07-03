"""
Shared test fixtures for WorkOS backend E2E tests.

Strategy:
  1. Set env vars to skip lifespan DB/mock-data initialization.
  2. Import ALL model modules so Base.metadata is fully populated.
  3. Pre-patch `core.database.db_manager` with an isolated SQLite engine.
  4. Seed reference tables (product_families) needed by business logic.
  5. Create TestClient AFTER patching so the lifespan sees the ready DB.
"""

import os
import sys
import importlib
import pkgutil

# Must set BEFORE any app import triggers lifespan logic
os.environ["MGX_IGNORE_INIT_DB"] = "1"
os.environ["MGX_IGNORE_INIT_DATA"] = "1"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test_placeholder.db"
os.environ["APP_ENV"] = "test"
os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-not-for-production"

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

# ---- CRITICAL: Import ALL model modules so Base.metadata is populated ----
_models_dir = os.path.join(BACKEND_ROOT, "models")
for _finder, _name, _ispkg in pkgutil.iter_modules([_models_dir]):
    try:
        importlib.import_module(f"models.{_name}")
    except Exception:
        pass  # Some models may have optional deps; skip gracefully

from tests._db_fixture import IsolatedDBFixture


def _seed_reference_data(fixture: IsolatedDBFixture):
    """Seed reference/lookup tables required by business logic validators."""
    from models.product_families import Product_families

    async def _do_seed():
        async with fixture.session_maker() as session:
            # Seed product families used in tests
            families = [
                Product_families(
                    family_id="signage",
                    label="Signage",
                    category="outdoor",
                    active=True,
                    description="Outdoor signage products",
                ),
                Product_families(
                    family_id="print",
                    label="Print",
                    category="indoor",
                    active=True,
                    description="Indoor print products",
                ),
                Product_families(
                    family_id="packaging",
                    label="Packaging",
                    category="industrial",
                    active=True,
                    description="Industrial packaging",
                ),
            ]
            session.add_all(families)
            await session.commit()

    fixture.run(_do_seed())


@pytest.fixture(scope="session")
def db_fixture():
    """Session-scoped isolated SQLite DB with all tables created and seeded."""
    fixture = IsolatedDBFixture(prefix="mgx_pytest_")
    fixture.setup()
    _seed_reference_data(fixture)
    yield fixture
    fixture.teardown()


@pytest_asyncio.fixture
async def db_session(db_fixture):
    async with db_fixture.session_maker() as session:
        yield session


@pytest.fixture
def unauth_client(db_fixture):
    """TestClient WITHOUT auth — expects 401/403 on protected endpoints."""
    from main import app
    from core.database import get_db
    from dependencies.auth import get_current_user

    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    # Remove any auth override so endpoints see no credentials
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(db_fixture):
    """TestClient WITH mocked admin auth — all protected endpoints accessible."""
    from main import app
    from core.database import get_db
    from dependencies.auth import get_current_user
    from schemas.auth import UserResponse

    async def _override_get_db():
        async with db_fixture.session_maker() as session:
            yield session

    async def _override_get_current_user():
        return UserResponse(
            id="test-user-id",
            email="test@example.com",
            name="Test Admin",
            role="admin",
            last_login=None,
        )

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()