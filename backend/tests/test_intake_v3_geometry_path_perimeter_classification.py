"""Intake V3 geometry path perimeter classification — role-based, no invented perimeters."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import func, select

from models.execution_plan import ExecutionPlan
from models.orders import Orders
from models.quotes import Quotes
from models.stock_movements import StockMovement
from services.intake_v3_geometry_path_perimeter_classification_service import (
    PATH_PERIMETER_CLASSIFICATION_VERSION,
    classify_geometry_path_perimeters,
    normalize_svg_layer_role,
)
from tests.test_intake_v3_quote_pricing_review_completion import _create_iv3_draft_quote
from tests.test_intake_v3_real_commercial_quote_creation import _seed_hub_workspace
from tests.test_intake_v3_svg_upload_analysis import _upload_svg

LITERE_LAYER_SVG = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50" width="100mm" height="50mm">
  <g id="LITERE"><path d="M10 40 L20 10 L30 40 Z"/></g>
</svg>"""

LAYERED_SVG = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50" width="100mm" height="50mm">
  <g id="LITERE"><path d="M10 40 L20 10 L30 40 Z"/></g>
  <g id="SPATE"><path d="M5 5 L95 5 L95 45 L5 45 Z"/></g>
  <g id="GOLURI"><path d="M15 20 L25 20 L25 30 L15 30 Z"/></g>
  <g id="CANT"><path d="M0 0 L10 0 L10 10 L0 10 Z"/></g>
</svg>"""


def _seed_and_upload(auth_client, svg_text: str) -> str:
    workspace_id = _seed_hub_workspace(auth_client)
    upload = _upload_svg(auth_client, workspace_id, "layers.svg", svg_text)
    assert upload.status_code == 200, upload.text
    return workspace_id


class TestPathPerimeterClassificationSafeResponses:
    @pytest.mark.asyncio
    async def test_missing_workspace_returns_not_found(self, auth_client, db_session):
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        response = auth_client.get(
            "/api/v1/intake-v3/workspaces/999999/geometry-path-perimeter-classification",
        )
        assert response.status_code == 404
        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        assert plans_after == plans_before

    @pytest.mark.asyncio
    async def test_missing_quote_returns_not_found(self, auth_client):
        response = auth_client.get("/api/v1/intake-v3/quotes/999999/geometry-path-perimeter-classification")
        assert response.status_code == 404


class TestPathPerimeterClassificationNonIv3:
    @pytest.mark.asyncio
    async def test_non_iv3_order_safe_response(self, auth_client, db_session):
        order = Orders(
            code="ORD-NON-IV3-PPC",
            client_name="Normal",
            status="locked",
            payment_status="pending",
            total_amount=100.0,
            notes=json.dumps({"human_summary": "normal order"}),
            snapshot_line_items=json.dumps({"source": "manual"}),
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        response = auth_client.get(
            f"/api/v1/intake-v3/orders/{order.id}/geometry-path-perimeter-classification",
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["is_intake_v3"] is False
        assert payload["creates_execution_tasks"] is False
        assert payload["mutates_inventory"] is False
        assert payload["costengine_used"] is False


class TestPathPerimeterClassificationMissingSource:
    @pytest.mark.asyncio
    async def test_no_path_metrics_means_missing(self, auth_client):
        workspace_id = _seed_hub_workspace(auth_client)
        patch = auth_client.patch(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/fields",
            json={"patches": [{"path": "path_geometry_summary", "value": None}]},
        )
        if patch.status_code != 200:
            pytest.skip("Workspace field patch for path_geometry_summary unavailable")
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/geometry-path-perimeter-classification",
        )
        assert response.status_code == 200
        payload = response.json()
        classification = payload["path_perimeter_classification"]
        assert classification["classification_status"] == "missing"
        assert classification["perimeters"]["face_cutting_perimeter_ml"]["value"] is None
        codes = [item["code"] for item in classification["warnings"]]
        assert "path_geometry_summary_missing" in codes


class TestPathPerimeterClassificationRules:
    def test_layer_role_mapping_classifies_face(self):
        path_summary = {
            "parse_status": "parsed",
            "layers": [
                {"layer_id": "LITERE", "layer_name": "LITERE", "perimeter_mm": 1200.0, "closed_contour_count": 1},
            ],
            "contour_split": {"split_quality": "missing"},
        }
        result = classify_geometry_path_perimeters(
            workspace=None,
            sections={},
            path_summary=path_summary,
            confirmed=None,
        )
        face = result["perimeters"]["face_cutting_perimeter_ml"]
        assert face["value"] == pytest.approx(1.2, rel=1e-3)
        assert face["quality"] in {"medium", "high"}
        assert "layer_role_mapping" in (face["source"] or "")

    def test_backing_not_invented_without_layer(self):
        path_summary = {
            "parse_status": "parsed",
            "layers": [
                {"layer_id": "LITERE", "layer_name": "LITERE", "perimeter_mm": 500.0, "closed_contour_count": 1},
            ],
            "contour_split": {"split_quality": "missing"},
        }
        result = classify_geometry_path_perimeters(
            workspace=None,
            sections={},
            path_summary=path_summary,
            confirmed=None,
        )
        assert result["perimeters"]["backing_cutting_perimeter_ml"]["value"] is None
        codes = [item["code"] for item in result["warnings"]]
        assert "backing_perimeter_missing" in codes

    def test_return_not_invented_without_layer(self):
        path_summary = {
            "parse_status": "parsed",
            "layers": [
                {"layer_id": "LITERE", "layer_name": "LITERE", "perimeter_mm": 500.0, "closed_contour_count": 1},
                {"layer_id": "SPATE", "layer_name": "SPATE", "perimeter_mm": 800.0, "closed_contour_count": 1},
            ],
            "contour_split": {"split_quality": "missing"},
        }
        result = classify_geometry_path_perimeters(
            workspace=None,
            sections={},
            path_summary=path_summary,
            confirmed=None,
        )
        assert result["perimeters"]["return_material_perimeter_ml"]["value"] is None
        assert "return_perimeter_missing" in [item["code"] for item in result["warnings"]]

    def test_bevel_not_assumed_equal_face(self):
        path_summary = {
            "parse_status": "parsed",
            "layers": [
                {"layer_id": "LITERE", "layer_name": "LITERE", "perimeter_mm": 500.0, "closed_contour_count": 1},
            ],
            "contour_split": {"split_quality": "missing"},
        }
        result = classify_geometry_path_perimeters(
            workspace=None,
            sections={},
            path_summary=path_summary,
            confirmed=None,
        )
        assert result["perimeters"]["bevel_perimeter_ml"]["value"] is None
        assert "bevel_perimeter_missing" in [item["code"] for item in result["warnings"]]

    def test_holes_not_letters_roles(self):
        assert normalize_svg_layer_role("GOLURI") == "inner_hole"
        assert normalize_svg_layer_role("LITERE") in {"face", "letters"}


class TestPathPerimeterClassificationIntegration:
    @pytest.mark.asyncio
    async def test_layered_svg_classifies_face_and_inner(self, auth_client):
        workspace_id = _seed_and_upload(auth_client, LAYERED_SVG)
        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/geometry-path-perimeter-classification",
        )
        assert response.status_code == 200, response.text
        classification = response.json()["path_perimeter_classification"]
        assert classification["schema_version"] == PATH_PERIMETER_CLASSIFICATION_VERSION
        assert classification["perimeters"]["face_cutting_perimeter_ml"]["value"] is not None
        assert classification["perimeters"]["backing_cutting_perimeter_ml"]["value"] is not None
        assert classification["perimeters"]["return_material_perimeter_ml"]["value"] is not None
        roles = {layer["normalized_role"] for layer in classification["classified_layers"]}
        assert "inner_hole" in roles

    @pytest.mark.asyncio
    async def test_geometry_snapshot_merge_preserves_classification(self, auth_client):
        workspace_id = _seed_and_upload(auth_client, LITERE_LAYER_SVG)
        response = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/geometry-metrics-snapshot")
        snapshot = response.json()["snapshot"]
        assert snapshot["path_perimeter_classification"] is not None
        assert snapshot["path_perimeter_classification"]["schema_version"] == PATH_PERIMETER_CLASSIFICATION_VERSION
        assert snapshot["counts"]["real_letter_count"] >= 0

    @pytest.mark.asyncio
    async def test_material_breakdown_consumes_classification(self, auth_client):
        workspace_id, quote_id, _ = _create_iv3_draft_quote(auth_client)
        _upload_svg(auth_client, workspace_id, "litere.svg", LITERE_LAYER_SVG)
        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/material-breakdown")
        assert response.status_code == 200
        geometry = response.json()["geometry_summary"]
        assert geometry.get("perimeter_classification_status") in {"partial", "complete", "missing"}
        assert response.json()["costengine_used"] is False

    @pytest.mark.asyncio
    async def test_task_dry_run_consumes_classification(self, auth_client):
        workspace_id, quote_id, _ = _create_iv3_draft_quote(auth_client)
        _upload_svg(auth_client, workspace_id, "litere.svg", LITERE_LAYER_SVG)
        response = auth_client.get(f"/api/v1/intake-v3/quotes/{quote_id}/production-task-dry-run")
        assert response.status_code == 200
        payload = response.json()
        assert payload["creates_execution_tasks"] is False
        assert payload["costengine_used"] is False
        labels = [
            entry["label"]
            for task in payload["candidate_tasks"]
            for entry in task["inputs_preview"]
        ]
        assert "Face cutting perimeter" in labels

    @pytest.mark.asyncio
    async def test_production_readiness_reports_classification(self, auth_client, db_session):
        from tests.test_intake_v3_geometry_metrics_snapshot import _prepare_converted_iv3_order

        order_id, _, _, _ = _prepare_converted_iv3_order(auth_client)
        response = auth_client.get(f"/api/v1/intake-v3/orders/{order_id}/production-readiness")
        assert response.status_code == 200
        available = response.json()["available_data"]
        assert available["perimeter_classification_status"] in {"partial", "complete", "missing", None}


class TestPathPerimeterClassificationNoSideEffects:
    @pytest.mark.asyncio
    async def test_get_does_not_create_execution_or_inventory(self, auth_client, db_session):
        workspace_id = _seed_and_upload(auth_client, LITERE_LAYER_SVG)
        plans_before = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        stock_before = await db_session.scalar(select(func.count()).select_from(StockMovement))
        quotes_before = await db_session.scalar(select(func.count()).select_from(Quotes))

        response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/geometry-path-perimeter-classification",
        )
        assert response.status_code == 200

        plans_after = await db_session.scalar(select(func.count()).select_from(ExecutionPlan))
        stock_after = await db_session.scalar(select(func.count()).select_from(StockMovement))
        quotes_after = await db_session.scalar(select(func.count()).select_from(Quotes))
        assert plans_after == plans_before
        assert stock_after == stock_before
        assert quotes_after == quotes_before
