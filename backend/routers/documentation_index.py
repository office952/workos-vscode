"""W0-B2 — Read-only documentation index API (admin).

GET-only. document_id lookup only — never arbitrary filesystem paths.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from dependencies.permissions import require_permission
from schemas.auth import UserResponse
from schemas.documentation_index import DocumentationIndexDetail, DocumentationIndexListResponse
from services.documentation_index_service import (
    DocumentationIndexNotFoundError,
    DocumentationIndexPathError,
    DocumentationIndexService,
)

router = APIRouter(
    prefix="/api/v1/system/documentation",
    tags=["system-documentation"],
)


def _service() -> DocumentationIndexService:
    return DocumentationIndexService()


@router.get(
    "",
    response_model=DocumentationIndexListResponse,
)
async def list_documentation_index(
    category: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    authority: str | None = Query(default=None),
    system: str | None = Query(default=None),
    page: str | None = Query(default=None),
    visibility: str | None = Query(default=None),
    stale_only: bool = Query(default=False),
    owner_review_required: bool = Query(default=False),
    _user: UserResponse = Depends(require_permission("system.documentation_read")),
) -> DocumentationIndexListResponse:
    """List allowlisted documentation metadata (read-only)."""
    svc = _service()
    return svc.list_documents(
        category=category,
        status=status_filter,
        authority=authority,
        system=system,
        page=page,
        visibility=visibility,
        stale_only=stale_only,
        owner_review_required=owner_review_required,
        admin_view=True,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentationIndexDetail,
)
async def get_documentation_index_item(
    document_id: str,
    include_content: bool = Query(default=False),
    _user: UserResponse = Depends(require_permission("system.documentation_read")),
) -> DocumentationIndexDetail:
    """Return metadata (and optional Markdown body) for one document_id."""
    svc = _service()
    try:
        return svc.get_document(
            document_id,
            include_content=include_content,
            admin_view=True,
        )
    except DocumentationIndexPathError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except DocumentationIndexNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="document not found",
        ) from None
