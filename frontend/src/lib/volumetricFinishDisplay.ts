import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import { findColorRegistryItem, formatColorRegistryLabel } from "@/lib/colorRegistry/colorRegistry";
import { isFaceVinylEnabled } from "@/lib/volumetricFrontlitIntake";

export type VolumetricFinishSummary = {
  returnFinishLabel: string;
  returnFinishDetail?: string;
  returnFinishCode?: string;
  returnFinishName?: string;
  returnPreviewHex?: string;
  returnApproximatePreview?: boolean;

  faceVinylLabel: string;
  faceVinylDetail?: string;
  faceVinylCode?: string;
  faceVinylName?: string;
  faceVinylPreviewHex?: string;
  faceVinylTranslucent?: boolean;

  warnings: string[];
};

const RETURN_COLOR_LABELS: Record<string, string> = {
  white: "Alb",
  black: "Negru",
};

const RAL_APPROX_NOTE =
  "Preview HEX/RGB este aproximativ — culoarea RAL reală depinde de vopsea, material și lumină.";

function resolveReturnFinishSystem(
  spec: IntakeProductSpec
): "standard" | "RAL" | "ORACAL" {
  if (spec.return_finish_system === "RAL" || spec.return_finish_system === "ORACAL") {
    return spec.return_finish_system;
  }
  if (spec.return_finish_system === "standard") return "standard";
  if (spec.return_ral_code?.trim() || spec.paint_ral_code?.trim()) return "RAL";
  if (spec.return_oracal_code?.trim()) return "ORACAL";
  return "standard";
}

function parseLegacyFaceVinylCode(spec: IntakeProductSpec): string | undefined {
  const direct = spec.face_vinyl_code?.trim();
  if (direct) return direct;
  const legacy = spec.face_vinyl_color_code?.trim();
  if (!legacy) return undefined;
  const match = legacy.match(/^(651|8500)-(.+)$/i);
  return match ? match[2] : legacy;
}

function resolveFaceVinylSeries(
  spec: IntakeProductSpec
): "651" | "8500" | undefined {
  if (spec.face_vinyl_series === "651" || spec.face_vinyl_series === "8500") {
    return spec.face_vinyl_series;
  }
  if (spec.face_finish_type === "oracal_8500") return "8500";
  if (spec.face_finish_type === "oracal_651") return "651";
  const legacy = spec.face_vinyl_color_code?.trim();
  if (legacy?.startsWith("8500")) return "8500";
  if (legacy?.startsWith("651")) return "651";
  return undefined;
}

/** Read-only display summary for volumetric return / face vinyl selections. */
export function formatVolumetricFinishSummary(
  spec: IntakeProductSpec | null | undefined
): VolumetricFinishSummary {
  const warnings: string[] = [];

  if (!spec) {
    return {
      returnFinishLabel: "—",
      faceVinylLabel: "—",
      warnings: ["Specificație indisponibilă"],
    };
  }

  const system = resolveReturnFinishSystem(spec);
  let returnFinishLabel = "—";
  let returnFinishDetail: string | undefined;
  let returnFinishCode: string | undefined;
  let returnFinishName: string | undefined;
  let returnPreviewHex: string | undefined;
  let returnApproximatePreview = false;

  if (system === "RAL") {
    const code = spec.return_ral_code?.trim() || spec.paint_ral_code?.trim();
    const name = spec.return_ral_name?.trim() || spec.paint_ral_name?.trim();
    returnFinishLabel = "Vopsit RAL";
    returnFinishCode = code;
    returnFinishName = name;
    returnPreviewHex = spec.return_ral_preview_hex?.trim();
    if (code) {
      const item = findColorRegistryItem("RAL", code);
      returnFinishDetail = item
        ? formatColorRegistryLabel(item)
        : `RAL ${code}${name ? ` — ${name}` : ""}`;
      if (!returnPreviewHex && item) returnPreviewHex = item.previewHex;
    } else {
      returnFinishDetail = "RAL — cod nespecificat";
    }
    returnApproximatePreview = true;
    if (!warnings.includes(RAL_APPROX_NOTE)) warnings.push(RAL_APPROX_NOTE);
    if (!spec.return_ral_code?.trim() && spec.paint_ral_code?.trim()) {
      warnings.push("Afișare din câmp legacy paint_ral_code.");
    }
  } else if (system === "ORACAL") {
    const series = spec.return_oracal_series ?? "651";
    const code = spec.return_oracal_code?.trim();
    const name = spec.return_oracal_name?.trim();
    returnFinishLabel = `Colantat Oracal ${series}`;
    returnFinishCode = code;
    returnFinishName = name;
    returnPreviewHex = spec.return_oracal_preview_hex?.trim();
    returnFinishDetail = code
      ? `Oracal ${series}-${code}${name ? ` — ${name}` : ""}`
      : "Oracal — cod nespecificat";
  } else {
    const color = spec.return_color ?? spec.return_edge_color ?? "white";
    const colorLabel = RETURN_COLOR_LABELS[color] ?? color;
    returnFinishLabel = `Standard — ${colorLabel}`;
    returnFinishDetail = `Cant aluminiu stoc (${colorLabel.toLowerCase()})`;
  }

  let faceVinylLabel = "Nu";
  let faceVinylDetail: string | undefined;
  let faceVinylCode: string | undefined;
  let faceVinylName: string | undefined;
  let faceVinylPreviewHex: string | undefined;
  let faceVinylTranslucent = false;

  if (isFaceVinylEnabled(spec)) {
    const series = resolveFaceVinylSeries(spec);
    const code = parseLegacyFaceVinylCode(spec);
    const name = spec.face_vinyl_name?.trim() || spec.face_vinyl_color_name?.trim();
    faceVinylCode = code;
    faceVinylName = name;
    faceVinylPreviewHex = spec.face_vinyl_preview_hex?.trim();

    if (series === "8500") {
      faceVinylTranslucent = true;
      faceVinylLabel = "Oracal 8500";
      faceVinylDetail = code
        ? `${series}-${code}${name ? ` — ${name}` : ""}`
        : "Cod nespecificat";
    } else if (series === "651") {
      faceVinylLabel = "Oracal 651";
      faceVinylDetail = code
        ? `${series}-${code}${name ? ` — ${name}` : ""}`
        : "Cod nespecificat";
    } else {
      faceVinylLabel = "Colantare față";
      faceVinylDetail = code || name || spec.face_finish_type || "—";
    }

    if (!spec.face_vinyl_code?.trim() && spec.face_vinyl_color_code?.trim()) {
      warnings.push("Afișare din câmp legacy face_vinyl_color_code.");
    }
    if (!faceVinylCode) {
      warnings.push("Alege culoarea / codul pentru a finaliza finisajul față.");
    }
  }

  if (system === "RAL" && !returnFinishCode) {
    warnings.push("Alege culoarea RAL pentru a finaliza finisajul cant.");
  }
  if (system === "ORACAL" && !returnFinishCode) {
    warnings.push("Alege codul Oracal pentru a finaliza finisajul cant.");
  }

  return {
    returnFinishLabel,
    returnFinishDetail,
    returnFinishCode,
    returnFinishName,
    returnPreviewHex,
    returnApproximatePreview,
    faceVinylLabel,
    faceVinylDetail,
    faceVinylCode,
    faceVinylName,
    faceVinylPreviewHex,
    faceVinylTranslucent,
    warnings,
  };
}
