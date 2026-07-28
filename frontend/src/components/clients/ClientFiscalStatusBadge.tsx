import { AlertTriangle, CheckCircle2, ShieldAlert } from "lucide-react";
import {
  getClientFiscalDisplayLabel,
  type ClientFiscalDisplayStatus,
} from "@/lib/api";

/** Shared Day/Night chip tokens for Clients list + detail fiscal status. */
export const CLIENT_FISCAL_CHIP_CLASS: Record<ClientFiscalDisplayStatus, string> = {
  saved:
    "bg-wo-success-muted text-wo-success border-wo-success/35",
  missing_cui:
    "bg-wo-error-muted text-wo-error border-wo-error/35",
  // Day: amber-900 on wo-warning-muted for readable contrast; Night keeps wo-warning
  non_fiscal:
    "bg-wo-warning-muted text-amber-900 border-wo-warning/35 dark:text-wo-warning",
};

export const CLIENT_REGISTRY_CHIP_CLASS =
  "bg-wo-info-muted text-wo-info border-wo-info/35";

export const CLIENT_ACTIVE_CHIP_CLASS =
  "bg-wo-success-muted text-wo-success border-wo-success/35";

const CHIP_BASE =
  "inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[9px] font-semibold";

function FiscalIcon({ status }: { status: ClientFiscalDisplayStatus }) {
  switch (status) {
    case "saved":
      return <CheckCircle2 className="w-2.5 h-2.5" />;
    case "missing_cui":
      return <AlertTriangle className="w-2.5 h-2.5" />;
    case "non_fiscal":
      return <ShieldAlert className="w-2.5 h-2.5" />;
    default: {
      const _exhaustive: never = status;
      return _exhaustive;
    }
  }
}

export function ClientFiscalStatusBadge({
  status,
}: {
  status: ClientFiscalDisplayStatus;
}) {
  return (
    <span className={`${CHIP_BASE} ${CLIENT_FISCAL_CHIP_CLASS[status]}`}>
      <FiscalIcon status={status} />
      {getClientFiscalDisplayLabel(status)}
    </span>
  );
}

export function ClientRegistryChip({
  label = "Registru entități",
}: {
  label?: string;
}) {
  return (
    <span className={`${CHIP_BASE} ${CLIENT_REGISTRY_CHIP_CLASS}`}>{label}</span>
  );
}

export function ClientActiveChip() {
  return (
    <span className={`px-2 py-0.5 text-[9px] font-semibold rounded border ${CLIENT_ACTIVE_CHIP_CLASS}`}>
      Activ
    </span>
  );
}
