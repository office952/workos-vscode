"""Service layer for ProductBlueprintDossier CRUD operations.

Phase A — Product Blueprint Dossier Foundation.
Phase B — Hardening (delete policy, status transitions, version increment,
          semantic validation, owner enforcement).

This service provides CRUD for the product_blueprint_dossier table with:
  - Delete policy: hard delete only for draft/deprecated; 409 for protected statuses
  - Status transition enforcement per hardening decision §10
  - Version auto-increment on approval transition; decrement blocked
  - Progressive semantic JSON validation for 6 priority sections
  - Owner role enforcement on write operations (permissive fallback)

This service does NOT calculate cost, create offers, create orders, create tasks,
modify stock, or rewrite snapshots.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.product_blueprint_dossier import ProductBlueprintDossier
from services.dossier_validation_models import validate_semantic_json_for_status

logger = logging.getLogger(__name__)

# --- Allowed status values for dossier lifecycle ---
ALLOWED_DOSSIER_STATUSES = {"draft", "needs_review", "approved", "blocked", "deprecated"}

# --- Allowed section completion states ---
ALLOWED_SECTION_STATES = {"not_started", "draft", "needs_review", "complete", "blocked", "deprecated"}

# --- JSON field names that must contain valid JSON if provided ---
JSON_FIELD_NAMES = [
    "sections_json",
    "variants_json",
    "layers_json",
    "task_rules_json",
    "time_assumptions_json",
    "costengine_mapping_json",
    "quote_readiness_json",
    "output_blocks_json",
    "visual_prompt_blocks_json",
    "production_notes_json",
    "qc_checkpoints_json",
    "risks_json",
    "completion_state_json",
]

# --- Status transition table (from hardening decision §10) ---
ALLOWED_STATUS_TRANSITIONS: Dict[str, set] = {
    "draft": {"needs_review", "blocked", "deprecated"},
    "needs_review": {"approved", "draft", "blocked", "deprecated"},
    "approved": {"needs_review", "deprecated"},
    "blocked": {"draft", "needs_review", "deprecated"},
    "deprecated": {"draft"},
}

# --- Statuses that allow hard delete (hardening decision §7) ---
DELETABLE_STATUSES = {"draft", "deprecated"}


def validate_json_fields(data: Dict[str, Any]) -> List[str]:
    """Validate that all JSON fields contain valid JSON strings.

    Returns a list of error messages (empty if all valid).
    """
    errors = []
    for field_name in JSON_FIELD_NAMES:
        value = data.get(field_name)
        if value is not None and isinstance(value, str) and value.strip():
            try:
                json.loads(value)
            except (json.JSONDecodeError, ValueError):
                errors.append(f"{field_name}: invalid JSON")
    return errors


def validate_status(status: Optional[str]) -> Optional[str]:
    """Validate dossier status. Returns error message or None."""
    if status is not None and status not in ALLOWED_DOSSIER_STATUSES:
        return (
            f"Invalid status '{status}'. "
            f"Allowed values: {', '.join(sorted(ALLOWED_DOSSIER_STATUSES))}"
        )
    return None


def validate_completion_state_json(data: Dict[str, Any]) -> Optional[str]:
    """Validate completion_state_json section states if provided.

    Returns error message or None.
    """
    value = data.get("completion_state_json")
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    try:
        parsed = json.loads(value) if isinstance(value, str) else value
    except (json.JSONDecodeError, ValueError):
        return "completion_state_json: invalid JSON"

    if not isinstance(parsed, dict):
        return "completion_state_json: must be a JSON object"

    for section_key, section_val in parsed.items():
        if isinstance(section_val, dict):
            section_status = section_val.get("status")
            if section_status and section_status not in ALLOWED_SECTION_STATES:
                return (
                    f"completion_state_json.{section_key}.status: "
                    f"invalid value '{section_status}'. "
                    f"Allowed: {', '.join(sorted(ALLOWED_SECTION_STATES))}"
                )
    return None


def validate_status_transition(current_status: str, new_status: str) -> Optional[str]:
    """Validate that a status transition is allowed per hardening decision §10.

    Returns error message or None.
    """
    if current_status == new_status:
        return None  # No transition — always allowed

    allowed = ALLOWED_STATUS_TRANSITIONS.get(current_status, set())
    if new_status not in allowed:
        return (
            f"Status transition from '{current_status}' to '{new_status}' is not allowed. "
            f"Allowed transitions from '{current_status}': {', '.join(sorted(allowed)) if allowed else 'none'}"
        )
    return None


def check_owner_permission(
    dossier: ProductBlueprintDossier,
    user_role: Optional[str],
) -> Optional[str]:
    """Check if user has permission to write to this dossier.

    Owner enforcement per hardening decision §14:
    - If owner_role is set on dossier, only users with that role (or admin) can write.
    - If auth context lacks role info, enforcement is skipped (permissive fallback).
    - Returns error message or None.
    """
    if not user_role:
        # Permissive fallback — auth context lacks role info
        return None

    dossier_owner = dossier.owner_role
    if not dossier_owner:
        # No owner set — anyone can write
        return None

    if user_role == "admin":
        # Admin can always write
        return None

    if user_role != dossier_owner:
        return (
            f"Permission denied. Dossier owner_role is '{dossier_owner}', "
            f"but your role is '{user_role}'. Only the owner role or admin can modify this dossier."
        )

    return None


class ProductBlueprintDossierService:
    """Service layer for ProductBlueprintDossier operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _template_exists(self, template_id: int) -> bool:
        """Check if a product_template with the given ID exists.

        Service-level FK validation — supplements the DB-level FK constraint
        which may not be enforced in all environments (e.g., SQLite without
        PRAGMA foreign_keys=ON).
        """
        from models.product_templates import Product_templates

        query = select(Product_templates.id).where(Product_templates.id == template_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def create(
        self,
        data: Dict[str, Any],
        user_role: Optional[str] = None,
    ) -> Optional[ProductBlueprintDossier]:
        """Create a new product blueprint dossier.

        If user_role is provided and owner_role is not in data, sets owner_role
        to the creating user's role.
        """
        try:
            # Set owner_role from auth context if not explicitly provided
            if user_role and not data.get("owner_role"):
                data["owner_role"] = user_role

            # Service-level FK validation: template must exist
            template_id = data.get("template_id")
            if template_id and not await self._template_exists(template_id):
                raise ValueError(
                    f"template_id {template_id} does not reference an existing product_template"
                )

            # Run semantic validation for the target status
            target_status = data.get("status", "draft")
            semantic_errors = validate_semantic_json_for_status(data, target_status)
            if semantic_errors:
                raise ValueError(f"Semantic validation errors: {'; '.join(semantic_errors)}")

            obj = ProductBlueprintDossier(**data)
            self.db.add(obj)
            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Created product_blueprint_dossier with id: {obj.id}")
            return obj
        except ValueError:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating product_blueprint_dossier: {str(e)}")
            raise

    async def get_by_id(self, obj_id: int) -> Optional[ProductBlueprintDossier]:
        """Get dossier by ID."""
        try:
            query = select(ProductBlueprintDossier).where(
                ProductBlueprintDossier.id == obj_id
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching product_blueprint_dossier {obj_id}: {str(e)}")
            raise

    async def get_by_template_id(
        self, template_id: int
    ) -> Optional[ProductBlueprintDossier]:
        """Get dossier by template_id (UNIQUE — at most one result)."""
        try:
            query = select(ProductBlueprintDossier).where(
                ProductBlueprintDossier.template_id == template_id
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Error fetching product_blueprint_dossier by template_id {template_id}: {str(e)}"
            )
            raise

    async def get_list(
        self,
        skip: int = 0,
        limit: int = 20,
        query_dict: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get paginated list of dossiers."""
        try:
            query = select(ProductBlueprintDossier)
            count_query = select(func.count(ProductBlueprintDossier.id))

            if query_dict:
                for field, value in query_dict.items():
                    if hasattr(ProductBlueprintDossier, field):
                        query = query.where(
                            getattr(ProductBlueprintDossier, field) == value
                        )
                        count_query = count_query.where(
                            getattr(ProductBlueprintDossier, field) == value
                        )

            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            if sort:
                if sort.startswith("-"):
                    field_name = sort[1:]
                    if hasattr(ProductBlueprintDossier, field_name):
                        query = query.order_by(
                            getattr(ProductBlueprintDossier, field_name).desc()
                        )
                else:
                    if hasattr(ProductBlueprintDossier, sort):
                        query = query.order_by(
                            getattr(ProductBlueprintDossier, sort)
                        )
            else:
                query = query.order_by(ProductBlueprintDossier.id.desc())

            result = await self.db.execute(query.offset(skip).limit(limit))
            items = result.scalars().all()

            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit,
            }
        except Exception as e:
            logger.error(f"Error fetching product_blueprint_dossier list: {str(e)}")
            raise

    async def update(
        self,
        obj_id: int,
        update_data: Dict[str, Any],
        user_role: Optional[str] = None,
    ) -> Optional[ProductBlueprintDossier]:
        """Update dossier with hardening rules:

        - Status transition enforcement (§10)
        - Version auto-increment on approval transition (§9)
        - Version decrement blocked (§9)
        - Semantic JSON validation progressive per status (§13)
        - Owner enforcement on writes (§14)
        """
        try:
            obj = await self.get_by_id(obj_id)
            if not obj:
                logger.warning(
                    f"ProductBlueprintDossier {obj_id} not found for update"
                )
                return None

            # --- Owner enforcement ---
            owner_err = check_owner_permission(obj, user_role)
            if owner_err:
                raise PermissionError(owner_err)

            # --- Status transition enforcement ---
            new_status = update_data.get("status")
            current_status = obj.status
            is_approval_transition = False

            if new_status and new_status != current_status:
                transition_err = validate_status_transition(current_status, new_status)
                if transition_err:
                    raise ValueError(transition_err)
                # Track if this is a transition TO approved
                if new_status == "approved":
                    is_approval_transition = True

            # --- Version decrement blocked ---
            new_version = update_data.get("dossier_version")
            if new_version is not None:
                current_version = obj.dossier_version or 1
                if new_version < current_version:
                    raise ValueError(
                        f"Version decrement not allowed. Current version: {current_version}, "
                        f"requested: {new_version}"
                    )

            # --- Determine effective status for semantic validation ---
            effective_status = new_status if new_status else current_status

            # Build a merged data dict for semantic validation (existing + updates)
            merged_data = {}
            for field_name in JSON_FIELD_NAMES:
                # Use updated value if provided, otherwise existing value
                if field_name in update_data:
                    merged_data[field_name] = update_data[field_name]
                else:
                    existing_val = getattr(obj, field_name, None)
                    if existing_val:
                        merged_data[field_name] = existing_val

            # --- Semantic validation ---
            semantic_errors = validate_semantic_json_for_status(merged_data, effective_status)
            if semantic_errors:
                raise ValueError(f"Semantic validation errors: {'; '.join(semantic_errors)}")

            # --- Apply updates ---
            for key, value in update_data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)

            # --- Auto-increment version on approval transition ---
            if is_approval_transition:
                # Only auto-increment if user did not explicitly set a higher version
                if new_version is None:
                    obj.dossier_version = (obj.dossier_version or 1) + 1
                    logger.info(
                        f"Auto-incremented dossier_version to {obj.dossier_version} "
                        f"on approval transition for dossier {obj_id}"
                    )

            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Updated product_blueprint_dossier {obj_id}")
            return obj
        except (ValueError, PermissionError):
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Error updating product_blueprint_dossier {obj_id}: {str(e)}"
            )
            raise

    async def delete(
        self,
        obj_id: int,
        user_role: Optional[str] = None,
    ) -> bool:
        """Delete dossier with hardening delete policy (§7):

        - Hard delete allowed ONLY for status 'draft' or 'deprecated'
        - Returns error for 'needs_review', 'approved', 'blocked'
        """
        try:
            obj = await self.get_by_id(obj_id)
            if not obj:
                logger.warning(
                    f"ProductBlueprintDossier {obj_id} not found for deletion"
                )
                return False

            # --- Owner enforcement ---
            owner_err = check_owner_permission(obj, user_role)
            if owner_err:
                raise PermissionError(owner_err)

            # --- Delete policy enforcement ---
            if obj.status not in DELETABLE_STATUSES:
                raise ValueError(
                    f"Cannot delete dossier with status '{obj.status}'. "
                    f"Only dossiers with status 'draft' or 'deprecated' can be deleted. "
                    f"Change status to 'deprecated' first."
                )

            await self.db.delete(obj)
            await self.db.commit()
            logger.info(f"Deleted product_blueprint_dossier {obj_id}")
            return True
        except (ValueError, PermissionError):
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Error deleting product_blueprint_dossier {obj_id}: {str(e)}"
            )
            raise