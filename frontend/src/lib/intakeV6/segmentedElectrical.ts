/**
 * Segmented ACM/ACP electrical connection management (shell-owned).
 * Nested under finish_setup.segmented_background.electrical_connection_management.
 */

export const SEGMENTED_ELECTRICAL_SCHEMA = "acm_segmented_electrical_connection_v1";

export type ElectricalSupplyMode =
  | "DIRECT_220V"
  | "SHARED_FROM_PANEL"
  | "NO_LOCAL_220V"
  | "UNCONFIRMED";

export type ServicePointPosition =
  | "TOP_LEFT"
  | "TOP_RIGHT"
  | "BOTTOM_LEFT"
  | "BOTTOM_RIGHT"
  | "TOP_CENTER"
  | "BOTTOM_CENTER"
  | "LEFT_CENTER"
  | "RIGHT_CENTER"
  | "CUSTOM"
  | "NONE";

export type ElectricalStatus = "INACTIVE" | "DRAFT" | "CONFIRMED";

export interface PanelWorkshopPrep {
  cables_routed_toward_service?: boolean;
  passages_prepared?: boolean;
  labeled?: boolean;
  reserve_required?: boolean;
  reserve_note_ro?: string | null;
}

export interface PanelInstallation {
  connect_to_client_220v?: boolean;
  finalize_after_alignment?: boolean;
  notes_ro?: string | null;
}

export interface PanelElectrical {
  panel_id: string;
  supply_mode: ElectricalSupplyMode;
  shared_from_panel_id?: string | null;
  service_point_position?: ServicePointPosition | null;
  custom_position_note?: string | null;
  sketch_ref?: string | null;
  cable_exit_position?: ServicePointPosition | null;
  routing_direction_note_ro?: string | null;
  power_supply_group_id?: string | null;
  letter_group_ref?: string | null;
  workshop_prep?: PanelWorkshopPrep;
  installation?: PanelInstallation;
  notes_ro?: string | null;
}

export interface InterPanelConnection {
  connection_id: string;
  source_panel_id: string;
  destination_panel_id: string;
  connection_type?: string;
  routing_direction_note_ro?: string | null;
  alignment_dependent?: boolean;
  prepared_in_workshop?: boolean;
  completed_on_site?: boolean;
  reserve_required?: boolean;
  estimated_length_m?: number | null;
  length_is_estimate?: boolean;
  sketch_ref?: string | null;
  notes_ro?: string | null;
}

export interface SegmentedElectrical {
  schema: typeof SEGMENTED_ELECTRICAL_SCHEMA;
  contract_version?: string;
  status: ElectricalStatus;
  operator_confirmed?: boolean;
  panels: PanelElectrical[];
  inter_panel_connections: InterPanelConnection[];
  confirmation?: { message_code?: string; message?: string; authority?: string };
  validation?: {
    blockers?: Array<{ code: string; level: string; message: string }>;
    warnings?: Array<{ code: string; level: string; message: string }>;
    infos?: Array<{ code: string; level: string; message: string }>;
  };
}

export const SUPPLY_LABELS_RO: Record<ElectricalSupplyMode, string> = {
  DIRECT_220V: "220V direct pe panou",
  SHARED_FROM_PANEL: "Alimentare din alt panou",
  NO_LOCAL_220V: "Fara 220V local",
  UNCONFIRMED: "Neconfirmat",
};

export const POSITION_LABELS_RO: Record<ServicePointPosition, string> = {
  TOP_LEFT: "Stanga sus",
  TOP_RIGHT: "Dreapta sus",
  BOTTOM_LEFT: "Stanga jos",
  BOTTOM_RIGHT: "Dreapta jos",
  TOP_CENTER: "Centru sus",
  BOTTOM_CENTER: "Centru jos",
  LEFT_CENTER: "Centru stanga",
  RIGHT_CENTER: "Centru dreapta",
  CUSTOM: "Pozitie dupa schita",
  NONE: "Fara punct local 220V",
};

export const ELECTRICAL_MESSAGES_RO = {
  indicate: "Indica unde este alimentarea de 220V pentru acest panou.",
  route: "Pregateste cablurile panoului spre pozitia de alimentare declarata.",
  shared: "Acest panou primeste alimentarea dintr-un alt panou al ansamblului.",
  reserve: "Lasa rezerva de cablu pentru legatura finala dintre panouri.",
  afterAlignment: "Aceasta legatura se finalizeaza dupa alinierea panourilor.",
  unconfirmed: "Pozitia alimentarii nu este confirmata.",
  confirmed: "Configuratia electrica a ansamblului a fost confirmata.",
} as const;

export function readSegmentedElectrical(
  segmented: Record<string, unknown> | null | undefined,
): SegmentedElectrical | null {
  const raw = segmented?.electrical_connection_management;
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
  const row = raw as SegmentedElectrical;
  if (row.schema && row.schema !== SEGMENTED_ELECTRICAL_SCHEMA) return null;
  return row;
}

export function emptyPanelElectrical(panelId: string): PanelElectrical {
  return {
    panel_id: panelId,
    supply_mode: "UNCONFIRMED",
    shared_from_panel_id: null,
    service_point_position: null,
    custom_position_note: null,
    sketch_ref: null,
    cable_exit_position: null,
    routing_direction_note_ro: null,
    power_supply_group_id: null,
    letter_group_ref: null,
    workshop_prep: {
      cables_routed_toward_service: false,
      passages_prepared: false,
      labeled: false,
      reserve_required: false,
    },
    installation: {
      connect_to_client_220v: false,
      finalize_after_alignment: false,
    },
    notes_ro: null,
  };
}

export function ensureElectricalForPanels(
  panelIds: string[],
  current: SegmentedElectrical | null,
): SegmentedElectrical {
  const byId = new Map((current?.panels || []).map((p) => [p.panel_id, p]));
  const panels = panelIds.map((id) => byId.get(id) || emptyPanelElectrical(id));
  return {
    schema: SEGMENTED_ELECTRICAL_SCHEMA,
    contract_version: "acm_segmented_electrical_connection/v1",
    status: current?.status || "DRAFT",
    operator_confirmed: false,
    panels,
    inter_panel_connections: current?.inter_panel_connections || [],
    validation: current?.validation,
  };
}

export function buildConfirmElectricalPatch(current: SegmentedElectrical): SegmentedElectrical {
  return {
    ...current,
    schema: SEGMENTED_ELECTRICAL_SCHEMA,
    status: "CONFIRMED",
    operator_confirmed: true,
    confirmation: {
      message_code: "ELEC_CONFIRMED",
      message: ELECTRICAL_MESSAGES_RO.confirmed,
      authority: "OPERATOR",
    },
  };
}

export function buildDraftElectricalPatch(current: SegmentedElectrical): SegmentedElectrical {
  return {
    ...current,
    schema: SEGMENTED_ELECTRICAL_SCHEMA,
    status: "DRAFT",
    operator_confirmed: false,
  };
}

export function electricalConfirmBlocked(current: SegmentedElectrical): string[] {
  const blockers: string[] = [];
  for (const panel of current.panels || []) {
    if (panel.supply_mode === "UNCONFIRMED") {
      blockers.push(ELECTRICAL_MESSAGES_RO.unconfirmed);
    }
    if (panel.supply_mode === "SHARED_FROM_PANEL") {
      if (!panel.shared_from_panel_id) {
        blockers.push("Selecteaza panoul sursa pentru alimentarea partajata.");
      } else if (panel.shared_from_panel_id === panel.panel_id) {
        blockers.push("Un panou nu poate primi alimentarea de la el insusi.");
      }
    }
    if (panel.supply_mode === "DIRECT_220V" && panel.service_point_position === "CUSTOM") {
      if (!panel.custom_position_note && !panel.sketch_ref) {
        blockers.push("Pentru pozitie personalizata, adauga nota sau referinta de schita.");
      }
    }
    if (panel.supply_mode === "DIRECT_220V" && !panel.service_point_position) {
      blockers.push(ELECTRICAL_MESSAGES_RO.indicate);
    }
  }
  return [...new Set(blockers)];
}
