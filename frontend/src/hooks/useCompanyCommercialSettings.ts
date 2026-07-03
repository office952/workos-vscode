import { useCallback, useEffect, useState } from "react";

import { getCompanyCommercialSettings } from "@/api/companyCommercialSettings";
import {
  DEFAULT_EUR_TO_RON_RATE,
  DEFAULT_VAT_PCT,
  normalizeEurToRonRate,
  normalizeVatPct,
} from "@/lib/companyCommercialSettings";

export function useCompanyCommercialSettings(enabled = true) {
  const [vatPct, setVatPct] = useState<number>(DEFAULT_VAT_PCT);
  const [eurToRonRate, setEurToRonRate] = useState<number>(DEFAULT_EUR_TO_RON_RATE);
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!enabled) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getCompanyCommercialSettings();
      setVatPct(normalizeVatPct(data.default_vat_pct));
      setEurToRonRate(normalizeEurToRonRate(data.eur_to_ron_rate));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load commercial settings");
      setVatPct(DEFAULT_VAT_PCT);
      setEurToRonRate(DEFAULT_EUR_TO_RON_RATE);
    } finally {
      setLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    reload();
  }, [reload]);

  return { vatPct, eurToRonRate, loading, error, reload };
}
