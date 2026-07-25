# Sistem LED — structure documentation (canonical prose)

**Date:** 2026-07-23  
**Status:** locked display documentation (model = Vizual față)

Source: `frontend/src/features/product-system/lettersLedStructureDocumentation.ts`

## Role

Pasul 4 — iluminare pe spate Forex, **doar litere**. Standard: Modul LED 12V. Alt: Bandă LED. PSU 60/100/160/200 W.

**Out of scope pe această pagină:** iluminare emblemă / casetă (densitate pe mp) — tratament separat.

## Identitate material (operator) — litere

- Tip standard: `MAT-LED-MODULE` — Modul LED 12V
- Putere modul: **0.75 / 1.00 / 1.44 W** — default **0.75** (`led_module_power_w`)
- Culoare lumină: **warm / neutral / cool** — default **warm** (`light_color`) — nu schimbă formula count/W
- Pitch litere: **250 mm** (Intake V4/V6)

## Cum calculăm (important — formula litere)

Nu inventăm consum pe job pe această pagină. Documentăm doar regula. **Fără emblemă.**

1. **Număr module litere**  
   `letter_led_module_count = ceil(perimeter_m × 1000 / 250)`
2. **Putere LED litere**  
   `estimated_led_watts = letter_led_module_count × led_module_power_w`
3. **PSU automat (din litere)**  
   `required_psu_watts = estimated_led_watts × 1.30`  
   → alocare pe `{60, 100, 160, 200}` → `psu_configuration[]`  
   Prioritate: mai puține unități → spare mai mic → PSU max mai mare.  
   Dacă `required > 200 W`: mai multe unități (ex. `[200, 100]`).  
   Cost = sumă prețuri SKU pe bucată — **nu** × W.

Prețuri doar prin „Verifică…” spre Pricing Registry.
