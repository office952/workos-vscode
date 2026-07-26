# PRODUCT_TRUTH_WRITER_DRY_RUN_RESPONSE_FIXTURE_V1

Status: PASS

Explicit statement:
- NO CODE IMPLEMENTATION
- no Product Truth writer implemented
- no dry-run endpoint implemented
- no POST endpoint implemented
- no UI button implemented
- no workspace payload mutation performed by this task
- no Product Truth storage mutation performed by this task
- no DB schema change
- no migration
- no seed

Scope:
- docs-only JSON response fixtures for a future Product Truth Writer Dry-Run
- define example dry-run responses for:
  - success with eligible entries and `proposed_mutations`
  - refusal with blocked entries and `refused_entries`
  - mixed visibility with both `proposed_mutations` and `refused_entries`
- preserve the fixed canonical target path `payload_json.product_truth.confirmed_snapshot_v1`
- preserve the rule that `payload.product_truth.components.return_cant` is not a generic writer sink

HEAD before:
- `96ca824`

Files read:
- `docs/worklog/realignment/2026-07-09_product_truth_writer_dry_run_contract_v1.md`
- `docs/worklog/realignment/2026-07-09_product_truth_storage_target_contract_v1.md`
- `docs/worklog/realignment/2026-07-09_product_truth_writer_readiness_audit_v1.md`
- `backend/services/product_truth_promotion_planner_service.py`
- `backend/tests/test_product_truth_promotion_planner_service.py`
- `backend/tests/test_product_truth_promotion_planner_endpoint.py`
- `backend/services/return_cant_product_truth_bridge.py`
- `backend/models/intake_v6_workspace.py`
- `docs/architecture/product-system/INTAKE_V6_PRODUCT_TRUTH_CONTRACT.md`
- `docs/architecture/product-system/PRODUCT_TRUTH_CONFIRMATION_POLICY.md`

Fixture purpose:
- provide stable docs-only examples for the future backend dry-run response shape
- give implementation and test authors exact JSON targets before any endpoint exists
- keep planner semantics unchanged by mirroring only current eligible and blocked field families
- prove no-mutation expectations directly in every fixture

Success fixture JSON:

```json
{
  "read_only": true,
  "dry_run": true,
  "workspace_id": "product-truth-promotion-planner-workspace",
  "workspace_record_id": "product-truth-promotion-planner-workspace",
  "workspace_code": "IV6-PRODUCT-TRUTH-PLANNER",
  "root_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
  "product_binding_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
  "planner_version": "v1",
  "target_path": "payload_json.product_truth.confirmed_snapshot_v1",
  "proposed_mutations": [
    {
      "entry_key": "svg.selected_layer_refs[]:layer_id:face-1",
      "field_key": "svg.selected_layer_refs[]",
      "source_path": "payload.svg.selected_layer_refs[layer_id=face-1]",
      "target_path": "payload_json.product_truth.confirmed_snapshot_v1.entries.svg.selected_layer_refs[layer_id:face-1]",
      "value": {
        "layer_id": "face-1",
        "role": "vector_litere",
        "confirmed": true
      },
      "value_state": "confirmed",
      "source_state": "confirmed",
      "source_type": "selected_layer_ref",
      "identity_key": "layer_id:face-1",
      "planner_entry_hash": "sha256:planner-entry-selected-layer-face-1",
      "promotion_hash": "sha256:promotion-success-fixture-v1",
      "provenance": {
        "workspace_id": "product-truth-promotion-planner-workspace",
        "workspace_code": "IV6-PRODUCT-TRUTH-PLANNER",
        "root_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
        "product_binding_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
        "planner_version": "v1",
        "planner_hash": "sha256:planner-success-fixture-v1",
        "payload_hash_basis": "sha256:payload-success-fixture-v1",
        "source_path": "payload.svg.selected_layer_refs[layer_id=face-1]",
        "source_state": "confirmed",
        "source_type": "selected_layer_ref",
        "identity_key": "layer_id:face-1",
        "actor": {
          "actor_id": "operator-123",
          "actor_email": "operator@example.com",
          "actor_role": "operator",
          "actor_label": "Operator Review"
        },
        "writer_contract_version": "dry_run_contract_v1",
        "target_contract_version": "confirmed_snapshot_v1",
        "planner_read_only": true,
        "promotion_reason": "eligible_entry_would_be_promoted"
      },
      "conflict_status": "no_conflict",
      "action": "would_write"
    },
    {
      "entry_key": "finish.finish_target",
      "field_key": "finish.finish_target",
      "source_path": "payload.finish_setup.finish_target",
      "target_path": "payload_json.product_truth.confirmed_snapshot_v1.entries.finish.finish_target",
      "value": "face",
      "value_state": "confirmed",
      "source_state": "confirmed",
      "source_type": "scalar",
      "identity_key": null,
      "planner_entry_hash": "sha256:planner-entry-finish-target-face",
      "promotion_hash": "sha256:promotion-success-fixture-v1",
      "provenance": {
        "workspace_id": "product-truth-promotion-planner-workspace",
        "workspace_code": "IV6-PRODUCT-TRUTH-PLANNER",
        "root_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
        "product_binding_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
        "planner_version": "v1",
        "planner_hash": "sha256:planner-success-fixture-v1",
        "payload_hash_basis": "sha256:payload-success-fixture-v1",
        "source_path": "payload.finish_setup.finish_target",
        "source_state": "confirmed",
        "source_type": "scalar",
        "identity_key": null,
        "actor": {
          "actor_id": "operator-123",
          "actor_email": "operator@example.com",
          "actor_role": "operator",
          "actor_label": "Operator Review"
        },
        "writer_contract_version": "dry_run_contract_v1",
        "target_contract_version": "confirmed_snapshot_v1",
        "planner_read_only": true,
        "promotion_reason": "eligible_entry_would_be_promoted"
      },
      "conflict_status": "no_conflict",
      "action": "would_write"
    },
    {
      "entry_key": "finish.print_required:layer_key:logo-left",
      "field_key": "finish.print_required",
      "source_path": "payload.finish_setup.artwork_finishes[layer_key=logo-left].print_required",
      "target_path": "payload_json.product_truth.confirmed_snapshot_v1.entries.finish.print_required[layer_key:logo-left]",
      "value": true,
      "value_state": "confirmed",
      "source_state": "confirmed",
      "source_type": "artwork_row_boolean",
      "identity_key": "layer_key:logo-left",
      "planner_entry_hash": "sha256:planner-entry-print-logo-left-true",
      "promotion_hash": "sha256:promotion-success-fixture-v1",
      "provenance": {
        "workspace_id": "product-truth-promotion-planner-workspace",
        "workspace_code": "IV6-PRODUCT-TRUTH-PLANNER",
        "root_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
        "product_binding_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
        "planner_version": "v1",
        "planner_hash": "sha256:planner-success-fixture-v1",
        "payload_hash_basis": "sha256:payload-success-fixture-v1",
        "source_path": "payload.finish_setup.artwork_finishes[layer_key=logo-left].print_required",
        "source_state": "confirmed",
        "source_type": "artwork_row_boolean",
        "identity_key": "layer_key:logo-left",
        "actor": {
          "actor_id": "operator-123",
          "actor_email": "operator@example.com",
          "actor_role": "operator",
          "actor_label": "Operator Review"
        },
        "writer_contract_version": "dry_run_contract_v1",
        "target_contract_version": "confirmed_snapshot_v1",
        "planner_read_only": true,
        "promotion_reason": "eligible_entry_would_be_promoted"
      },
      "conflict_status": "no_conflict",
      "action": "would_write"
    }
  ],
  "refused_entries": [],
  "blockers": [],
  "idempotency_basis": {
    "workspace_id": "product-truth-promotion-planner-workspace",
    "workspace_code": "IV6-PRODUCT-TRUTH-PLANNER",
    "root_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
    "product_binding_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
    "planner_version": "v1",
    "planner_hash": "sha256:planner-success-fixture-v1",
    "payload_hash_basis": "sha256:payload-success-fixture-v1",
    "normalized_entries": [
      {
        "entry_key": "finish.finish_target",
        "field_key": "finish.finish_target",
        "target_path": "payload_json.product_truth.confirmed_snapshot_v1.entries.finish.finish_target",
        "identity_key": null,
        "value": "face"
      },
      {
        "entry_key": "finish.print_required:layer_key:logo-left",
        "field_key": "finish.print_required",
        "target_path": "payload_json.product_truth.confirmed_snapshot_v1.entries.finish.print_required[layer_key:logo-left]",
        "identity_key": "layer_key:logo-left",
        "value": true
      },
      {
        "entry_key": "svg.selected_layer_refs[]:layer_id:face-1",
        "field_key": "svg.selected_layer_refs[]",
        "target_path": "payload_json.product_truth.confirmed_snapshot_v1.entries.svg.selected_layer_refs[layer_id:face-1]",
        "identity_key": "layer_id:face-1",
        "value": {
          "layer_id": "face-1",
          "role": "vector_litere",
          "confirmed": true
        }
      }
    ]
  },
  "promotion_hash": "sha256:promotion-success-fixture-v1",
  "payload_hash_before": "sha256:payload-success-fixture-v1",
  "payload_hash_after": "sha256:payload-success-fixture-v1",
  "payload_hash_unchanged": true,
  "planner_hash_before": "sha256:planner-success-fixture-v1",
  "planner_hash_after": "sha256:planner-success-fixture-v1",
  "planner_hash_unchanged": true,
  "product_truth_target_mutated": false,
  "return_cant_bridge_mutated": false,
  "downstream_mutated": false,
  "downstream_write_intent": {
    "product_truth_write": false,
    "pricing_write": false,
    "quote_write": false,
    "order_write": false,
    "product_definition_write": false,
    "product_aggregate_write": false,
    "task_graph_write": false,
    "execution_runtime_write": false,
    "inventory_movement": false,
    "db_write": false
  },
  "notes": [
    "Dry-run visibility only; no persistence performed.",
    "Target path remains payload_json.product_truth.confirmed_snapshot_v1.",
    "payload.product_truth.components.return_cant is not used as a generic sink.",
    "No Product Truth target mutation was committed."
  ]
}
```

Refusal fixture JSON:

```json
{
  "read_only": true,
  "dry_run": true,
  "workspace_id": "product-truth-promotion-planner-blocked",
  "workspace_record_id": "product-truth-promotion-planner-blocked",
  "workspace_code": "IV6-PRODUCT-TRUTH-PLANNER-BLOCKED",
  "root_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
  "product_binding_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
  "planner_version": "v1",
  "target_path": "payload_json.product_truth.confirmed_snapshot_v1",
  "proposed_mutations": [],
  "refused_entries": [
    {
      "entry_key": "svg.selected_layer_refs[]",
      "field_key": "svg.selected_layer_refs[]",
      "source_path": "payload.svg.selected_layer_refs",
      "target_path": "payload_json.product_truth.confirmed_snapshot_v1.entries.svg.selected_layer_refs",
      "reason": "Selected layer refs are missing, so no canonical selected-layer Product Truth entry can be proposed.",
      "blockers": [
        "SELECTED_LAYER_REFS_MISSING"
      ],
      "action": "refused",
      "refusal_is_blocking": true,
      "source_state": "missing",
      "source_type": "selected_layer_ref",
      "planner_entry_hash": "sha256:planner-entry-refused-selected-layer-missing"
    },
    {
      "entry_key": "finish.finish_target",
      "field_key": "finish.finish_target",
      "source_path": "payload.finish_setup.finish_target",
      "target_path": "payload_json.product_truth.confirmed_snapshot_v1.entries.finish.finish_target",
      "reason": "Finish target is missing, so scalar Product Truth promotion cannot be planned.",
      "blockers": [
        "FINISH_TARGET_MISSING"
      ],
      "action": "refused",
      "refusal_is_blocking": true,
      "source_state": "missing",
      "source_type": "scalar",
      "planner_entry_hash": "sha256:planner-entry-refused-finish-target-missing"
    },
    {
      "entry_key": "finish.print_required:layer_key:logo-left",
      "field_key": "finish.print_required",
      "source_path": "payload.finish_setup.artwork_finishes[layer_key=logo-left].print_required",
      "target_path": "payload_json.product_truth.confirmed_snapshot_v1.entries.finish.print_required[layer_key:logo-left]",
      "reason": "Artwork print boolean is not explicitly present; execution_type evidence alone is not canonical truth.",
      "blockers": [
        "ARTWORK_BOOLEAN_EXPLICIT_VALUE_MISSING"
      ],
      "action": "refused",
      "refusal_is_blocking": true,
      "identity_key": "layer_key:logo-left",
      "source_state": "suggested",
      "source_type": "artwork_row_boolean",
      "planner_entry_hash": "sha256:planner-entry-refused-print-logo-left-derived"
    },
    {
      "entry_key": "mounting.mounting_scope",
      "field_key": "mounting.mounting_scope",
      "source_path": "payload.finish_setup.mounting_scope",
      "target_path": "payload_json.product_truth.confirmed_snapshot_v1.entries.mounting.mounting_scope",
      "reason": "Mounting scope is missing, so no canonical mounting Product Truth mutation can be proposed.",
      "blockers": [
        "MOUNTING_SCOPE_MISSING"
      ],
      "action": "refused",
      "refusal_is_blocking": true,
      "source_state": "missing",
      "source_type": "scalar",
      "planner_entry_hash": "sha256:planner-entry-refused-mounting-scope-missing"
    },
    {
      "entry_key": "support.support_type",
      "field_key": "support.support_type",
      "source_path": "payload.finish_setup.support_type",
      "target_path": "payload_json.product_truth.confirmed_snapshot_v1.entries.support.support_type",
      "reason": "Support type is missing; support-like evidence does not authorize canonical Product Truth promotion.",
      "blockers": [
        "SUPPORT_TYPE_MISSING"
      ],
      "action": "refused",
      "refusal_is_blocking": true,
      "source_state": "suggested",
      "source_type": "scalar",
      "planner_entry_hash": "sha256:planner-entry-refused-support-type-missing"
    }
  ],
  "blockers": [
    {
      "field_key": "svg.selected_layer_refs[]",
      "blockers": [
        "SELECTED_LAYER_REFS_MISSING"
      ],
      "state": "missing"
    },
    {
      "field_key": "finish.finish_target",
      "blockers": [
        "FINISH_TARGET_MISSING"
      ],
      "state": "missing"
    },
    {
      "field_key": "mounting.mounting_scope",
      "blockers": [
        "MOUNTING_SCOPE_MISSING"
      ],
      "state": "missing"
    },
    {
      "field_key": "support.support_type",
      "blockers": [
        "SUPPORT_TYPE_MISSING"
      ],
      "state": "suggested"
    }
  ],
  "idempotency_basis": {
    "workspace_id": "product-truth-promotion-planner-blocked",
    "workspace_code": "IV6-PRODUCT-TRUTH-PLANNER-BLOCKED",
    "root_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
    "product_binding_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
    "planner_version": "v1",
    "planner_hash": "sha256:planner-refusal-fixture-v1",
    "payload_hash_basis": "sha256:payload-refusal-fixture-v1",
    "normalized_entries": []
  },
  "promotion_hash": null,
  "payload_hash_before": "sha256:payload-refusal-fixture-v1",
  "payload_hash_after": "sha256:payload-refusal-fixture-v1",
  "payload_hash_unchanged": true,
  "planner_hash_before": "sha256:planner-refusal-fixture-v1",
  "planner_hash_after": "sha256:planner-refusal-fixture-v1",
  "planner_hash_unchanged": true,
  "product_truth_target_mutated": false,
  "return_cant_bridge_mutated": false,
  "downstream_mutated": false,
  "downstream_write_intent": {
    "product_truth_write": false,
    "pricing_write": false,
    "quote_write": false,
    "order_write": false,
    "product_definition_write": false,
    "product_aggregate_write": false,
    "task_graph_write": false,
    "execution_runtime_write": false,
    "inventory_movement": false,
    "db_write": false
  },
  "notes": [
    "No proposed mutations were produced because all requested entries are blocked or missing.",
    "Dry-run remains read-only and performs no payload mutation.",
    "payload.product_truth.components.return_cant remains untouched.",
    "No ProductDefinition, Pricing, Quote, Order, or Execution mutation occurred."
  ]
}
```

Mixed fixture JSON:

```json
{
  "read_only": true,
  "dry_run": true,
  "dry_run_visibility": "can_show_both",
  "writer_real_atomic_policy": "fail_closed_if_request_contains_blocked",
  "workspace_id": "product-truth-promotion-planner-mixed",
  "workspace_record_id": "product-truth-promotion-planner-mixed",
  "workspace_code": "IV6-PRODUCT-TRUTH-PLANNER-MIXED",
  "root_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
  "product_binding_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
  "planner_version": "v1",
  "target_path": "payload_json.product_truth.confirmed_snapshot_v1",
  "proposed_mutations": [
    {
      "entry_key": "finish.finish_target",
      "field_key": "finish.finish_target",
      "source_path": "payload.finish_setup.finish_target",
      "target_path": "payload_json.product_truth.confirmed_snapshot_v1.entries.finish.finish_target",
      "value": "face",
      "value_state": "confirmed",
      "source_state": "confirmed",
      "source_type": "scalar",
      "identity_key": null,
      "planner_entry_hash": "sha256:planner-entry-mixed-finish-target-face",
      "promotion_hash": "sha256:promotion-mixed-fixture-v1",
      "provenance": {
        "workspace_id": "product-truth-promotion-planner-mixed",
        "workspace_code": "IV6-PRODUCT-TRUTH-PLANNER-MIXED",
        "root_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
        "product_binding_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
        "planner_version": "v1",
        "planner_hash": "sha256:planner-mixed-fixture-v1",
        "payload_hash_basis": "sha256:payload-mixed-fixture-v1",
        "source_path": "payload.finish_setup.finish_target",
        "source_state": "confirmed",
        "source_type": "scalar",
        "identity_key": null,
        "actor": {
          "actor_id": "operator-789",
          "actor_email": "operator@example.com",
          "actor_role": "operator",
          "actor_label": "Operator Review"
        },
        "writer_contract_version": "dry_run_contract_v1",
        "target_contract_version": "confirmed_snapshot_v1",
        "planner_read_only": true,
        "promotion_reason": "eligible_entry_would_be_promoted"
      },
      "conflict_status": "no_conflict",
      "action": "would_write"
    },
    {
      "entry_key": "finish.lamination_required:layer_key:logo-right",
      "field_key": "finish.lamination_required",
      "source_path": "payload.finish_setup.artwork_finishes[layer_key=logo-right].lamination_required",
      "target_path": "payload_json.product_truth.confirmed_snapshot_v1.entries.finish.lamination_required[layer_key:logo-right]",
      "value": true,
      "value_state": "confirmed",
      "source_state": "confirmed",
      "source_type": "artwork_row_boolean",
      "identity_key": "layer_key:logo-right",
      "planner_entry_hash": "sha256:planner-entry-mixed-lamination-logo-right-true",
      "promotion_hash": "sha256:promotion-mixed-fixture-v1",
      "provenance": {
        "workspace_id": "product-truth-promotion-planner-mixed",
        "workspace_code": "IV6-PRODUCT-TRUTH-PLANNER-MIXED",
        "root_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
        "product_binding_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
        "planner_version": "v1",
        "planner_hash": "sha256:planner-mixed-fixture-v1",
        "payload_hash_basis": "sha256:payload-mixed-fixture-v1",
        "source_path": "payload.finish_setup.artwork_finishes[layer_key=logo-right].lamination_required",
        "source_state": "confirmed",
        "source_type": "artwork_row_boolean",
        "identity_key": "layer_key:logo-right",
        "actor": {
          "actor_id": "operator-789",
          "actor_email": "operator@example.com",
          "actor_role": "operator",
          "actor_label": "Operator Review"
        },
        "writer_contract_version": "dry_run_contract_v1",
        "target_contract_version": "confirmed_snapshot_v1",
        "planner_read_only": true,
        "promotion_reason": "eligible_entry_would_be_promoted"
      },
      "conflict_status": "no_conflict",
      "action": "would_write"
    }
  ],
  "refused_entries": [
    {
      "entry_key": "support.support_type",
      "field_key": "support.support_type",
      "source_path": "payload.finish_setup.support_type",
      "target_path": "payload_json.product_truth.confirmed_snapshot_v1.entries.support.support_type",
      "reason": "Support type is missing; dry-run can display the refusal but the real writer must fail-closed if this blocked entry is included in the request.",
      "blockers": [
        "SUPPORT_TYPE_MISSING"
      ],
      "action": "refused",
      "refusal_is_blocking": true,
      "source_state": "missing",
      "source_type": "scalar",
      "planner_entry_hash": "sha256:planner-entry-mixed-refused-support-type-missing"
    },
    {
      "entry_key": "finish.print_required:layer_key:logo-left",
      "field_key": "finish.print_required",
      "source_path": "payload.finish_setup.artwork_finishes[layer_key=logo-left].print_required",
      "target_path": "payload_json.product_truth.confirmed_snapshot_v1.entries.finish.print_required[layer_key:logo-left]",
      "reason": "Artwork row lacks explicit print boolean confirmation; execution_type-only evidence remains blocked for canonical Product Truth.",
      "blockers": [
        "ARTWORK_BOOLEAN_EXPLICIT_VALUE_MISSING"
      ],
      "action": "refused",
      "refusal_is_blocking": true,
      "identity_key": "layer_key:logo-left",
      "source_state": "suggested",
      "source_type": "artwork_row_boolean",
      "planner_entry_hash": "sha256:planner-entry-mixed-refused-print-logo-left-derived"
    }
  ],
  "blockers": [
    {
      "field_key": "support.support_type",
      "blockers": [
        "SUPPORT_TYPE_MISSING"
      ],
      "state": "missing"
    },
    {
      "field_key": "finish.print_required",
      "identity_key": "layer_key:logo-left",
      "blockers": [
        "ARTWORK_BOOLEAN_EXPLICIT_VALUE_MISSING"
      ],
      "state": "suggested"
    }
  ],
  "idempotency_basis": {
    "workspace_id": "product-truth-promotion-planner-mixed",
    "workspace_code": "IV6-PRODUCT-TRUTH-PLANNER-MIXED",
    "root_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
    "product_binding_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
    "planner_version": "v1",
    "planner_hash": "sha256:planner-mixed-fixture-v1",
    "payload_hash_basis": "sha256:payload-mixed-fixture-v1",
    "normalized_entries": [
      {
        "entry_key": "finish.finish_target",
        "field_key": "finish.finish_target",
        "target_path": "payload_json.product_truth.confirmed_snapshot_v1.entries.finish.finish_target",
        "identity_key": null,
        "value": "face"
      },
      {
        "entry_key": "finish.lamination_required:layer_key:logo-right",
        "field_key": "finish.lamination_required",
        "target_path": "payload_json.product_truth.confirmed_snapshot_v1.entries.finish.lamination_required[layer_key:logo-right]",
        "identity_key": "layer_key:logo-right",
        "value": true
      }
    ]
  },
  "promotion_hash": "sha256:promotion-mixed-fixture-v1",
  "payload_hash_before": "sha256:payload-mixed-fixture-v1",
  "payload_hash_after": "sha256:payload-mixed-fixture-v1",
  "payload_hash_unchanged": true,
  "planner_hash_before": "sha256:planner-mixed-fixture-v1",
  "planner_hash_after": "sha256:planner-mixed-fixture-v1",
  "planner_hash_unchanged": true,
  "product_truth_target_mutated": false,
  "return_cant_bridge_mutated": false,
  "downstream_mutated": false,
  "no_persistence": true,
  "downstream_write_intent": {
    "product_truth_write": false,
    "pricing_write": false,
    "quote_write": false,
    "order_write": false,
    "product_definition_write": false,
    "product_aggregate_write": false,
    "task_graph_write": false,
    "execution_runtime_write": false,
    "inventory_movement": false,
    "db_write": false
  },
  "notes": [
    "Dry-run may show both proposed eligible mutations and refused blocked entries.",
    "Real writer policy remains fail_closed_if_request_contains_blocked.",
    "No persistence occurred during dry-run visibility.",
    "payload.product_truth.components.return_cant remains untouched and is not treated as the canonical sink."
  ]
}
```

No-mutation proof fields:
- `payload_hash_before`
- `payload_hash_after`
- `payload_hash_unchanged = true`
- `planner_hash_before`
- `planner_hash_after`
- `planner_hash_unchanged = true`
- `product_truth_target_mutated = false`
- `return_cant_bridge_mutated = false`
- `downstream_mutated = false`

Fixture usage guidance:
1. success fixture proves exact `proposed_mutations` shape for eligible current planner families
2. refusal fixture proves exact `refused_entries` shape when dry-run sees only blocked or missing entries
3. mixed fixture proves that dry-run visibility may include both arrays while the future real writer remains atomic and fail-closed
4. all fixtures preserve `downstream_write_intent` as fully false
5. all fixtures keep the canonical target path fixed at `payload_json.product_truth.confirmed_snapshot_v1`
6. all fixtures explicitly show that `payload.product_truth.components.return_cant` is not used as a generic Product Truth sink

Roadmap awareness checkpoint:
- roadmap alignment score: `10/10`
- current spine position:
  `Product System -> Form System -> Intake V6 runtime payload -> Runtime Capture Read Model -> Product Truth Promotion Planner -> Planner Endpoint -> Planner UI Consumer -> Product Truth Writer Readiness Audit -> Product Truth Storage Target Contract -> Product Truth Writer Dry-Run Contract -> Product Truth Writer Dry-Run Response Fixtures`
- direction alignment: `98/100%`
- dead pieces check:
  - no runtime code introduced
  - no endpoint introduced
  - no UI surface introduced
  - no payload branch introduced
  - no DB or schema artifact introduced
- forbidden scope confirmation:
  - no writer
  - no endpoint
  - no UI CTA
  - no payload mutation
  - no DB migration
  - no seed live
  - no Pricing / Quote / Order / Execution
  - no ProductDefinition consumer
  - no ProductAggregate / TaskGraph / ExecutionPlan

Forbidden scope confirmation:
- no Product Truth writer implemented
- no dry-run endpoint added
- no POST endpoint added
- no UI button added
- no Product Truth mutation
- no workspace payload mutation
- no Product Truth storage real mutation
- no DB migration
- no seed live
- no Pricing
- no Quote/Order
- no Execution
- no ProductDefinition consumer
- no ProductAggregate/TaskGraph

Next recommended prompt:
- `TASK — PRODUCT_TRUTH_WRITER_DRY_RUN_BACKEND_READINESS_AUDIT_V1`
- Goal: audit docs-only the exact backend dependencies, helper boundaries, hash sources, and test seams required to implement the dry-run server-side without persisting anything
- Boundary: no backend implementation, no endpoint, no UI CTA, no payload mutation, no DB migration, no ProductDefinition consumer changes