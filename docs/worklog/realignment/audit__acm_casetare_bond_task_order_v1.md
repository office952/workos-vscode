# Audit — Ordine taskuri casetare bond (Corp Alucobond)

| Field | Value |
|-------|--------|
| Date | 2026-07-23 |
| Status | **OWNER_CONFIRMED** (atelier sequence locked) |
| Template | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |
| Display SoT | `frontend/src/features/product-system/acmBoxedStructurePrincipalTaskOrder.ts` |

---

## Verdict

Ordinea atelier pentru casetare bond este **blocată de owner** (10 pași). Seed DAG poate diferi — non-blocking.

---

## Ordine OWNER (1–10)

| # | Task |
|---|------|
| 1 | Pregătire fișier **ArtCAM**: cote finale, desfășurată/blank intern, linii V-groove, contur exterior, toleranțe |
| 2 | Frezare **V-groove** / linii de îndoire pentru casetare |
| 3 | **Debitare finală** pe conturul exterior |
| 4 | Curățare muchii / debavurare + îndoiri laterale / formare casetă |
| 5 | Confecționare **cadru metalic** cf. specificații |
| 6 | **Prindere** cadru metalic de corpul casetat din Alucobond |
| 7 | **Aplicare autocolant** solicitat (dacă e selectat) cf. specificații |
| 8 | Dacă **nu** e solicitat autocolant → **vopsire autoforante** la culoarea Alucobondului |
| 9 | Pregătire **accesorii de montaj** |
| 10 | **Impachetare** produs cf. specificații |

Regulă: **7 XOR 8** (colant după fixare **sau** vopsire șuruburi — nu ambele).

ArtCAM: exterior negru = Cut outside; dungi roșii = V-groove along line  
→ `docs/architecture/ACM_ARTCAM_DXF_OWNER_GOLDEN.md`

---

## Seed vs owner

Seed încă: cut → V → fold (+ assembly/mount).  
Owner: ArtCAM → V → cut → fold → frame → …  
Status: **gap documentat, non-blocking** (ACCEPT: contează grafica CNC).

---

## Next stage (neschimbat)

1. Finisaje ACM în Intake (neapărat) — alimentează pașii 7/8  
2. Qty Decupare pe material desfășurat  
3. Contract Litere↔ACM  

---

## Sources

- Owner message 2026-07-23 (atelier list)  
- `acmBoxedStructurePrincipalTaskOrder.ts`  
- `MIXED_ACM_ACP_TECHNICAL_TRUTH_AND_OWNERSHIP.md` §4  
- `2026-07-23_acm_ps_structure_ui_closed.md`  
