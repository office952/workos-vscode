# Wave 2 — simplification candidates (not implementation)

1. Remove or demote **Produse** from the Cereri/Oferte/Comenzi flux strip (IA honesty).
2. Show **one work id** (IR or IV6), put the other in disclosure.
3. One **currency story** per commercial surface (display only — no pricing change now).
4. Clients: either join Lucrări or stop pretending they are the commercial hub.
5. Orders: one next-step, not two flux strips + Vezi produse.
6. V6: keep confirm checklist; demote “25 linii” / internal mappings from the first fold.
7. Shared master-detail list primitive for Cereri / Oferte / Comenzi / Clienți (F gap).
8. Client stub tabs: LEGACY_LABEL or hide until real.
9. Quote detail: link client name to `/clients/:name`.
10. Do not locally “fix” V4 filename shims — classify only (G).

Dependencies that block local cleanup: Product System freeze; CPP money authority; dual client stores; snapshot lock semantics.
