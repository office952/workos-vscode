import type { ProductTemplateEntity } from "@/lib/api";
import {
  filterActiveTemplatesForQuote,
  isOwnerValidActiveTemplate,
  OWNER_VALID_ACTIVE_TEMPLATE_CODE,
} from "@/lib/activeTemplateScope";

const LAST_TEMPLATE_KEY = "workos_product_system_last_template_id";
const RECENT_TEMPLATES_KEY = "workos_product_system_recent_templates";
const OPEN_COUNTS_KEY = "workos_product_system_open_counts";
const MAX_RECENT = 12;

type RecentEntry = { id: number; openedAt: string };

function readRecent(): RecentEntry[] {
  try {
    const raw = localStorage.getItem(RECENT_TEMPLATES_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter((e): e is RecentEntry => {
        return (
          !!e &&
          typeof e === "object" &&
          typeof (e as RecentEntry).id === "number" &&
          typeof (e as RecentEntry).openedAt === "string"
        );
      })
      .slice(0, MAX_RECENT);
  } catch {
    return [];
  }
}

function readOpenCounts(): Record<string, number> {
  try {
    const raw = localStorage.getItem(OPEN_COUNTS_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as unknown;
    if (!parsed || typeof parsed !== "object") return {};
    return parsed as Record<string, number>;
  } catch {
    return {};
  }
}

export function getLastOpenedTemplateId(): number | null {
  try {
    const raw = localStorage.getItem(LAST_TEMPLATE_KEY);
    if (!raw) return null;
    const id = Number(raw);
    return Number.isFinite(id) ? id : null;
  } catch {
    return null;
  }
}

export function getRecentTemplateIds(): number[] {
  return readRecent().map((e) => e.id);
}

/** Browser-local open frequency only — not backend usage metrics. */
export function getMostUsedTemplateIds(): number[] {
  const counts = readOpenCounts();
  return Object.entries(counts)
    .sort(([, a], [, b]) => b - a)
    .map(([id]) => Number(id))
    .filter((id) => Number.isFinite(id));
}

export function recordTemplateOpened(templateId: number): void {
  try {
    localStorage.setItem(LAST_TEMPLATE_KEY, String(templateId));

    const recent = readRecent().filter((e) => e.id !== templateId);
    recent.unshift({ id: templateId, openedAt: new Date().toISOString() });
    localStorage.setItem(RECENT_TEMPLATES_KEY, JSON.stringify(recent.slice(0, MAX_RECENT)));

    const counts = readOpenCounts();
    const key = String(templateId);
    counts[key] = (counts[key] ?? 0) + 1;
    localStorage.setItem(OPEN_COUNTS_KEY, JSON.stringify(counts));
  } catch {
    // localStorage unavailable — ignore
  }
}

function findTemplateById(
  templates: ProductTemplateEntity[],
  id: number | null
): ProductTemplateEntity | null {
  if (id == null) return null;
  return templates.find((t) => t.id === id) ?? null;
}

function sortByCreatedDesc(templates: ProductTemplateEntity[]): ProductTemplateEntity[] {
  return [...templates].sort((a, b) => {
    const ta = a.created_at ? Date.parse(a.created_at) : 0;
    const tb = b.created_at ? Date.parse(b.created_at) : 0;
    return tb - ta;
  });
}

/**
 * Safe frontend default — no invented backend usage counts.
 * Priority: last opened → local open count → latest created → volumetric → first active.
 */
export function resolveDefaultTemplate(
  templates: ProductTemplateEntity[]
): ProductTemplateEntity | null {
  if (templates.length === 0) return null;

  const last = findTemplateById(templates, getLastOpenedTemplateId());
  if (last) return last;

  for (const id of getMostUsedTemplateIds()) {
    const match = findTemplateById(templates, id);
    if (match) return match;
  }

  const latest = sortByCreatedDesc(templates)[0];
  if (latest) return latest;

  const volumetric = templates.find((t) =>
    isOwnerValidActiveTemplate(t.template_code)
  );
  if (volumetric) return volumetric;

  return filterActiveTemplatesForQuote(templates)[0] ?? null;
}

export function getDefaultTemplateCodeHint(): string {
  return OWNER_VALID_ACTIVE_TEMPLATE_CODE;
}
