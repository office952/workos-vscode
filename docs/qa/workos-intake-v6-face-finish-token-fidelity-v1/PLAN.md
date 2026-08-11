# Plan — Intake V6 Face Finish Token Fidelity V1

## Problem

Operator `oracal_641` persisted correctly, but pricing adapter collapsed identity to V3 `vinyl` / template `oracal_651`, so CPP material gates never matched series-specific rules.

## Approach (smallest)

1. Preserve series in `_template_face_finish_type`.
2. Restore persisted commercial face token onto `quote_input` after V3 operation-flag mapping.
3. Bridge workspace face fields in dry-run enrich; overwrite only collapsed `vinyl` / `printed_vinyl`.
4. Keep V3 `_map_v4_face_finish` vinyl mapping for operation flags (`face_vinyl_active`).
5. No Pricing Registry / Product Truth / schema / UI / GET-diet changes.

## Out of scope

GET diet, vocabulary Slice 4, back bevel, mounting, rate changes, push.
