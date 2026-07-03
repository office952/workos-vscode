import type { ReactNode } from "react";
import { AlertTriangle, CheckCircle2, Info } from "lucide-react";
import {
  classifyQuoteGateItems,
  readinessStatusLabel,
  summarizeVolumetricQuoteGate,
  type ClassifiedReadinessItem,
  type VolumetricCommercialReadinessStatus,
  type VolumetricQuoteGate,
} from "@/lib/volumetricQuoteReady";

const STATUS_STYLES: Record<
  VolumetricCommercialReadinessStatus,
  { container: string; badge: string; icon: typeof CheckCircle2 }
> = {
  ready: {
    container: "bg-emerald-900/20 border-emerald-800/50",
    badge: "bg-emerald-900/40 text-emerald-300 border-emerald-700/50",
    icon: CheckCircle2,
  },
  ready_with_warnings: {
    container: "bg-blue-900/20 border-blue-800/50",
    badge: "bg-blue-900/40 text-blue-300 border-blue-700/50",
    icon: Info,
  },
  requires_acknowledgement: {
    container: "bg-amber-900/20 border-amber-800/50",
    badge: "bg-amber-900/40 text-amber-300 border-amber-700/50",
    icon: AlertTriangle,
  },
  blocked: {
    container: "bg-red-900/20 border-red-800/50",
    badge: "bg-red-900/40 text-red-300 border-red-700/50",
    icon: AlertTriangle,
  },
};

const ITEM_STATUS_LABEL: Record<ClassifiedReadinessItem["status"], string> = {
  blocking: "blocking",
  needs_acknowledgement: "needs acknowledgement",
  informational: "informational",
  satisfied: "satisfied at quote input",
};

function ReadinessItemRow({ item }: { item: ClassifiedReadinessItem }) {
  const tone =
    item.status === "blocking"
      ? "text-red-300"
      : item.status === "needs_acknowledgement"
        ? "text-amber-300"
        : "text-slate-400";
  return (
    <li className={`text-[11px] ${tone}`}>
      <span className="font-medium">{item.label}</span>
      <span className="ml-1 font-mono text-[10px] text-slate-500">({item.code})</span>
      <span className="ml-1 text-[10px] uppercase tracking-wide text-slate-600">
        [{ITEM_STATUS_LABEL[item.status]}]
      </span>
    </li>
  );
}

export interface VolumetricCommercialReadinessPanelProps {
  gate: VolumetricQuoteGate | null | undefined;
  testId?: string;
  showAcknowledgementControl?: boolean;
  acknowledgementChecked?: boolean;
  onAcknowledgementChange?: (checked: boolean) => void;
  compact?: boolean;
}

export function VolumetricCommercialReadinessPanel({
  gate,
  testId = "volumetric-commercial-readiness",
  showAcknowledgementControl = false,
  acknowledgementChecked = false,
  onAcknowledgementChange,
  compact = false,
}: VolumetricCommercialReadinessPanelProps) {
  if (!gate) return null;

  const summary = summarizeVolumetricQuoteGate(gate);
  const items = classifyQuoteGateItems(gate);
  const styles = STATUS_STYLES[summary.status];
  const StatusIcon = styles.icon;

  const blocking = items.filter((i) => i.status === "blocking");
  const ackPending = items.filter((i) => i.status === "needs_acknowledgement");
  const informational = items.filter((i) => i.status === "informational");

  return (
    <div
      data-testid={testId}
      className={`border rounded-lg px-3 py-2 space-y-2 ${styles.container}`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <StatusIcon className="w-4 h-4 shrink-0" />
          <div>
            <p className="text-[12px] font-semibold text-slate-200">
              Pregătire comercială volumetrică
            </p>
            <span
              className={`inline-flex mt-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${styles.badge}`}
              data-testid={`${testId}-status`}
            >
              {readinessStatusLabel(summary.status)}
            </span>
          </div>
        </div>
      </div>

      {!compact && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[10px]">
          <Metric label="can_create_commercial_quote" value={String(summary.canCreate)} />
          <Metric
            label="requires_acknowledgement"
            value={String(summary.requiresAcknowledgement)}
          />
          <Metric label="blockers" value={String(summary.blockerCount)} />
          <Metric
            label="ack_pending"
            value={String(summary.acknowledgementPendingCount)}
          />
        </div>
      )}

      {gate.notes?.map((note) => (
        <p key={note} className="text-[11px] text-slate-400">
          {note}
        </p>
      ))}

      {blocking.length > 0 && (
        <Section title="Blocking issues" testId={`${testId}-blockers`}>
          <ul className="list-disc pl-5 space-y-0.5">
            {blocking.map((item) => (
              <ReadinessItemRow key={item.code} item={item} />
            ))}
          </ul>
        </Section>
      )}

      {ackPending.length > 0 && (
        <Section title="Warnings requiring acknowledgement" testId={`${testId}-ack-pending`}>
          <ul className="list-disc pl-5 space-y-0.5">
            {ackPending.map((item) => (
              <ReadinessItemRow key={item.code} item={item} />
            ))}
          </ul>
        </Section>
      )}

      {informational.length > 0 && (
        <Section title="Informational warnings" testId={`${testId}-warnings`}>
          <ul className="list-disc pl-5 space-y-0.5">
            {informational.map((item) => (
              <ReadinessItemRow key={item.code} item={item} />
            ))}
          </ul>
        </Section>
      )}

      {summary.reasonCodes.length > 0 && !compact && (
        <details className="text-[10px] text-slate-500">
          <summary className="cursor-pointer hover:text-slate-400">Reason codes</summary>
          <ul className="mt-1 font-mono space-y-0.5 pl-2">
            {summary.reasonCodes.map((code) => (
              <li key={code}>{code}</li>
            ))}
          </ul>
        </details>
      )}

      {showAcknowledgementControl && summary.requiresAcknowledgement && (
        <div
          className="border-t border-[#1E293B] pt-2"
          data-testid={`${testId}-ack-control`}
        >
          <label className="flex items-start gap-2 text-[11px] text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              id="quote_convert_acknowledge_warnings"
              checked={acknowledgementChecked}
              onChange={(e) => onAcknowledgementChange?.(e.target.checked)}
              className="w-4 h-4 mt-0.5 rounded border-[#2A3548] bg-[#1A2236] accent-blue-600"
            />
            <span>
              Confirm că am verificat avertizările comerciale și continui cu conversia.
            </span>
          </label>
        </div>
      )}

      {showAcknowledgementControl && !summary.requiresAcknowledgement && summary.canCreate && (
        <p className="text-[10px] text-slate-500" data-testid={`${testId}-no-ack`}>
          No acknowledgement required
        </p>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-[#0B111E]/60 border border-[#1E293B] rounded px-2 py-1">
      <p className="text-slate-500 truncate">{label}</p>
      <p className="font-mono text-slate-300">{value}</p>
    </div>
  );
}

function Section({
  title,
  children,
  testId,
}: {
  title: string;
  children: ReactNode;
  testId?: string;
}) {
  return (
    <div data-testid={testId}>
      <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500 mb-1">
        {title}
      </p>
      {children}
    </div>
  );
}
