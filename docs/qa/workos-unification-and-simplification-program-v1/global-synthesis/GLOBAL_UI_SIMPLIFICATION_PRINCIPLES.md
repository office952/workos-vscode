# Global UI simplification principles

Derived from Waves 1–5. **5–10 rules. Not a design system rewrite.**

1. **Workflow before architecture.** Nav teaches Cerere → Intake → Ofertă → Comandă, then production watch/act. Compiler terms stay in admin language.
2. **One business concept, one primary home.** Same truth may have projections; only one owner writes it.
3. **Demo/mock cannot look authoritative.** DEMO / MOCK / coming-soon must stay visible; disabled CTAs are not a live module.
4. **Planned/unwired cannot look live.** Hide or label `plannedSection` Product System shells.
5. **Internal IDs are secondary.** Show the human work id first; IR / IV6 / numeric `order_id` / `JOB-*` belong in disclosure.
6. **Commercial grain ≠ execution grain ≠ operator card.** Do not flatten PA nodes or WC enums into the sold-work story.
7. **Admin/audit stays out of everyday nav.** Ops-Graph, Reality Review, operational reports, blueprint preview = Sistem / Audit.
8. **Role surfaces expose decisions, not inventories.** Unbounded `/operator` lists and admin KPI stacks are not operator homes.
9. **Change the label before the contract.** Display Romanian first; route / enum / API / DB rename only with audit + tests + Owner GO.
10. **Light/dark uses shared primitives.** Page-local cards are debt; do not “fix” theme with one-off CSS per page.

Visual target (practical, not Figma):

- **Density:** operational tables for lists; cards only for a single decision.
- **Hierarchy:** one H1 that matches nav; one primary CTA; status in Romanian.
- **Technical detail:** behind “Detalii sistem” / audit routes.
- **Empty states:** say empty, mock, or blocked — never invent completeness.
- **Role complexity:** sales sees money + readiness; operator sees current work; admin sees map + gaps.
