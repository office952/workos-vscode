# Agent C — F7C UI Copy Review (Operator-Safe Wording)

**Status:** COPY PROPOSALS ONLY · **NO UI CODE CHANGES**  
**Surface:** `ResourceReadinessPanel` + `resourceReadinessDisplay.ts` on `/execution/:orderId`  
**Evidence:** F7C report § UI evidence; screenshot `docs/qa/workos-f7c-operational-resource-readiness-v1/screenshots/f7c-01-execution-880811-resource-readiness-panel.png`; live 880811 JSON  
**Goal:** Labels must not imply atelier booked, scheduled, assigned, or full machine capability

---

## 1. Verdict

F7C panel placement and “no Assign/Schedule/Start controls” are correct. Several Romanian labels over-promise readiness or under-explain “workcenter / work-area only.” Both amber states (`ready_with_warnings` and `workcenter_only`) look the same tone — operators cannot tell “minutes gap” from “no utilaj by policy.”

**Recommend copy tightening before any formal enum activation.** No code in this pack.

---

## 2. Current copy inventory

| UI element | Current RO text | Risk |
|------------|-----------------|------|
| Section title | Pregătire resurse | Mild — OK if subtitle clarifies “constatare” |
| Section subtitle | Sursă: registru ORR ∩ registru utilaje. Nicio alocare automată — doar constatare. | Good honesty |
| Column | Operație | OK |
| Column | Punct de lucru | OK (WC, not atelier seat) |
| Column | Cerință resursă | OK |
| Column | Utilaje compatibile | **Over-broad** — also shows work areas; implies capability fit |
| Column | Stare | OK |
| Status | Pregătit | Over-strong if used alone |
| Status | **Pregătit (cu atenționări)** | **Over-strong** — reads as shop-ready; today = allow-list ∩ active machine + minutes warn |
| Status | Doar punct de lucru (fără utilaj) | Acceptable direction; “fără utilaj” can sound like a defect |
| Mode | Listă utilaje admise (ORR) | OK if “admise” = eligibility |
| Mode | Doar punct de lucru | OK |
| Footer | N pregătit(e) · M cu atenționări · K blocate | “pregătit” stacks the same over-promise |
| Task name (data) | **Painting module (alias)** | Lab/English; hides that policy is `assembly` WA |
| Task names | Face CNC Cut / Side Forming / … | English lab names on operator surface |

---

## 3. Term-by-term review

### 3.1 „Pregătit (cu atenționări)” (`ready_with_warnings`)

**What it actually means today (880811):** ORR allow-list has ≥1 active machine/tool candidate; WC resolved; **no** assignment; minutes still null (`PLANNING_MINUTES_SOURCE_MISSING`).

**Must not imply:** utilaj rezervat, operator alocat, slot în calendar, atelier pregătit de start, capacitate verificată (grosime/material).

| Propose | RO | When |
|---------|----|------|
| Preferred | **Eligibil (cu atenționări)** | Default replacement |
| Alt | **Candidat utilaj găsit (cu atenționări)** | If Owner wants machine emphasis |
| Avoid | Pregătit / Gata de execuție / Resurse OK | Over-promise |

Subtitle/tooltip (optional later): „Există utilaj/activ în registru pe lista ORR. Nu înseamnă alocare sau programare. Verificați atenționările (ex. minute de planificare lipsă).”

---

### 3.2 `workcenter_only` — „Doar punct de lucru (fără utilaj)”

**What it means:** ORR allow-list is work-area-only (or derived as such); absence of MCH-* is **expected**, not a missing CNC.

**Must not imply:** defect, lipsă utilaj greșită, sau „poate rula oriunde în atelier.”

| Propose | RO |
|---------|----|
| Preferred | **Doar punct de lucru (fără utilaj cerut)** |
| Alt | **Resursă de tip zonă de lucru** |
| Mode label | **Zonă / punct de lucru (fără utilaj obligatoriu)** |
| Avoid | „Fără utilaj” alone (sounds broken); „Gata pe masă”; „Atelier OK” |

---

### 3.3 „Painting module (alias)”

**Truth:** `source_operation_code=painting` → registry `assembly` → WA-ASSEMBLY-01/02 → status `workcenter_only`. Display string is English lab residue from module alias path (DEC-004 parent `painting` canonical).

| Propose | RO |
|---------|----|
| Operator label | **Vopsire** |
| Secondary (muted) | mapare registru: `assembly` · zone WA-ASSEMBLY |
| Avoid | „Painting module”, „alias” as primary chrome |

Owner still must decide (resource-policy pack) whether painting should keep assembly WA policy or get a booth/machine ORR — copy must not claim a paint booth exists.

---

### 3.4 „Utilaje compatibile” column

**Truth:** cells show `compatible_machine_candidates` **or** fall back to `work_area_candidates` codes. Not capability (thickness/material), not booking.

| Propose | RO |
|---------|----|
| Column header | **Candidați din registru** |
| Alt | **Resurse eligibile (ORR)** |
| Empty machine + WA present | Show WA codes with prefix **Zonă:** `WA-ASSEMBLY-01` |
| Avoid | „Utilaje compatibile” when listing WA; „Compatibil 100%”; „Verificat pentru material” |

---

### 3.5 „Pregătire resurse” / resource readiness framing

| Propose | RO |
|---------|----|
| Title (keep or soft) | **Pregătire resurse** *or* **Eligibilitate resurse** |
| Keep subtitle spirit | Nicio alocare automată — doar constatare din ORR ∩ registru |
| Stronger subtitle | **Constatare eligibilitate** — nu programare, nu alocare angajat, nu verificare capacitate utilaj |

---

### 3.6 Status „Pregătit” (`ready`)

Rare on current fixtures (minutes always warn). Same over-promise risk.

| Propose | **Eligibil** |
| Avoid | Pregătit / Ready / Gata |

---

### 3.7 Danger statuses (not live on 880811 — keep honest)

| Status code | Current | Propose |
|-------------|---------|---------|
| `machine_required_but_none_compatible` | Utilaj necesar — niciunul compatibil | **Utilaj necesar — niciun candidat activ în registru** (still contingent on formal `machine_required` stamp) |
| `machine_optional_no_candidate` | Utilaj opțional — niciun candidat | **Utilaj opțional — niciun candidat (se poate continua pe punct de lucru)** |
| `machine_unavailable` | Utilaj indisponibil | **Utilaj implicit inactiv / indisponibil în registru** |
| `unknown_resource_policy` | Politică de resurse necunoscută | Keep — good honesty |
| `missing_workcenter` | Punct de lucru lipsă | Keep |
| `maintenance_conflict` | Conflict mentenanță | Keep — but unreachable until maintenance source exists; do not show as if live |

---

## 4. Fixture-specific preferred wording (880811)

| Task | Current display cues | Operator-safe story (proposed) |
|------|----------------------|--------------------------------|
| Face CNC Cut | Pregătit (cu atenționări) · MCH-CNC-4020 | **Eligibil (cu atenționări)** — candidat `MCH-CNC-4020` în registru; minute planificare lipsă; **nealocat** |
| Side Forming | same · MCH-CNC-CANT-LITERE | Same pattern for cant CNC |
| Return Face Bonding | same · weld tools + WA | **Eligibil (cu atenționări)** — unelte sudură pe listă; **fără utilaj implicit**; zonă `WA-WELD-TABLE` posibilă; minute lipsă |
| Painting module (alias) | workcenter_only · WA-ASSEMBLY | **Vopsire** — **doar zonă de lucru** (politică assembly); **nu** cabină vopsire dovedită |
| Packaging | workcenter_only · WA-ASSEMBLY | **Ambalare** — doar zonă de lucru; fără utilaj cerut |

---

## 5. Tone / visual note (from F7C report — copy-adjacent)

Both `ready_with_warnings` and `workcenter_only` use **warning** amber. Operators cannot distinguish “minutes gap on CNC” from “policy is place-only.”

**Copy-only mitigation (no code here):** differentiate labels strongly (Eligibil cu atenționări vs Doar punct de lucru…).  
**Later UI GO (out of scope):** distinct tone or secondary badge for `PLANNING_MINUTES_SOURCE_MISSING` vs policy mode.

---

## 6. Forbidden implications checklist

Operator-facing copy must **not** claim:

- [ ] Atelier / masă **rezervată**
- [ ] Utilaj **programat** sau **alocat** task-ului
- [ ] Angajat **asignat**
- [ ] Capacitate **completă** (grosime, material, software)
- [ ] Mentenanță **verificată** (source missing)
- [ ] Gata de **start execuție**
- [ ] Commercial / cost readiness

Footer propose: `N eligibile · M cu atenționări · K blocate (politică/registru)` — not „pregătit(e)”.

---

## 7. Owner / Lead decisions on copy

1. Replace „Pregătit (cu atenționări)” → **„Eligibil (cu atenționări)”**? `YES` / `NO` / `ALT: ___`  
2. Replace column „Utilaje compatibile” → **„Candidați din registru”**?  
3. Painting primary label → **„Vopsire”** (hide “module/alias”)?  
4. workcenter_only → **„Doar punct de lucru (fără utilaj cerut)”**?  
5. Defer all copy changes to post-formal-enum GO? `YES` / `NO`

**Agent C recommendation:** adopt 1–4 in the next small UI copy GO; do not wait for formal enum, because current amber “Pregătit” already misleads on live 880811.

---

## 8. Lead summary — UI copy

| Priority | Action |
|----------|--------|
| P0 | Stop saying **Pregătit** for allow-list ∩ active registry |
| P0 | Clarify workcenter_only as **policy** (fără utilaj *cerut*), not defect |
| P1 | Rename painting for operators; demote “alias/module” |
| P1 | Column header must cover machines **and** work areas |
| P2 | Separate minutes warning text from resource eligibility when UI GO opens |

**No UI code changed in this audit.**
