import { useEffect, useState } from "react";
import {
  getProductAggregate,
  type ProductAggregate,
} from "@/api/productAggregate";
import { getAggregateDisplayCounts, hasParentComponentsEmptyWarning } from "./productAggregateDisplay";

export type LibraryAggregateSummary = {
  parentCounts: { components: number; operations: number; materials: number };
  aggregateCounts: { components: number; operations: number; materials: number } | null;
  showDualCounts: boolean;
};

export function useProductAggregateLibrarySummaries(templateCodes: string[]) {
  const [summaries, setSummaries] = useState<Map<string, LibraryAggregateSummary>>(new Map());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const codes = [...new Set(templateCodes.map((c) => c.trim()).filter(Boolean))];
    if (!codes.length) {
      setSummaries(new Map());
      return;
    }

    let cancelled = false;
    setLoading(true);

    Promise.all(
      codes.map(async (code) => {
        try {
          const aggregate: ProductAggregate = await getProductAggregate(code);
          const showDual = hasParentComponentsEmptyWarning(aggregate);
          const parent = aggregate.provenance_summary?.parent ?? {};
          return {
            code,
            summary: {
              parentCounts: {
                components: parent.components ?? 0,
                operations: parent.operations ?? 0,
                materials: parent.materials ?? 0,
              },
              aggregateCounts: showDual ? getAggregateDisplayCounts(aggregate) : null,
              showDualCounts: showDual,
            } satisfies LibraryAggregateSummary,
          };
        } catch {
          return null;
        }
      }),
    ).then((results) => {
      if (cancelled) return;
      const next = new Map<string, LibraryAggregateSummary>();
      for (const row of results) {
        if (row) next.set(row.code, row.summary);
      }
      setSummaries(next);
      setLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, [templateCodes.join("|")]);

  return { summaries, loading };
}
