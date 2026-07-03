import type { Quote } from "@/lib/mockData";

export function isIntakeV6Quote(quote: Pick<Quote, "intakeId" | "id"> | null | undefined): boolean {
  if (!quote) return false;
  const intakeCode = quote.intakeId?.trim() ?? "";
  if (intakeCode.startsWith("IV6-")) return true;
  return /^Q-V6-IV6-/i.test(quote.id?.trim() ?? "");
}

export function isUnpricedIntakeV6Quote(
  quote: Pick<Quote, "intakeId" | "id" | "grandTotal" | "status"> | null | undefined,
): boolean {
  if (!quote || !isIntakeV6Quote(quote)) return false;
  if (quote.status !== "draft") return false;
  return !(quote.grandTotal > 0);
}

export function formatV6QuoteTotalLabel(
  quote: Pick<Quote, "intakeId" | "id" | "grandTotal" | "status">,
  formattedTotal: string,
): string {
  if (isUnpricedIntakeV6Quote(quote)) {
    return "Nepretuit (draft V6)";
  }
  return formattedTotal;
}
