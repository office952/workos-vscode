import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
import IntakeV6OfferScopePanel from "../IntakeV6OfferScopePanel";
import IntakeV6SvgPreviewInspectDialog from "../IntakeV6SvgPreviewInspectDialog";
import { isSingleLayerColorMode } from "../IntakeV6LayersColorBreakdown";
import { detectArtworkOnlyRequiresDecision } from "@/lib/intakeV6/intakeV6ArtworkOnlyGuard";
import { buildIntakeV6LayersAnalysisWarningSummaries } from "@/lib/intakeV6/intakeV6LayersAnalysisWarningSummaries";
import IntakeV6TechnicalDetailsAccordion from "../atoms/IntakeV6TechnicalDetailsAccordion";
import { useIntakeV6WorkspaceHeaderStatusOptional } from "../IntakeV6WorkspaceHeaderStatusContext";
import { v6 } from "../atoms/intakeV6Presentation";
import type { IntakeV6FinishSetup } from "@/lib/intakeV6/intakeV6Api";
import { INTAKE_V6_LETTERS_TEMPLATE_CODE } from "@/lib/intakeV6/intakeV6LayerTargetTemplate";
import { useIntakeV6SvgBindables } from "@/lib/intakeV6/useIntakeV6SvgBindables";
import {
	buildLayerRoleComponentBindings,
	findBindableByGeometryRole,
	layerRoleBindingsSyncKey,
	readSvgComponentBindings,
} from "@/lib/intakeV6/svgComponentBindings";
import {
	buildClearSupportContourPatch,
	resolvePrimaryClosedContourCandidate,
} from "@/lib/intakeV6/associatePrimarySupportContour";
import { readSegmentedBackground } from "@/lib/intakeV6/segmentedBackground";
import {
	buildSupportPanelConfirmationPath,
	confirmationIncludesConfirmedSupportPanel,
} from "@/lib/intakeV6/intakeV6SupportPanelConfirmationPath";
import { mergeLetterLogoBindingsPreservingAcmPanelDomain } from "@/lib/intakeV6/acmPanel";
import { applyLayerRoleSelection, readSvgSupportSelection } from "@/lib/svgAnalyzer";
import type { LayerAutoRole } from "@/lib/svgAnalyzer";

export interface IntakeV6SvgAnalyzerStepProps {
	hook: IntakeV6WorkspaceHook;
}

export default function IntakeV6SvgAnalyzerStep({ hook }: IntakeV6SvgAnalyzerStepProps) {
	const {
		state,
		importSvgFile,
		updateLayerRole,
		confirmAllLayerRoles,
		canImportSvg,
		confirmProductComposition,
		saveOfferScope,
		saveFinishSetup,
		persistAnalysisBundle,
	} = hook;
	const statusCtx = useIntakeV6WorkspaceHeaderStatusOptional();
	const [previewInspectOpen, setPreviewInspectOpen] = useState(false);
	const [hoveredLayerKey, setHoveredLayerKey] = useState<string | null>(null);
	const [selectedContourId, setSelectedContourId] = useState<string | null>(null);
	const [supportAssociateError, setSupportAssociateError] = useState<string | null>(null);
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
	const resolvedTemplateCode = templateCode || INTAKE_V6_LETTERS_TEMPLATE_CODE;
	const finishSetup =
		(payload?.finish_setup as Record<string, unknown> | undefined) ?? null;
	const { bindables } = useIntakeV6SvgBindables(resolvedTemplateCode);
	const componentBindings = useMemo(
		() => readSvgComponentBindings(finishSetup),
		[finishSetup],
	);
	const supportComp = useMemo(
		() => findBindableByGeometryRole(bindables, "SUPPORT_CONTOUR"),
		[bindables],
	);
	const lastSyncedLayerBindingsKey = useRef<string | null>(null);
	/** Latest segmented truth — binding-only finish patches must not wipe a live proposal. */
	const segmentedBackgroundRef = useRef<Record<string, unknown> | null>(
		readSegmentedBackground(finishSetup as Record<string, unknown> | null) as Record<
			string,
			unknown
		> | null,
	);
	/** Serialize finish PUTs so letter sync cannot race ACM upsert. */
	const finishPersistChain = useRef(Promise.resolve(true));
	segmentedBackgroundRef.current =
		(readSegmentedBackground(finishSetup as Record<string, unknown> | null) as Record<
			string,
			unknown
		> | null) ?? segmentedBackgroundRef.current;

	const persistFinishPatch = useCallback(
		async (
			patch: {
				svg_support_selection?: Record<string, unknown> | null;
				svg_component_bindings?: ReturnType<typeof readSvgComponentBindings>;
				mounting_solution?: Record<string, unknown> | null;
				power_supply_service_corner?: string | null;
				segmented_background?: Record<string, unknown> | null;
				acm_panel_domain_action?: "preserve" | "upsert" | "clear";
				acm_panel_instance?: Record<string, unknown> | null;
			},
			options?: { errorContext?: "support" | "bindings" },
		): Promise<boolean> => {
			const run = async (): Promise<boolean> => {
				const prev =
					(payload?.finish_setup as Record<string, unknown> | undefined) ?? {};
				const next: IntakeV6FinishSetup = {
					...(prev as IntakeV6FinishSetup),
				} as IntakeV6FinishSetup;
				const nextRec = next as Record<string, unknown>;
				if (patch.svg_support_selection !== undefined) {
					nextRec.svg_support_selection = patch.svg_support_selection;
				}
				if (patch.svg_component_bindings !== undefined) {
					nextRec.svg_component_bindings = patch.svg_component_bindings;
				}
				if (patch.mounting_solution !== undefined) {
					nextRec.mounting_solution = patch.mounting_solution;
				}
				if (patch.power_supply_service_corner !== undefined) {
					nextRec.power_supply_service_corner = patch.power_supply_service_corner;
				}
				if (patch.acm_panel_instance !== undefined) {
					nextRec.acm_panel_instance = patch.acm_panel_instance;
				}
				if (patch.acm_panel_domain_action !== undefined) {
					nextRec.acm_panel_domain_action = patch.acm_panel_domain_action;
				} else if (patch.svg_component_bindings !== undefined && patch.svg_support_selection === undefined) {
					nextRec.acm_panel_domain_action = "preserve";
				}
				if (patch.segmented_background !== undefined) {
					nextRec.segmented_background = patch.segmented_background;
					segmentedBackgroundRef.current = patch.segmented_background;
				} else if (segmentedBackgroundRef.current != null) {
					nextRec.segmented_background = segmentedBackgroundRef.current;
				} else if (prev.segmented_background != null) {
					nextRec.segmented_background = prev.segmented_background;
				}
				// Preserve ACM shell on bindings-only sync when action=preserve.
				if (nextRec.acm_panel_domain_action === "preserve") {
					if (nextRec.svg_support_selection == null && prev.svg_support_selection != null) {
						nextRec.svg_support_selection = prev.svg_support_selection;
					}
					if (nextRec.mounting_solution == null && prev.mounting_solution != null) {
						nextRec.mounting_solution = prev.mounting_solution;
					}
					if (nextRec.acm_panel_instance == null && prev.acm_panel_instance != null) {
						nextRec.acm_panel_instance = prev.acm_panel_instance;
					}
				}
				const saved = await saveFinishSetup(next);
				if (!saved.ok) {
					const prefix =
						options?.errorContext === "support"
							? "Salvarea Contur suport / ACP a eșuat (FinishSetup). "
							: "Salvarea asociărilor SVG a eșuat (FinishSetup). ";
					setSupportAssociateError(`${prefix}${saved.message}`);
					return false;
				}
				setSupportAssociateError(null);
				return true;
			};
			const queued = finishPersistChain.current.then(run, run);
			finishPersistChain.current = queued.then(
				() => true,
				() => true,
			);
			return queued;
		},
		[payload?.finish_setup, saveFinishSetup],
	);

	const handleUpdateLayerRole = useCallback(
		(layerKey: string, role: LayerAutoRole) => {
			if (!confirmation) {
				updateLayerRole(layerKey, role);
				return;
			}
			const nextConfirmation = applyLayerRoleSelection(confirmation, layerKey, role);
			updateLayerRole(layerKey, role);
			setSupportAssociateError(null);

			const letterLogoBindings = buildLayerRoleComponentBindings({
				confirmation: nextConfirmation,
				bindables,
				sourceSvgHash: state.localFileHash,
				previous: componentBindings,
			});

			if (role === "support_panel") {
				const path = buildSupportPanelConfirmationPath({
					report,
					confirmation: nextConfirmation,
					finishSetup,
					bindables,
					svgSourceHash: state.localFileHash,
				});
				if (!path.ok || !path.finishPatch) {
					setSupportAssociateError(path.blockers.join(" ") || "Asociere Contur suport eșuată.");
					return;
				}
				lastSyncedLayerBindingsKey.current = layerRoleBindingsSyncKey(path.mergedBindings);
				if (path.contourId) setSelectedContourId(path.contourId);
				if (path.segmentedProposal) {
					segmentedBackgroundRef.current = path.segmentedProposal as unknown as Record<
						string,
						unknown
					>;
				}
				void (async () => {
					const analysisOk = await persistAnalysisBundle({
						layerRoleConfirmation: nextConfirmation,
					});
					if (!analysisOk) {
						setSupportAssociateError(
							"Contur suport: analiza SVG trebuie salvată înainte de asocierea FinishSetup. Reîncearcă după ce salvarea reușește.",
						);
						return;
					}
					// Atomic single PUT: ACM instance + binding + selection + mounting + segmented.
					await persistFinishPatch(path.finishPatch!, { errorContext: "support" });
				})();
				return;
			}

			const othersKeepSupport = nextConfirmation.layers.some(
				(layer) =>
					layer.layerKey !== layerKey &&
					layer.confirmedRole === "support_panel" &&
					layer.confirmationState !== "ignored",
			);
			const currentWasSupport =
				confirmation.layers.find((layer) => layer.layerKey === layerKey)?.confirmedRole ===
				"support_panel";
			if (currentWasSupport && !othersKeepSupport) {
				const cleared = buildClearSupportContourPatch({
					finishSetup,
					componentTemplateCode: supportComp?.component_template_code,
				});
				const mergedBindings = [
					...letterLogoBindings.filter((b) => b.geometry_role !== "SUPPORT_CONTOUR"),
					...cleared.svg_component_bindings.filter((b) => b.geometry_role === "SUPPORT_CONTOUR"),
				];
				lastSyncedLayerBindingsKey.current = layerRoleBindingsSyncKey(mergedBindings);
				void (async () => {
					await persistAnalysisBundle();
					await persistFinishPatch(
						{
							...cleared,
							svg_component_bindings: mergedBindings,
						},
						{ errorContext: "support" },
					);
				})();
				return;
			}

			// Letter/logo FinishSetup sync only after roles are complete (or support early path above).
			if (nextConfirmation.confirmationStatus !== "complete") {
				return;
			}
			const preserved = mergeLetterLogoBindingsPreservingAcmPanelDomain({
				letterLogoBindings,
				finishSetup,
				supportRoleStillConfirmed: confirmationIncludesConfirmedSupportPanel(nextConfirmation),
			});
			lastSyncedLayerBindingsKey.current = layerRoleBindingsSyncKey(
				preserved.svg_component_bindings,
			);
			void persistFinishPatch(
				{
					svg_component_bindings: preserved.svg_component_bindings,
					svg_support_selection: preserved.svg_support_selection as Record<string, unknown> | undefined,
					mounting_solution: preserved.mounting_solution as Record<string, unknown> | undefined,
					acm_panel_instance: preserved.acm_panel_instance as Record<string, unknown> | undefined,
					segmented_background: preserved.segmented_background as Record<string, unknown> | undefined,
					acm_panel_domain_action: preserved.acm_panel_domain_action,
				},
				{ errorContext: "bindings" },
			);
		},
		[
			updateLayerRole,
			report,
			finishSetup,
			state.localFileHash,
			confirmation,
			bindables,
			componentBindings,
			supportComp?.component_template_code,
			persistFinishPatch,
			persistAnalysisBundle,
		],
	);

	/** Confirm All uses the same support + segmented write-path as manual Contur suport (R4). */
	const handleConfirmAllRoles = useCallback(() => {
		if (!report) {
			confirmAllLayerRoles();
			return;
		}
		const next = confirmAllLayerRoles();
		if (!next || !confirmationIncludesConfirmedSupportPanel(next)) return;
		const path = buildSupportPanelConfirmationPath({
			report,
			confirmation: next,
			finishSetup,
			bindables,
			svgSourceHash: state.localFileHash,
		});
		if (!path.ok || !path.finishPatch) {
			setSupportAssociateError(path.blockers.join(" ") || "Asociere Contur suport eșuată.");
			return;
		}
		lastSyncedLayerBindingsKey.current = layerRoleBindingsSyncKey(path.mergedBindings);
		if (path.contourId) setSelectedContourId(path.contourId);
		if (path.segmentedProposal) {
			segmentedBackgroundRef.current = path.segmentedProposal as unknown as Record<string, unknown>;
		}
		void (async () => {
			const analysisOk = await persistAnalysisBundle({ layerRoleConfirmation: next });
			if (!analysisOk) {
				setSupportAssociateError(
					"Contur suport: analiza SVG trebuie salvată înainte de asocierea FinishSetup.",
				);
				return;
			}
			// Atomic single PUT — no second segmented write, no auto composition confirm.
			await persistFinishPatch(path.finishPatch!, { errorContext: "support" });
		})();
	}, [
		report,
		confirmAllLayerRoles,
		finishSetup,
		bindables,
		state.localFileHash,
		persistAnalysisBundle,
		persistFinishPatch,
	]);

	/** Auto-sync letter/logo bindings when layer roles change — preserve ACM shell via domain action. */
	useEffect(() => {
		if (!confirmation || bindables.length === 0 || state.phase === "persisting") return;
		const next = buildLayerRoleComponentBindings({
			confirmation,
			bindables,
			sourceSvgHash: state.localFileHash,
			previous: componentBindings,
		});
		const preserved = mergeLetterLogoBindingsPreservingAcmPanelDomain({
			letterLogoBindings: next,
			finishSetup,
			supportRoleStillConfirmed: confirmationIncludesConfirmedSupportPanel(confirmation),
		});
		const nextKey = layerRoleBindingsSyncKey(preserved.svg_component_bindings);
		const prevKey = layerRoleBindingsSyncKey(componentBindings);
		if (nextKey === prevKey || nextKey === lastSyncedLayerBindingsKey.current) return;
		const rolesComplete = confirmation.confirmationStatus === "complete";
		const hasSupportContour = preserved.svg_component_bindings.some(
			(b) => b.geometry_role === "SUPPORT_CONTOUR",
		);
		if (!rolesComplete && !hasSupportContour) return;
		lastSyncedLayerBindingsKey.current = nextKey;
		void persistFinishPatch(
			{
				svg_component_bindings: preserved.svg_component_bindings,
				svg_support_selection: preserved.svg_support_selection as Record<string, unknown> | undefined,
				mounting_solution: preserved.mounting_solution as Record<string, unknown> | undefined,
				acm_panel_instance: preserved.acm_panel_instance as Record<string, unknown> | undefined,
				segmented_background: preserved.segmented_background as Record<string, unknown> | undefined,
				acm_panel_domain_action: preserved.acm_panel_domain_action,
			},
			{ errorContext: "bindings" },
		);
	}, [
		confirmation,
		bindables,
		componentBindings,
		finishSetup,
		state.localFileHash,
		state.phase,
		persistFinishPatch,
	]);

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

	const analysisWarningSummaries = useMemo(
		() =>
			buildIntakeV6LayersAnalysisWarningSummaries({
				report,
				confirmation,
				parseWarning,
				scopeWarnings,
			}),
		[report, confirmation, parseWarning, scopeWarnings],
	);

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
			secondaryWarnings: analysisWarningSummaries,
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
			analysisWarningSummaries,
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

	const contourOverlay = useMemo(() => {
		const cand = report?.closedContourCandidates?.candidates.find(
			(c) => c.contour_id === selectedContourId,
		);
		if (!cand) return null;
		return {
			contour_id: cand.contour_id,
			mode: "selected" as const,
			bbox: cand.bbox,
			overlay_d: cand.overlay_d,
			overlay_points: cand.overlay_points,
		};
	}, [report, selectedContourId]);

	useEffect(() => {
		const selection = readSvgSupportSelection(finishSetup ?? undefined);
		if (
			selection.contour_id &&
			(selection.status === "confirmed" ||
				selection.status === "draft" ||
				selection.status === "reconfirm_required")
		) {
			setSelectedContourId(selection.contour_id);
		}
	}, [finishSetup]);

	const handleSaveOfferScope = useCallback(
		(input: {
			mode: "full_product" | "component_subset";
			soldModules: Array<"FACE" | "RETURN-CANT" | "BACK" | "LIGHTING" | "ELECTRICAL">;
			confirmed: boolean;
			dependencyConfirmationCodes?: string[];
		}) =>
			saveOfferScope({
				mode: input.mode,
				soldModules: input.soldModules,
				confirmed: input.confirmed,
				dependencyConfirmationCodes: input.dependencyConfirmationCodes,
			}),
		[saveOfferScope],
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
						contourOverlay={contourOverlay}
					/>

					{showLayerDecisions && artworkOnlyRequiresDecision && report && confirmation ? (
						<IntakeV6ArtworkOnlyDecisionPanel
							report={report}
							confirmation={confirmation}
							onUpdateLayerRole={handleUpdateLayerRole}
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
							{supportComp && report?.closedContourCandidates?.candidate_count ? (
								<p
									className="mb-2 text-[11px] text-cyan-200/90"
									data-testid="intake-v6-contur-suport-hint"
								>
									Pentru panoul exterior ACP: pe cardul <span className="font-semibold">contur negru</span>{" "}
									alege rolul <span className="font-semibold">Contur suport</span> — apare{" "}
									<span className="font-semibold">Panou Alucobond casetat</span> în Compoziție produs
									propusă.
								</p>
							) : null}
							{supportAssociateError ? (
								<p
									className="mb-2 rounded border border-amber-500/40 bg-amber-500/10 px-2 py-1.5 text-[11px] text-amber-100"
									data-testid="intake-v6-contur-suport-error"
								>
									{supportAssociateError}
								</p>
							) : null}
							<IntakeV6LayersRoleTable
								report={report!}
								confirmation={confirmation!}
								onUpdateLayerRole={handleUpdateLayerRole}
								layout="cards"
								hoveredLayerKey={hoveredLayerKey}
								onHoverLayerKey={(key) => {
									setHoveredLayerKey(key);
									if (!key || !confirmation || !report) return;
									const entry = confirmation.layers.find(
										(layer) => layer.layerKey === key,
									);
									if (entry?.confirmedRole === "support_panel") {
										const sel = readSvgSupportSelection(finishSetup);
										const primary = resolvePrimaryClosedContourCandidate(
											report.closedContourCandidates?.candidates,
										);
										setSelectedContourId(sel.contour_id ?? primary?.contour_id ?? null);
									}
								}}
								workspaceTemplateCode={resolvedTemplateCode}
								bindables={bindables}
								componentBindings={componentBindings}
							/>
						</div>
					) : null}

					<IntakeV6ProductCompositionPanel
						payload={payload}
						onConfirm={(items) => void confirmProductComposition(items)}
					/>

					<IntakeV6OfferScopePanel
						payload={payload}
						disabled={state.phase === "persisting"}
						onSave={handleSaveOfferScope}
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
					onConfirmAllRoles={() => handleConfirmAllRoles()}
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
					onUpdateLayerRole={handleUpdateLayerRole}
					contourOverlay={contourOverlay}
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
