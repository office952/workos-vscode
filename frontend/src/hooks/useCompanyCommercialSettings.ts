import { useCallback, useEffect, useState } from "react";

import { getCompanyCommercialSettings } from "@/api/companyCommercialSettings";
import {
  DEFAULT_VAT_PCT,
  normalizeVatPct,
  parseConfiguredEurToRonRate,
} from "@/lib/companyCommercialSettings";

export function useCompanyCommercialSettings(enabled = true) {
  const [vatPct, setVatPct] = useState<number>(DEFAULT_VAT_PCT);
  const [eurToRonRate, setEurToRonRate] = useState<number | null>(null);
  const [fxConfigured, setFxConfigured] = useState(false);
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!enabled) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getCompanyCommercialSettings();
      setVatPct(normalizeVatPct(data.default_vat_pct));
      const rate = parseConfiguredEurToRonRate(data.eur_to_ron_rate);
      setEurToRonRate(rate);
      setFxConfigured(rate != null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load commercial settings");
      setVatPct(DEFAULT_VAT_PCT);
      setEurToRonRate(null);
      setFxConfigured(false);
    } finally {
      setLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    reload();
  }, [reload]);

  return { vatPct, eurToRonRate, fxConfigured, loading, error, reload };
}
