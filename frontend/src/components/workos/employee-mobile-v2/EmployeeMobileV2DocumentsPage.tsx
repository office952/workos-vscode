import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { FileText } from "lucide-react";
import { useEmployeeMobileV2Tasks } from "@/hooks/useEmployeeMobileV2Tasks";
import {
  EmployeeMobileEmptyState,
  EmployeeMobileErrorState,
  EmployeeMobileLoadingState,
} from "@/components/workos/employee-mobile/EmployeeMobileStates";
import EmployeeMobileV2PageHeader from "@/components/workos/employee-mobile-v2/EmployeeMobileV2PageHeader";
import { v2InteractiveRowClass, v2Motion } from "@/lib/employeeMobileV2Effects";
import {
  collectDocumentsForOrder,
  resolveDocumentsOrderId,
} from "@/lib/employeeMobileV2Documents";
import { documentTypeLabel } from "@/lib/employeeMobileTaskDocuments";
import { cn } from "@/lib/utils";

export default function EmployeeMobileV2DocumentsPage() {
  const [searchParams] = useSearchParams();
  const { tasks, loading, error } = useEmployeeMobileV2Tasks();

  const orderIdParam = searchParams.get("orderId");
  const orderIdFilter =
    orderIdParam && Number.isFinite(Number(orderIdParam)) ? Number(orderIdParam) : null;

  const orderId = useMemo(
    () => resolveDocumentsOrderId(tasks, orderIdFilter),
    [tasks, orderIdFilter],
  );

  const documents = useMemo(
    () => collectDocumentsForOrder(tasks, orderId),
    [tasks, orderId],
  );

  const orderContext = useMemo(() => {
    if (orderId == null) return null;
    const task = tasks.find((row) => row.order_id === orderId);
    if (!task) return null;
    return [task.client, task.order_code || `Comandă #${task.order_id}`].filter(Boolean).join(" · ");
  }, [tasks, orderId]);

  return (
    <div data-testid="employee-mobile-v2-documents">
      <EmployeeMobileV2PageHeader
        backTo="/employee-app-v2"
        title="Documente"
        subtitle={orderContext ? `Lucrare: ${orderContext}` : undefined}
        testId="employee-mobile-v2-documents-header"
      />

      {loading ? (
        <EmployeeMobileLoadingState
          message="Se încarcă documentele…"
          testId="employee-mobile-v2-documents-loading"
        />
      ) : null}

      {!loading && error ? (
        <EmployeeMobileErrorState message={error} testId="employee-mobile-v2-documents-error" />
      ) : null}

      {!loading && !error && documents.length === 0 ? (
        <EmployeeMobileEmptyState
          message="Nu există documente disponibile pentru lucrarea curentă."
          hint="Documentele apar când sunt atașate taskurilor sau comenzii."
          testId="employee-mobile-v2-documents-empty"
        />
      ) : null}

      {!loading && !error && documents.length > 0 ? (
        <ul className="space-y-2" data-testid="employee-mobile-v2-documents-list">
          {documents.map((doc) => {
            const rowContent = (
              <>
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-violet-500/12 text-violet-400 shadow-[0_0_12px_rgba(139,92,246,0.1)]">
                  <FileText className="w-[18px] h-[18px]" aria-hidden />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-[15px] font-medium text-slate-100 truncate">{doc.name}</p>
                  <p className="text-[12px] text-slate-500">{documentTypeLabel(doc.type)}</p>
                </div>
                {doc.url ? (
                  <span className="shrink-0 text-sm font-medium text-blue-400">Deschide</span>
                ) : (
                  <span className="text-xs text-slate-600">Fără link</span>
                )}
              </>
            );

            return (
              <li key={`${doc.taskId}-${doc.id}`} data-testid={`employee-mobile-v2-document-${doc.id}`}>
                {doc.url ? (
                  <a
                    href={doc.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={cn(
                      v2InteractiveRowClass(),
                      "flex min-h-[64px] w-full items-center gap-3 px-4 py-3",
                      v2Motion.tapTarget,
                    )}
                  >
                    {rowContent}
                  </a>
                ) : (
                  <div
                    className={cn(
                      v2InteractiveRowClass(),
                      "flex min-h-[64px] items-center gap-3 px-4 py-3 opacity-70",
                    )}
                  >
                    {rowContent}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}
