"""W0-B2 Documentation Index — Hybrid allowlisted read model (read-only).

Canonical docs remain in Git. Registry membership ≠ canonical architecture.
Display labels never replace technical document_id values.
"""

from __future__ import annotations

import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote

from schemas.documentation_index import (
    DOCUMENTATION_INDEX_VERSION,
    DocumentationFreshness,
    DocumentationIndexDetail,
    DocumentationIndexListItem,
    DocumentationIndexListResponse,
    document_to_list_item,
)
from schemas.truth_metadata import (
    TRUTH_METADATA_VERSION,
    DocumentReference,
    DriftStatus,
    VisibilityClass,
)
from schemas.truth_metadata.enums import DocumentAuthority, DocumentCategory
from schemas.truth_metadata.references import DisplayMetadata, normalize_repo_path

logger = logging.getLogger(__name__)

_SERVICE_FILE = Path(__file__).resolve()
_BACKEND_DIR = _SERVICE_FILE.parent.parent
_REPO_ROOT = _BACKEND_DIR.parent
_DEFAULT_REGISTRY = _BACKEND_DIR / "config" / "document_index_registry.json"

# Max Markdown body size for optional content (bytes).
_MAX_CONTENT_BYTES = 512_000

# Roles → visibility classes exposed via API (admin path).
_ADMIN_VISIBLE: frozenset[VisibilityClass] = frozenset(
    {
        VisibilityClass.OPERATOR_SAFE,
        VisibilityClass.ADMIN_ONLY,
        VisibilityClass.INTERNAL_TECHNICAL,
    }
)

# Never returned through public documentation APIs.
_API_HIDDEN: frozenset[VisibilityClass] = frozenset(
    {
        VisibilityClass.HIDDEN_FROM_UI,
        VisibilityClass.RESTRICTED,
        VisibilityClass.OWNER_ONLY,  # no dedicated owner role yet — withhold
    }
)


class DocumentationIndexError(Exception):
    """Base error for documentation index."""


class DocumentationIndexPathError(DocumentationIndexError):
    """Unsafe or disallowed path."""


class DocumentationIndexNotFoundError(DocumentationIndexError):
    """Unknown or not visible document_id."""


class DocumentationIndexConfigError(DocumentationIndexError):
    """Invalid registry configuration."""


def resolve_repo_root(explicit: Path | None = None) -> Path:
    return (explicit or _REPO_ROOT).resolve()


def is_path_allowlisted(
    relative_path: str,
    *,
    prefixes: Iterable[str],
    exact_paths: Iterable[str],
    allowed_extensions: Iterable[str],
    excluded_substrings: Iterable[str],
) -> bool:
    """Return True if relative_path is within the controlled allowlist."""
    norm = normalize_repo_path(relative_path)
    lower = norm.lower()
    for bad in excluded_substrings:
        if bad.lower() in lower:
            return False
    ext_ok = any(lower.endswith(ext.lower()) for ext in allowed_extensions)
    if not ext_ok:
        return False
    exact = {normalize_repo_path(p) for p in exact_paths}
    if norm in exact:
        return True
    for prefix in prefixes:
        p = prefix.replace("\\", "/").lstrip("/")
        if not p.endswith("/"):
            p = p + "/"
        if norm.startswith(p) or norm + "/" == p:
            return True
    return False


def assert_safe_resolved_path(repo_root: Path, relative_path: str) -> Path:
    """Normalize, resolve, and ensure path stays under repo_root."""
    # Reject obvious traversal / absolute forms before normalize.
    raw = relative_path.strip()
    decoded = unquote(raw)
    if decoded != raw and (".." in decoded or decoded.startswith(("/", "\\"))):
        raise DocumentationIndexPathError("encoded path traversal is not allowed")
    if ".." in raw.replace("\\", "/").split("/"):
        raise DocumentationIndexPathError("path traversal is not allowed")
    if raw.startswith(("/", "\\")) or (len(raw) >= 2 and raw[1] == ":"):
        raise DocumentationIndexPathError("absolute paths are not allowed")
    if raw.startswith("\\\\") or raw.startswith("//"):
        raise DocumentationIndexPathError("UNC paths are not allowed")

    norm = normalize_repo_path(raw)
    candidate = (repo_root / norm).resolve()
    root = repo_root.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise DocumentationIndexPathError("resolved path escapes repository root") from exc
    return candidate


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    return datetime.fromisoformat(text)


def _git_last_changed(repo_root: Path, relative_path: str) -> datetime | None:
    try:
        proc = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", relative_path],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if proc.returncode != 0:
            return None
        line = (proc.stdout or "").strip().splitlines()
        if not line:
            return None
        return _parse_iso(line[0])
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def _filesystem_mtime(path: Path) -> datetime | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except OSError:
        return None


def compute_validation_status(
    *,
    last_validated_at: datetime | None,
    drift_status: DriftStatus,
) -> str:
    if drift_status == DriftStatus.DOCUMENTATION_DRIFT:
        return "STALE_HINT"
    if last_validated_at is None:
        return "UNKNOWN"
    return "VALIDATED"


class DocumentationIndexService:
    """Load controlled registry, verify on-disk files, expose list/detail."""

    def __init__(
        self,
        *,
        repo_root: Path | None = None,
        registry_path: Path | None = None,
    ) -> None:
        self.repo_root = resolve_repo_root(repo_root)
        self.registry_path = registry_path or _DEFAULT_REGISTRY
        self._raw: dict = {}
        self._docs: dict[str, DocumentReference] = {}
        self._reasons: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if not self.registry_path.is_file():
            raise DocumentationIndexConfigError(f"registry missing: {self.registry_path}")
        data = json.loads(self.registry_path.read_text(encoding="utf-8"))
        if data.get("metadata_version") != TRUTH_METADATA_VERSION:
            raise DocumentationIndexConfigError("unsupported registry metadata_version")
        if data.get("index_version") != DOCUMENTATION_INDEX_VERSION:
            raise DocumentationIndexConfigError("unsupported index_version")

        prefixes = list(data.get("allowlisted_prefixes") or [])
        exact = list(data.get("allowlisted_exact_paths") or [])
        extensions = list(data.get("allowed_extensions") or [".md"])
        excluded = list(data.get("excluded_name_substrings") or [])

        seen_ids: set[str] = set()
        docs: dict[str, DocumentReference] = {}
        reasons: dict[str, str] = {}

        for entry in data.get("entries") or []:
            doc_id = entry["document_id"]
            if doc_id in seen_ids:
                raise DocumentationIndexConfigError(f"duplicate document_id: {doc_id}")
            seen_ids.add(doc_id)

            path = entry["path"]
            if not is_path_allowlisted(
                path,
                prefixes=prefixes,
                exact_paths=exact,
                allowed_extensions=extensions,
                excluded_substrings=excluded,
            ):
                raise DocumentationIndexConfigError(
                    f"entry path not allowlisted: {path} ({doc_id})"
                )
            # Path safety (no traversal)
            assert_safe_resolved_path(self.repo_root, path)

            display_raw = entry.get("display")
            display = DisplayMetadata.model_validate(display_raw) if display_raw else None

            doc = DocumentReference(
                document_id=doc_id,
                title=entry["title"],
                path=normalize_repo_path(path),
                category=DocumentCategory(entry["category"]),
                authority=DocumentAuthority(entry["authority"]),
                status=DocumentAuthority(entry["status"]),
                owner=entry.get("owner"),
                last_validated_at=_parse_iso(entry.get("last_validated_at")),
                supersedes=list(entry.get("supersedes") or []),
                superseded_by=entry.get("superseded_by"),
                systems=list(entry.get("systems") or []),
                pages=list(entry.get("pages") or []),
                routes=list(entry.get("routes") or []),
                contracts=list(entry.get("contracts") or []),
                code_refs=list(entry.get("code_refs") or []),
                api_refs=list(entry.get("api_refs") or []),
                test_refs=list(entry.get("test_refs") or []),
                qa_refs=list(entry.get("qa_refs") or []),
                worklog_refs=list(entry.get("worklog_refs") or []),
                runtime_refs=list(entry.get("runtime_refs") or []),
                drift_status=DriftStatus(entry.get("drift_status") or "NOT_VALIDATED"),
                visibility_class=VisibilityClass(entry["visibility_class"]),
                display=display,
            )
            # Authority safety: never invent CANONICAL from path — already explicit in entry.
            docs[doc_id] = doc
            reasons[doc_id] = entry.get("reason_for_inclusion") or ""

        self._raw = data
        self._docs = docs
        self._reasons = reasons
        self._prefixes = prefixes
        self._exact = exact
        self._extensions = extensions
        self._excluded = excluded

    @property
    def document_ids(self) -> list[str]:
        return sorted(self._docs.keys())

    def visible_for_admin(self, doc: DocumentReference) -> bool:
        if doc.visibility_class in _API_HIDDEN:
            return False
        return doc.visibility_class in _ADMIN_VISIBLE

    def list_documents(
        self,
        *,
        category: str | None = None,
        status: str | None = None,
        authority: str | None = None,
        system: str | None = None,
        page: str | None = None,
        visibility: str | None = None,
        stale_only: bool = False,
        owner_review_required: bool = False,
        admin_view: bool = True,
    ) -> DocumentationIndexListResponse:
        items: list[DocumentationIndexListItem] = []
        for doc in self._docs.values():
            if admin_view and not self.visible_for_admin(doc):
                continue
            if not admin_view and doc.visibility_class != VisibilityClass.OPERATOR_SAFE:
                continue
            if category and str(doc.category) != category:
                continue
            if status and str(doc.status) != status:
                continue
            if authority and str(doc.authority) != authority:
                continue
            if system and system not in doc.systems:
                continue
            if page and page not in doc.pages:
                continue
            if visibility and str(doc.visibility_class) != visibility:
                continue
            if owner_review_required and doc.status != DocumentAuthority.OWNER_REVIEW_REQUIRED:
                continue
            if stale_only:
                hint = compute_validation_status(
                    last_validated_at=doc.last_validated_at,
                    drift_status=doc.drift_status,
                )
                if hint not in ("STALE_HINT", "UNKNOWN") and doc.drift_status != DriftStatus.DOCUMENTATION_DRIFT:
                    continue
            items.append(document_to_list_item(doc))

        items.sort(key=lambda i: i.document_id)
        return DocumentationIndexListResponse(count=len(items), items=items)

    def get_document(
        self,
        document_id: str,
        *,
        include_content: bool = False,
        admin_view: bool = True,
    ) -> DocumentationIndexDetail:
        # Reject path-like IDs (no filesystem browser)
        if "/" in document_id or "\\" in document_id or ".." in document_id:
            raise DocumentationIndexPathError("document_id must not be a filesystem path")
        doc = self._docs.get(document_id)
        if doc is None:
            raise DocumentationIndexNotFoundError(document_id)
        if admin_view and not self.visible_for_admin(doc):
            raise DocumentationIndexNotFoundError(document_id)
        if not admin_view and doc.visibility_class != VisibilityClass.OPERATOR_SAFE:
            raise DocumentationIndexNotFoundError(document_id)

        abs_path = assert_safe_resolved_path(self.repo_root, doc.path)
        exists = abs_path.is_file()
        mtime = _filesystem_mtime(abs_path) if exists else None
        git_changed = _git_last_changed(self.repo_root, doc.path) if exists else None
        validation_status = compute_validation_status(
            last_validated_at=doc.last_validated_at,
            drift_status=doc.drift_status,
        )
        content: str | None = None
        if include_content and exists:
            content = self._read_markdown(abs_path)

        # Ensure technical_id stays document_id even if display label differs
        assert doc.document_id == document_id

        return DocumentationIndexDetail(
            document=doc,
            technical_id=doc.document_id,
            reason_for_inclusion=self._reasons.get(document_id),
            freshness=DocumentationFreshness(
                filesystem_mtime=mtime,
                git_last_changed_at=git_changed,
                last_validated_at=doc.last_validated_at,
                validation_status=validation_status,
            ),
            file_exists=exists,
            content_markdown=content,
        )

    def _read_markdown(self, path: Path) -> str:
        if path.suffix.lower() != ".md":
            raise DocumentationIndexPathError("only Markdown content is supported")
        data = path.read_bytes()
        if len(data) > _MAX_CONTENT_BYTES:
            raise DocumentationIndexPathError("document exceeds content size limit")
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DocumentationIndexPathError("document is not valid UTF-8") from exc

    def reject_arbitrary_path_lookup(self, raw_path: str) -> None:
        """Helper for tests / API guards — never accept path as lookup key."""
        raise DocumentationIndexPathError(
            f"arbitrary path lookup forbidden: {raw_path!r}; use document_id"
        )
