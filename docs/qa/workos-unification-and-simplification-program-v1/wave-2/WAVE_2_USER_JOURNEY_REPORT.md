# Wave 2 user journey report

**REQUEST_TO_ORDER_JOURNEY = PARTIAL**

Understandable pieces: Cereri list → Deschide Intake V6 works. Orders say they do not re-price. Confirm step blocks dishonest handoff.

Breaks: (1) FLUX teaches Cerere→Produs not Cerere→V6. (2) IR vs IV6 identity. (3) Confirm blocked on the opened workspace — cannot complete to quote without mutation. (4) Quote has no client link. (5) Clients are a side door. (6) Quote observe opened a **different** V6 id than the Cereri row.

See `lane-h-nav-journeys/EDGES.md` and `WAVE_2_BACK_NAV_CONTEXT_REPORT.md`.

Browser back: Cereri→V6→Back and Clients→detail→Back return to the list. Orders→detail→Back lands on a blank document (SPA history). Scroll is not preserved.
