/**
 * Safe parsing for intake_requests.dimensions — DB may return null.
 */

export function normalizeIntakeDimensionsText(
  dimensions: string | null | undefined
): string {
  const trimmed = (dimensions ?? "").trim();
  return trimmed || "—";
}

export function parseIntakeDimensionNumbers(
  dimensions: string | null | undefined
): number[] {
  const text = normalizeIntakeDimensionsText(dimensions);
  if (text === "—") return [];
  return (
    text
      .match(/\d+/g)
      ?.map(Number)
      .filter((n) => Number.isFinite(n) && n > 0) ?? []
  );
}

export function parseIntakeDimensionsStruct(
  dimensions: string | null | undefined
): { width?: number; height?: number; depth?: number; unit: "mm" } | null {
  const numbers = parseIntakeDimensionNumbers(dimensions);
  if (numbers.length === 0) return null;
  return {
    width: numbers[0],
    height: numbers[1],
    depth: numbers[2],
    unit: "mm",
  };
}
