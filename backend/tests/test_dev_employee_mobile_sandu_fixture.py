"""Lightweight tests for dev Sandu Employee Mobile fixture helpers."""

from __future__ import annotations

import unittest

from services.dev_employee_mobile_sandu_fixture_service import (
    CALIN_TASK_ID,
    DEV_PREPARED_BY_USER_ID,
    FIXTURE_INTAKE_CODE,
    SANDU_SMOKE_INSTRUCTION_TASK_ID,
    SANDU_SMOKE_INSTRUCTION_TEXT,
    SANDU_TASK_IDS,
    WORK_FILE_ID,
    build_work_file_attachment_metadata,
    merge_work_file_attachment_into_spec,
    plan_document_backfill_action,
    plan_sandu_task_assignment_actions,
    plan_smoke_instruction_action,
)
from services.volumetric_return_task_taxonomy_service import (
    BONDING_DISPLAY_NAME,
    MODELING_DISPLAY_NAME,
    RETURN_BONDING_PROCESS_ID,
    SIDE_FORMING_PROCESS_ID,
    apply_volumetric_return_taxonomy_to_plan_tasks,
    is_legacy_wrong_return_bonding_task,
)


class DevSanduFixtureHelperTests(unittest.TestCase):
    def test_build_work_file_attachment_metadata(self) -> None:
        row = build_work_file_attachment_metadata(intake_code=FIXTURE_INTAKE_CODE, size_bytes=42)
        self.assertEqual(row["id"], WORK_FILE_ID)
        self.assertEqual(row["mimeType"], "image/svg+xml")
        self.assertIn(FIXTURE_INTAKE_CODE, row["fileUrl"])

    def test_merge_work_file_attachment_idempotent(self) -> None:
        attachment = build_work_file_attachment_metadata(intake_code=FIXTURE_INTAKE_CODE, size_bytes=10)
        spec = {"workFileAttachments": []}
        merged, action = merge_work_file_attachment_into_spec(spec, attachment)
        self.assertEqual(action, "added")
        self.assertEqual(len(merged["workFileAttachments"]), 1)

        again, action2 = merge_work_file_attachment_into_spec(merged, attachment)
        self.assertEqual(action2, "unchanged")
        self.assertEqual(len(again["workFileAttachments"]), 1)

    def test_plan_assignments_skip_calin_and_already_assigned(self) -> None:
        tasks = [
            {"task_id": CALIN_TASK_ID, "assigned_employee_id": 1},
            {"task_id": "T-004", "assigned_employee_id": 4},
            {"task_id": "T-006", "assigned_employee_id": None},
        ]
        actions = plan_sandu_task_assignment_actions(tasks, sandu_employee_id=4, reality_lookup={})
        by_id = {a["task_id"]: a for a in actions}
        self.assertEqual(by_id["T-004"]["action"], "skip")
        self.assertEqual(by_id["T-006"]["action"], "assign")
        self.assertNotIn(CALIN_TASK_ID, SANDU_TASK_IDS)

    def test_plan_document_backfill_idempotent(self) -> None:
        docs = [
            {
                "id": WORK_FILE_ID,
                "name": WORK_FILE_ID,
                "type": "svg",
                "source": "intake_work_file",
                "downloadable": True,
            }
        ]
        tasks = [{"task_id": "T-008", "documents": []}]
        updated, action = plan_document_backfill_action(tasks, documents=docs)
        self.assertEqual(action, "updated")
        again, action2 = plan_document_backfill_action(updated, documents=docs)
        self.assertEqual(action2, "unchanged")

    def test_plan_smoke_instruction_only_on_target_task(self) -> None:
        tasks = [{"task_id": "T-007"}, {"task_id": SANDU_SMOKE_INSTRUCTION_TASK_ID}]
        updated, action = plan_smoke_instruction_action(
            tasks,
            task_id=SANDU_SMOKE_INSTRUCTION_TASK_ID,
            instructions=SANDU_SMOKE_INSTRUCTION_TEXT,
        )
        self.assertEqual(action, "updated")
        by_id = {t["task_id"]: t for t in updated}
        self.assertIn("instructions", by_id[SANDU_SMOKE_INSTRUCTION_TASK_ID])
        self.assertNotIn("instructions", by_id["T-007"])

    def test_return_taxonomy_fixes_wrong_bonding_task(self) -> None:
        tasks = [
            {
                "task_id": "T-004",
                "process_id": SIDE_FORMING_PROCESS_ID,
                "process_type": "welding",
                "machine_type": "RETURN_PROFILE_FACE_BONDING",
                "display_name": "Lipire cant pe față",
            },
            {
                "task_id": "T-005",
                "process_id": RETURN_BONDING_PROCESS_ID,
                "process_type": "welding",
                "machine_type": "RETURN_PROFILE_FACE_BONDING",
                "display_name": "Lipire cant pe față",
            },
        ]
        self.assertTrue(is_legacy_wrong_return_bonding_task(tasks[1]))
        updated, action = apply_volumetric_return_taxonomy_to_plan_tasks(tasks, set_owner_instructions=True)
        self.assertEqual(action, "updated")
        by_id = {t["task_id"]: t for t in updated}
        self.assertEqual(by_id["T-004"]["display_name"], MODELING_DISPLAY_NAME)
        self.assertEqual(by_id["T-005"]["display_name"], BONDING_DISPLAY_NAME)
        self.assertNotEqual(by_id["T-005"]["process_type"], "welding")
        self.assertNotEqual(by_id["T-005"]["machine_type"], "RETURN_PROFILE_FACE_BONDING")

    def test_dev_prepared_by_user_constant(self) -> None:
        self.assertEqual(DEV_PREPARED_BY_USER_ID, "dev-admin-user-00000000")


if __name__ == "__main__":
    unittest.main()
