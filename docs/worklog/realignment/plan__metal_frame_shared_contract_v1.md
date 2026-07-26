# Plan — Metal frame shared contract v1

| Field | Value |
|-------|-------|
| **Date** | 2026-07-24 |
| **Decision** | Cadru = modul partajat, **nu** template root oferteabil |
| **Consumers** | AcmPanel casetat · litere+support · banner tensionat pe cadru (aceeași configurație) |
| **Boundary** | Contract + mapare prețuri propuse; **fără** seed registry / Form System root până la owner GO |

## 1. Schema `metal_frame_config_v1`

```ts
// Conceptual TypeScript — implement later in FE + BE mirror

type MetalFrameFieldAuthority =
  | "catalog_default"
  | "derived"
  | "proposed"
  | "operator_confirmed"
  | "inactive";

type MetalFrameConfigV1 = {
  schema: "metal_frame_config_v1";
  enabled: boolean;

  /** Outer frame size (mm). Often derived from host shell. */
  outer_width_mm: number | null;
  outer_height_mm: number | null;
  dimension_source:
    | "derived_from_host" // panel − 2×thickness − 2 mm (ACM)
    | "operator_override"
    | "host_equals_frame"; // banner: frame = visible size (policy per root)

  material_code: "steel" | "aluminum" | null; // SKU catalog later
  profile_sku: string | null; // DEFERRED — do not hardcode 20×20×1.5 as runtime default
  profile_width_mm: number | null; // from SKU when resolved
  profile_wall_mm: number | null;

  orientation: "portrait" | "landscape" | "square" | null;
  long_members_mm: number[]; // full span
  short_members_mm: number[]; // span − 2×profile_width
  cross_members_mm: number[]; // operator-confirmed; propose steel~1000 / alu~750

  cut_list: Array<{
    member_id: string;
    role: "long" | "short" | "cross";
    length_mm: number;
    qty: number;
  }>;
  total_profile_length_m: number | null;

  /** How this frame attaches to the selling root — root-specific. */
  host_attachment: {
    host_kind: "acm_boxed_panel" | "letters_support" | "banner_tensioned" | "other";
    mount_method: "screws_to_shell" | "tension_hardware" | "other" | null;
  };

  field_authority: Record<string, MetalFrameFieldAuthority>;
  updated_at: string | null;
};
```

### Derivare dimensiuni (host)

| Host root | Default `dimension_source` | Formulă |
|-----------|----------------------------|---------|
| ACM casetat | `derived_from_host` | `frame = panel − 2×grosime_ACM − 2 mm` |
| Banner tensionat | `host_equals_frame` *sau* derived per owner GO | de confirmat: cadru = vizibil / vizibil−clearance |
| Litere + support | din envelope support / ACM host | la fel ca host-ul de suport |

## 2. Unde trăiește în payload

```text
finish_setup.metal_frame                  ← canonical shared blob
finish_setup.acm_panel_instance
  .configuration.internal_frame_enabled   ← projection boolean (compat)
  .configuration.metal_frame_ref          ← optional "canonical"
banner / letters hosts
  .frame.enabled + same metal_frame blob via finish_setup
```

Un singur writer: `buildMetalFramePatch` (ca `operatorPatch` AcmPanel).  
AcmPanel toggle „Cadru interior” doar setează `enabled` + re-derive dims.

## 3. Linii CPP partajate (propuse — nu seed)

Prefix **`frame_`** (nu `acm_frame_*`) ca să servească banner + ACM.

| line_code | Label | Bază | Tarif propus* |
|-----------|-------|------|---------------|
| `frame_material` | Material profil cadru | ml profil | 3.50 EUR/ml |
| `frame_fabrication` | Confecție cadru (debitare + asamblare) | ml *sau* min/cadru | 2.50 EUR/ml **sau** min 25 EUR |
| `frame_mount_to_host` | Prindere cadru pe shell | fixed / panou | 15 EUR (ACM screws) / TBD banner tension |

\* `AGENT_PROPOSED_NOT_REGISTRY` — vezi `note__acm_panel_labor_gaps_and_frame_model_v1.md`.

Emitere: doar dacă `metal_frame.enabled === true` **și** authority dims/profil suficiente.

## 4. UI

- Un panel **„Cadru metalic”** reutilizat (Intake + Product System teaching).
- Pe ACM: secțiunea Structure din inspector → leagă toggle + panel shared.
- Pe banner: același panel; `host_attachment.mount_method = tension_hardware`.
- OFF → „Cadru neinclus / neprețuit”.

## 5. Ce nu facem în v1

- `TPL-METAL-FRAME` ca root Intake oferteabil  
- Hardcodare profil 20×20×1.5 ca default runtime  
- Seed tarife fără owner GO  
- Manoperă ArtCAM / foil în contractul de cadru (rămân pe root)

## 6. Ordine implementare (după GO)

1. Types + derive cut_list (unit tests pe formula ACM Remus 2000×500×3 → 1992×492)  
2. Persist `finish_setup.metal_frame` + projection AcmPanel  
3. CPP emit `frame_*` gated by enabled  
4. Inspector shared + banner host stub când există root banner  
5. Owner confirm rates → seed registry  

## Related

- Ownership: `docs/architecture/MIXED_ACM_ACP_TECHNICAL_TRUTH_AND_OWNERSHIP.md` §6  
- Prețuri gaps: `docs/worklog/realignment/note__acm_panel_labor_gaps_and_frame_model_v1.md`
