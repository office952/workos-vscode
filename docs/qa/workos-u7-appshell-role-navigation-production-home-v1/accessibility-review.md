# Accessibility review (U7)

| Item | Result |
|------|--------|
| Nav `aria-label` | Navigare principală |
| Collapse button | aria-label + aria-expanded |
| Nav drawer | existing aria-expanded |
| Focus-visible | outline on nav links, user menu, collapse |
| Role in user menu | “Rol: {role}” + aria-label pe avatar |
| Status badges | included in aria-label when present |
| Keyboard | native NavLink + buttons; no trap introduced |

Not a full WCAG audit — targeted shell improvements only.
