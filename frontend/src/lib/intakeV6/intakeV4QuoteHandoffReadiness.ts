import type { IntakeV4QuoteHandoffPreviewResponse } from "./intakeV4Api";

export type QuoteHandoffUiTone = "ok" | "pending" | "warn";

export type QuoteHandoffUiOptions = {
  loading?: boolean;
  fetchError?: string | null;
};

function formatHandoffUiOperatorLabel(code: string): string {
  switch (code) {
    case "HANDOFF_PREVIEW_UNAVAILABLE":
      return "Previzualizare handoff indisponibilă";
    case "LOADING_HANDOFF":
      return "Se încarcă previzualizarea handoff…";
    case "READY_FOR_INTERNAL_DRAFT_REVIEW":
      return "Draft intern: pregătit pentru review";
    case "HANDOFF_ALLOWED":
      return "Handoff permis (draft intern)";
    case "ACTION_NEEDED":
      return "Acțiune necesară înainte de handoff";
    case "QUOTE_HANDOFF_BLOCKED":
      return "Handoff către ofertă reală: blocat";
    case "WORKSPACE_READY":
      return "Pregătit pentru previzualizare ofertă";
    default:
      return code.replace(/_/g, " ");
  }
}

export function formatQuoteHandoffBlocker(code: string): string {
  if (code.startsWith("artwork_execution_undecided:")) {
    const layerKey = code.split(":")[1] ?? "artwork";
    return `Artwork execution undecided on ${layerKey}.`;
  }
  if (code === "unclassified_vector_artwork_requires_decision") {
    return "Artwork/logo neconfirmat: confirmă finisajele pe Logo/litere — protecția de perimetru rămâne activă.";
  }
  if (code === "artwork_only_requires_decision") {
    return "Nu există straturi de litere volumetrice confirmate. Artwork/policromie necesită decizie operator. Template-ul curent este Litere volumetrice; fișierul încărcat pare artwork-only.";
  }
  if (code === "operator_confirmation_missing") {
    return "Operatorul trebuie să confirme finisajele și datele de ofertare pentru draft intern.";
  }
  if (code === "missing_client_analysis_hash") {
    return "Analiza SVG nu este sincronizată complet cu workspace-ul. Salvează/confirmă din nou analiza sau reîncarcă fișierul.";
  }
  if (code === "analysis_hash_mismatch") {
    return "SVG analysis hash does not match persisted workspace identity.";
  }
  if (code === "missing_svg_source_hash") {
    return "Persisted SVG source hash is missing.";
  }
  if (code.startsWith("readiness_not_ready:")) {
    return `Workspace readiness: ${code.split(":")[1] ?? "unknown"}.`;
  }
  if (code === "finish_setup_not_confirmed") {
    return "Finalizează și confirmă finisajele în Review înainte de draft quote.";
  }
  if (code === "layer_roles_incomplete") {
    return "Layer roles are incomplete.";
  }
  if (code === "missing_svg_analysis") {
    return "SVG analysis bundle is missing.";
  }
  if (code === "missing_quote_geometry") {
    return "Quote geometry is missing.";
  }
  if (code.startsWith("missing_face_oracal_color:")) {
    return "Lipsește culoarea Oracal pentru față.";
  }
  if (code.startsWith("missing_ral_color:")) {
    return "Lipsește culoarea RAL.";
  }
  return code.replace(/_/g, " ");
}

export function hasFinishSetupIncompleteBlocker(
  fatalBlockers: string[] | null | undefined,
  readinessStatus?: string | null,
): boolean {
  const blockers = fatalBlockers ?? [];
  return (
    readinessStatus === "finish_setup_incomplete" ||
    blockers.includes("finish_setup_not_confirmed") ||
    blockers.some((code) => code === "readiness_not_ready:finish_setup_incomplete")
  );
}

export function hasArtworkNeedsDecisionWarning(
  reviewWarnings: string[] | null | undefined,
): boolean {
  return (reviewWarnings ?? []).some(
    (code) =>
      code.startsWith("artwork_execution_undecided:") ||
      code === "unclassified_vector_artwork_requires_decision" ||
      code === "artwork_only_requires_decision",
  );
}

export function hasUnclassifiedVectorArtworkWarning(
  reviewWarnings: string[] | null | undefined,
): boolean {
  return (reviewWarnings ?? []).includes("unclassified_vector_artwork_requires_decision");
}

export function hasUnconfirmedArtworkFinishes(
  rows: Array<{ confirmed?: boolean }> | null | undefined,
): boolean {
  return (rows ?? []).some((row) => row.confirmed !== true);
}

export function resolveQuoteHandoffUiStatus(
  handoff: IntakeV4QuoteHandoffPreviewResponse | null | undefined,
  options?: QuoteHandoffUiOptions,
): { label: string; tone: QuoteHandoffUiTone; handoffAllowed: boolean; debugLabel: string } {
  if (options?.fetchError) {
    return {
      label: formatHandoffUiOperatorLabel("HANDOFF_PREVIEW_UNAVAILABLE"),
      debugLabel: "HANDOFF_PREVIEW_UNAVAILABLE",
      tone: "warn",
      handoffAllowed: false,
    };
  }
  if (!handoff) {
    if (options?.loading) {
      return {
        label: formatHandoffUiOperatorLabel("LOADING_HANDOFF"),
        debugLabel: "LOADING_HANDOFF",
        tone: "pending",
        handoffAllowed: false,
      };
    }
    return {
      label: formatHandoffUiOperatorLabel("HANDOFF_PREVIEW_UNAVAILABLE"),
      debugLabel: "HANDOFF_PREVIEW_UNAVAILABLE",
      tone: "warn",
      handoffAllowed: false,
    };
  }

  const canCreate =
    handoff.can_create_internal_draft_quote ?? handoff.handoff_allowed;

  if (handoff.status_label === "READY_FOR_INTERNAL_DRAFT_REVIEW" && canCreate) {
    return {
      label: formatHandoffUiOperatorLabel("READY_FOR_INTERNAL_DRAFT_REVIEW"),
      debugLabel: "READY_FOR_INTERNAL_DRAFT_REVIEW",
      tone: "warn",
      handoffAllowed: true,
    };
  }
  if (canCreate) {
    return {
      label: formatHandoffUiOperatorLabel("HANDOFF_ALLOWED"),
      debugLabel: "HANDOFF_ALLOWED",
      tone: "ok",
      handoffAllowed: true,
    };
  }
  if (handoff.status_label === "ACTION_NEEDED") {
    return {
      label: formatHandoffUiOperatorLabel("ACTION_NEEDED"),
      debugLabel: "ACTION_NEEDED",
      tone: "warn",
      handoffAllowed: false,
    };
  }
  return {
    label: formatHandoffUiOperatorLabel("QUOTE_HANDOFF_BLOCKED"),
    debugLabel: "QUOTE_HANDOFF_BLOCKED",
    tone: "warn",
    handoffAllowed: false,
  };
}

export function resolveWorkspaceSummaryBadgeLabel(
  workspaceReadiness: string | null | undefined,
  handoff: IntakeV4QuoteHandoffPreviewResponse | null | undefined,
  options?: QuoteHandoffUiOptions,
): { label: string; tone: QuoteHandoffUiTone } {
  const handoffUi = resolveQuoteHandoffUiStatus(handoff, options);
  if (!handoffUi.handoffAllowed) {
    return { label: handoffUi.label, tone: handoffUi.tone };
  }
  if (handoff?.status_label === "READY_FOR_INTERNAL_DRAFT_REVIEW") {
    return {
      label: formatHandoffUiOperatorLabel("READY_FOR_INTERNAL_DRAFT_REVIEW"),
      tone: "warn",
    };
  }
  if (workspaceReadiness === "ready_for_quote_preview") {
    return { label: formatHandoffUiOperatorLabel("WORKSPACE_READY"), tone: "ok" };
  }
  return {
    label: formatWorkspaceReadinessLabel(workspaceReadiness),
    tone: "pending",
  };
}

function formatWorkspaceReadinessLabel(status: string | null | undefined): string {
  if (status === "ready_for_quote_preview") {
    return "Pregătit pentru previzualizare ofertă";
  }
  if (status === "finish_setup_incomplete") {
    return "Finisaje incomplete";
  }
  return status?.replace(/_/g, " ") ?? "—";
}

export function collectArtworkUndecidedWarnings(
  blockers: string[] | null | undefined,
): string[] {
  return (blockers ?? [])
    .filter(
      (code) =>
        code.startsWith("artwork_execution_undecided:") ||
        code === "unclassified_vector_artwork_requires_decision",
    )
    .map(formatQuoteHandoffBlocker);
}

export function collectFatalHandoffBlockers(handoff: IntakeV4QuoteHandoffPreviewResponse | null): string[] {
  if (!handoff) return [];
  if (handoff.fatal_blockers?.length) return handoff.fatal_blockers;
  return (handoff.blockers ?? []).filter(
    (code) =>
      !code.startsWith("artwork_execution_undecided:") &&
      code !== "unclassified_vector_artwork_requires_decision",
  );
}

export type ReviewHandoffSurfacing = {
  showBanner: boolean;
  reasons: string[];
  actions: string[];
};

export function buildReviewHandoffSurfacing(args: {
  handoff: IntakeV4QuoteHandoffPreviewResponse | null | undefined;
  handoffOptions?: QuoteHandoffUiOptions;
  containsMissingPrices?: boolean;
  allArtworkFinishesConfirmed?: boolean;
}): ReviewHandoffSurfacing {
  const handoffUi = resolveQuoteHandoffUiStatus(args.handoff, args.handoffOptions);
  const reviewWarnings = args.handoff?.review_warnings ?? [];
  const fatalBlockers = args.handoff?.fatal_blockers ?? args.handoff?.blockers ?? [];
  const artworkNeedsDecision = hasArtworkNeedsDecisionWarning(reviewWarnings);
  const vectorResidualWarning = hasUnclassifiedVectorArtworkWarning(reviewWarnings);
  const artworkUnconfirmed = args.allArtworkFinishesConfirmed === false;
  const operatorConfirmationMissing = fatalBlockers.includes("operator_confirmation_missing");
  const containsMissingPrices = args.containsMissingPrices === true;

  const showBanner =
    !handoffUi.handoffAllowed ||
    artworkNeedsDecision ||
    artworkUnconfirmed ||
    containsMissingPrices ||
    operatorConfirmationMissing;

  const reasons: string[] = [];
  if (artworkUnconfirmed) {
    reasons.push("Artwork neconfirmat în Review.");
  } else if (args.allArtworkFinishesConfirmed && vectorResidualWarning) {
    reasons.push(
      "Artwork/logo neconfirmat în finisaje — există diferență de perimetru față de SVG. Confirmă Logo 1/2 (și literele) în Review.",
    );
  } else if (artworkNeedsDecision) {
    reasons.push("Artwork/logo neconfirmat sau fără decizie de execuție.");
  }
  if (operatorConfirmationMissing) {
    reasons.push("Confirmarea operatorului pentru draft intern lipsește încă.");
  }
  if (containsMissingPrices) {
    reasons.push("Calculul live conține linii fără tarif configurat.");
  }
  if (!handoffUi.handoffAllowed && reasons.length === 0) {
    reasons.push("Handoff-ul către ofertă reală este blocat.");
  }

  const actions: string[] = [];
  if (artworkUnconfirmed) {
    actions.push(
      "Apasă Confirm artwork pentru fiecare logo după ce verifici execuția print/laminare/translucid.",
    );
  } else if (args.allArtworkFinishesConfirmed && vectorResidualWarning) {
    actions.push("Confirmă finisajele pe Logo 1/2 (și litere) pentru a include perimetrul confirmat.");
  } else if (artworkNeedsDecision) {
    actions.push("Rezolvă deciziile artwork în Review.");
  }
  if (containsMissingPrices) {
    actions.push("Verifică liniile cu tarif lipsă în Calcul live.");
  }
  if (operatorConfirmationMissing) {
    actions.push("Confirmarea finală se face în pasul Confirmare.");
  }

  return { showBanner, reasons, actions };
}

export function resolveReviewReadinessDisplay(
  workspaceReadiness: string | null | undefined,
  handoff: IntakeV4QuoteHandoffPreviewResponse | null | undefined,
  options?: QuoteHandoffUiOptions,
): { primary: string; secondary: string | null } {
  const handoffUi = resolveQuoteHandoffUiStatus(handoff, options);
  const workspaceReady = workspaceReadiness === "ready_for_quote_preview";

  if (workspaceReady && !handoffUi.handoffAllowed) {
    return {
      primary: "Date tehnice pregătite pentru preview",
      secondary:
        "Handoff ofertă necesită verificări finale. Confirmarea poate fi blocată de artwork, tarife sau confirmarea operatorului.",
    };
  }

  if (workspaceReady && hasArtworkNeedsDecisionWarning(handoff?.review_warnings)) {
    return {
      primary: "Date tehnice pregătite pentru preview",
      secondary: "Există atenționări artwork de rezolvat înainte de draft final.",
    };
  }

  return {
    primary: formatWorkspaceReadinessLabel(workspaceReadiness),
    secondary: null,
  };
}
