# Owner decision pack — labor productivity / formula gaps

Do not invent numbers. One consolidated ask for a future build.

| Operation | Required basis | Available evidence | Missing owner input | Recommended unit |
|-----------|----------------|--------------------|---------------------|------------------|
| PACKAGING | commercial packaging rule | VOL_V2_PACKAGING_PENDING | fixed/set vs m² rule | set or mp |
| PREPRESS (priced) | labor qty if commercially priced | readiness gate only | buc/job vs gate-only | buc or produs |
| ELECTRICAL_WIRING | consumption qty | module role only | per letter / PSU / job | buc |
| LED_ASSEMBLY time (optional) | minutes from module count | `letter_led_module_count` confirmed; `led_assembly_time` defaults exist but unbound | modules/minute if time formula desired | min / module |
| PAINTING vs RETURN_CANT_RAL_PAINT_LABOR | single owner XOR | both perimeter-linked | which commercial owner | ml |
| RETURN_CANT_VINYL wrap | perimeter vs wrap area | perimeter qty | confirm wrap basis | ml or mp |
| ACM FOLD_CASSETTE / MOUNT | labor qty | ops without formula | qty key + formula | buc / mp |
| Volum Aluminiu bonding formula name | registered handler | seed `return_profile_face_bonding` unregistered | register or replace formula_id | — |
| SITE_INSTALLATION_STANDARD rate | registry rate | commercial fixed confirmed; rate may block | owner rate if commercial needed | locatie |

**Rule recorded:** no productivity value is invented to obtain a green status.
