# BEFORE_AFTER_PRICING_TRACE

## Before (audit @ `27a0cbac`)

```
UI / persisted: oracal_641
quote_input.face_finish_type: vinyl
handoff.face_finish_type: oracal_651  (raw=oracal_641, series=641)
finish_setup (CPP): vinyl (coalesced from top-level)
CPP face Oracal lines: MISSING
Ofertă still READY with incomplete face money
```

## After (this slice)

```
UI / persisted: oracal_641
quote_input.face_finish_type: oracal_641
handoff.face_finish_type: oracal_641  (raw=oracal_641, series=641)
finish_setup (CPP): oracal_641
CPP: finisaje_oracal_641_material + finisaje_aplicare_autocolant_fata
```

## Root cause → fix

| Cause | Fix |
|---|---|
| `_template_face_finish_type` collapsed all vinyl family → `oracal_651` | Preserve `oracal_641` / `oracal_8500`; only true aliases → `oracal_651` |
| V3 `_map_v4_face_finish` emits `vinyl` for 641/651 (operation flags) | Restore commercial token from persisted setup onto `quote_input.face_finish_type` |
| Dry-run enrich omitted face identity | Bridge `face_finish_type` + `letter_group_finishes`; overwrite collapsed `vinyl`/`printed_vinyl` |

## Identity matrix

| Token | Before QI | After QI | Before CPP gate | After CPP gate |
|---|---|---|---|---|
| none | none | none | no face charge | no face charge |
| 641 | vinyl | oracal_641 | miss | 641 material |
| 651 | vinyl | oracal_651 | miss | 651 material |
| 8500 | oracal_8500 | oracal_8500 | ok (QI) / handoff wrong | ok + handoff 8500 |
| print_laminate | printed_vinyl | print_laminate | unpriced / miss | print laminate line |
