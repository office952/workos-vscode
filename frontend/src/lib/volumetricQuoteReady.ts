export interface QuoteGateClassified {
  cost_blockers?: string[];
  readiness_blockers?: string[];
  geometry_blockers?: string[];
  vector_blockers?: string[];
  production_metadata_blockers?: string[];
  capture_blockers?: string[];
  warnings?: string[];
  acknowledgement_pending?: string[];
}

export interface VolumetricQuoteGate {
  simulate_ready?: boolean;
  ready_for_quote?: boolean;
  can_create_commercial_quote?: boolean;
  requires_acknowledgement?: boolean;
  blockers?: string[];
  warnings?: string[];
  notes?: string[];
  reason_codes?: string[];
  classified?: QuoteGateClassified;
}

export type VolumetricCommercialReadinessStatus =
  | "blocked"
  | "ready"
  | "ready_with_warnings"
  | "requires_acknowledgement";

export type ReadinessItemStatus =
  | "blocking"
  | "needs_acknowledgement"
  | "satisfied"
  | "informational";

export interface ClassifiedReadinessItem {
  code: string;
  label: string;
  status: ReadinessItemStatus;
}

export interface QuoteReadinessSnapshot {
  quoteGate?: VolumetricQuoteGate;
  readinessResult?: Record<string, unknown>;
  policy?: {
    requires_warning_acknowledgement?: boolean;
    quote_gate?: string;
    authority?: string;
  };
  templateCode?: string;
}

const BLOCKER_MESSAGES: Record<string, string> = {
  letters_vector_file_required: "Lipsește fișierul vector pentru litere.",
  vector_layer_mapping_pending: "Mapează layerul principal al literelor.",
  vector_manual_review_required:
    "Confirmă verificarea manuală a vectorului sau folosește analiză geometrică validă.",
  vector_analysis_failed: "Analiza vectorului a eșuat — review manual necesar.",
  "quote_input_missing:letter_face_area_m2": "Completează aria, perimetrul și numărul de litere.",
  "quote_input_missing:letter_perimeter_m": "Completează aria, perimetrul și numărul de litere.",
  "quote_input_missing:letter_count": "Completează aria, perimetrul și numărul de litere.",
  "production_metadata_missing:face_vinyl_color_code":
    "Completează codul/culoarea foliei Oracal.",
  "production_metadata_missing:face_vinyl_roll_width_mm":
    "Completează lățimea rolei Oracal (1000 sau 1260 mm).",
  "production_metadata_missing:paint_ral_code": "Completează codul RAL pentru vopsire.",
};

const WARNING_MESSAGES: Record<string, string> = {
  vector_analysis_pending:
    "Fișierul vector este atașat; analiza automată nu este încă finalizată (review manual acceptat).",
  operations_missing: "Șablonul nu listează operațiile — verifică înainte de conversie.",
  components_missing: "Șablonul nu listează componentele — verifică înainte de conversie.",
  blueprint_dossier_missing: "Dossier blueprint lipsă — verifică pregătirea șablonului.",
};

const WARNING_PREFIX_MESSAGES: [string, string][] = [
  [
    "volumetric_psu_wattage_variant_pricing:",
    "Variante PSU în registry — selectează puterea sursei la ofertare.",
  ],
  [
    "volumetric_profile_depth_variant_pricing:",
    "Variante profil lateral în registry — confirmă adâncimea cantului la ofertare.",
  ],
  [
    "volumetric_profile_return_depth_required_at_quote:",
    "Adâncimea profilului lateral trebuie confirmată în quote_input la ofertare.",
  ],
  [
    "volumetric_psu_wattage_required_at_quote:",
    "Puterea PSU trebuie confirmată în quote_input la ofertare.",
  ],
  ["acknowledgement_required:", "Confirmare necesară înainte de conversie:"],
];

export function humanizeQuoteBlocker(code: string): string {
  if (BLOCKER_MESSAGES[code]) return BLOCKER_MESSAGES[code];
  if (code.includes("captured_option_requires_separate_template")) {
    return "Panoul ACM casetat trebuie ofertat prin template separat.";
  }
  if (code.includes("mounting_bar_profile_price_missing")) {
    return "Profilul de bară selectat nu are preț confirmat.";
  }
  if (code.startsWith("quote_input_missing:")) {
    return "Completează aria, perimetrul și numărul de litere.";
  }
  return humanizeQuoteWarning(code);
}

export function humanizeQuoteWarning(code: string): string {
  if (WARNING_MESSAGES[code]) return WARNING_MESSAGES[code];
  for (const [prefix, message] of WARNING_PREFIX_MESSAGES) {
    if (code === prefix || code.startsWith(prefix)) return message;
  }
  if (code.startsWith("technical_readiness:")) {
    return "Pregătire tehnică necesită review (fără blockers duri).";
  }
  if (code.startsWith("costengine_readiness:")) {
    return "CostEngine raportează avertismente la ofertare.";
  }
  if (code === "ready_for_quote:false") {
    return "Flag legacy ready_for_quote=false — gate volumetric decide conversia.";
  }
  return code;
}

export function groupQuoteGateBlockers(gate: VolumetricQuoteGate | null | undefined) {
  const classified = gate?.classified ?? {};
  return {
    vector: classified.vector_blockers ?? [],
    geometry: classified.geometry_blockers ?? [],
    cost: classified.cost_blockers ?? [],
    metadata: classified.production_metadata_blockers ?? [],
    dossier: classified.readiness_blockers ?? [],
    other: classified.capture_blockers ?? [],
  };
}

export function deriveVolumetricCommercialReadinessStatus(
  gate: VolumetricQuoteGate | null | undefined
): VolumetricCommercialReadinessStatus {
  if (!gate || gate.can_create_commercial_quote !== true) return "blocked";
  if (gate.requires_acknowledgement) return "requires_acknowledgement";
  if ((gate.warnings?.length ?? 0) > 0) return "ready_with_warnings";
  return "ready";
}

export function readinessStatusLabel(status: VolumetricCommercialReadinessStatus): string {
  switch (status) {
    case "ready":
      return "Ready";
    case "ready_with_warnings":
      return "Ready with warnings";
    case "requires_acknowledgement":
      return "Requires acknowledgement";
    default:
      return "Blocked";
  }
}

export function classifyQuoteGateItems(
  gate: VolumetricQuoteGate | null | undefined
): ClassifiedReadinessItem[] {
  if (!gate) return [];

  const items: ClassifiedReadinessItem[] = [];
  const seen = new Set<string>();
  const ackPending = new Set(gate.classified?.acknowledgement_pending ?? []);
  const blockerSet = new Set(gate.blockers ?? []);

  const push = (code: string, status: ReadinessItemStatus) => {
    if (!code || seen.has(code)) return;
    seen.add(code);
    items.push({
      code,
      label:
        status === "blocking"
          ? humanizeQuoteBlocker(code)
          : humanizeQuoteWarning(code),
      status,
    });
  };

  const grouped = groupQuoteGateBlockers(gate);
  for (const codes of Object.values(grouped)) {
    for (const code of codes) push(code, "blocking");
  }
  for (const code of gate.blockers ?? []) {
    if (!seen.has(code)) push(code, "blocking");
  }
  for (const code of ackPending) {
    if (!blockerSet.has(code)) push(code, "needs_acknowledgement");
  }
  for (const code of gate.warnings ?? []) {
    if (blockerSet.has(code) || ackPending.has(code)) continue;
    push(code, "informational");
  }
  for (const code of gate.reason_codes ?? []) {
    if (code.startsWith("acknowledgement_required:")) {
      const inner = code.slice("acknowledgement_required:".length);
      if (!seen.has(inner)) push(inner, "needs_acknowledgement");
    }
  }

  return items;
}

export function summarizeVolumetricQuoteGate(gate: VolumetricQuoteGate | null | undefined) {
  const items = classifyQuoteGateItems(gate);
  return {
    status: deriveVolumetricCommercialReadinessStatus(gate),
    blockerCount: items.filter((i) => i.status === "blocking").length,
    warningCount: items.filter((i) => i.status === "informational").length,
    acknowledgementPendingCount: items.filter(
      (i) => i.status === "needs_acknowledgement"
    ).length,
    canCreate: gate?.can_create_commercial_quote === true,
    requiresAcknowledgement: gate?.requires_acknowledgement === true,
    reasonCodes: gate?.reason_codes ?? [],
  };
}

function isCanonicalSnapshot(obj: unknown): boolean {
  if (!obj || typeof obj !== "object" || Array.isArray(obj)) return false;
  const snap = obj as Record<string, unknown>;
  return (
    "product_definition" in snap &&
    ("cost_result" in snap || "pricing" in snap || "price" in snap)
  );
}

function parseReadinessPayload(
  readiness: unknown,
  productId?: string
): QuoteReadinessSnapshot | null {
  if (!readiness || typeof readiness !== "object") return null;
  const rr = readiness as Record<string, unknown>;
  const quoteGate = rr.quote_gate as VolumetricQuoteGate | undefined;
  if (!quoteGate && !rr.overall_status) return null;
  const policy = rr.policy as QuoteReadinessSnapshot["policy"] | undefined;
  return {
    quoteGate,
    readinessResult: rr,
    policy,
    templateCode: productId,
  };
}

/** Extract volumetric readiness from persisted quote.line_items JSON. */
export function extractQuoteReadinessFromLineItems(
  raw?: string
): QuoteReadinessSnapshot | null {
  if (!raw) return null;
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return null;
  }
  if (!parsed || typeof parsed !== "object") return null;

  if (Array.isArray(parsed)) return null;

  const root = parsed as Record<string, unknown>;

  if (root.readiness_result) {
    const inner = isCanonicalSnapshot(root.line_items)
      ? (root.line_items as Record<string, unknown>).product_definition
      : undefined;
    const productId =
      inner && typeof inner === "object"
        ? String((inner as Record<string, unknown>).product_id ?? "")
        : undefined;
    return parseReadinessPayload(root.readiness_result, productId || undefined);
  }

  if (isCanonicalSnapshot(root)) {
    const snap = root as Record<string, unknown>;
    const pd = snap.product_definition as Record<string, unknown> | undefined;
    const productId = pd?.product_id ? String(pd.product_id) : undefined;
    if (snap.readiness_result) {
      return parseReadinessPayload(snap.readiness_result, productId);
    }
    if (snap.quote_gate) {
      return {
        quoteGate: snap.quote_gate as VolumetricQuoteGate,
        readinessResult: snap,
        templateCode: productId,
      };
    }
  }

  if (root.line_items && typeof root.line_items === "object") {
    const inner = root.line_items as Record<string, unknown>;
    const pd = inner.product_definition as Record<string, unknown> | undefined;
    const productId = pd?.product_id ? String(pd.product_id) : undefined;
    if (inner.readiness_result) {
      return parseReadinessPayload(inner.readiness_result, productId);
    }
  }

  return null;
}

export function isVolumetricCommercialQuoteReadiness(
  snapshot: QuoteReadinessSnapshot | null | undefined
): boolean {
  if (!snapshot?.quoteGate) return false;
  const code = snapshot.templateCode ?? "";
  return (
    code.includes("VOLUMETRIC") ||
    code.includes("TPL-VOLUMETRIC-LETTERS") ||
    snapshot.quoteGate.classified !== undefined
  );
}
