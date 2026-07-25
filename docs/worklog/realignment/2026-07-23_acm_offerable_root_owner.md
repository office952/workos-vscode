# ACM = offerable root — owner lock

| Field | Value |
|-------|-------|
| **Date** | 2026-07-23 |
| **Decision** | §8 Q2 ANSWERED |
| **Verdict** | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` / **Alucobond casetat** is an **offerable Product Template root** |

## Owner rationale

ACM will be reused beyond Letters-on-bond:

- panou simplu cu autocolant
- alte modele de litere pe el (nu doar Litere volumetrice v2)
- pur decorativ / panel-only (`applied_content=none`)

## Implications

1. Do **not** treat ACM as Letters-only accessory in commercial / Composer productization.
2. Letters↔ACM contract remains a **composition attach** onto an offerable ACM root (or Letters root attaching ACM — both roots stay clean).
3. XOR `applied_content` (none / letters / logo) stays the content axis; panel commercial lines (cut / V / assembly) stay on ACM root.
4. Future content types = new composition/contracts, not a second ACM product identity.

## Related

- `decision__letters_acm_compatibility_composer_direction_v1.md` §8 Q2
- `LETTERS_ACM_COMPATIBILITY_CONTRACT_V1.md` §5 matrix
- `acm_boxed_support_composition_v1.py` — `applied_content`
