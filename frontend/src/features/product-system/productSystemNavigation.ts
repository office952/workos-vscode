import type { ProductTemplateEntity } from "@/lib/api";
import {
  filterActiveTemplatesForQuote,
  filterArchivedExperimentalTemplates,
  isActiveTemplateForQuote,
} from "@/lib/activeTemplateScope";

export type ProductSystemScreen = "library" | "editor";

export type LibraryTab = "active" | "archived" | "all";

export function getInitialProductSystemScreen(): ProductSystemScreen {
  return "library";
}

export function shouldShowEditorScreen(
  screen: ProductSystemScreen,
  draft: unknown | null
): boolean {
  return screen === "editor" && draft != null;
}

export function shouldShowLibraryScreen(screen: ProductSystemScreen): boolean {
  return screen === "library";
}

export function filterLibraryTemplates(
  templates: ProductTemplateEntity[],
  tab: LibraryTab,
  search: string
): ProductTemplateEntity[] {
  let scoped: ProductTemplateEntity[];
  switch (tab) {
    case "active":
      scoped = filterActiveTemplatesForQuote(templates);
      break;
    case "archived":
      scoped = filterArchivedExperimentalTemplates(templates);
      break;
    default:
      scoped = templates;
  }

  if (!search.trim()) return scoped;
  const q = search.toLowerCase();
  return scoped.filter(
    (t) =>
      t.template_code.toLowerCase().includes(q) ||
      (t.family_name || "").toLowerCase().includes(q) ||
      (t.description || "").toLowerCase().includes(q)
  );
}

export function isTemplateEditableForQuote(template: ProductTemplateEntity): boolean {
  return isActiveTemplateForQuote(template);
}

export function formatTemplateListDate(value: string | undefined): string | null {
  if (!value) return null;
  try {
    return new Date(value).toLocaleDateString("ro-RO");
  } catch {
    return null;
  }
}
