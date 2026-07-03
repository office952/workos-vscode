import type { ReviewHandoffSurfacing } from "./intakeV6QuoteHandoffReadiness";

export type ReviewHeaderStatusTone = "success" | "warning" | "danger" | "neutral";

export type ReviewHeaderStatusDetailTone = "ok" | "warn" | "bad" | "muted";

export interface ReviewHeaderStatusDetail {
  id: string;
  label: string;
  value: string;
  tone: ReviewHeaderStatusDetailTone;
}

export interface ReviewHeaderStatusAction {
  id: string;
  label: string;
}

export interface ReviewHeaderStatusModel {
  label: string;
  tone: ReviewHeaderStatusTone;
  actionCount: number;
  details: ReviewHeaderStatusDetail[];
  actions: ReviewHeaderStatusAction[];
}

export interface BuildReviewHeaderStatusInput {
  loading?: boolean;
  analysisReady: boolean;
  svgReady: boolean;
  containsMissingPrices?: boolean;
  layersConfirmed: number;
  layersTotal: number;
  artworkTotal: number;
  artworkConfirmed: number;
  operatorConfirmationMissing?: boolean;
  reviewWarnings?: readonly string[];
  surfacing: ReviewHandoffSurfacing;
  pendingSave?: boolean;
  pendingConfirmationCount?: number;
  widthMm?: number | null;
  heightMm?: number | null;
  perimeterM?: number | null;
}

function fmtMm(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return `${Math.round(value)} mm`;
}

function fmtM(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value) || value <= 0) return "—";
  return `${value.toFixed(2)} m`;
}

function pluralActiuni(count: number): string {
  if (count === 1) return "1 acțiune necesară";
  return `${count} acțiuni necesare`;
}

export function buildReviewHeaderStatus(input: BuildReviewHeaderStatusInput): ReviewHeaderStatusModel {
  if (input.loading) {
    return {
      label: "Se verifică…",
      tone: "neutral",
      actionCount: 0,
      details: [],
      actions: [],
    };
  }

  const artworkAllConfirmed =
    input.artworkTotal === 0 || input.artworkConfirmed >= input.artworkTotal;
  const layersAllConfirmed =
    input.layersTotal === 0 || input.layersConfirmed >= input.layersTotal;

  let actionCount = input.pendingConfirmationCount ?? 0;
  if (input.pendingSave) actionCount += 1;
  if (input.operatorConfirmationMissing) actionCount += 1;

  const hasReviewWarnings = (input.reviewWarnings?.length ?? 0) > 0;
  const surfacingReasonsExcludingOperator = input.surfacing.reasons.filter(
    (reason) =>
      !reason.toLowerCase().includes("confirmarea operatorului") &&
      !reason.toLowerCase().includes("operator"),
  );

  const hasProblems =
    input.containsMissingPrices === true ||
    hasReviewWarnings ||
    surfacingReasonsExcludingOperator.length > 0 ||
    (!input.svgReady && input.analysisReady);

  const details: ReviewHeaderStatusDetail[] = [
    {
      id: "svg",
      label: "SVG",
      value: input.svgReady ? "OK" : "Necesită upload",
      tone: input.svgReady ? "ok" : input.analysisReady ? "warn" : "bad",
    },
    {
      id: "pricing",
      label: "Pricing",
      value: input.containsMissingPrices ? "Lipsesc tarife" : "OK",
      tone: input.containsMissingPrices ? "bad" : "ok",
    },
    {
      id: "layers",
      label: "Layers",
      value:
        input.layersTotal > 0
          ? `${input.layersConfirmed}/${input.layersTotal} confirmate`
          : "—",
      tone: layersAllConfirmed ? "ok" : "warn",
    },
    {
      id: "artwork",
      label: "Artwork",
      value:
        input.artworkTotal === 0
          ? "—"
          : artworkAllConfirmed
            ? "Confirmat"
            : "Necesită decizie",
      tone:
        input.artworkTotal === 0 ? "muted" : artworkAllConfirmed ? "ok" : "warn",
    },
    {
      id: "operator",
      label: "Operator confirmation",
      value: input.operatorConfirmationMissing ? "Lipsește" : "Complet",
      tone: input.operatorConfirmationMissing ? "warn" : "ok",
    },
    {
      id: "dimensions",
      label: "Dimensiuni",
      value: `${fmtMm(input.widthMm)} × ${fmtMm(input.heightMm)}`,
      tone: "muted",
    },
    {
      id: "perimeter",
      label: "Perimetru",
      value: fmtM(input.perimeterM),
      tone: "muted",
    },
  ];

  const actions: ReviewHeaderStatusAction[] = [];
  if (input.operatorConfirmationMissing) {
    actions.push({ id: "confirm-step", label: "Confirmă în pasul Confirmare" });
  }
  if (!artworkAllConfirmed && input.artworkTotal > 0) {
    actions.push({ id: "jump-artwork", label: "Mergi la Artwork" });
  }
  if (input.containsMissingPrices) {
    actions.push({ id: "jump-live-calc", label: "Vezi Calcul Live" });
  }
  if (!layersAllConfirmed && input.layersTotal > 0) {
    actions.push({ id: "jump-layers", label: "Mergi la Straturi" });
  }
  if (actionCount > 0 && actions.length === 0) {
    actions.push({ id: "jump-actions", label: "Salt la acțiuni" });
  }

  if (hasProblems) {
    return {
      label: "Probleme",
      tone: "danger",
      actionCount,
      details,
      actions,
    };
  }

  if (actionCount > 0) {
    return {
      label: pluralActiuni(actionCount),
      tone: "warning",
      actionCount,
      details,
      actions,
    };
  }

  return {
    label: "Totul OK",
    tone: "success",
    actionCount: 0,
    details,
    actions: [],
  };
}
