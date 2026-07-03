"""Integration tests for Sprint #5 deliverables.

Covers:
  - `/api/v1/admin/integrity/product-families` health-check endpoint.
  - `scripts.migrate_legacy_family_labels.migrate_intake_legacy_labels`.
  - PUT validation for family_id on product_templates and intake_requests.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

# Ensure app/backend is on sys.path so `core`, `models`, `services` import.
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("ENVIRONMENT", "dev")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import models  # noqa: F401,E402 - register all models
from dependencies.auth import get_current_user  # noqa: E402
from models.intake_requests import Intake_requests  # noqa: E402
from models.product_families import Product_families  # noqa: E402
from models.product_templates import Product_templates  # noqa: E402
from schemas.auth import UserResponse  # noqa: E402
from tests._db_fixture import IsolatedDBFixture  # noqa: E402

_FAKE_ADMIN = UserResponse(id="test-admin-id", email="admin@test.local", name="Test Admin", role="admin")


class IntegrityAndMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Isolated DB for this suite; patches db_manager in place.
        cls.db = IsolatedDBFixture(prefix="mgx_integrity_")
        cls.db.setup()

        # Import app AFTER DB is patched so lifespan-triggered side effects
        # resolve to this suite's engine.
        from main import app  # noqa: E402

        app.dependency_overrides[get_current_user] = lambda: _FAKE_ADMIN
        cls.app = app
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.client.close()
        except Exception:
            pass
        # Remove auth override so it doesn't leak into other tests sharing the app singleton
        cls.app.dependency_overrides.pop(get_current_user, None)
        cls.db.teardown()

    def setUp(self):
        # Reset all tables between tests
        self.db.reset_tables([Intake_requests, Product_templates, Product_families])

    async def _seed_registry(self):
        async with self.db.session_maker() as s:
            s.add_all(
                [
                    Product_families(
                        family_id="casete_luminoase",
                        label="Casete luminoase",
                        category="semnalistica",
                        active=True,
                    ),
                    Product_families(
                        family_id="print_large_format",
                        label="Print format mare",
                        category="print",
                        active=True,
                    ),
                    Product_families(
                        family_id="servicii_montaj",
                        label="Servicii montaj",
                        category="servicii",
                        active=False,  # inactive on purpose
                    ),
                ]
            )
            await s.commit()

    # -------- Health-check endpoint --------

    def test_integrity_ok_when_clean(self):
        self.db.run(self._seed_registry())

        async def _add_clean_template():
            async with self.db.session_maker() as s:
                s.add(
                    Product_templates(
                        template_code="TPL-CL-1",
                        family_id="casete_luminoase",
                        family_name="Casete luminoase",
                        active=True,
                    )
                )
                await s.commit()

        self.db.run(_add_clean_template())

        r = self.client.get("/api/v1/admin/integrity/product-families")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["issues_count"], 0)
        self.assertEqual(body["registry"]["total"], 3)
        self.assertEqual(body["registry"]["active"], 2)

    def test_integrity_detects_all_issue_classes(self):
        self.db.run(self._seed_registry())

        async def _seed_bad():
            async with self.db.session_maker() as s:
                s.add(
                    Product_templates(
                        template_code="TPL-ORPHAN",
                        family_id="nonexistent_slug",
                        family_name="Whatever",
                        active=True,
                    )
                )
                s.add(
                    Product_templates(
                        template_code="TPL-NOFID",
                        family_id=None,
                        family_name="Legacy Name",
                        active=True,
                    )
                )
                s.add(
                    Product_templates(
                        template_code="TPL-CL-A",
                        family_id="casete_luminoase",
                        family_name="CL A",
                        active=True,
                    )
                )
                s.add(
                    Product_templates(
                        template_code="TPL-CL-B",
                        family_id="casete_luminoase",
                        family_name="CL B",
                        active=True,
                    )
                )
                s.add(
                    Intake_requests(
                        code="INQ-001",
                        client_name="Acme",
                        product_family="Casete Luminoase LED",  # legacy label
                        status="new",
                    )
                )
                s.add(
                    Intake_requests(
                        code="INQ-002",
                        client_name="Beta",
                        product_family="servicii_montaj",  # inactive in registry
                        status="new",
                    )
                )
                await s.commit()

        self.db.run(_seed_bad())

        r = self.client.get("/api/v1/admin/integrity/product-families")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "degraded")
        self.assertGreaterEqual(body["issues_count"], 4)

        tpl = body["templates"]
        self.assertTrue(
            any(x["family_id"] == "nonexistent_slug" for x in tpl["orphan_family_id"])
        )
        self.assertTrue(
            any(x["template_code"] == "TPL-NOFID" for x in tpl["missing_family_id"])
        )
        self.assertTrue(
            any(x["family_id"] == "casete_luminoase" for x in tpl["ambiguous_families"])
        )

        intake = body["intake"]
        self.assertTrue(
            any(x["product_family"] == "Casete Luminoase LED" for x in intake["orphan_family_id"])
        )
        self.assertTrue(
            any(x["product_family"] == "servicii_montaj" for x in intake["orphan_family_id"])
        )

    # -------- Migration script --------

    def test_migration_dry_run_does_not_mutate(self):
        self.db.run(self._seed_registry())

        async def _seed_intake():
            async with self.db.session_maker() as s:
                s.add_all(
                    [
                        Intake_requests(
                            code="I1",
                            client_name="C1",
                            product_family="Casete Luminoase LED",
                            status="new",
                        ),
                        Intake_requests(
                            code="I2",
                            client_name="C2",
                            product_family="casete_luminoase",
                            status="new",
                        ),
                        Intake_requests(
                            code="I3",
                            client_name="C3",
                            product_family="Some Random Label",
                            status="new",
                        ),
                    ]
                )
                await s.commit()

        self.db.run(_seed_intake())

        from scripts.migrate_legacy_family_labels import migrate_intake_legacy_labels

        stats = self.db.run(migrate_intake_legacy_labels(dry_run=True))
        self.assertEqual(stats["scanned"], 3)
        self.assertEqual(stats["already_canonical"], 1)
        self.assertEqual(stats["rewritten"], 1)
        self.assertEqual(stats["unmapped"], 1)

        async def _verify():
            async with self.db.session_maker() as s:
                rows = (await s.execute(select(Intake_requests))).scalars().all()
                return {r.code: r.product_family for r in rows}

        values = self.db.run(_verify())
        self.assertEqual(values["I1"], "Casete Luminoase LED")
        self.assertEqual(values["I2"], "casete_luminoase")
        self.assertEqual(values["I3"], "Some Random Label")

    def test_migration_applies_and_is_idempotent(self):
        self.db.run(self._seed_registry())

        async def _seed_intake():
            async with self.db.session_maker() as s:
                s.add_all(
                    [
                        Intake_requests(
                            code="I1",
                            client_name="C1",
                            product_family="Casete luminoase",  # exact label match
                            status="new",
                        ),
                        Intake_requests(
                            code="I2",
                            client_name="C2",
                            product_family="banner pvc",  # legacy alias
                            status="new",
                        ),
                        Intake_requests(
                            code="I3",
                            client_name="C3",
                            product_family="print_large_format",  # already canonical
                            status="new",
                        ),
                        Intake_requests(
                            code="I4",
                            client_name="C4",
                            product_family="unknown thing",  # unmapped
                            status="new",
                        ),
                    ]
                )
                await s.commit()

        self.db.run(_seed_intake())

        from scripts.migrate_legacy_family_labels import migrate_intake_legacy_labels

        stats = self.db.run(migrate_intake_legacy_labels(dry_run=False))
        self.assertEqual(stats["scanned"], 4)
        self.assertEqual(stats["rewritten"], 2)
        self.assertEqual(stats["already_canonical"], 1)
        self.assertEqual(stats["unmapped"], 1)

        async def _verify():
            async with self.db.session_maker() as s:
                rows = (await s.execute(select(Intake_requests))).scalars().all()
                return {r.code: r.product_family for r in rows}

        values = self.db.run(_verify())
        self.assertEqual(values["I1"], "casete_luminoase")
        self.assertEqual(values["I2"], "print_large_format")
        self.assertEqual(values["I3"], "print_large_format")
        self.assertEqual(values["I4"], "unknown thing")

        # Re-run — should be idempotent (0 rewrites)
        stats2 = self.db.run(migrate_intake_legacy_labels(dry_run=False))
        self.assertEqual(stats2["rewritten"], 0)
        self.assertEqual(stats2["already_canonical"], 3)

    # -------- PUT validation --------

    def test_put_template_rejects_invalid_family_id(self):
        self.db.run(self._seed_registry())

        async def _add_tpl():
            async with self.db.session_maker() as s:
                t = Product_templates(
                    template_code="TPL-X",
                    family_id="casete_luminoase",
                    family_name="Casete luminoase",
                    active=True,
                )
                s.add(t)
                await s.commit()
                await s.refresh(t)
                return t.id

        tpl_id = self.db.run(_add_tpl())

        r = self.client.put(
            f"/api/v1/entities/product_templates/{tpl_id}",
            json={"family_id": "no_such_family"},
        )
        self.assertEqual(r.status_code, 422)
        self.assertIn("Invalid family_id", r.json()["detail"])

        r = self.client.put(
            f"/api/v1/entities/product_templates/{tpl_id}",
            json={"family_id": "print_large_format"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["family_id"], "print_large_format")

    def test_put_intake_rejects_invalid_family_id(self):
        self.db.run(self._seed_registry())

        async def _add_intake():
            async with self.db.session_maker() as s:
                it = Intake_requests(
                    code="INQ-PUT",
                    client_name="Client",
                    product_family="casete_luminoase",
                    status="new",
                )
                s.add(it)
                await s.commit()
                await s.refresh(it)
                return it.id

        iid = self.db.run(_add_intake())

        r = self.client.put(
            f"/api/v1/entities/intake_requests/{iid}",
            json={"product_family": "Casete Luminoase LED"},
        )
        self.assertEqual(r.status_code, 422)
        self.assertIn("Invalid product_family", r.json()["detail"])

        r = self.client.put(
            f"/api/v1/entities/intake_requests/{iid}",
            json={"product_family": "print_large_format"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["product_family"], "print_large_format")


if __name__ == "__main__":
    unittest.main(verbosity=2)