"""Intake V6 template option contract service namespace."""

from __future__ import annotations

from typing import Literal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from models.product_blueprint_dossier import ProductBlueprintDossier
from models.product_templates import Product_templates
from schemas.intake_v6 import IntakeV6TemplateFormContractResponse, IntakeV6WorkspacePayload
from services.intake_v4_template_option_contract_service import (
	FALLBACK_DOSSIER_VARIANTS,
	_canonical_row_response,
	_issue_response,
	_json_loads,
	_variant_fields_from_dossier,
	evaluate_v4_template_option_contract,
	validate_finish_setup_against_dossier,
)
from services.intake_v6_response_normalization import normalize_intake_v6_value


async def get_template_form_contract_for_workspace(
	db: AsyncSession,
	workspace_id: str,
) -> IntakeV6TemplateFormContractResponse:
	record_result = await db.execute(
		select(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == workspace_id)
	)
	record = record_result.scalar_one_or_none()
	if record is None:
		raise HTTPException(
			status_code=404,
			detail={"error": "workspace_not_found", "workspace_id": workspace_id},
		)

	payload_raw = _json_loads(record.payload_json, {})
	payload = IntakeV6WorkspacePayload.model_validate(payload_raw)
	template_code = record.template_code or payload.product_binding.template_code

	template_result = await db.execute(
		select(Product_templates).where(Product_templates.template_code == template_code)
	)
	template = template_result.scalar_one_or_none()

	dossier_result = await db.execute(
		select(ProductBlueprintDossier).where(ProductBlueprintDossier.template_code == template_code)
	)
	dossier = dossier_result.scalar_one_or_none()
	variants = FALLBACK_DOSSIER_VARIANTS
	dossier_source: Literal["product_blueprint_dossier", "static_contract_fallback"] = (
		"static_contract_fallback"
	)
	dossier_status: str | None = None
	if dossier is not None:
		parsed_variants = _json_loads(dossier.variants_json, [])
		if isinstance(parsed_variants, list):
			variants = [v for v in parsed_variants if isinstance(v, dict)]
			dossier_source = "product_blueprint_dossier"
		dossier_status = dossier.status

	contract = evaluate_v4_template_option_contract(payload)
	alignment_status: Literal["aligned", "partial", "blocked"] = "partial"
	if contract.blockers:
		alignment_status = "blocked"
	elif not contract.warnings:
		alignment_status = "aligned"

	return IntakeV6TemplateFormContractResponse(
		workspace_id=workspace_id,
		template_code=template_code,
		alignment_status=alignment_status,
		template_active=bool(template.active) if template is not None else False,
		dossier_status=dossier_status,
		dossier_source=dossier_source,
		variant_fields=normalize_intake_v6_value(
			[field.model_dump(mode="json") for field in _variant_fields_from_dossier(variants, source=dossier_source)]
		),
		canonical_rows=normalize_intake_v6_value(
			[_canonical_row_response(row).model_dump(mode="json") for row in contract.canonical_rows]
		),
		warnings=normalize_intake_v6_value(
			[_issue_response(issue).model_dump(mode="json") for issue in contract.warnings]
		),
		blockers=normalize_intake_v6_value(
			[_issue_response(issue).model_dump(mode="json") for issue in contract.blockers]
		),
		discovered_v6_values=normalize_intake_v6_value(contract.discovered_v4_values),
	)
