import asyncio
from unittest import mock

import pytest
from fastapi import FastAPI

import main
from core.startup_safety import EnvironmentReadinessReport, SafetyCheckResult


@pytest.mark.asyncio
async def test_lifespan_blocks_boot_when_startup_checks_blocked():
    blocked_report = EnvironmentReadinessReport(
        environment="live",
        overall_status="BLOCKED",
        checks=[
            SafetyCheckResult(
                name="APP_ENV_SET",
                status="BLOCKED",
                message="Deployed environment requires an explicit runtime environment value",
            )
        ],
    )

    with mock.patch.object(main, "run_startup_safety_checks", return_value=blocked_report), \
        mock.patch.object(main, "log_startup_safety_report") as log_mock, \
        mock.patch.object(main, "initialize_database", new=mock.AsyncMock()) as init_db_mock, \
        mock.patch.object(main, "initialize_mock_data", new=mock.AsyncMock()) as init_mock_data_mock, \
        mock.patch.object(main, "initialize_admin_user", new=mock.AsyncMock()) as init_admin_mock:
        with pytest.raises(RuntimeError, match="Startup blocked by environment safety checks"):
            async with main.lifespan(FastAPI()):
                pass

        log_mock.assert_called_once()
        init_db_mock.assert_not_called()
        init_mock_data_mock.assert_not_called()
        init_admin_mock.assert_not_called()