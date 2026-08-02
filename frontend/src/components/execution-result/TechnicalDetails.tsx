import { GateVerdictCard } from "@/components/execution/GateVerdictCard";
import { ProductSystemPreviewPanel } from "@/components/execution/ProductSystemPreviewPanel";
import { ProfitabilityAnalysisPanel } from "@/components/execution/ProfitabilityAnalysisPanel";
import { useGateEvaluation } from "@/hooks/useGateEvaluation";
import { useProductSystemPreview } from "@/hooks/useProductSystemPreview";

export function TechnicalDetails({ orderId }: { orderId: number }) {
  const gate = useGateEvaluation(orderId);
  const preview = useProductSystemPreview(orderId);
  return <details className="rounded-lg border border-wo-border-subtle bg-wo-surface p-4" data-testid="execution-technical-details">
    <summary className="cursor-pointer text-sm font-semibold text-wo-text-secondary">Detalii tehnice și diagnostic</summary>
    <div className="mt-4 space-y-4">
      {gate.data ? <GateVerdictCard gate={gate.data} loading={gate.loading} onRefresh={() => { void gate.refresh(); void preview.refresh(); }} /> : <p className="text-[12px] text-wo-text-muted">{gate.error ?? "Evaluarea gate este indisponibilă."}</p>}
      {preview.data ? <ProductSystemPreviewPanel preview={preview.data} /> : null}
      {preview.error ? <p className="text-[12px] text-wo-text-muted">Previzualizarea Product System este indisponibilă: {preview.error}</p> : null}
      <div><p className="mb-2 text-[11px] text-wo-text-muted">Analiza veche de profitabilitate este păstrată doar pentru diagnostic.</p><ProfitabilityAnalysisPanel orderId={orderId} /></div>
    </div>
  </details>;
}
