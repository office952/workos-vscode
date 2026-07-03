import { useEffect, useState } from "react";
import { operationalRegistryApi, type EligibleEmployeePool } from "@/api/operationalRegistry";
import {
  formatOperationResolutionLabel,
  resolveOperationFromPool,
} from "@/features/operational-registry/operationResolution";
import { Users, AlertTriangle } from "lucide-react";

interface Props {
  operationCode: string | null | undefined;
  machineType?: string | null;
}

export function OperationPoolPreviewPanel({ operationCode, machineType }: Props) {
  const [pool, setPool] = useState<EligibleEmployeePool | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!operationCode) {
      setPool(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    operationalRegistryApi
      .getEligibleEmployeesForOperation(operationCode, machineType ?? undefined)
      .then((res) => {
        if (!cancelled) setPool(res);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Eroare pool eligibil");
          setPool(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [operationCode, machineType]);

  if (!operationCode) return null;

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900/30 p-3 space-y-2">
      <div className="flex items-center gap-2 text-xs font-semibold text-slate-200">
        <Users className="w-3.5 h-3.5" />
        Pool eligibil (preview — guard soft, fără block)
      </div>
      {loading && <p className="text-[11px] text-slate-400">Se calculează eligibilitatea…</p>}
      {error && (
        <p className="text-[11px] text-amber-300 flex items-center gap-1">
          <AlertTriangle className="w-3 h-3" />
          {error}
        </p>
      )}
      {pool && !loading && (
        <>
          <p className="text-[10px] text-slate-500">
            {formatOperationResolutionLabel({
              originalOperationCode: pool.operation_code,
              resolvedOperationCode: pool.resolved_operation_code,
              authorizationMode: pool.authorization_mode,
              eligibleCount: pool.total,
            })}
          </p>
          {resolveOperationFromPool(pool).warning && (
            <p className="text-[11px] text-amber-300 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3 shrink-0" />
              {resolveOperationFromPool(pool).warning}
            </p>
          )}
          {pool.items.length === 0 && !resolveOperationFromPool(pool).warning ? (
            <p className="text-[11px] text-amber-300">Niciun angajat eligibil configurat.</p>
          ) : pool.items.length === 0 ? null : (
            <ul className="flex flex-wrap gap-1.5">
              {pool.items.map((emp) => (
                <li
                  key={emp.id}
                  className="text-[10px] px-2 py-0.5 rounded border border-emerald-700/50 bg-emerald-950/20 text-emerald-200"
                >
                  {emp.name}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  );
}
