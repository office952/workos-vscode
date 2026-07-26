"""W0-B2 Documentation Index — unit and API tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from schemas.documentation_index import document_to_list_item
from schemas.truth_metadata import DocumentReference, VisibilityClass
from schemas.truth_metadata.enums import DocumentAuthority, DocumentCategory, DriftStatus
from services.documentation_index_service import (
    DocumentationIndexConfigError,
    DocumentationIndexNotFoundError,
    DocumentationIndexPathError,
    DocumentationIndexService,
    assert_safe_resolved_path,
    is_path_allowlisted,
    resolve_repo_root,
)

REPO = resolve_repo_root()
REGISTRY = REPO / "backend" / "config" / "document_index_registry.json"


@pytest.fixture
def svc() -> DocumentationIndexService:
    return DocumentationIndexService(repo_root=REPO, registry_path=REGISTRY)


def test_registry_loads_and_lists(svc: DocumentationIndexService):
    resp = svc.list_documents(admin_view=True)
    assert resp.count >= 5
    ids = {i.document_id for i in resp.items}
    assert "workos-truth-metadata-contract" in ids
    assert "workos-page-completion-foundation" in ids


def test_allowlisted_discovery_and_exclusions():
    prefixes = ["docs/architecture/"]
    exact = ["AGENTS.md"]
    ext = [".md"]
    excl = [".env", "secret"]
    assert is_path_allowlisted(
        "docs/architecture/WORKOS_TRUTH_METADATA_CONTRACT.md",
        prefixes=prefixes,
        exact_paths=exact,
        allowed_extensions=ext,
        excluded_substrings=excl,
    )
    assert is_path_allowlisted(
        "AGENTS.md",
        prefixes=prefixes,
        exact_paths=exact,
        allowed_extensions=ext,
        excluded_substrings=excl,
    )
    assert not is_path_allowlisted(
        "backend/main.py",
        prefixes=prefixes,
        exact_paths=exact,
        allowed_extensions=ext,
        excluded_substrings=excl,
    )
    assert not is_path_allowlisted(
        "docs/architecture/foo.env.md",
        prefixes=prefixes,
        exact_paths=exact,
        allowed_extensions=ext,
        excluded_substrings=excl,
    )


def test_path_traversal_rejected():
    with pytest.raises(DocumentationIndexPathError):
        assert_safe_resolved_path(REPO, "../secret.md")
    with pytest.raises(DocumentationIndexPathError):
        assert_safe_resolved_path(REPO, "/etc/passwd")
    with pytest.raises((DocumentationIndexPathError, ValueError)):
        assert_safe_resolved_path(REPO, "C:/Windows/system32/x.md")
    with pytest.raises(DocumentationIndexPathError):
        assert_safe_resolved_path(REPO, "docs/%2e%2e/secret.md")


def test_duplicate_document_id_rejected(tmp_path: Path):
    raw = json.loads(REGISTRY.read_text(encoding="utf-8"))
    entry = dict(raw["entries"][0])
    entry["document_id"] = raw["entries"][0]["document_id"]
    raw["entries"].append(entry)
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(DocumentationIndexConfigError, match="duplicate"):
        DocumentationIndexService(repo_root=REPO, registry_path=bad)


def test_authority_not_inferred_from_directory(svc: DocumentationIndexService):
    detail = svc.get_document("workos-canonical-documentation-authority-policy")
    # In docs/architecture but explicitly OWNER_REVIEW_REQUIRED — not auto-canonical
    assert detail.document.authority == DocumentAuthority.OWNER_REVIEW_REQUIRED
    assert detail.document.authority != DocumentAuthority.CANONICAL_CURRENT


def test_no_automatic_canonical_from_recent(svc: DocumentationIndexService):
    for item in svc.list_documents().items:
        # Corpus must not invent CANONICAL_CURRENT without explicit registry value
        if item.authority == "CANONICAL_CURRENT":
            pytest.fail("unexpected automatic CANONICAL_CURRENT in corpus")


def test_visibility_hides_owner_only(tmp_path: Path):
    raw = json.loads(REGISTRY.read_text(encoding="utf-8"))
    raw["entries"] = [
        {
            "document_id": "hidden-owner-doc",
            "title": "Hidden",
            "path": "docs/architecture/WORKOS_TRUTH_METADATA_CONTRACT.md",
            "category": "CONTRACTS",
            "authority": "SUPPORTING_CURRENT",
            "status": "SUPPORTING_CURRENT",
            "visibility_class": "OWNER_ONLY",
            "drift_status": "NOT_VALIDATED",
            "systems": [],
            "pages": [],
            "routes": [],
            "contracts": [],
            "reason_for_inclusion": "visibility test",
            "display": {
                "display_label_ro": "Ascuns",
                "technical_alias": "Hidden",
                "translation_key": "docs.hidden.title",
            },
        }
    ]
    reg = tmp_path / "reg.json"
    reg.write_text(json.dumps(raw), encoding="utf-8")
    svc = DocumentationIndexService(repo_root=REPO, registry_path=reg)
    assert svc.list_documents(admin_view=True).count == 0
    with pytest.raises(DocumentationIndexNotFoundError):
        svc.get_document("hidden-owner-doc", admin_view=True)


def test_technical_id_not_replaced_by_display(svc: DocumentationIndexService):
    detail = svc.get_document("workos-ui-terminology-registry")
    assert detail.technical_id == "workos-ui-terminology-registry"
    assert detail.document.document_id == detail.technical_id
    assert detail.document.display is not None
    assert detail.document.display.display_label_ro != detail.technical_id
    item = document_to_list_item(detail.document)
    assert item.technical_id == item.document_id
    dumped = item.model_dump()
    assert dumped["technical_id"] == "workos-ui-terminology-registry"
    assert dumped["document_id"] == "workos-ui-terminology-registry"


def test_relationships_and_supersession_fields(svc: DocumentationIndexService):
    detail = svc.get_document("commercial-preview-boundary-contract")
    assert "pricing" in detail.document.systems
    assert "/inventory/pricing" in detail.document.routes
    assert detail.document.superseded_by is None


def test_freshness_separated_from_validation(svc: DocumentationIndexService):
    detail = svc.get_document("workos-truth-metadata-contract", include_content=False)
    assert detail.file_exists is True
    assert detail.freshness.validation_status in ("VALIDATED", "UNKNOWN", "STALE_HINT")
    # mtime may exist but must not equal validation proof automatically
    if detail.freshness.filesystem_mtime and detail.freshness.last_validated_at:
        # They are independent fields — both present is fine
        assert detail.freshness.filesystem_mtime != detail.document.authority


def test_path_like_document_id_rejected(svc: DocumentationIndexService):
    with pytest.raises(DocumentationIndexPathError):
        svc.get_document("docs/architecture/foo.md")


def test_detail_optional_content(svc: DocumentationIndexService):
    detail = svc.get_document("workos-truth-metadata-contract", include_content=True)
    assert detail.content_markdown is not None
    assert "Truth Metadata" in detail.content_markdown


def test_api_viewer_forbidden():
    from dependencies.auth import get_current_user
    from main import app
    from schemas.auth import UserResponse

    async def _viewer():
        return UserResponse(
            id="viewer-1",
            email="viewer@test.local",
            name="Viewer",
            role="viewer",
        )

    app.dependency_overrides[get_current_user] = _viewer
    try:
        client = TestClient(app)
        r = client.get("/api/v1/system/documentation")
        assert r.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_api_list_and_detail_with_admin():
    from dependencies.auth import get_current_user
    from main import app
    from schemas.auth import UserResponse

    async def _admin():
        return UserResponse(
            id="admin-1",
            email="admin@test.local",
            name="Admin",
            role="admin",
        )

    app.dependency_overrides[get_current_user] = _admin
    try:
        client = TestClient(app)
        r = client.get("/api/v1/system/documentation")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["count"] >= 1
        assert body["index_version"] == "workos_documentation_index/v1"
        doc_id = body["items"][0]["document_id"]
        assert body["items"][0]["technical_id"] == doc_id

        d = client.get(f"/api/v1/system/documentation/{doc_id}")
        assert d.status_code == 200
        detail = d.json()
        assert detail["technical_id"] == doc_id
        assert detail["document"]["document_id"] == doc_id

        missing = client.get("/api/v1/system/documentation/does-not-exist-xyz")
        assert missing.status_code == 404

        bad = client.get("/api/v1/system/documentation/docs%2Farchitecture%2Ffoo.md")
        assert bad.status_code in (400, 404)
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_permission_matrix_has_documentation_read():
    from dependencies.permissions import PERMISSION_MATRIX, has_permission

    assert "system.documentation_read" in PERMISSION_MATRIX
    assert has_permission("admin", "system.documentation_read")
    assert not has_permission("viewer", "system.documentation_read")
