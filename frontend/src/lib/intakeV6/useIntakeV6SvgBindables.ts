/**
 * Loads Product System svg_bindable_components for Intake V6 Step 1 cards.
 * Read-only availability — not a second assignment SoT.
 */

import { useEffect, useState } from "react";
import { productTemplateAvailabilityApi, type SvgBindableComponent } from "@/lib/api";
import { filterBindableForUi } from "./svgComponentBindings";

export function useIntakeV6SvgBindables(templateCode: string | null | undefined) {
  const [bindables, setBindables] = useState<SvgBindableComponent[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [usingLegacyFallback, setUsingLegacyFallback] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const code = (templateCode ?? "").trim();
    if (!code) {
      setBindables([]);
      setLoadError(null);
      setUsingLegacyFallback(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setLoadError(null);
    setUsingLegacyFallback(false);
    productTemplateAvailabilityApi
      .list({ include_runtime_modules: true, include_archived: false })
      .then((res) => {
        if (cancelled) return;
        const item = res.items.find((row) => row.template_code === code);
        const list = filterBindableForUi(item?.svg_bindable_components ?? []);
        if (!item || list.length === 0) {
          setBindables([]);
          setLoadError("Product System nu a returnat componente SVG-bindable pentru template.");
          setUsingLegacyFallback(true);
          return;
        }
        setBindables(list);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setBindables([]);
        setUsingLegacyFallback(true);
        setLoadError(err instanceof Error ? err.message : "Nu s-a putut încărca availability.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [templateCode]);

  return { bindables, loadError, usingLegacyFallback, loading };
}
