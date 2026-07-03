"""TPL-VOLUMETRIC-LETTERS vector file readiness policy tests."""

from __future__ import annotations

import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.product_readiness_service import ProductReadinessService  # noqa: E402
from services.volumetric_vector_readiness_policy import (  # noqa: E402
    WARN_DWG_ANALYSIS_NOT_SUPPORTED,
    WARN_DXF_ANALYSIS_NOT_SUPPORTED,
    WARN_LETTERS_VECTOR_FILE_REQUIRED,
    WARN_VECTOR_ANALYSIS_FAILED,
    WARN_VECTOR_ANALYSIS_PENDING,
    WARN_VECTOR_FILE_TYPE_UNSUPPORTED,
    WARN_VECTOR_MANUAL_REVIEW_REQUIRED,
    evaluate_volumetric_vector_readiness,
)
from tests._db_fixture import IsolatedDBFixture  # noqa: E402
from seeds.seed_active_template_scope import seed_active_template_scope  # noqa: E402
from seeds.seed_build4_templates import seed_build4_templates  # noqa: E402

from models.product_templates import Product_templates  # noqa: E402
from sqlalchemy import select  # noqa: E402


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestVolumetricVectorReadinessPolicy(unittest.TestCase):
    def test_no_vector_template_level(self) -> None:
        result = evaluate_volumetric_vector_readiness(None, template_level=True)
        self.assertIn(WARN_LETTERS_VECTOR_FILE_REQUIRED, result.warnings)
        self.assertFalse(result.vector_gate_satisfied)

    def test_no_vector_intake_spec(self) -> None:
        result = evaluate_volumetric_vector_readiness({})
        self.assertIn(WARN_LETTERS_VECTOR_FILE_REQUIRED, result.warnings)
        self.assertFalse(result.vector_gate_satisfied)

    def test_dwg_unanalyzed(self) -> None:
        spec = {
            "vector_file_present": True,
            "vector_file_name": "litere.dwg",
            "vector_file_type": "dwg",
            "vector_analysis_status": "attached_unanalyzed",
        }
        result = evaluate_volumetric_vector_readiness(spec)
        self.assertNotIn(WARN_LETTERS_VECTOR_FILE_REQUIRED, result.warnings)
        self.assertIn(WARN_DWG_ANALYSIS_NOT_SUPPORTED, result.warnings)
        self.assertIn(WARN_VECTOR_MANUAL_REVIEW_REQUIRED, result.warnings)
        self.assertFalse(result.vector_gate_satisfied)
        self.assertTrue(result.vector_file_present)

    def test_dwg_manual_review_approved(self) -> None:
        spec = {
            "vector_file_name": "litere.dwg",
            "vector_file_type": "dwg",
            "vector_manual_review_approved": True,
        }
        result = evaluate_volumetric_vector_readiness(spec)
        self.assertNotIn(WARN_LETTERS_VECTOR_FILE_REQUIRED, result.warnings)
        self.assertTrue(result.vector_gate_satisfied)
        self.assertIn(WARN_DWG_ANALYSIS_NOT_SUPPORTED, result.warnings)

    def test_dxf_unanalyzed(self) -> None:
        spec = {
            "vector_file_name": "contur.dxf",
            "vector_file_type": "dxf",
        }
        result = evaluate_volumetric_vector_readiness(spec)
        self.assertIn(WARN_DXF_ANALYSIS_NOT_SUPPORTED, result.warnings)
        self.assertIn(WARN_VECTOR_MANUAL_REVIEW_REQUIRED, result.warnings)
        self.assertFalse(result.vector_gate_satisfied)

    def test_svg_analyzed(self) -> None:
        spec = {
            "vector_file_name": "litere.svg",
            "vector_file_type": "svg",
            "vector_analysis_status": "analyzed",
            "vector_layer_mapping_status": "mapped",
            "vector_manual_review_approved": True,
            "svg_layer_mappings": {"Layer_x0020_1": "TPL-VOLUMETRIC-LETTERS"},
        }
        result = evaluate_volumetric_vector_readiness(spec)
        self.assertNotIn(WARN_LETTERS_VECTOR_FILE_REQUIRED, result.warnings)
        self.assertTrue(result.vector_gate_satisfied)

    def test_svg_analysis_failed(self) -> None:
        spec = {
            "vector_file_name": "bad.svg",
            "vector_file_type": "svg",
            "vector_analysis_status": "analysis_failed",
        }
        result = evaluate_volumetric_vector_readiness(spec)
        self.assertIn(WARN_VECTOR_ANALYSIS_FAILED, result.warnings)
        self.assertIn(WARN_VECTOR_MANUAL_REVIEW_REQUIRED, result.warnings)
        self.assertFalse(result.vector_gate_satisfied)

    def test_unsupported_other_type(self) -> None:
        spec = {
            "vector_file_name": "scan.pdf",
            "vector_file_type": "other",
        }
        result = evaluate_volumetric_vector_readiness(spec)
        self.assertIn(WARN_VECTOR_FILE_TYPE_UNSUPPORTED, result.warnings)
        self.assertFalse(result.vector_gate_satisfied)


class TestVolumetricVectorReadinessIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_fixture = IsolatedDBFixture(prefix="vol_vector_")
        cls.db_fixture.setup()
        _run(cls._seed())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_fixture.teardown()

    @classmethod
    async def _seed(cls) -> None:
        await seed_build4_templates()
        await seed_active_template_scope()

    async def _tpl_id(self) -> int:
        from core.database import db_manager

        async with db_manager.async_session_maker() as session:
            tpl = (
                await session.execute(
                    select(Product_templates).where(
                        Product_templates.template_code == "TPL-VOLUMETRIC-LETTERS"
                    )
                )
            ).scalar_one()
            return int(tpl.id)

    def test_template_level_still_warns_vector(self) -> None:
        async def _go():
            from core.database import db_manager

            async with db_manager.async_session_maker() as session:
                return await ProductReadinessService(session).evaluate(await self._tpl_id())

        result = _run(_go())
        self.assertIn(
            WARN_LETTERS_VECTOR_FILE_REQUIRED,
            result.technical_readiness.warnings,
        )
        self.assertFalse(result.ready_for_quote)

    def test_dwg_manual_review_clears_file_missing_warning(self) -> None:
        spec = {
            "vector_file_name": "litere.dwg",
            "vector_file_type": "dwg",
            "vector_manual_review_approved": True,
        }

        async def _go():
            from core.database import db_manager

            async with db_manager.async_session_maker() as session:
                return await ProductReadinessService(session).evaluate(
                    await self._tpl_id(),
                    product_spec=spec,
                )

        result = _run(_go())
        self.assertNotIn(
            WARN_LETTERS_VECTOR_FILE_REQUIRED,
            result.technical_readiness.warnings,
        )
        self.assertIn(WARN_DWG_ANALYSIS_NOT_SUPPORTED, result.technical_readiness.warnings)


if __name__ == "__main__":
    unittest.main()
