import { useEffect, useMemo, useState } from "react";
import type { IntakeV6WorkspaceHook } from "@/lib/intakeV6/useIntakeV6Workspace";
import {
	findOutOfScopeLayerWarnings,
	resolveQuoteGeometryForWorkspace,
} from "@/lib/intakeV6/intakeV6QuoteGeometry";
import {
	buildIntakeV6GeometryMetricDisplay,
	getFullVectorPerimeterM,
} from "@/lib/intakeV6/intakeV6GeometryMetricDisplay";
import { resolveSvgPreviewLayerHighlightTarget } from "@/lib/intakeV6/intakeV6SvgPreviewLayerHighlight";
import IntakeV6GeometryPanel from "../IntakeV6GeometryPanel";
import IntakeV6LayersMetricsStrip from "../IntakeV6LayersMetricsStrip";
import IntakeV6LayersFileConfirmPanel from "../IntakeV6LayersFileConfirmPanel";
import IntakeV6LayersOperatorPanel from "../IntakeV6LayersOperatorPanel";
import IntakeV6ArtworkOnlyDecisionPanel from "../IntakeV6ArtworkOnlyDecisionPanel";
import IntakeV6LayersRoleTable from "../IntakeV6LayersRoleTable";
import IntakeV6ProductCompositionPanel from "../IntakeV6ProductCompositionPanel";
import IntakeV6SvgPreviewInspectDialog from "../IntakeV6SvgPreviewInspectDialog";
import { isSingleLayerColorMode } from "../IntakeV6LayersColorBreakdown";
import { detectArtworkOnlyRequiresDecision } from "@/lib/intakeV6/intakeV6ArtworkOnlyGuard";
import IntakeV6TechnicalDetailsAccordion from "../atoms/IntakeV6TechnicalDetailsAccordion";
import { useIntakeV6WorkspaceHeaderStatusOptional } from "../IntakeV6WorkspaceHeaderStatusContext";
import { v6 } from "../atoms/intakeV6Presentation";

export interface IntakeV6SvgAnalyzerStepProps {
	hook: IntakeV6WorkspaceHook;
}

export default function IntakeV6SvgAnalyzerStep({ hook }: IntakeV6SvgAnalyzerStepProps) {
	const { state, importSvgFile, updateLayerRole, confirmAllLayerRoles, canImportSvg, confirmProductComposition } = hook;
	const statusCtx = useIntakeV6WorkspaceHeaderStatusOptional();
	const [previewInspectOpen, setPreviewInspectOpen] = useState(false);
	const [hoveredLayerKey, setHoveredLayerKey] = useState<string | null>(null);
	const analyzing = state.analyzerStatus === "analyzing";
	const report = state.analyzerReport;
	const confirmation = state.layerRoleConfirmation;
	const fatalError =
		state.analyzerStatus === "error" ? (state.analyzerError ?? state.error) : state.error;
	const parseWarning = state.analyzerStatus === "ready" ? state.analyzerError : null;
	const workspaceReady = Boolean(state.workspace?.id);

	const quoteGeometry = useMemo(
		() =>
			resolveQuoteGeometryForWorkspace({
				payload: state.workspace?.payload as Record<string, unknown> | undefined,
				analyzerReport: report,
				layerRoleConfirmation: confirmation,
				localFileHash: state.localFileHash,
			}),
		[report, confirmation, state.workspace?.payload, state.localFileHash],
	);
	const scopeWarnings = useMemo(() => findOutOfScopeLayerWarnings(confirmation), [confirmation]);

	const payload = state.workspace?.payload as Record<string, unknown> | undefined;
	const templateCode =
		payload?.product_binding != null &&
		typeof payload.product_binding === "object" &&
		!Array.isArray(payload.product_binding)
			? String((payload.product_binding as Record<string, unknown>).template_code ?? "")
			: null;

	const geometryMetrics = useMemo(
		() =>
			buildIntakeV6GeometryMetricDisplay({
				report,
				confirmation,
				geometry: quoteGeometry,
				payload,
				analysisBundleReady: false,
				templateCode,
			}),
		[report, confirmation, quoteGeometry, payload, templateCode],
	);

	const layerStats = useMemo(() => {
		if (!report || !confirmation) {
			return { total: 0, confirmed: 0, pending: 0 };
		}
		const total = report.layers.length;
		const confirmed = confirmation.layers.filter(
			(item) => item.confirmationState === "confirmed" || item.confirmationState === "ignored",
		).length;
		return { total, confirmed, pending: total - confirmed };
	}, [report, confirmation]);

	const missingExternalRaster = useMemo(() => {
		if (!report?.artworkComplexity?.assessments?.length) return false;
		return report.artworkComplexity.assessments.some(
			(row) => row.has_raster_image && row.missing_external_image_asset,
		);
	}, [report]);

	const layoutMode = report
		? isSingleLayerColorMode(report)
			? "single-color"
			: "semantic-layers"
		: "empty";

	const headerOverlay = useMemo(
		() => ({
			loading: analyzing,
			analysisReady: confirmation?.confirmationStatus === "complete",
			svgReady: Boolean(report),
			layersConfirmed: layerStats.confirmed,
			layersTotal: layerStats.total,
			pendingConfirmationCount: layerStats.pending,
			widthMm: report?.document.widthMm ?? quoteGeometry.width_mm,
			heightMm: report?.document.heightMm ?? quoteGeometry.height_mm,
			perimeterM: getFullVectorPerimeterM(geometryMetrics),
		}),
		[
			analyzing,
			confirmation?.confirmationStatus,
			report,
			layerStats.confirmed,
			layerStats.total,
			layerStats.pending,
			quoteGeometry.width_mm,
			quoteGeometry.height_mm,
			geometryMetrics,
		],
	);

	const setHeaderOverlay = statusCtx?.setOverlay;
	const setHeaderHandlers = statusCtx?.setHandlers;

	useEffect(() => {
		if (!setHeaderOverlay) return;
		setHeaderOverlay(headerOverlay);
		return () => setHeaderOverlay({});
	}, [setHeaderOverlay, headerOverlay]);

	useEffect(() => {
		if (!setHeaderHandlers) return;
		setHeaderHandlers({
			onJumpToPending: () => {
				document
					.querySelector('[data-testid="intake-v6-layer-table"]')
					?.scrollIntoView({ behavior: "smooth", block: "start" });
			},
		});
		return () => setHeaderHandlers({ onJumpToPending: undefined });
	}, [setHeaderHandlers]);

	const handleImport = async (file: File) => {
		await importSvgFile(file);
	};

	const scrollToPending = () => {
		document
			.querySelector('[data-testid="intake-v6-layer-table"]')
			?.scrollIntoView({ behavior: "smooth", block: "start" });
	};

	const jumpToLayer = (layerKey: string) => {
		const row = document.querySelector(`[data-testid="intake-v6-layer-row-${layerKey}"]`);
		if (row) {
			row.scrollIntoView({ behavior: "smooth", block: "center" });
			row.classList.add("ring-2", "ring-cyan-400/40");
			window.setTimeout(() => row.classList.remove("ring-2", "ring-cyan-400/40"), 1600);
		} else {
			scrollToPending();
		}
	};

	const showLayerDecisions = Boolean(report && confirmation);
	const artworkOnlyRequiresDecision = useMemo(
		() => detectArtworkOnlyRequiresDecision(report, confirmation),
		[report, confirmation],
	);

	const highlightedLayer = useMemo(
		() =>
			report && confirmation
				? resolveSvgPreviewLayerHighlightTarget(report, confirmation, hoveredLayerKey)
				: null,
		[report, confirmation, hoveredLayerKey],
	);

	return (
		<section data-testid="intake-v6-svg-analyzer-step">
			<div
				className={v6.layersStepGrid}
				data-testid="intake-v6-layers-layout"
				data-intake-v6-layers-layout-mode={layoutMode}
			>
				<div className="min-w-0 space-y-4" data-testid="intake-v6-layers-main-column">
					<IntakeV6LayersFileConfirmPanel
						fileName={state.svg?.fileName}
						previewSource={state.svg?.previewSource}
						missingExternalRaster={missingExternalRaster}
						report={report}
						quoteGeometry={quoteGeometry}
						geometryMetrics={geometryMetrics}
						analyzing={analyzing}
						canImportSvg={canImportSvg}
						onImportFile={handleImport}
						onOpenInspect={() => setPreviewInspectOpen(true)}
						highlightedLayer={highlightedLayer}
					/>

					{showLayerDecisions && artworkOnlyRequiresDecision && report && confirmation ? (
						<IntakeV6ArtworkOnlyDecisionPanel
							report={report}
							confirmation={confirmation}
							onUpdateLayerRole={(layerKey, role) => updateLayerRole(layerKey, role)}
							onRequestReload={() => {
								document
									.querySelector('[data-testid="intake-v6-nest2-uploader"] button')
									?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
							}}
							variant="step1"
						/>
					) : null}

					{showLayerDecisions ? (
						<div className={`${v6.cardCompact} min-w-0`} data-testid="intake-v6-layers-decision-band">
							<IntakeV6LayersRoleTable
								report={report!}
								confirmation={confirmation!}
								onUpdateLayerRole={updateLayerRole}
								layout="cards"
								hoveredLayerKey={hoveredLayerKey}
								onHoverLayerKey={setHoveredLayerKey}
							/>
						</div>
					) : null}

					<IntakeV6ProductCompositionPanel
						payload={payload}
						onConfirm={(items) => void confirmProductComposition(items)}
					/>

					{report ? (
						<IntakeV6TechnicalDetailsAccordion
							title="Metrici tehnice & geometrie"
							testId="intake-v6-layers-metrics-advanced"
						>
							<IntakeV6LayersMetricsStrip
								report={report}
								geometry={quoteGeometry}
								metrics={geometryMetrics}
								widthMm={report.document.widthMm}
								heightMm={report.document.heightMm}
								variant="full"
							/>
							<div className="mt-3">
								<IntakeV6GeometryPanel
									geometry={quoteGeometry}
									metrics={geometryMetrics}
									scopeWarnings={scopeWarnings}
									variant="advanced"
								/>
							</div>
						</IntakeV6TechnicalDetailsAccordion>
					) : null}
				</div>

				<IntakeV6LayersOperatorPanel
					analyzing={analyzing}
					canImportSvg={canImportSvg}
					workspaceReady={workspaceReady}
					report={report}
					confirmation={confirmation}
					layerStats={layerStats}
					parseWarning={parseWarning}
					scopeWarnings={scopeWarnings}
					artworkOnlyRequiresDecision={artworkOnlyRequiresDecision}
					onImportFile={handleImport}
					onConfirmAllRoles={() => confirmAllLayerRoles()}
					onScrollToPending={layerStats.pending > 0 ? scrollToPending : undefined}
					onJumpToLayer={jumpToLayer}
				/>
			</div>

			{state.svg?.previewSource && report && confirmation ? (
				<IntakeV6SvgPreviewInspectDialog
					open={previewInspectOpen}
					onOpenChange={setPreviewInspectOpen}
					fileName={state.svg.fileName}
					previewSource={state.svg.previewSource}
					missingExternalRaster={missingExternalRaster}
					report={report}
					confirmation={confirmation}
					onUpdateLayerRole={updateLayerRole}
				/>
			) : null}

			{workspaceReady && !report && !analyzing && !fatalError ? (
				<p className={`${v6.helper} mt-4`} data-testid="intake-v6-empty-analyzer-state">
					Nu există încă o analiză SVG salvată. Folosește panoul operator pentru upload.
				</p>
			) : null}

			{fatalError ? (
				<p className="mt-3 text-[12px] text-red-300" data-testid="intake-v6-error">
					{fatalError}
				</p>
			) : null}
		</section>
	);
}
