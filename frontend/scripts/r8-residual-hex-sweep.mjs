/**
 * R8 residual night-hex → wo-* token sweep (Track C MUST SWEEP + leftovers).
 * Chrome-only mechanical replace. Excludes Employee Mobile, intake-v6, tokens.ts.
 */
import fs from "node:fs";
import path from "node:path";

const root = path.resolve("C:/w/psiso/frontend/src");

/** Explicit MUST SWEEP + secondary leftover surfaces from Track C inventory. */
const files = [
  // Track C top hotspots
  "pages/Governance.tsx",
  "components/inventory/InventorySheetQualityPanel.tsx",
  "pages/IntakeDetail.tsx",
  "pages/Inventory.tsx",
  "pages/TabletMode.tsx",
  "pages/ClientWorkspace.tsx",
  "pages/BlueprintDossierStudio.tsx",
  "pages/ModuleChain.tsx",
  // PS deep #0A0F1A leaks (post-R4 residual)
  "features/product-system/AcmBoxedStructureDetailPage.tsx",
  "features/product-system/candidateModuleProdusReadonlyUiShared.tsx",
  "features/product-system/CandidateModuleProdusSettingsSheet.tsx",
  "features/product-system/MaterialRegistryPicker.tsx",
  // Employee HR suite (non-mobile)
  "pages/EmployeeAdvances.tsx",
  "pages/EmployeePayments.tsx",
  "pages/Attendance.tsx",
  "pages/EmployeeProfile.tsx",
  "pages/EmployeesRecords.tsx",
  "pages/EmployeeAttendanceEffects.tsx",
  "pages/EmployeeManagerTeamWorkspace.tsx",
  "pages/Personal.tsx",
  "components/workos/employees/EmployeeAdminOperationalSummary.tsx",
  // Legacy intake / docs / orders
  "pages/DocumentCenter.tsx",
  "pages/Orders.tsx",
  "pages/WorkIntake.tsx",
  "pages/OutputBlocksPreview.tsx",
  "pages/Clients.tsx",
  "pages/OperatorView.tsx",
  "pages/ShopFloor.tsx",
  "pages/Reports.tsx",
  "pages/OperationalReports.tsx",
  "pages/OperationalRealityReview.tsx",
  "pages/CommercialSpineDemo.tsx",
  "pages/VolumetricLetterPreviewDemo.tsx",
  "components/dossier/DossierSectionEditors.tsx",
  "components/clients/ClientFiscalVerifyPanel.tsx",
  // WorkOS leftover chrome (not intake-v6, not employee-mobile)
  "components/workos/VolumetricLettersQuoteFlow.tsx",
  "components/workos/NewIntakeDialog.tsx",
  "components/workos/Product001IntakeSpecEditor.tsx",
  "components/workos/VectorIntakeFastAskPanel.tsx",
  "components/workos/NextStepPanel.tsx",
  "components/workos/SharedComponents.tsx",
  "components/workos/IntakeActionSummary.tsx",
  "components/workos/IntakePathwaySelector.tsx",
  "components/workos/IntakeWorkTypePicker.tsx",
  "components/workos/MaterialsCapturePanel.tsx",
  "components/workos/ImportantDocumentsSection.tsx",
  "components/workos/DocumentGovernanceTerminologyCard.tsx",
  "components/workos/OrderDocumentGovernancePanel.tsx",
  "components/workos/QuoteDocumentGovernancePanel.tsx",
  "components/workos/QuoteCommercialActionPanel.tsx",
  "components/workos/QuoteCommercialDocument.tsx",
  "components/workos/QuoteOutputCompositionPreview.tsx",
  "components/workos/QuotePdfPanel.tsx",
  "components/workos/QuoteRevisionDialog.tsx",
  "components/workos/QuoteSendDialog.tsx",
  "components/workos/RecalibrationModal.tsx",
  "components/workos/ReadinessWarningAcknowledgementModal.tsx",
  "components/workos/OperatorOwnerDecisionDetailsPanel.tsx",
  "components/workos/OperatorOwnerDecisionResolutionForm.tsx",
  "components/workos/OperatorProductionBlueprintPanel.tsx",
  "components/workos/OperatorTaskAssignmentPanel.tsx",
  "components/workos/OutputBlocksCoverageDiagnostics.tsx",
  "components/workos/FieldInstallationTeamPanel.tsx",
  "components/workos/FlatMaterialNestingSummary.tsx",
  "components/workos/LettersBackForexMaterialPanel.tsx",
  "components/workos/LettersFaceFinishOptionBadges.tsx",
  "components/workos/LettersLedSystemPanel.tsx",
  "components/workos/LettersVolumeAluminumWidthBadges.tsx",
  "components/workos/SvgLayerAnalysisPanel.tsx",
  "components/workos/VectorStudioPanel.tsx",
  "components/workos/VolumetricCommercialReadinessPanel.tsx",
  "components/workos/VolumetricFinishDisplayPanel.tsx",
  "components/workos/VolumetricWorkIntakeHandoffPanel.tsx",
  "components/workos/CncProcessableBadge.tsx",
  "components/workos/EnvironmentBanner.tsx",
  "components/workos/colorRegistry/ColorRegistrySelect.tsx",
  "components/workos/collaboration/OperatorTaskCollaborationPanel.tsx",
  "components/workos/templateIntakeWorkspace/InfoHint.tsx",
  "components/workos/templateIntakeWorkspace/ReadinessGatePanel.tsx",
  "components/workos/templateIntakeWorkspace/RequestContextPanel.tsx",
  "components/workos/templateIntakeWorkspace/TemplateConfirmationPanel.tsx",
  "components/workos/templateIntakeWorkspace/TemplateStatusPanel.tsx",
  "components/workos/templateIntakeWorkspace/TerrainRequirementPanel.tsx",
  "components/workos/templateIntakeWorkspace/WorkspaceTabBar.tsx",
  "components/workos/preview/VolumetricLetterExpandedPreview.tsx",
  "components/workos/preview/VolumetricLetterIsometricPreview.tsx",
  // Execution residual (beyond plan strip)
  "components/execution/ProductSystemPreviewPanel.tsx",
  "components/execution/ProfitabilityAnalysisPanel.tsx",
  "components/execution/GateTraceSource.tsx",
  "components/execution/GateVerdictCard.tsx",
  "components/execution/PostJobTruthPanel.tsx",
  // Misc chrome
  "components/ErrorBoundary.tsx",
  "components/system/VersionBadge.tsx",
  // Light PS residual (non-IA)
  "features/product-system/CandidateModuleProdusPanel.tsx",
  "features/product-system/TemplateDownstreamLinkagePanel.tsx",
  "features/product-system/TemplateGeneralTabPanel.tsx",
  "features/product-system/TemplateLibraryView.tsx",
  "features/product-system/TemplateSelectorSheet.tsx",
  "features/product-system/templateStudioPanels.tsx",
];

/** Longer / opacity-aware keys first. */
const replacements = [
  // Opacity / hover / from-to variants
  ["bg-[#111827]/50", "bg-wo-surface-raised/50"],
  ["bg-[#111827]/40", "bg-wo-surface-raised/40"],
  ["bg-[#111827]/60", "bg-wo-surface-raised/60"],
  ["bg-[#111827]/80", "bg-wo-surface-raised/80"],
  ["bg-[#111827]/90", "bg-wo-surface-raised/90"],
  ["bg-[#111827]/95", "bg-wo-surface-raised/95"],
  ["bg-[#0A0F1A]/95", "bg-wo-surface-inset/95"],
  ["bg-[#0A0F1A]/90", "bg-wo-surface-inset/90"],
  ["bg-[#0A0F1A]/80", "bg-wo-surface-inset/80"],
  ["bg-[#0A0F1C]/50", "bg-wo-surface-inset/50"],
  ["bg-[#0D1321]/50", "bg-wo-surface-inset/50"],
  ["bg-[#0D1321]/80", "bg-wo-surface-inset/80"],
  ["bg-[#1A2236]/50", "bg-wo-surface-raised/50"],
  ["bg-[#1A2236]/80", "bg-wo-surface-raised/80"],
  ["hover:bg-[#1A2236]", "hover:bg-wo-hover"],
  ["hover:bg-[#111827]", "hover:bg-wo-hover"],
  ["hover:bg-[#0D1321]", "hover:bg-wo-hover"],
  ["hover:bg-[#1E293B]", "hover:bg-wo-hover"],
  ["border-[#1E293B]/50", "border-wo-border-subtle/50"],
  ["border-[#1E293B]/40", "border-wo-border-subtle/40"],
  ["border-[#2A3548]/50", "border-wo-border-strong/50"],
  ["border-[#2A3548]/40", "border-wo-border-strong/40"],
  ["from-[#111827]", "from-wo-surface-raised"],
  ["to-[#111827]", "to-wo-surface-raised"],
  ["via-[#111827]", "via-wo-surface-raised"],
  ["from-[#0D1321]", "from-wo-surface-inset"],
  ["to-[#0D1321]", "to-wo-surface-inset"],
  ["from-[#0A0F1A]", "from-wo-surface-inset"],
  ["to-[#0A0F1A]", "to-wo-surface-inset"],
  ["from-[#0B1220]", "from-wo-surface-input"],
  ["to-[#0B1220]", "to-wo-surface-input"],
  // Solid backgrounds
  ["bg-[#111827]", "bg-wo-surface-raised"],
  ["bg-[#101827]", "bg-wo-surface-raised"],
  ["bg-[#141B29]", "bg-wo-surface-raised"],
  ["bg-[#151d2e]", "bg-wo-surface-raised"],
  ["bg-[#1A2236]", "bg-wo-surface-raised"],
  ["bg-[#121B2C]", "bg-wo-surface-raised"],
  ["bg-[#131B2E]", "bg-wo-surface-raised"],
  ["bg-[#0A0F1A]", "bg-wo-surface-inset"],
  ["bg-[#0A0F1C]", "bg-wo-surface-inset"],
  ["bg-[#0D1321]", "bg-wo-surface-inset"],
  ["bg-[#0d1321]", "bg-wo-surface-inset"],
  ["bg-[#0F1629]", "bg-wo-surface-inset"],
  ["bg-[#0F1724]", "bg-wo-surface-inset"],
  ["bg-[#0f172a]", "bg-wo-surface-inset"],
  ["bg-[#0F172A]", "bg-wo-surface-inset"],
  ["bg-[#0d1420]", "bg-wo-surface-inset"],
  ["bg-[#090f18]", "bg-wo-surface-inset"],
  ["bg-[#0a0f18]", "bg-wo-surface-inset"],
  ["bg-[#05080f]", "bg-wo-surface-inset"],
  ["bg-[#0B1120]", "bg-wo-surface-input"],
  ["bg-[#0B1220]", "bg-wo-surface-input"],
  ["bg-[#1E293B]", "bg-wo-hover"],
  ["bg-[#2A3548]", "bg-wo-hover"],
  // Borders
  ["border-[#2A3548]", "border-wo-border-strong"],
  ["border-[#243044]", "border-wo-border-strong"],
  ["border-[#334155]", "border-wo-border-strong"],
  ["border-[#3d4f6a]", "border-wo-border-strong"],
  ["border-[#1E293B]", "border-wo-border-subtle"],
  ["border-[#1F2A3D]", "border-wo-border-subtle"],
  ["border-[#1C2433]", "border-wo-border-subtle"],
  // Divide / ring (rare)
  ["divide-[#1E293B]", "divide-wo-border-subtle"],
  ["divide-[#2A3548]", "divide-wo-border-strong"],
  ["ring-[#1E293B]", "ring-wo-border-subtle"],
  ["ring-[#2A3548]", "ring-wo-border-strong"],
  // Text
  ["text-[#F1F5F9]", "text-wo-text-primary"],
  ["text-[#E2E8F0]", "text-wo-text-secondary"],
  ["text-[#94A3B8]", "text-wo-text-muted"],
  ["text-[#64748B]", "text-wo-text-dim"],
];

let changed = 0;
let skipped = 0;
const report = [];

for (const rel of files) {
  const full = path.join(root, rel);
  if (!fs.existsSync(full)) {
    skipped++;
    report.push(`SKIP missing: ${rel}`);
    continue;
  }
  let content = fs.readFileSync(full, "utf8");
  const orig = content;
  for (const [from, to] of replacements) {
    if (content.includes(from)) {
      content = content.split(from).join(to);
    }
  }
  if (content !== orig) {
    fs.writeFileSync(full, content, "utf8");
    changed++;
    report.push(`OK: ${rel}`);
  } else {
    report.push(`unchanged: ${rel}`);
  }
}

console.log(`Changed: ${changed}; missing: ${skipped}; listed: ${files.length}`);
for (const line of report) console.log(line);
