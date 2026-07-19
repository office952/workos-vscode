# Desktop Composition Proposal

Derived from inventory + stress + nesting audits. **Not an implementation.** Not a mandated pixel layout — a composition contract the owner can accept/reject.

## Shared desktop chrome

```text
[ App nav | Intake header: product id · step ]
[ L1 product identity (compact) + required gate CTA if any ]

[ Main decision column (~65–70%)     ] [ L3 results rail (~30%) ]
[ L2 active decisions                ] [ commercial summary     ]
[ L4 local/compact attention         ] [ expand details         ]

[ L6 technical disclosure — collapsed ]

[ Footer spine: counts · next action · primary CTA ]
```

Rules:
- Fixed: header stepper, footer spine, optional sticky compact attention chip.
- Scrolls: decision column.
- Sticky: commercial rail on desktop ≥1280; footer always.
- Warnings: local-first near cause; summary chip if multi-issue.
- Technical: collapsed.
- Commercial: rail summary always; lines on demand.

---

## Page 1 — Straturi

```text
[ Product / file identity ]

[ SVG preview (dominant visual)     ] [ Role actions rail ]
[ Layer role cards (decision grid)  ] [ Confirm all / gaps ]

[ Composition confirm if required ]

[ Technical metrics disclosure ]

[ Footer: Continuă la Configurare ]
```

- Support contour: inside role card (current truth path) — do not resurrect orphan geometry card without GO.
- Warnings: rail only if actionable; else footer.

---

## Page 2 — Finisaje

```text
[ Produs compact · status · Confirm CTA if needed ]

[ Tabs: Finisaje | Iluminare | Montaj ]

[ Letter / Logo anatomy decisions (L2) ] [ Rezultat comercial (L3) ]
[ Local Cant/Față blockers if any      ] [ Detalii linii on demand  ]

[ Finish technical disclosure (L6) ]
[ Footer next action ]
```

- Scope: one quiet line under Produs or inside disclosure — not a competing card.
- Blocker banner: replace full-bleed rose slab with compact sticky chip unless expanded.
- Product decisions must start **above the fold** on 1440×1000 after Produs compact.

---

## Page 2 — Iluminare

```text
[ Same Produs + tabs ]

[ LED master + lighting decisions (ONE group) ] [ Commercial rail ]
[ PSU decision in same group                  ] [                ]
[ Rezultate calculate (L3 band)               ] [                ]
[ Detalii calcul LED (L6)                     ] [                ]
```

- **Remove dual top “Tip iluminare / PSU” contract row as separate floating owners** — merge with specialized section (presentation merge; same fields/truth).
- Empty lower third: results should sit immediately under decisions.

---

## Page 2 — Montaj

```text
[ Same Produs + tabs ]

[ A. Product support / Fundal (L2) — primary when ACM present ]
[    ACP geometry decisions · segmented confirm if proposed  ] [ Rail ]
[ B. Commercial mounting (L2) — only if scope ≠ none         ]
[    Scope → conditional prep/site/cable                     ]
[ C. Avansat (L6) collapsed                                  ]
```

- Flip current emphasis: today commercial/template chrome appears before Fundal; **product support should lead** when ACM composition exists.
- Inactive prep/site: no empty bordered cards.
- Product System badge / hashes: L6 only.
- Cable / service corner: only when solution requires.

---

## Page 3 — Confirmare

```text
[ Status L1: ready / blocked — always visible ]
[ Checklist L2 + primary draft CTA ]
[ Recap L3 ]
[ Pricing L3 ]
[ Technical L6 disclosure ]
[ Footer ]
```

- Must **not** bury checklist in default-collapsed technical accordion.

---

## Responsive (narrow desktop only)

- <1280: stack rail under decisions; keep footer spine.
- Do not design Employee Mobile here.

---

## Recommendation confidence

| Choice | Recommendation | Confidence |
|--------|----------------|------------|
| Local-first warnings | Yes | High |
| Pricing as secondary rail | Keep (already quieted) | High |
| Montaj product-first when ACM | Yes | High |
| Merge Iluminare dual renderers visually | Yes | High |
| Confirmare first-paint checklist | Yes | High |
| Kill composition confirm gate | **No** — truth frozen | Absolute |
