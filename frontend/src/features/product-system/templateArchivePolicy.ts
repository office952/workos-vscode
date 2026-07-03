import { isActiveTemplateForQuote } from "@/lib/activeTemplateScope";

export function getTemplateArchivePolicy(
  template: { active?: boolean | null; template_code: string },
  activeQuoteTemplateCount: number
): {
  isArchivedForQuote: boolean;
  canArchive: boolean;
  blockReason: string | null;
} {
  const isArchivedForQuote = !isActiveTemplateForQuote(template);

  if (isArchivedForQuote) {
    return {
      isArchivedForQuote: true,
      canArchive: false,
      blockReason: null,
    };
  }

  if (activeQuoteTemplateCount <= 1) {
    return {
      isArchivedForQuote: false,
      canArchive: false,
      blockReason:
        "Nu poți arhiva ultimul șablon activ. Creează sau activează alt șablon înainte.",
    };
  }

  return {
    isArchivedForQuote: false,
    canArchive: true,
    blockReason: null,
  };
}
