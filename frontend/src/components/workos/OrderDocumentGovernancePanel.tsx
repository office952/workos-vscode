import { useEffect, useState } from "react";
import { AlertTriangle, Link2, ShieldCheck } from "lucide-react";
import {
  getOrderDocumentSnapshotReference,
  type OrderDocumentSnapshotReferenceResponse,
} from "@/api/orders";
import DocumentGovernanceTerminologyCard from "@/components/workos/DocumentGovernanceTerminologyCard";

interface OrderDocumentGovernancePanelProps {
  orderId: number | null;
  orderCode: string;
  visible: boolean;
}

export default function OrderDocumentGovernancePanel({
  orderId,
  orderCode,
  visible,
}: OrderDocumentGovernancePanelProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<OrderDocumentSnapshotReferenceResponse | null>(null);

  useEffect(() => {
    let cancelled = false;

    if (!visible || !orderId) {
      setLoading(false);
      setError(null);
      setData(null);
      return;
    }

    setLoading(true);
    setError(null);

    getOrderDocumentSnapshotReference(orderId)
      .then((result) => {
        if (cancelled) return;
        setData(result);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Nu s-a putut încărca referința de snapshot");
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [orderId, visible]);

  if (!visible || !orderId) return null;

  return (
    <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4" data-testid="order-document-governance-panel">
      <div className="flex items-center gap-2 mb-2">
        <ShieldCheck className="w-4 h-4 text-blue-400" />
        <p className="text-[12px] font-semibold text-blue-300">Document Governance (read-only)</p>
      </div>

      <p className="text-[11px] text-slate-400">
        Order {orderCode}: legătura la document snapshot este afișată transparent. Lipsa referinței este informativă, nu eroare fatală.
      </p>

      {loading && <p className="mt-2 text-[11px] text-slate-500">Se încarcă referința de document snapshot...</p>}

      {error && (
        <div className="mt-2 flex items-start gap-2 rounded border border-red-800/40 bg-red-900/20 px-2.5 py-2">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-red-300" />
          <p className="text-[11px] text-red-300">{error}</p>
        </div>
      )}

      {!loading && !error && data && (
        <div className="mt-3 space-y-2 text-[11px]">
          <div className="flex items-center justify-between rounded border border-wo-border-strong bg-wo-surface-raised px-2.5 py-2">
            <span className="text-slate-400">Document snapshot reference</span>
            <span
              className={`rounded border px-2 py-0.5 font-semibold ${
                data.has_document_snapshot
                  ? "border-emerald-700/50 bg-emerald-900/30 text-emerald-300"
                  : "border-amber-700/50 bg-amber-900/30 text-amber-300"
              }`}
            >
              {data.has_document_snapshot ? "Atașată" : "Lipsă"}
            </span>
          </div>

          {data.has_document_snapshot && data.reference ? (
            <div className="rounded border border-wo-border-strong bg-wo-surface-raised px-2.5 py-2 text-slate-300">
              <p className="flex items-center gap-1.5">
                <Link2 className="h-3.5 w-3.5 text-slate-400" />
                Snapshot: {data.reference.snapshot_code ?? "fără cod"}
              </p>
              <p className="mt-0.5">Status la acceptare: {data.reference.snapshot_status_at_acceptance}</p>
              <p className="mt-0.5">
                Acceptat la: {data.reference.accepted_at ? new Date(data.reference.accepted_at).toLocaleString("ro-RO") : "n/a"}
              </p>
            </div>
          ) : (
            <div className="rounded border border-wo-border-strong bg-wo-surface-raised px-2.5 py-2 text-slate-300">
              <p>
                Comanda există fără referință document snapshot aprobat. Conversia rămâne validă, dar trasabilitatea documentară este incompletă.
              </p>
            </div>
          )}
        </div>
      )}

      <DocumentGovernanceTerminologyCard />
    </div>
  );
}