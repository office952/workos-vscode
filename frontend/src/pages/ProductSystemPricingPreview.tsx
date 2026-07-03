import { useMemo, useState } from "react";
import { useCompanyVatPct } from "@/hooks/useCompanyVatPct";
import { AlertTriangle, Calculator, Loader2, ShieldCheck, FileText } from "lucide-react";
import { productSystemPricingPreviewAdminApi, type ProductSystemPricingPreviewResult } from "@/api/productSystemPricingPreviewAdmin";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";

function fmtMoney(value: number | null | undefined, currency?: string | null): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const formatted = value.toLocaleString("ro-RO", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return currency ? `${formatted} ${currency}` : formatted;
}

function fmtPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${value}%`;
}

function formatQuantity(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toLocaleString("ro-RO", { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

export default function ProductSystemPricingPreview() {
  const [materialCode, setMaterialCode] = useState("DEV-SMOKE-LED-MODULE");
  const [quantity, setQuantity] = useState("2");
  const { vatPct: settingsVatPct } = useCompanyVatPct();
  const [includeVat, setIncludeVat] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ProductSystemPricingPreviewResult | null>(null);

  const is401 = useMemo(() => error?.includes("HTTP 401") ?? false, [error]);

  async function runPreview() {
    setLoading(true);
    setError(null);
    try {
      const parsedQuantity = Number(quantity);
      const response = await productSystemPricingPreviewAdminApi.runProductSystemPricingPreview({
        material_code: materialCode.trim(),
        quantity: Number.isFinite(parsedQuantity) ? parsedQuantity : 1,
        vat_percent: settingsVatPct,
        include_vat: includeVat,
      });
      setResult(response);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      setLoading(false);
    }
  }

  const hasResult = !!result;
  const appliedPolicy = result?.applied_markup_policy;

  return (
    <div className="space-y-5 w-full">
      {/* Read-only notice */}
      <div className="flex items-start gap-3 rounded-xl border border-slate-800/60 bg-slate-900/40 px-5 py-4">
        <ShieldCheck className="mt-0.5 h-4 w-4 text-cyan-400 shrink-0" />
        <div className="space-y-0.5 text-[12px]">
          <p className="font-medium text-slate-200">Preview read-only</p>
          <p className="text-slate-500">
            Material Registry, CostEngine, ProductSystem, ofertele și comenzile rămân neschimbate.
            Nu creează ofertă, comandă sau modificări în sistem.
          </p>
        </div>
      </div>

      {/* Two-column layout */}
      <div className="grid gap-5 lg:grid-cols-[380px_minmax(0,1fr)]">
        {/* Left: Input form */}
        <Card className="border-slate-800/60 bg-slate-950/70 shadow-none h-fit">
          <CardHeader className="px-5 py-4 border-b border-slate-800/40">
            <CardTitle className="text-[14px] font-semibold text-slate-100">Date simulare</CardTitle>
            <p className="text-[11px] text-slate-500 mt-0.5">Completează datele și rulează preview-ul.</p>
          </CardHeader>
          <CardContent className="px-5 py-5 space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="preview_material_code" className="text-[11px] font-medium text-slate-400">Cod material</Label>
              <Input
                id="preview_material_code"
                value={materialCode}
                onChange={(e) => setMaterialCode(e.target.value)}
                placeholder="ex: DEV-SMOKE-LED-MODULE"
                className="border-slate-700/60 bg-slate-900/60 text-[12px] text-slate-200 h-9 placeholder:text-slate-600"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="preview_quantity" className="text-[11px] font-medium text-slate-400">Cantitate</Label>
              <Input
                id="preview_quantity"
                type="number"
                step="0.01"
                min="0"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                className="border-slate-700/60 bg-slate-900/60 text-[12px] text-slate-200 h-9"
              />
            </div>

            <div className="space-y-1.5" data-testid="productsystem-preview-settings-vat">
              <Label className="text-[11px] font-medium text-slate-400">TVA (%)</Label>
              <p className="text-[12px] text-slate-200 border border-slate-700/60 bg-slate-900/60 rounded-md px-3 py-2 h-9">
                TVA din Settings: {settingsVatPct}%
              </p>
            </div>

            <div className="flex items-center justify-between rounded-lg border border-slate-800/50 bg-slate-900/30 px-4 py-3">
              <div>
                <p className="text-[12px] font-medium text-slate-200">Include TVA în total</p>
                <p className="text-[11px] text-slate-500">Afișează totalul cu TVA inclus.</p>
              </div>
              <Switch checked={includeVat} onCheckedChange={setIncludeVat} />
            </div>

            <Button
              onClick={runPreview}
              disabled={loading || !materialCode.trim()}
              className="w-full h-10 bg-slate-800 text-slate-100 hover:bg-slate-700 border border-slate-700/60 font-medium"
            >
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Calculator className="mr-2 h-4 w-4" />}
              Calculează preview
            </Button>

            {error && (
              <div className={`rounded-lg border px-4 py-3 text-[12px] ${is401 ? "border-amber-700/40 bg-amber-900/15 text-amber-200" : "border-red-700/40 bg-red-900/15 text-red-200"}`}>
                <div className="flex items-start gap-2">
                  <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                  <div>
                    <p className="font-medium">{is401 ? "Preview indisponibil — verifică sesiunea." : "Eroare la calcul."}</p>
                    <p className="mt-0.5 text-[11px] opacity-80">{error}</p>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right: Result */}
        <Card className={`border-slate-800/60 shadow-none ${hasResult ? "bg-slate-950/70" : "bg-slate-950/40"}`}>
          <CardHeader className="px-5 py-4 border-b border-slate-800/40">
            <CardTitle className="text-[14px] font-semibold text-slate-100">Rezultat estimare</CardTitle>
            <p className="text-[11px] text-slate-500 mt-0.5">
              {hasResult ? "Simulare completă — valorile de mai jos sunt informative." : "Rulează preview-ul pentru a vedea rezultatul."}
            </p>
          </CardHeader>
          <CardContent className="px-5 py-5">
            {!hasResult ? (
              <div className="flex flex-col items-center justify-center min-h-[280px] text-center px-6">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-slate-800/60 bg-slate-900/40 mb-4">
                  <FileText className="h-5 w-5 text-slate-600" />
                </div>
                <p className="text-[13px] font-medium text-slate-300 mb-2">
                  Completează cod material, cantitate și TVA, apoi rulează preview-ul.
                </p>
                <p className="text-[11px] text-slate-600 max-w-sm">
                  Nu creează ofertă, comandă sau modificări în sistem. Rezultatul este doar informativ.
                </p>
              </div>
            ) : (
              <div className="space-y-5">
                {/* Breakdown rows */}
                <div className="space-y-2">
                  <ResultRow label="Cost unitar material" value={fmtMoney(result?.unit_cost, result?.currency)} />
                  <ResultRow label="Cantitate" value={formatQuantity(result?.quantity)} />
                  <ResultRow label="Cost total bază" value={fmtMoney(result?.base_cost_total, result?.currency)} emphasized />
                </div>

                <div className="h-px bg-slate-800/60" />

                <div className="space-y-2">
                  <ResultRow label="Markup aplicat" value={fmtMoney(result?.markup_amount, result?.currency)} />
                  <ResultRow label="Preț unitar (fără TVA)" value={fmtMoney(result?.commercial_unit_price_ex_vat, result?.currency)} />
                  <ResultRow label="Total fără TVA" value={fmtMoney(result?.commercial_total_ex_vat, result?.currency)} />
                </div>

                <div className="h-px bg-slate-800/60" />

                <div className="space-y-2">
                  <ResultRow label="TVA" value={fmtPercent(result?.vat_percent)} />
                  <div className="rounded-xl border border-cyan-700/30 bg-cyan-900/15 px-4 py-4">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-cyan-400 mb-1">Total cu TVA</p>
                    <p className="text-[22px] font-bold text-cyan-50">{fmtMoney(result?.commercial_total_inc_vat, result?.currency)}</p>
                  </div>
                </div>

                {/* Applied policy */}
                {appliedPolicy && (
                  <div className="rounded-lg border border-slate-800/50 bg-slate-900/30 px-4 py-3">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-600 mb-2">Politică aplicată</p>
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="outline" className="border-slate-700/50 bg-slate-800/40 text-slate-300 text-[10px] px-2 py-0.5">
                        {appliedPolicy.scope_type}:{appliedPolicy.scope_value}
                      </Badge>
                      <Badge variant="outline" className="border-slate-700/50 bg-slate-800/40 text-slate-300 text-[10px] px-2 py-0.5">
                        {appliedPolicy.markup_type}
                      </Badge>
                      <Badge variant="outline" className="border-slate-700/50 bg-slate-800/40 text-slate-300 text-[10px] px-2 py-0.5">
                        priority: {appliedPolicy.priority}
                      </Badge>
                    </div>
                  </div>
                )}

                {/* Warnings */}
                {result?.warnings && result.warnings.length > 0 && (
                  <div className="rounded-lg border border-amber-800/40 bg-amber-900/15 px-4 py-3 space-y-1.5">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-amber-400">Avertizări</p>
                    {result.warnings.map((w) => (
                      <div key={`${w.code}-${w.message}`} className="flex items-start gap-2 text-[12px] text-amber-200">
                        <AlertTriangle className="w-3 h-3 mt-0.5 shrink-0" />
                        <span>{w.code}: {w.message}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function ResultRow({ label, value, emphasized = false }: { label: string; value: string; emphasized?: boolean }) {
  return (
    <div className={`flex items-center justify-between rounded-lg px-4 py-2.5 ${emphasized ? "border border-slate-700/50 bg-slate-900/40" : ""}`}>
      <span className="text-[12px] text-slate-500">{label}</span>
      <span className={`text-[13px] font-medium ${emphasized ? "text-slate-100" : "text-slate-300"}`}>{value}</span>
    </div>
  );
}