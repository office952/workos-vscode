import type { ReactNode } from "react";
import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import type { IntakeSiteAuditJson } from "@/lib/intakeSiteAudit";
import type { IntakeActionSummaryModel } from "@/lib/intakeActionSummary";
import type { DeliveryType, IntakeRequest } from "@/lib/mockData";

/** Shared props passed from IntakeDetail into template workspaces. */
export interface TemplateWorkspaceBaseProps {
  request: IntakeRequest;
  source: string;
  error: string | null;
  persistError: string | null;
  selectedDeliveryType: DeliveryType;
  assignedTo: string;
  setAssignedTo: (value: string) => void;
  confirmedTemplateCode: string | null;
  productSpecInitial: IntakeProductSpec | null;
  actionSummary: IntakeActionSummaryModel;
  readiness: { canMarkReady: boolean; missing: string[] };
  statusConflict: boolean;
  requiresInstallAudit: boolean;
  markReadyLoading: boolean;
  markReadyMessage: string | null;
  confirmingTemplate: boolean;
  hasFiscalIdentity: boolean;
  installTerrainSection: ReactNode | null;
  intakeDbId: number | null;
  siteAuditJson: IntakeSiteAuditJson | null;
  onDeliveryTypeChange: (dt: DeliveryType) => void;
  onAssignedBlur: () => void;
  onSaveProductSpec: (
    spec: IntakeProductSpec | null,
    options?: { skipRefresh?: boolean }
  ) => Promise<void>;
  onMarkReadyForQuote: () => void;
  onConfirmTemplate: () => void;
}

export type WorkspaceTab = "spec" | "quote";
