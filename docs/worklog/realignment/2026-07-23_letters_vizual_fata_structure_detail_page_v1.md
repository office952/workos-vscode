# Vizual față — structure detail page (UI test)

**Date:** 2026-07-23  
**Status:** pilot

## Intent

Move face documentation off the structure list onto a dedicated page. Structure row stays thin; click opens detail.

## Route

`/product-system/products/:templateCode/structure/vizual-fata`

## UI composition (visual-first + document)

1. Hero — step `01` · Vizual față · material name · CNC badge · role line  
2. Material card + CNC process cards (Debitare / Șanfren)  
3. Finisaj față chips (existing lock components)  
4. **Document componentă** — secțiuni explicative + direcționale (`lettersFaceStructureDocumentation.ts`)  
5. Surse owner/lock listate la final

Canonical prose mirror: `2026-07-23_letters_vizual_fata_structure_documentation.md`

## Structure list change

Face row: teaser + chevron → navigate. Dense CNC/finish strip removed from list.
