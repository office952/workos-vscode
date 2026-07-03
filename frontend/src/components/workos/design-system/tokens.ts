/**
 * WorkOS design-system tokens — TypeScript source for primitives.
 * Document reference: docs/design/WORKOS_UI_TOKENS_DRAFT.md
 *
 * No global CSS; Tailwind utility classes only.
 */

export const woSurfaces = {
  app: "#0A0F1C",
  shell: "#0D1321",
  surface: "#111827",
  surfaceRaised: "#1A2236",
  input: "#0B1220",
  inset: "#0B0E13",
} as const;

export const woBorders = {
  subtle: "#1E293B",
  strong: "#2A3548",
} as const;

export const woText = {
  primary: "#F1F5F9",
  secondary: "#CBD5E1",
  muted: "#94A3B8",
  dim: "#5C6B80",
} as const;

export const woAccent = {
  primary: "#3B82F6",
  primaryHover: "#60A5FA",
  violet: "#8B5CF6",
  cyan: "#22D3EE",
} as const;

export type ToneKey =
  | "slate"
  | "blue"
  | "cyan"
  | "violet"
  | "emerald"
  | "amber"
  | "orange"
  | "red";

export type ToneClasses = {
  bg: string;
  text: string;
  border: string;
  dot: string;
};

export const semanticTones: Record<ToneKey, ToneClasses> = {
  slate: {
    bg: "bg-slate-800/80",
    text: "text-slate-300",
    border: "border-slate-600",
    dot: "bg-slate-500",
  },
  blue: {
    bg: "bg-blue-900/40",
    text: "text-blue-300",
    border: "border-blue-700",
    dot: "bg-blue-500",
  },
  cyan: {
    bg: "bg-cyan-900/40",
    text: "text-cyan-300",
    border: "border-cyan-700",
    dot: "bg-cyan-500",
  },
  violet: {
    bg: "bg-purple-900/40",
    text: "text-purple-300",
    border: "border-purple-700",
    dot: "bg-purple-500",
  },
  emerald: {
    bg: "bg-emerald-900/50",
    text: "text-emerald-200",
    border: "border-emerald-700",
    dot: "bg-emerald-500",
  },
  amber: {
    bg: "bg-amber-900/50",
    text: "text-amber-200",
    border: "border-amber-700",
    dot: "bg-amber-500",
  },
  orange: {
    bg: "bg-orange-900/40",
    text: "text-orange-300",
    border: "border-orange-700",
    dot: "bg-orange-500",
  },
  red: {
    bg: "bg-red-900/50",
    text: "text-red-200",
    border: "border-red-700",
    dot: "bg-red-500",
  },
};

export type StatusDomain =
  | "quote"
  | "order"
  | "executionTask"
  | "payment"
  | "reality"
  | "intake"
  | "productSystem"
  | "pricing"
  | "generic";

export type SourceState =
  | "db"
  | "empty"
  | "mock"
  | "demo"
  | "error"
  | "loading"
  | "mixed"
  | string
  | null
  | undefined;

const quoteStatusTones: Record<string, ToneKey> = {
  draft: "slate",
  priced: "violet",
  sent: "blue",
  trimisa: "blue",
  viewed: "cyan",
  negotiating: "amber",
  in_negociere: "amber",
  accepted: "emerald",
  acceptata: "emerald",
  rejected: "red",
  refuzata: "red",
  expired: "orange",
  expirata: "orange",
  cancelled: "slate",
  anulata: "slate",
};

const orderStatusTones: Record<string, ToneKey> = {
  created: "slate",
  confirmed: "blue",
  locked: "violet",
  in_execution: "emerald",
  in_productie: "emerald",
  completed: "emerald",
  delivered: "cyan",
  cancelled: "red",
  anulat: "red",
};

const executionTaskStatusTones: Record<string, ToneKey> = {
  created: "slate",
  planned: "slate",
  assigned: "blue",
  in_progress: "emerald",
  running: "emerald",
  paused: "amber",
  blocked: "red",
  done: "emerald",
  completed: "emerald",
  cancelled: "slate",
  anulat: "slate",
};

const paymentStatusTones: Record<string, ToneKey> = {
  due: "amber",
  unpaid: "amber",
  pending: "amber",
  neplatit: "amber",
  partial: "orange",
  advance: "cyan",
  paid: "emerald",
  platit: "emerald",
  cancelled: "slate",
  adjusted: "violet",
  missing_base: "red",
};

const realityStatusTones: Record<string, ToneKey> = {
  reported: "cyan",
  verified: "emerald",
  valid: "emerald",
  invalidated: "red",
};

const intakeStatusTones: Record<string, ToneKey> = {
  new: "slate",
  in_review: "blue",
  needs_info: "amber",
  ready_for_quote: "emerald",
  blocked: "red",
  cancelled: "slate",
  quoted: "violet",
  converted: "violet",
};

const productSystemStatusTones: Record<string, ToneKey> = {
  active: "emerald",
  inactive: "slate",
  draft: "violet",
  archived: "slate",
  legacy: "slate",
  experimental: "violet",
  approved: "emerald",
  configured: "emerald",
  unconfigured: "amber",
  needs_review: "amber",
  needs_owner_review: "orange",
};

const pricingStatusTones: Record<string, ToneKey> = {
  active: "emerald",
  inactive: "slate",
  draft: "violet",
  archived: "slate",
  owner_confirmed: "emerald",
  needs_owner_review: "amber",
  needs_owner_input: "orange",
  needs_review: "amber",
  needs_price: "orange",
  missing_price: "red",
  missing: "red",
  reviewed: "emerald",
  approved: "emerald",
  configured: "emerald",
  unconfigured: "amber",
  ready: "emerald",
  blocked: "red",
  missing_source: "orange",
  no_price: "red",
  estimated: "amber",
  accepted_override: "emerald",
  accepted: "emerald",
  pending: "amber",
  rejected: "red",
  stale: "orange",
};

const sourceTones: Record<string, ToneKey> = {
  db: "emerald",
  empty: "emerald",
  mock: "amber",
  demo: "amber",
  error: "red",
  loading: "slate",
  mixed: "slate",
};

const quoteStatusLabels: Record<string, string> = {
  draft: "Draft",
  priced: "Prețuit",
  sent: "Trimis",
  trimisa: "Trimis",
  viewed: "Vizualizat",
  negotiating: "Negociere",
  in_negociere: "Negociere",
  accepted: "Acceptat",
  acceptata: "Acceptat",
  rejected: "Respins",
  refuzata: "Respins",
  expired: "Expirat",
  expirata: "Expirat",
  cancelled: "Anulat",
  anulata: "Anulat",
};

const orderStatusLabels: Record<string, string> = {
  created: "Creat",
  confirmed: "Confirmat",
  locked: "Înghețat",
  in_execution: "În execuție",
  in_productie: "În producție",
  completed: "Finalizat",
  delivered: "Livrat",
  cancelled: "Anulat",
  anulat: "Anulat",
};

const executionTaskStatusLabels: Record<string, string> = {
  created: "Planificat",
  planned: "Planificat",
  assigned: "Alocat",
  in_progress: "În lucru",
  running: "În lucru",
  paused: "Pauză",
  blocked: "Blocat",
  done: "Finalizat",
  completed: "Finalizat",
  cancelled: "Anulat",
  anulat: "Anulat",
};

const paymentStatusLabels: Record<string, string> = {
  due: "Neplătit",
  unpaid: "Neplătit",
  pending: "Neplătit",
  neplatit: "Neplătit",
  partial: "Parțial plătit",
  advance: "Avans",
  paid: "Plătit",
  platit: "Plătit",
  cancelled: "Anulat",
  adjusted: "Ajustat",
  missing_base: "Bază lipsă",
};

const realityStatusLabels: Record<string, string> = {
  reported: "Raportat",
  verified: "Verificat",
  valid: "Verificat",
  invalidated: "Invalidat",
};

const intakeStatusLabels: Record<string, string> = {
  new: "Nou",
  in_review: "În Analiză",
  needs_info: "Lipsă Info",
  ready_for_quote: "Gata pt. Ofertă",
  blocked: "Blocat",
  cancelled: "Anulat",
  quoted: "Ofertat",
  converted: "Convertit",
};

const productSystemStatusLabels: Record<string, string> = {
  active: "Activ",
  inactive: "Inactiv",
  draft: "Draft",
  archived: "Arhivat",
  legacy: "Legacy",
  experimental: "Experimental",
  approved: "Aprobat",
  configured: "Configurat",
  unconfigured: "Neconfigurat",
  needs_review: "Necesită revizuire",
  needs_owner_review: "Necesită owner",
};

const pricingStatusLabels: Record<string, string> = {
  active: "Activ",
  inactive: "Inactiv",
  draft: "Draft",
  archived: "Arhivat",
  owner_confirmed: "Owner-confirmed",
  needs_owner_review: "Necesită owner",
  needs_owner_input: "Necesită owner",
  needs_review: "Necesită verificare",
  needs_price: "Necesită preț",
  missing_price: "Lipsă preț",
  missing: "Lipsă",
  reviewed: "Revizuit",
  approved: "Aprobat",
  configured: "Configurat",
  unconfigured: "Neconfigurat",
  ready: "Pregătit",
  blocked: "Blocat",
  missing_source: "Sursă lipsă",
  no_price: "Preț lipsă",
  estimated: "Estimat",
  accepted_override: "Acceptat (override)",
  accepted: "Verificată",
  pending: "În așteptare",
  rejected: "Respins",
  stale: "Sursă învechită",
};

const sourceLabels: Record<string, string> = {
  db: "Live DB",
  empty: "Live DB (gol)",
  mock: "Mock Data",
  demo: "Demo",
  error: "Source Error",
  loading: "Loading",
  mixed: "Mixed Source",
};

const domainToneMaps: Record<StatusDomain, Record<string, ToneKey>> = {
  quote: quoteStatusTones,
  order: orderStatusTones,
  executionTask: executionTaskStatusTones,
  payment: paymentStatusTones,
  reality: realityStatusTones,
  intake: intakeStatusTones,
  productSystem: productSystemStatusTones,
  pricing: pricingStatusTones,
  generic: {
    ...quoteStatusTones,
    ...orderStatusTones,
    ...executionTaskStatusTones,
    ...paymentStatusTones,
    ...realityStatusTones,
    ...intakeStatusTones,
    ...productSystemStatusTones,
    ...pricingStatusTones,
  },
};

const domainLabelMaps: Record<StatusDomain, Record<string, string>> = {
  quote: quoteStatusLabels,
  order: orderStatusLabels,
  executionTask: executionTaskStatusLabels,
  payment: paymentStatusLabels,
  reality: realityStatusLabels,
  intake: intakeStatusLabels,
  productSystem: productSystemStatusLabels,
  pricing: pricingStatusLabels,
  generic: {
    ...quoteStatusLabels,
    ...orderStatusLabels,
    ...executionTaskStatusLabels,
    ...paymentStatusLabels,
    ...realityStatusLabels,
    ...intakeStatusLabels,
    ...productSystemStatusLabels,
    ...pricingStatusLabels,
  },
};

export function normalizeStatusKey(
  status: string | null | undefined,
): string {
  if (status == null) return "";
  const trimmed = String(status).trim();
  if (!trimmed) return "";
  return trimmed.toLowerCase().replace(/\s+/g, "_");
}

export function getToneClasses(tone: ToneKey): ToneClasses {
  return semanticTones[tone] ?? semanticTones.slate;
}

export function getStatusTone(
  domain: StatusDomain,
  status: string | null | undefined,
): ToneKey {
  const key = normalizeStatusKey(status);
  if (!key) return "slate";

  const domainMap = domainToneMaps[domain] ?? domainToneMaps.generic;
  const tone = domainMap[key];
  if (tone) return tone;

  if (domain !== "generic") {
    const fallback = domainToneMaps.generic[key];
    if (fallback) return fallback;
  }

  return "slate";
}

export function getSourceTone(source: SourceState): ToneKey {
  const key = normalizeStatusKey(source);
  if (!key) return "slate";
  return sourceTones[key] ?? "slate";
}

export function normalizeSourceLabel(source: SourceState): string {
  const key = normalizeStatusKey(source);
  if (!key) return "Unknown Source";
  return sourceLabels[key] ?? key;
}

export function normalizeStatusLabel(
  domain: StatusDomain,
  status: string | null | undefined,
): string {
  const key = normalizeStatusKey(status);
  if (!key) return "Necunoscut";

  const domainMap = domainLabelMaps[domain] ?? domainLabelMaps.generic;
  const label = domainMap[key];
  if (label) return label;

  if (domain !== "generic") {
    const fallback = domainLabelMaps.generic[key];
    if (fallback) return fallback;
  }

  return key
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export const statusBadgeSizeClasses = {
  sm: "px-2 py-0.5 text-[10px]",
  md: "px-2.5 py-1 text-xs",
  lg: "px-3 py-1.5 text-sm",
} as const;

/** Muted emerald variant for live-empty source indicator. */
export const sourceEmptyToneClasses: ToneClasses = {
  bg: "bg-emerald-900/20",
  text: "text-emerald-300/90",
  border: "border-emerald-800/30",
  dot: "bg-emerald-500/70",
};

/** Non-live mixed source — slate, not confused with Live DB. */
export const sourceMixedToneClasses: ToneClasses = {
  bg: "bg-slate-700/50",
  text: "text-slate-300",
  border: "border-slate-600/40",
  dot: "bg-slate-500",
};
