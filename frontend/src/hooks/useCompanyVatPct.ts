import { useCallback, useEffect, useState } from "react";

import { getCompanyCommercialSettings } from "@/api/companyCommercialSettings";
import { DEFAULT_VAT_PCT, normalizeVatPct } from "@/lib/companyCommercialSettings";

export function useCompanyVatPct(enabled = true) {
  const [vatPct, setVatPct] = useState<number>(DEFAULT_VAT_PCT);
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!enabled) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getCompanyCommercialSettings();
      setVatPct(normalizeVatPct(data.default_vat_pct));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load VAT settings");
      setVatPct(DEFAULT_VAT_PCT);
    } finally {
      setLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    reload();
  }, [reload]);

  return { vatPct, loading, error, reload };
}
