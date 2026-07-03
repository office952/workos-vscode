"""Tests for Product Blueprint Dossier CRUD API.

Phase A — Foundation tests (1-16).
Phase B — Hardening tests (17+).

Covers:
  - CRUD happy paths
  - FK/template integrity (create with non-existent template rejected)
  - Delete policy (draft/deprecated allowed, protected statuses blocked with 409)
  - Version increment on approval transition
  - Version decrement blocked
  - Status transition enforcement
  - Section state validation
  - Semantic JSON validation (loose for draft, strict for approved)
  - sections_json key validation
  - Owner enforcement on writes
  - Boundary import verification (AST scan)
  - product_templates regression
"""

import ast
import json
import os

import pytest

API_PREFIX = "/api/v1/entities/product-blueprint-dossiers"
TEMPLATES_PREFIX = "/api/v1/entities/product_templates"

# Counter to generate unique template codes per test
_template_counter = 0


def _make_canonical_costengine_mapping() -> dict:
    return {
        "version": "27.09N",
        "template_code": "TPL-DOSSIER-TEST",
        "family_id": "signage",
        "status": "draft_structural_mapping",
        "quote_ready": False,
        "pricing_ready": False,
        "inputs": {
            "required": ["width_mm", "height_mm", "quantity"],
            "optional": ["material_type"],
        },
        "derived_primitives": {
            "area_m2": "width_mm * height_mm / 1000000 * quantity",
        },
        "material_keys": ["sheet_material"],
        "operation_keys": ["cutting"],
        "cost_basis_refs": {
            "material_unit_cost_ref": "configured_material_catalog",
            "operation_rate_ref": "configured_operation_rates",
        },
        "readiness_notes": ["Structural mapping only."],
    }


def _make_valid_template_payload(suffix: str = "") -> dict:
    """Build a fully valid product_template payload that passes strict contract validation."""
    global _template_counter
    _template_counter += 1
    code = f"TPL_DOSSIER_TEST_{_template_counter:04d}{suffix}"
    cid = f"comp_{_template_counter}"

    components = [
        {
            "component_id": cid,
            "type": "STRUCTURA",
            "name": "Test Structure Component",
            "operations": [
                {
                    "code": "OP_CUT",
                    "name": "Cutting",
                    "workcenter": "WC_CUT",
                    "estimatedMinutes": 30,
                    "sequence": 1,
                    "component_ref": cid,
                    "calculation_type": "static",
                }
            ],
            "materials": [
                {
                    "materialCode": "MAT_STEEL",
                    "name": "Steel Sheet",
                    "quantity": 2.0,
                    "unit": "m2",
                    "component_ref": cid,
                    "calculation_type": "static",
                }
            ],
        }
    ]
    flat_ops = [
        {
            "code": "OP_CUT",
            "name": "Cutting",
            "workcenter": "WC_CUT",
            "estimatedMinutes": 30,
            "sequence": 1,
            "component_ref": cid,
            "calculation_type": "static",
        }
    ]
    flat_mats = [
        {
            "materialCode": "MAT_STEEL",
            "name": "Steel Sheet",
            "quantity": 2.0,
            "unit": "m2",
            "component_ref": cid,
            "calculation_type": "static",
        }
    ]

    return {
        "template_code": code,
        "family_id": "signage",
        "family_name": "Signage",
        "description": "Test template for dossier tests",
        "active": True,
        "components_json": json.dumps(components),
        "operations_json": json.dumps(flat_ops),
        "required_materials_json": json.dumps(flat_mats),
    }


@pytest.fixture
def _seed_template(auth_client):
    """Seed a product_template so we have a valid template_id to reference."""
    payload = _make_valid_template_payload()
    resp = auth_client.post(TEMPLATES_PREFIX, json=payload)
    assert resp.status_code == 201, f"Failed to seed template: {resp.text}"
    return resp.json()


def _create_dossier(auth_client, template, **overrides):
    """Helper to create a dossier and return the response JSON."""
    payload = {
        "template_id": template["id"],
        "template_code": template["template_code"],
        "costengine_mapping_json": json.dumps(_make_canonical_costengine_mapping()),
        **overrides,
    }
    resp = auth_client.post(API_PREFIX, json=payload)
    assert resp.status_code == 201, f"Create failed: {resp.text}"
    return resp.json()


# ============================================================
# Phase A — Foundation Tests (preserved)
# ============================================================


class TestDossierCRUD:
    """Basic CRUD tests for product_blueprint_dossier."""

    def test_create_dossier_valid(self, auth_client, _seed_template):
        """1. Create dossier with valid data."""
        template = _seed_template
        resp = auth_client.post(
            API_PREFIX,
            json={
                "template_id": template["id"],
                "template_code": template["template_code"],
                "dossier_version": 1,
                "status": "draft",
                "variants_json": json.dumps({"options": ["standard", "premium"]}),
                "production_notes_json": json.dumps({"note": "Handle with care"}),
                "completion_state_json": json.dumps({
                    "variants": {"status": "draft", "updated_at": None},
                    "layers": {"status": "not_started", "updated_at": None},
                }),
            },
        )
        assert resp.status_code == 201, f"Create failed: {resp.text}"
        body = resp.json()
        assert body["template_id"] == template["id"]
        assert body["template_code"] == template["template_code"]
        assert body["dossier_version"] == 1
        assert body["status"] == "draft"
        assert body["id"] is not None

    def test_get_dossier_by_id(self, auth_client, _seed_template):
        """2. Get dossier by id."""
        template = _seed_template
        dossier = _create_dossier(auth_client, template)
        resp = auth_client.get(f"{API_PREFIX}/{dossier['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == dossier["id"]

    def test_get_dossier_by_template_id(self, auth_client, _seed_template):
        """3. Get dossier by template_id."""
        template = _seed_template
        _create_dossier(auth_client, template)
        resp = auth_client.get(f"{API_PREFIX}/by-template/{template['id']}")
        assert resp.status_code == 200
        assert resp.json()["template_id"] == template["id"]

    def test_update_dossier_status_valid(self, auth_client, _seed_template):
        """4. Update dossier status with valid transition (draft -> needs_review)."""
        template = _seed_template
        dossier = _create_dossier(auth_client, template)
        resp = auth_client.put(
            f"{API_PREFIX}/{dossier['id']}",
            json={"status": "needs_review"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "needs_review"

    def test_reject_invalid_status(self, auth_client, _seed_template):
        """5. Reject invalid status on create."""
        template = _seed_template
        resp = auth_client.post(
            API_PREFIX,
            json={
                "template_id": template["id"],
                "template_code": template["template_code"],
                "status": "invalid_status_xyz",
            },
        )
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"

    def test_reject_invalid_json_field(self, auth_client, _seed_template):
        """6. Reject invalid JSON in a JSON field."""
        template = _seed_template
        resp = auth_client.post(
            API_PREFIX,
            json={
                "template_id": template["id"],
                "template_code": template["template_code"],
                "variants_json": "this is not valid json {{{",
            },
        )
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"

    def test_delete_dossier_draft(self, auth_client, _seed_template):
        """7. Delete dossier with draft status succeeds."""
        template = _seed_template
        dossier = _create_dossier(auth_client, template)
        resp = auth_client.delete(f"{API_PREFIX}/{dossier['id']}")
        assert resp.status_code == 200

        # Verify it's gone
        resp2 = auth_client.get(f"{API_PREFIX}/{dossier['id']}")
        assert resp2.status_code == 404

    def test_reject_duplicate_template_id(self, auth_client, _seed_template):
        """8. Reject duplicate template_id (one dossier per template)."""
        template = _seed_template
        _create_dossier(auth_client, template)
        resp2 = auth_client.post(
            API_PREFIX,
            json={
                "template_id": template["id"],
                "template_code": template["template_code"],
            },
        )
        assert resp2.status_code == 409, f"Expected 409, got {resp2.status_code}: {resp2.text}"

    def test_reject_missing_template_id(self, auth_client):
        """9. Reject missing template_id."""
        resp = auth_client.post(
            API_PREFIX,
            json={"template_code": "TPL_NO_TEMPLATE_ID"},
        )
        assert resp.status_code == 422

    def test_validate_completion_state_section_states(self, auth_client, _seed_template):
        """10. Validate completion_state_json section states."""
        template = _seed_template
        resp = auth_client.post(
            API_PREFIX,
            json={
                "template_id": template["id"],
                "template_code": template["template_code"],
                "completion_state_json": json.dumps({
                    "variants": {"status": "invalid_state_xyz"},
                }),
            },
        )
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"

    def test_list_dossiers(self, auth_client, _seed_template):
        """11. List dossiers endpoint works."""
        template = _seed_template
        _create_dossier(auth_client, template)
        resp = auth_client.get(API_PREFIX)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body

    def test_update_reject_invalid_status(self, auth_client, _seed_template):
        """12. Reject invalid status on update."""
        template = _seed_template
        dossier = _create_dossier(auth_client, template)
        resp = auth_client.put(
            f"{API_PREFIX}/{dossier['id']}",
            json={"status": "bogus_status"},
        )
        assert resp.status_code == 422

    def test_update_reject_invalid_json(self, auth_client, _seed_template):
        """13. Reject invalid JSON on update."""
        template = _seed_template
        dossier = _create_dossier(auth_client, template)
        resp = auth_client.put(
            f"{API_PREFIX}/{dossier['id']}",
            json={"risks_json": "not valid json!!!"},
        )
        assert resp.status_code == 422

    def test_get_nonexistent_dossier(self, auth_client):
        """14. Get nonexistent dossier returns 404."""
        resp = auth_client.get(f"{API_PREFIX}/999999")
        assert resp.status_code == 404

    def test_delete_nonexistent_dossier(self, auth_client):
        """15. Delete nonexistent dossier returns 404."""
        resp = auth_client.delete(f"{API_PREFIX}/999999")
        assert resp.status_code == 404

    def test_get_by_template_nonexistent(self, auth_client):
        """16. Get by nonexistent template_id returns 404."""
        resp = auth_client.get(f"{API_PREFIX}/by-template/999999")
        assert resp.status_code == 404


# ============================================================
# Phase B — FK / Template Integrity Tests
# ============================================================


class TestDossierFKIntegrity:
    """FK and template integrity tests."""

    def test_create_dossier_nonexistent_template(self, auth_client):
        """17. Reject create dossier for non-existent template_id."""
        resp = auth_client.post(
            API_PREFIX,
            json={
                "template_id": 999888,
                "template_code": "TPL_NONEXISTENT",
            },
        )
        # Service-level FK validation rejects non-existent template_id with 422
        assert resp.status_code == 422, (
            f"Expected 422 for non-existent template, got {resp.status_code}: {resp.text}"
        )
        assert "does not reference" in resp.text


# ============================================================
# Phase B — Delete Policy Tests
# ============================================================


class TestDossierDeletePolicy:
    """Delete policy enforcement tests per hardening decision §7."""

    def test_delete_draft_allowed(self, auth_client, _seed_template):
        """18. DELETE on draft dossier succeeds."""
        template = _seed_template
        dossier = _create_dossier(auth_client, template)
        assert dossier["status"] == "draft"
        resp = auth_client.delete(f"{API_PREFIX}/{dossier['id']}")
        assert resp.status_code == 200

    def test_delete_deprecated_allowed(self, auth_client, _seed_template):
        """19. DELETE on deprecated dossier succeeds."""
        template = _seed_template
        dossier = _create_dossier(auth_client, template)
        # Transition: draft -> deprecated
        auth_client.put(
            f"{API_PREFIX}/{dossier['id']}",
            json={"status": "deprecated"},
        )
        resp = auth_client.delete(f"{API_PREFIX}/{dossier['id']}")
        assert resp.status_code == 200

    def test_delete_approved_blocked(self, auth_client, _seed_template):
        """20. DELETE on approved dossier returns 409."""
        template = _seed_template
        dossier = _create_dossier(auth_client, template)
        # Transition: draft -> needs_review -> approved
        auth_client.put(
            f"{API_PREFIX}/{dossier['id']}",
            json={"status": "needs_review"},
        )
        auth_client.put(
            f"{API_PREFIX}/{dossier['id']}",
            json={"status": "approved"},
        )
        resp = auth_client.delete(f"{API_PREFIX}/{dossier['id']}")
        assert resp.status_code == 409, f"Expected 409, got {resp.status_code}: {resp.text}"

    def test_delete_needs_review_blocked(self, auth_client, _seed_template):
        """21. DELETE on needs_review dossier returns 409."""
        template = _seed_template
        dossier = _create_dossier(auth_client, template)
        auth_client.put(
            f"{API_PREFIX}/{dossier['id']}",
            json={"status": "needs_review"},
        )
        resp = auth_client.delete(f"{API_PREFIX}/{dossier['id']}")
        assert resp.status_code == 409

    def test_delete_blocked_status_blocked(self, auth_client, _seed_template):
        """22. DELETE on blocked dossier returns 409."""
        template = _seed_template
        dossier = _create_dossier(auth_client, template)
        # Transition: draft -> blocked
        auth_client.put(
            f"{API_PREFIX}/{dossier['id']}",
            json={"status": "blocked"},
        )
        resp = auth_client.delete(f"{API_PREFIX}/{dossier['id']}")
        assert resp.status_code == 409


# ============================================================
# Phase B — Versioning Tests
# ============================================================


class TestDossierVersioning:
    """Version increment and decrement tests per hardening decision §9."""

    def test_version_increment_on_approval(self, auth_client, _seed_template):
        """23. Transitioning to approved increments dossier_version."""
        template = _seed_template
        dossier = _create_dossier(auth_client, template)
        assert dossier["dossier_version"] == 1

        # draft -> needs_review
        auth_client.put(
            f"{API_PREFIX}/{dossier['id']}",
            json={"status": "needs_review"},
        )
        # needs_review -> approved
        resp = auth_client.put(
            f"{API_PREFIX}/{dossier['id']}",
            json={"status": "approved"},
        )
        assert resp.status_code == 200
        assert resp.json()["dossier_version"] == 2

    def test_version_no_increment_without_status_change(self, auth_client, _seed_template):
        """24. Updating content without status change does NOT increment version."""
        template = _seed_template
        dossier = _create_dossier(auth_client, template)
        resp = auth_client.put(
            f"{API_PREFIX}/{dossier['id']}",
            json={"production_notes_json": json.dumps({"note": "updated"})},
        )
        assert resp.status_code == 200
        assert resp.json()["dossier_version"] == 1

    def test_version_decrement_blocked(self, auth_client, _seed_template):
        """25. Setting dossier_version to lower value is rejected."""
        template = _seed_template
        dossier = _create_dossier(auth_client, template)
        # First bump version via approval cycle
        auth_client.put(
            f"{API_PREFIX}/{dossier['id']}",
            json={"status": "needs_review"},
        )
        resp_approve = auth_client.put(
            f"{API_PREFIX}/{dossier['id']}",
            json={"status": "approved"},
        )
        assert resp_approve.json()["dossier_version"] == 2

        # Now try to set version back to 1 (with valid transition approved -> needs_review)
        resp = auth_client.put(
            f"{API_PREFIX}/{dossier['id']}",
            json={"dossier_version": 1, "status": "needs_review"},
        )
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"

    def test_version_manual_increment_allowed(self, auth_client, _seed_template):
        """26. Manual version increment to higher value is allowed."""
        template = _seed_template
        dossier = _create_dossier(auth_client, template)
        resp = auth_client.put(
            f"{API_PREFIX}/{dossier['id']}",
            json={"dossier_version": 5},
        )
        assert resp.status_code == 200
        assert resp.json()["dossier_version"] == 5


# ============================================================
# Phase B — Status Transition Tests
# ============================================================


class TestDossierStatusTransitions:
    """Status transition enforcement tests per hardening decision §10."""

    def test_valid_transitions(self, auth_client, _seed_template):
        """27. Test all valid transitions from the transition table."""
        template = _seed_template
        dossier = _create_dossier(auth_client, template)
        did = dossier["id"]

        # draft -> needs_review
        resp = auth_client.put(f"{API_PREFIX}/{did}", json={"status": "needs_review"})
        assert resp.status_code == 200

        # needs_review -> approved
        resp = auth_client.put(f"{API_PREFIX}/{did}", json={"status": "approved"})
        assert resp.status_code == 200

        # approved -> needs_review (re-review cycle)
        resp = auth_client.put(f"{API_PREFIX}/{did}", json={"status": "needs_review"})
        assert resp.status_code == 200

        # needs_review -> draft (send back)
        resp = auth_client.put(f"{API_PREFIX}/{did}", json={"status": "draft"})
        assert resp.status_code == 200

        # draft -> blocked
        resp = auth_client.put(f"{API_PREFIX}/{did}", json={"status": "blocked"})
        assert resp.status_code == 200

        # blocked -> needs_review
        resp = auth_client.put(f"{API_PREFIX}/{did}", json={"status": "needs_review"})
        assert resp.status_code == 200

        # needs_review -> blocked
        resp = auth_client.put(f"{API_PREFIX}/{did}", json={"status": "blocked"})
        assert resp.status_code == 200

        # blocked -> draft
        resp = auth_client.put(f"{API_PREFIX}/{did}", json={"status": "draft"})
        assert resp.status_code == 200

        # draft -> deprecated
        resp = auth_client.put(f"{API_PREFIX}/{did}", json={"status": "deprecated"})
        assert resp.status_code == 200

        # deprecated -> draft (reactivation)
        resp = auth_client.put(f"{API_PREFIX}/{did}", json={"status": "draft"})
        assert resp.status_code == 200

    def test_invalid_transition_approved_to_draft(self, auth_client, _seed_template):
        """28. Transition from approved to draft is NOT allowed."""
        template = _seed_template
        dossier = _create_dossier(auth_client, template)
        did = dossier["id"]

        # draft -> needs_review -> approved
        auth_client.put(f"{API_PREFIX}/{did}", json={"status": "needs_review"})
        auth_client.put(f"{API_PREFIX}/{did}", json={"status": "approved"})

        # approved -> draft should fail
        resp = auth_client.put(f"{API_PREFIX}/{did}", json={"status": "draft"})
        assert resp.status_code == 409, f"Expected 409, got {resp.status_code}: {resp.text}"

    def test_invalid_transition_approved_to_blocked(self, auth_client, _seed_template):
        """29. Transition from approved to blocked is NOT allowed."""
        template = _seed_template
        dossier = _create_dossier(auth_client, template)
        did = dossier["id"]

        auth_client.put(f"{API_PREFIX}/{did}", json={"status": "needs_review"})
        auth_client.put(f"{API_PREFIX}/{did}", json={"status": "approved"})

        resp = auth_client.put(f"{API_PREFIX}/{did}", json={"status": "blocked"})
        assert resp.status_code == 409

    def test_invalid_transition_deprecated_to_approved(self, auth_client, _seed_template):
        """30. Transition from deprecated directly to approved is NOT allowed."""
        template = _seed_template
        dossier = _create_dossier(auth_client, template)
        did = dossier["id"]

        auth_client.put(f"{API_PREFIX}/{did}", json={"status": "deprecated"})

        resp = auth_client.put(f"{API_PREFIX}/{did}", json={"status": "approved"})
        assert resp.status_code == 409


# ============================================================
# Phase B — Section State Validation Tests
# ============================================================


class TestDossierSectionStates:
    """Section state validation tests."""

    @pytest.mark.parametrize(
        "state",
        ["not_started", "draft", "needs_review", "complete", "blocked", "deprecated"],
    )
    def test_all_valid_section_states_accepted(self, auth_client, _seed_template, state):
        """31. All 6 valid section states are accepted in completion_state_json."""
        template = _seed_template
        resp = auth_client.post(
            API_PREFIX,
            json={
                "template_id": template["id"],
                "template_code": template["template_code"],
                "completion_state_json": json.dumps({
                    "variants": {"status": state},
                }),
            },
        )
        assert resp.status_code == 201, f"State '{state}' rejected: {resp.text}"

    def test_unknown_section_state_rejected(self, auth_client, _seed_template):
        """32. Unknown section state is rejected."""
        template = _seed_template
        resp = auth_client.post(
            API_PREFIX,
            json={
                "template_id": template["id"],
                "template_code": template["template_code"],
                "completion_state_json": json.dumps({
                    "variants": {"status": "unknown_state"},
                }),
            },
        )
        assert resp.status_code == 422


# ============================================================
# Phase B — Semantic JSON Validation Tests
# ============================================================


class TestDossierSemanticValidation:
    """Semantic JSON validation tests per hardening decision §13."""

    def test_draft_accepts_loose_variants_json(self, auth_client, _seed_template):
        """33. Draft dossier accepts loose/unstructured variants_json."""
        template = _seed_template
        resp = auth_client.post(
            API_PREFIX,
            json={
                "template_id": template["id"],
                "template_code": template["template_code"],
                "status": "draft",
                "variants_json": json.dumps({"anything": "goes", "no_structure": True}),
            },
        )
        assert resp.status_code == 201, f"Draft should accept loose JSON: {resp.text}"

    def test_approved_rejects_invalid_variants_json(self, auth_client, _seed_template):
        """34. Approved dossier rejects variants_json without name/variant_key."""
        template = _seed_template
        dossier = _create_dossier(
            auth_client,
            template,
            variants_json=json.dumps([{"no_name_field": "bad"}]),
        )
        did = dossier["id"]

        # draft -> needs_review
        auth_client.put(f"{API_PREFIX}/{did}", json={"status": "needs_review"})

        # needs_review -> approved should fail due to invalid variants_json
        resp = auth_client.put(f"{API_PREFIX}/{did}", json={"status": "approved"})
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"

    def test_approved_accepts_valid_variants_json(self, auth_client, _seed_template):
        """35. Approved dossier accepts properly structured variants_json."""
        template = _seed_template
        dossier = _create_dossier(
            auth_client,
            template,
            variants_json=json.dumps([
                {"name": "Color", "allowed_values": ["red", "blue"]},
                {"variant_key": "size", "default_value": "M"},
            ]),
        )
        did = dossier["id"]

        auth_client.put(f"{API_PREFIX}/{did}", json={"status": "needs_review"})
        resp = auth_client.put(f"{API_PREFIX}/{did}", json={"status": "approved"})
        assert resp.status_code == 200

    def test_approved_rejects_invalid_task_rules_json(self, auth_client, _seed_template):
        """36. Approved dossier rejects task_rules_json without task_name/task_type."""
        template = _seed_template
        dossier = _create_dossier(
            auth_client,
            template,
            task_rules_json=json.dumps([{"missing_required_fields": True}]),
        )
        did = dossier["id"]

        auth_client.put(f"{API_PREFIX}/{did}", json={"status": "needs_review"})
        resp = auth_client.put(f"{API_PREFIX}/{did}", json={"status": "approved"})
        assert resp.status_code == 422

    def test_approved_rejects_negative_time_value(self, auth_client, _seed_template):
        """37. Approved dossier rejects time_assumptions_json with negative time."""
        template = _seed_template
        dossier = _create_dossier(
            auth_client,
            template,
            time_assumptions_json=json.dumps([
                {"operation": "cutting", "time_value": -5}
            ]),
        )
        did = dossier["id"]

        auth_client.put(f"{API_PREFIX}/{did}", json={"status": "needs_review"})
        resp = auth_client.put(f"{API_PREFIX}/{did}", json={"status": "approved"})
        assert resp.status_code == 422

    def test_approved_costengine_mapping_needs_category(self, auth_client, _seed_template):
        """38. Approved dossier requires at least one mapping category in costengine_mapping_json."""
        template = _seed_template
        dossier = _create_dossier(
            auth_client,
            template,
            costengine_mapping_json=json.dumps({"notes": "no real categories"}),
        )
        did = dossier["id"]

        auth_client.put(f"{API_PREFIX}/{did}", json={"status": "needs_review"})
        resp = auth_client.put(f"{API_PREFIX}/{did}", json={"status": "approved"})
        assert resp.status_code == 422

    def test_approved_accepts_valid_costengine_mapping(self, auth_client, _seed_template):
        """39. Approved dossier accepts costengine_mapping_json with valid category."""
        template = _seed_template
        dossier = _create_dossier(
            auth_client,
            template,
            costengine_mapping_json=json.dumps({
                "material_inputs": {"steel": {"source": "inventory"}},
            }),
        )
        did = dossier["id"]

        auth_client.put(f"{API_PREFIX}/{did}", json={"status": "needs_review"})
        resp = auth_client.put(f"{API_PREFIX}/{did}", json={"status": "approved"})
        assert resp.status_code == 200

    def test_approved_rejects_invalid_qc_checkpoints(self, auth_client, _seed_template):
        """40. Approved dossier rejects qc_checkpoints_json without checkpoint_name/what_to_verify."""
        template = _seed_template
        dossier = _create_dossier(
            auth_client,
            template,
            qc_checkpoints_json=json.dumps([{"no_name": True}]),
        )
        did = dossier["id"]

        auth_client.put(f"{API_PREFIX}/{did}", json={"status": "needs_review"})
        resp = auth_client.put(f"{API_PREFIX}/{did}", json={"status": "approved"})
        assert resp.status_code == 422

    def test_approved_rejects_invalid_risks_severity(self, auth_client, _seed_template):
        """41. Approved dossier rejects risks_json with invalid severity."""
        template = _seed_template
        dossier = _create_dossier(
            auth_client,
            template,
            risks_json=json.dumps([
                {"risk_name": "Fire", "severity": "catastrophic"}
            ]),
        )
        did = dossier["id"]

        auth_client.put(f"{API_PREFIX}/{did}", json={"status": "needs_review"})
        resp = auth_client.put(f"{API_PREFIX}/{did}", json={"status": "approved"})
        assert resp.status_code == 422

    def test_draft_accepts_invalid_risks_severity(self, auth_client, _seed_template):
        """42. Draft dossier accepts risks_json with any severity (loose validation)."""
        template = _seed_template
        resp = auth_client.post(
            API_PREFIX,
            json={
                "template_id": template["id"],
                "template_code": template["template_code"],
                "status": "draft",
                "risks_json": json.dumps([
                    {"risk_name": "Fire", "severity": "catastrophic"}
                ]),
            },
        )
        assert resp.status_code == 201


# ============================================================
# Phase B — sections_json Validation Tests
# ============================================================


class TestDossierSectionsJson:
    """sections_json umbrella metadata validation tests."""

    def test_sections_json_unknown_section_rejected_on_approved(self, auth_client, _seed_template):
        """43. sections_json with unknown section name rejected when transitioning to approved."""
        template = _seed_template
        dossier = _create_dossier(
            auth_client,
            template,
            sections_json=json.dumps({
                "section_order": ["variants", "unknown_section_xyz"],
            }),
        )
        did = dossier["id"]

        auth_client.put(f"{API_PREFIX}/{did}", json={"status": "needs_review"})
        resp = auth_client.put(f"{API_PREFIX}/{did}", json={"status": "approved"})
        assert resp.status_code == 422

    def test_sections_json_valid_keys_accepted(self, auth_client, _seed_template):
        """44. sections_json with valid section names accepted."""
        template = _seed_template
        resp = auth_client.post(
            API_PREFIX,
            json={
                "template_id": template["id"],
                "template_code": template["template_code"],
                "sections_json": json.dumps({
                    "section_order": ["variants", "layers", "task_rules"],
                    "section_labels": {"variants": "Product Variants"},
                }),
            },
        )
        assert resp.status_code == 201


# ============================================================
# Phase B — Boundary Import Verification Tests
# ============================================================


class TestDossierBoundaryImports:
    """Static AST analysis to verify no forbidden imports in dossier modules."""

    FORBIDDEN_MODULES = {
        "services.cost_engine_service",
        "services.formula_handlers",
        "services.quote_orchestrator",
        "services.order_snapshot_service",
        "services.execution_plan_service",
        "services.execution_reality_service",
        "services.divergence_service",
        "validators.status_lifecycle",
        "models.quotes",
        "models.orders",
        "models.execution_plan",
        "models.execution_reality",
        "models.inventory_materials",
    }

    def _get_imports(self, filepath: str) -> set:
        """Extract all import module names from a Python file using AST."""
        with open(filepath, "r") as f:
            tree = ast.parse(f.read())

        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
        return imports

    def test_service_no_forbidden_imports(self):
        """45. Dossier service has no forbidden imports."""
        backend_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )
        service_path = os.path.join(
            backend_root, "services", "product_blueprint_dossier_service.py"
        )
        imports = self._get_imports(service_path)
        violations = imports & self.FORBIDDEN_MODULES
        assert not violations, f"Forbidden imports in service: {violations}"

    def test_router_no_forbidden_imports(self):
        """46. Dossier router has no forbidden imports."""
        backend_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )
        router_path = os.path.join(
            backend_root, "routers", "product_blueprint_dossier.py"
        )
        imports = self._get_imports(router_path)
        violations = imports & self.FORBIDDEN_MODULES
        assert not violations, f"Forbidden imports in router: {violations}"

    def test_validation_models_no_forbidden_imports(self):
        """47. Dossier validation models have no forbidden imports."""
        backend_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )
        models_path = os.path.join(
            backend_root, "services", "dossier_validation_models.py"
        )
        imports = self._get_imports(models_path)
        violations = imports & self.FORBIDDEN_MODULES
        assert not violations, f"Forbidden imports in validation models: {violations}"


# ============================================================
# Phase B — Owner Enforcement Tests
# ============================================================


class TestDossierOwnerEnforcement:
    """Verify owner enforcement rejects unauthorized writes (403 path).

    The default auth_client uses role='admin' which bypasses owner checks.
    These tests use a dedicated non-admin client to exercise the rejection path.
    """

    @pytest.fixture
    def operator_client(self, db_fixture):
        """TestClient with mocked non-owner auth (role='manager').

        BUILD 24: Changed from 'operator' to 'manager' because operator no
        longer has dossier.update/delete permissions after BUILD 24 hardening.
        Manager has dossier permissions but is NOT the dossier owner ('designer'),
        so owner enforcement still triggers the 403 rejection path.
        """
        from fastapi.testclient import TestClient as _TestClient
        from main import app
        from core.database import get_db
        from dependencies.auth import get_current_user
        from schemas.auth import UserResponse

        async def _override_get_db():
            async with db_fixture.session_maker() as session:
                yield session

        async def _override_get_current_user():
            return UserResponse(
                id="manager-user-id",
                email="manager@example.com",
                name="Test Manager",
                role="manager",
                last_login=None,
            )

        app.dependency_overrides[get_db] = _override_get_db
        app.dependency_overrides[get_current_user] = _override_get_current_user

        with _TestClient(app, raise_server_exceptions=False) as c:
            yield c

        app.dependency_overrides.clear()

    def test_owner_enforcement_rejects_non_owner_update(
        self, auth_client, operator_client, db_fixture
    ):
        """51. Non-owner user receives 403 when updating a dossier owned by another role."""
        # Create template with admin client
        template_payload = _make_valid_template_payload("_owner_test_upd")
        resp = auth_client.post(TEMPLATES_PREFIX, json=template_payload)
        assert resp.status_code == 201
        template_id = resp.json()["id"]

        # Create dossier with explicit owner_role='designer' using admin client
        dossier_payload = {
            "template_id": template_id,
            "template_code": f"OWN_UPD_{template_id}",
            "status": "draft",
            "owner_role": "designer",
        }
        resp = auth_client.post(API_PREFIX, json=dossier_payload)
        assert resp.status_code == 201, f"Dossier create failed: {resp.text}"
        did = resp.json()["id"]

        # Attempt update with operator_client (role='operator') — should get 403
        resp = operator_client.put(
            f"{API_PREFIX}/{did}", json={"status": "needs_review"}
        )
        assert resp.status_code == 403, (
            f"Expected 403 for non-owner update, got {resp.status_code}: {resp.text}"
        )
        assert "Permission denied" in resp.json().get("detail", "")

    def test_owner_enforcement_rejects_non_owner_delete(
        self, auth_client, operator_client, db_fixture
    ):
        """52. Non-owner user receives 403 when deleting a dossier owned by another role."""
        # Create template with admin client
        template_payload = _make_valid_template_payload("_owner_test_del")
        resp = auth_client.post(TEMPLATES_PREFIX, json=template_payload)
        assert resp.status_code == 201
        template_id = resp.json()["id"]

        # Create dossier with explicit owner_role='designer' using admin client
        dossier_payload = {
            "template_id": template_id,
            "template_code": f"OWN_DEL_{template_id}",
            "status": "draft",
            "owner_role": "designer",
        }
        resp = auth_client.post(API_PREFIX, json=dossier_payload)
        assert resp.status_code == 201, f"Dossier create failed: {resp.text}"
        did = resp.json()["id"]

        # Attempt delete with operator_client (role='operator') — should get 403
        resp = operator_client.delete(f"{API_PREFIX}/{did}")
        assert resp.status_code == 403, (
            f"Expected 403 for non-owner delete, got {resp.status_code}: {resp.text}"
        )
        assert "Permission denied" in resp.json().get("detail", "")

    def test_owner_enforcement_allows_admin_override(
        self, auth_client, db_fixture
    ):
        """53. Admin user can update dossier owned by another role (admin bypass)."""
        template_payload = _make_valid_template_payload("_owner_test_admin")
        resp = auth_client.post(TEMPLATES_PREFIX, json=template_payload)
        assert resp.status_code == 201
        template_id = resp.json()["id"]

        # Create dossier with explicit owner_role='designer'
        dossier_payload = {
            "template_id": template_id,
            "template_code": f"OWN_ADM_{template_id}",
            "status": "draft",
            "owner_role": "designer",
        }
        resp = auth_client.post(API_PREFIX, json=dossier_payload)
        assert resp.status_code == 201
        did = resp.json()["id"]

        # Admin can update despite not being 'designer'
        resp = auth_client.put(
            f"{API_PREFIX}/{did}", json={"status": "needs_review"}
        )
        assert resp.status_code == 200, (
            f"Expected 200 for admin override, got {resp.status_code}: {resp.text}"
        )

    def test_owner_enforcement_allows_matching_role(
        self, db_fixture
    ):
        """54. User with matching owner_role can update their own dossier.

        BUILD 24: Changed from 'designer' (unknown role → viewer → 403 at
        permission layer) to 'manager' which has dossier.* permissions AND
        matches the owner_role set on the dossier.
        """
        from fastapi.testclient import TestClient as _TestClient
        from main import app
        from core.database import get_db
        from dependencies.auth import get_current_user
        from schemas.auth import UserResponse

        async def _override_get_db():
            async with db_fixture.session_maker() as session:
                yield session

        async def _override_get_current_user():
            return UserResponse(
                id="manager-owner-id",
                email="manager-owner@example.com",
                name="Test Manager Owner",
                role="manager",
                last_login=None,
            )

        app.dependency_overrides[get_db] = _override_get_db
        app.dependency_overrides[get_current_user] = _override_get_current_user

        with _TestClient(app, raise_server_exceptions=False) as manager_client:
            # First create template and dossier with this client
            template_payload = _make_valid_template_payload("_owner_test_match")
            resp = manager_client.post(TEMPLATES_PREFIX, json=template_payload)
            assert resp.status_code == 201
            template_id = resp.json()["id"]

            dossier_payload = {
                "template_id": template_id,
                "template_code": f"OWN_MATCH_{template_id}",
                "status": "draft",
                "owner_role": "manager",
            }
            resp = manager_client.post(API_PREFIX, json=dossier_payload)
            assert resp.status_code == 201
            did = resp.json()["id"]

            # Manager can update their own dossier (role matches owner_role)
            resp = manager_client.put(
                f"{API_PREFIX}/{did}", json={"status": "needs_review"}
            )
            assert resp.status_code == 200, (
                f"Expected 200 for matching role, got {resp.status_code}: {resp.text}"
            )

        app.dependency_overrides.clear()

    def test_check_owner_permission_unit(self):
        """55. Unit test for check_owner_permission function — all paths."""
        from services.product_blueprint_dossier_service import check_owner_permission

        class FakeDossier:
            def __init__(self, owner_role):
                self.owner_role = owner_role

        # Path 1: No user_role — permissive fallback
        assert check_owner_permission(FakeDossier("designer"), None) is None

        # Path 2: No owner on dossier — anyone can write
        assert check_owner_permission(FakeDossier(None), "operator") is None
        assert check_owner_permission(FakeDossier(""), "operator") is None

        # Path 3: Admin bypasses
        assert check_owner_permission(FakeDossier("designer"), "admin") is None

        # Path 4: Matching role — allowed
        assert check_owner_permission(FakeDossier("designer"), "designer") is None

        # Path 5: Mismatched role — REJECTED
        result = check_owner_permission(FakeDossier("designer"), "operator")
        assert result is not None
        assert "Permission denied" in result
        assert "designer" in result
        assert "operator" in result

        # Path 6: Another mismatch
        result = check_owner_permission(FakeDossier("manager"), "designer")
        assert result is not None
        assert "Permission denied" in result


# ============================================================
# Phase B — product_templates Regression Test
# ============================================================


class TestProductTemplatesRegression:
    """Verify product_templates CRUD still works after FK addition."""

    def test_create_and_get_template(self, auth_client):
        """48. product_templates CRUD still works unchanged."""
        payload = _make_valid_template_payload("_regression")
        resp = auth_client.post(TEMPLATES_PREFIX, json=payload)
        assert resp.status_code == 201, f"Template create failed: {resp.text}"
        template_id = resp.json()["id"]

        resp2 = auth_client.get(f"{TEMPLATES_PREFIX}/{template_id}")
        assert resp2.status_code == 200
        assert resp2.json()["id"] == template_id

    def test_template_list_works(self, auth_client):
        """49. product_templates list endpoint still works."""
        resp = auth_client.get(TEMPLATES_PREFIX)
        assert resp.status_code == 200


# ============================================================
# Phase B — Router Accessibility Test
# ============================================================


class TestDossierRouterAccessibility:
    """Verify router is accessible and responds correctly."""

    def test_router_responds(self, auth_client):
        """50. Dossier router responds to GET request."""
        resp = auth_client.get(API_PREFIX)
        assert resp.status_code == 200