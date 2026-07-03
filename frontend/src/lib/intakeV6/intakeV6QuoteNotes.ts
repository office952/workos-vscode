export function readIntakeV6QuoteHumanSummary(notes: string | null | undefined): string | null {
  if (!notes?.trim()) return null;
  const trimmed = notes.trim();
  if (!trimmed.startsWith("{")) return trimmed;
  try {
    const parsed = JSON.parse(trimmed) as Record<string, unknown>;
    const summary = parsed.human_summary;
    return typeof summary === "string" && summary.trim() ? summary.trim() : null;
  } catch {
    return null;
  }
}

export function shouldHideRawIntakeV6QuoteNotes(notes: string | null | undefined): boolean {
  if (!notes?.trim()) return false;
  return notes.trim().startsWith("{") && readIntakeV6QuoteHumanSummary(notes) != null;
}
