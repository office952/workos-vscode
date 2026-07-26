/**
 * Read-only Structură produs — aligned with the classic editor timeline
 * (chips + numbered rows + type colors). No add/edit; owner can read the product.
 */
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  ChevronRight,
  Frame,
  Hammer,
  Layers,
  Layers2,
  Lightbulb,
  Paintbrush,
  ScanLine,
  Sparkles,
  Tags,
} from "lucide-react";
import {
  parseTemplateComponentsWithLegacy,
  type ProductComponentType,
  type ProductTemplateComponent,
  type ProductTemplateEntity,
} from "@/lib/api";
import { CncProcessableBadge } from "@/components/workos/CncProcessableBadge";
import { formatComponentDisplayName } from "@/features/product-system/templateCalibrationDisplay";
import {
  deriveConstructionStages,
  parseExplicitConstructionStagesFromNotes,
  type DerivedConstructionStage,
} from "@/features/product-system/templateConstructionStages";
import {
  getComponentTypeDisplayLabel,
  isVolumetricLettersTemplate,
} from "@/features/product-system/componentTypeDisplay";
import {
  ComponentTimelineWrap,
  TemplateConstructionStageRow,
  type ConstructionStageStyle,
} from "@/features/product-system/templateStudioPanels";
import {
  LETTERS_FACE_PLEXI_3MM_OPAL_DISPLAY_NAME,
  LETTERS_FACE_STRUCTURE_DISPLAY_NAME,
} from "@/lib/materials/lettersFacePlexiMaterialDisplay";
import { LETTERS_BACK_STRUCTURE_DISPLAY_NAME } from "@/lib/materials/lettersBackForexMaterialDisplay";
import { LETTERS_LED_STRUCTURE_DISPLAY_NAME } from "@/lib/materials/lettersLedMaterialDisplay";
import { LETTERS_VOLUME_STRUCTURE_DISPLAY_NAME } from "@/lib/materials/lettersVolumeAluminumMaterialDisplay";
import { PS_SURFACE_PANEL } from "./productSystemSurfaces";
import { isLettersFinisajStructureComponent } from "./lettersFinishAvailabilityDisplay";
import { isLettersBackForexStructureComponent } from "./lettersBackForexProcessDisplay";
import { isLettersFaceStructureComponent } from "./lettersFaceProcessDisplay";
import { isLettersLedStructureComponent } from "./lettersLedProcessDisplay";
import { isLettersVolumeAluminumStructureComponent } from "./lettersVolumeAluminumProcessDisplay";
import { resolveLettersStructureDetailPath } from "./lettersStructureDetailRoutes";
import { LETTERS_STRUCTURE_CARD_NOT_TASK_HELPER_RO } from "./lettersStructurePrincipalTaskOrder";
import {
  ACM_BOXED_CARD_NOT_TASK_HELPER_RO,
  ACM_BOXED_STRUCTURE_HELPER_RO,
  ACM_BOXED_STRUCTURE_TEACHING_CARDS,
} from "./acmBoxedStructureDocumentation";
import {
  buildAcmBoxedStructureStepPath,
  type AcmBoxedStructureStepId,
} from "./acmBoxedStructureDetailRoutes";
import { isAcmBoxedMountingTemplate } from "./acmBoxedTemplateIdentity";
import { buildLettersAcmConnectionPricesPath } from "./lettersAcmCompositionConnectionPricesRoutes";
import {
  countOwnerVerifiedConnectionPrices,
  LETTERS_ACM_CONNECTION_PRICES_PAGE_TITLE_RO,
} from "./lettersAcmCompositionConnectionPrices";
import { buildLettersAcmComposerPath } from "./lettersAcmComposerIaMockRoutes";

/** Thin teaser — full volume documentation lives on the detail page. */
function LettersVolumeAluminumDetailTeaser() {
  return (
    <div
      className="flex items-center justify-between gap-2 border-t border-sky-800/35 bg-sky-950/15 px-4 py-2"
      data-testid="product-system-v2-letters-volume-detail-teaser"
    >
      <p className="truncate text-[11px] text-sky-200/80">
        <span className="font-medium text-sky-100">{LETTERS_VOLUME_STRUCTURE_DISPLAY_NAME}</span>
        <span className="text-sky-500/70"> · 30/60/80/100 · ml</span>
      </p>
      <span className="inline-flex shrink-0 items-center gap-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-sky-300/90">
        Detaliu
        <ChevronRight className="h-3.5 w-3.5" aria-hidden />
      </span>
    </div>
  );
}

/** Thin teaser — full back documentation lives on the detail page. */
function LettersBackForexDetailTeaser() {
  return (
    <div
      className="flex items-center justify-between gap-2 border-t border-amber-800/35 bg-amber-950/15 px-4 py-2"
      data-testid="product-system-v2-letters-back-detail-teaser"
    >
      <p className="truncate text-[11px] text-amber-200/80">
        <span className="font-medium text-amber-100">{LETTERS_BACK_STRUCTURE_DISPLAY_NAME}</span>
        <span className="text-amber-500/70"> · CNC · șanfren opț.</span>
      </p>
      <span className="inline-flex shrink-0 items-center gap-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-amber-300/90">
        Detaliu
        <ChevronRight className="h-3.5 w-3.5" aria-hidden />
      </span>
    </div>
  );
}

/** Thin teaser — full LED documentation lives on the detail page. */
function LettersLedDetailTeaser() {
  return (
    <div
      className="flex items-center justify-between gap-2 border-t border-yellow-800/35 bg-yellow-950/15 px-4 py-2"
      data-testid="product-system-v2-letters-led-detail-teaser"
    >
      <p className="truncate text-[11px] text-yellow-200/80">
        <span className="font-medium text-yellow-100">{LETTERS_LED_STRUCTURE_DISPLAY_NAME}</span>
        <span className="text-yellow-500/70"> · module · PSU</span>
      </p>
      <span className="inline-flex shrink-0 items-center gap-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-yellow-300/90">
        Detaliu
        <ChevronRight className="h-3.5 w-3.5" aria-hidden />
      </span>
    </div>
  );
}

/** Thin teaser — full face documentation lives on the detail page. */
function LettersFaceDetailTeaser() {
  return (
    <div
      className="flex items-center justify-between gap-2 border-t border-violet-800/35 bg-violet-950/15 px-4 py-2"
      data-testid="product-system-v2-letters-face-detail-teaser"
    >
      <p className="truncate text-[11px] text-violet-200/80">
        <span className="font-medium text-violet-100">{LETTERS_FACE_PLEXI_3MM_OPAL_DISPLAY_NAME}</span>
        <span className="text-violet-500/70"> · CNC · finisaj</span>
      </p>
      <span className="inline-flex shrink-0 items-center gap-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-violet-300/90">
        Detaliu
        <ChevronRight className="h-3.5 w-3.5" aria-hidden />
      </span>
    </div>
  );
}

function LettersAcmConnectionPricesEntryCard({ templateCode }: { templateCode: string }) {
  const navigate = useNavigate();
  const path = buildLettersAcmConnectionPricesPath(templateCode);
  const verifiedCount = countOwnerVerifiedConnectionPrices();

  return (
    <button
      type="button"
      onClick={() => navigate(path)}
      className="mt-3 w-full overflow-hidden rounded-xl border border-emerald-500/35 bg-emerald-950/20 px-4 py-3 text-left transition-colors hover:border-emerald-400/50 hover:bg-emerald-950/30"
      data-testid="product-system-v2-letters-acm-connection-prices-entry"
    >
      <div className="flex items-center gap-3">
        <div className="shrink-0 rounded-lg bg-emerald-500/15 p-2 text-emerald-300 [&>svg]:h-5 [&>svg]:w-5">
          <Tags className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-[11px] font-bold uppercase tracking-wide text-emerald-300">
            Prețuri conexiune
          </p>
          <p className="mt-0.5 truncate text-[13px] font-semibold text-wo-text-primary">
            {LETTERS_ACM_CONNECTION_PRICES_PAGE_TITLE_RO}
          </p>
          <p className="mt-0.5 text-[11px] text-emerald-200/70">
            Șablon 20 EUR/mp · {verifiedCount} linii verificate owner
          </p>
        </div>
        <ChevronRight className="h-4 w-4 shrink-0 text-emerald-300/80" aria-hidden />
      </div>
    </button>
  );
}

function LettersAcmComposerEntryCard({ templateCode }: { templateCode: string }) {
  const navigate = useNavigate();
  const path = buildLettersAcmComposerPath(templateCode);

  return (
    <button
      type="button"
      onClick={() => navigate(path)}
      className="mt-2 w-full overflow-hidden rounded-xl border border-violet-500/35 bg-violet-950/20 px-4 py-3 text-left transition-colors hover:border-violet-400/50 hover:bg-violet-950/30"
      data-testid="product-system-v2-letters-acm-composer-entry"
    >
      <div className="flex items-center gap-3">
        <div className="shrink-0 rounded-lg bg-violet-500/15 p-2 text-violet-300 [&>svg]:h-5 [&>svg]:w-5">
          <Layers2 className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-[11px] font-bold uppercase tracking-wide text-violet-300">
            Composer
          </p>
          <p className="mt-0.5 truncate text-[13px] font-semibold text-wo-text-primary">
            Litere ↔ Alucobond — mock IA
          </p>
          <p className="mt-0.5 text-[11px] text-violet-200/70">
            Compatibil v1 · composit readonly · fără CostEngine
          </p>
        </div>
        <ChevronRight className="h-4 w-4 shrink-0 text-violet-300/80" aria-hidden />
      </div>
    </button>
  );
}

function AcmBoxedTeachingCard({
  templateCode,
  index,
  typeLabel,
  displayName,
  teaserRo,
  teaserHintRo,
  stepId,
  selected,
  onSelect,
}: {
  templateCode: string;
  index: number;
  typeLabel: string;
  displayName: string;
  teaserRo: string;
  teaserHintRo: string;
  stepId: AcmBoxedStructureStepId;
  selected: boolean;
  onSelect: () => void;
}) {
  const navigate = useNavigate();
  const detailPath = buildAcmBoxedStructureStepPath(templateCode, stepId);
  const isFrame = stepId === "structura-metalica";

  return (
    <div
      data-component-index={index}
      data-testid={`product-system-v2-structure-row-${index}`}
      className={`overflow-hidden rounded-xl border transition-all duration-200 ${
        selected
          ? "border-purple-500/50 bg-purple-500/[0.06] ring-1 ring-purple-500/25"
          : "border-wo-border-subtle bg-wo-surface-raised"
      } ${isFrame ? "hover:border-amber-500/40" : "hover:border-cyan-500/40"}`}
    >
      <button
        type="button"
        onClick={() => {
          onSelect();
          navigate(detailPath);
        }}
        className="w-full px-4 py-3 text-left hover:bg-slate-900/20"
        data-testid={`product-system-v2-acm-teaching-open-${stepId}`}
      >
        <div className="flex items-center gap-3">
          <div
            className={`shrink-0 rounded-lg p-2 ${
              isFrame ? "bg-amber-500/15 text-amber-300" : "bg-cyan-500/15 text-cyan-300"
            } [&>svg]:h-5 [&>svg]:w-5`}
          >
            {isFrame ? <Frame className="h-5 w-5" /> : <Box className="h-5 w-5" />}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-[10px] text-wo-text-muted">#{index + 1}</span>
              <span
                className={`text-[11px] font-bold uppercase tracking-wide ${
                  isFrame ? "text-amber-300" : "text-cyan-300"
                }`}
              >
                {typeLabel}
              </span>
            </div>
            <p className="mt-0.5 truncate text-[13px] font-semibold text-wo-text-primary">{displayName}</p>
          </div>
          <ChevronRight
            className={`h-4 w-4 shrink-0 ${isFrame ? "text-amber-300/80" : "text-cyan-300/80"}`}
            aria-hidden
          />
        </div>
      </button>
      <div
        className={`flex items-center justify-between gap-2 border-t px-4 py-2 ${
          isFrame
            ? "border-amber-800/35 bg-amber-950/15"
            : "border-cyan-800/35 bg-cyan-950/15"
        }`}
        data-testid="product-system-v2-acm-boxed-detail-teaser"
      >
        <p className={`truncate text-[11px] ${isFrame ? "text-amber-200/80" : "text-cyan-200/80"}`}>
          <span className={`font-medium ${isFrame ? "text-amber-100" : "text-cyan-100"}`}>
            {teaserRo}
          </span>
          <span className={isFrame ? "text-amber-500/70" : "text-cyan-500/70"}>{teaserHintRo}</span>
        </p>
        <span
          className={`inline-flex shrink-0 items-center gap-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] ${
            isFrame ? "text-amber-300/90" : "text-cyan-300/90"
          }`}
        >
          Detaliu
          <ChevronRight className="h-3.5 w-3.5" aria-hidden />
        </span>
      </div>
    </div>
  );
}

/** Owner hide: Finisaj produs row confuses with Față/Volum finish options. Data stays in template. */
function isHiddenLettersFinisajStructureRow(
  templateCode: string,
  component: { type: string; component_id: string; name: string },
): boolean {
  return (
    isVolumetricLettersTemplate(templateCode) &&
    isLettersFinisajStructureComponent(component)
  );
}

type StageVisual = {
  icon: React.ReactNode;
  color: string;
  bgColor: string;
  borderColor: string;
  label: string;
};

const STAGE_VISUAL_BY_TYPE: Record<ProductComponentType, StageVisual> = {
  STRUCTURA: {
    icon: <Frame className="w-5 h-5" />,
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/30",
    label: "Structură Metalică",
  },
  FATA_ACP_ROUTATA: {
    icon: <Layers className="w-5 h-5" />,
    color: "text-amber-400",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/30",
    label: "Față ACP Routată",
  },
  DIFUZIE_PLEXI: {
    icon: <Sparkles className="w-5 h-5" />,
    color: "text-cyan-400",
    bgColor: "bg-cyan-500/10",
    borderColor: "border-cyan-500/30",
    label: "Difuzie Plexiglas",
  },
  ILUMINARE: {
    icon: <Lightbulb className="w-5 h-5" />,
    color: "text-yellow-400",
    bgColor: "bg-yellow-500/10",
    borderColor: "border-yellow-500/30",
    label: "Iluminare LED",
  },
  RELIEF_PLEXI_10MM: {
    icon: <Box className="w-5 h-5" />,
    color: "text-purple-400",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/30",
    label: "Relief Plexiglas 10mm",
  },
  FINISAJ: {
    icon: <Paintbrush className="w-5 h-5" />,
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/30",
    label: "Finisaj",
  },
  PRINT_SUBSTRATE: {
    icon: <Layers className="w-5 h-5" />,
    color: "text-rose-400",
    bgColor: "bg-rose-500/10",
    borderColor: "border-rose-500/30",
    label: "Substrat Print",
  },
  VINYL_APPLICATION: {
    icon: <Layers className="w-5 h-5" />,
    color: "text-pink-400",
    bgColor: "bg-pink-500/10",
    borderColor: "border-pink-500/30",
    label: "Aplicare Vinyl",
  },
  PLEXI_PANEL: {
    icon: <Box className="w-5 h-5" />,
    color: "text-sky-400",
    bgColor: "bg-sky-500/10",
    borderColor: "border-sky-500/30",
    label: "Panou Plexiglas",
  },
  FRAME_PROFILE: {
    icon: <Frame className="w-5 h-5" />,
    color: "text-orange-400",
    bgColor: "bg-orange-500/10",
    borderColor: "border-orange-500/30",
    label: "Profil Cadru",
  },
  LITERE_3D: {
    icon: <ScanLine className="w-5 h-5" />,
    color: "text-violet-400",
    bgColor: "bg-violet-500/10",
    borderColor: "border-violet-500/30",
    label: "Litere 3D",
  },
  ELECTRIC_LED: {
    icon: <Lightbulb className="w-5 h-5" />,
    color: "text-yellow-400",
    bgColor: "bg-yellow-500/10",
    borderColor: "border-yellow-500/30",
    label: "Sistem LED",
  },
  EXTERNALIZARE: {
    icon: <Layers className="w-5 h-5" />,
    color: "text-wo-text-secondary",
    bgColor: "bg-slate-500/10",
    borderColor: "border-slate-500/30",
    label: "Externalizare",
  },
  TAIERE_CNC_LASER: {
    icon: <ScanLine className="w-5 h-5" />,
    color: "text-cyan-300",
    bgColor: "bg-cyan-500/10",
    borderColor: "border-cyan-500/30",
    label: "Tăiere CNC / Laser",
  },
  LAMINARE: {
    icon: <Layers className="w-5 h-5" />,
    color: "text-teal-300",
    bgColor: "bg-teal-500/10",
    borderColor: "border-teal-500/30",
    label: "Laminare",
  },
};

function stageVisual(type: ProductComponentType): StageVisual {
  return STAGE_VISUAL_BY_TYPE[type];
}

function volumetricStageIcon(stage: { code: string; label: string }): React.ReactNode | null {
  const key = `${stage.code} ${stage.label}`.toLowerCase();
  if (key.includes("face") || key.includes("față") || key.includes("fata") || key.includes("vizual")) {
    return <ScanLine className="w-5 h-5" />;
  }
  if (key.includes("lateral") || key.includes("volum") || key.includes("profil")) {
    return <Box className="w-5 h-5" />;
  }
  if (key.includes("spate") || key.includes("capac") || key.includes("forex")) {
    return <Layers className="w-5 h-5" />;
  }
  if (key.includes("led") || key.includes("electric")) {
    return <Lightbulb className="w-5 h-5" />;
  }
  if (key.includes("finis")) {
    return <Paintbrush className="w-5 h-5" />;
  }
  if (key.includes("structur") || key.includes("premont") || key.includes("bare")) {
    return <Frame className="w-5 h-5" />;
  }
  return null;
}

function ReadonlyStructureCard({
  component,
  templateCode,
  index,
  selected,
  onSelect,
}: {
  component: ProductTemplateComponent;
  templateCode: string;
  index: number;
  selected: boolean;
  onSelect: () => void;
}) {
  const navigate = useNavigate();
  const visual = stageVisual(component.type);
  const typeLabel = getComponentTypeDisplayLabel(component, templateCode, visual.label);
  const icon =
    (isVolumetricLettersTemplate(templateCode)
      ? volumetricStageIcon({ code: component.component_id, label: component.name })
      : null) ?? visual.icon;
  const showLettersFaceProcess =
    isVolumetricLettersTemplate(templateCode) &&
    isLettersFaceStructureComponent(component);
  const showLettersVolumeAluminum =
    isVolumetricLettersTemplate(templateCode) &&
    !showLettersFaceProcess &&
    isLettersVolumeAluminumStructureComponent(component);
  const showLettersBackForex =
    isVolumetricLettersTemplate(templateCode) &&
    !showLettersFaceProcess &&
    !showLettersVolumeAluminum &&
    isLettersBackForexStructureComponent(component);
  const showLettersLed =
    isVolumetricLettersTemplate(templateCode) &&
    !showLettersFaceProcess &&
    !showLettersVolumeAluminum &&
    !showLettersBackForex &&
    isLettersLedStructureComponent(component);
  const displayName = showLettersFaceProcess
    ? LETTERS_FACE_STRUCTURE_DISPLAY_NAME
    : showLettersVolumeAluminum
      ? LETTERS_VOLUME_STRUCTURE_DISPLAY_NAME
      : showLettersBackForex
        ? LETTERS_BACK_STRUCTURE_DISPLAY_NAME
        : showLettersLed
          ? LETTERS_LED_STRUCTURE_DISPLAY_NAME
          : formatComponentDisplayName(component.name);

  const detailPath = resolveLettersStructureDetailPath(templateCode, component);
  const opensDetailPage = detailPath != null;

  const handleSelect = () => {
    onSelect();
    if (detailPath) {
      navigate(detailPath);
    }
  };

  return (
    <div
      data-component-index={index}
      data-testid={`product-system-v2-structure-row-${index}`}
      className={`overflow-hidden rounded-xl border transition-all duration-200 ${
        selected
          ? "border-purple-500/50 bg-purple-500/[0.06] ring-1 ring-purple-500/25"
          : "border-wo-border-subtle bg-wo-surface-raised"
      } ${showLettersFaceProcess ? "hover:border-violet-500/40" : ""} ${
        showLettersVolumeAluminum ? "hover:border-sky-500/40" : ""
      } ${showLettersBackForex ? "hover:border-amber-500/40" : ""} ${
        showLettersLed ? "hover:border-yellow-500/40" : ""
      }`}
    >
      <button
        type="button"
        onClick={handleSelect}
        className="w-full px-4 py-3 text-left hover:bg-slate-900/20"
        data-testid={
          showLettersFaceProcess
            ? "product-system-v2-letters-face-open-detail"
            : showLettersVolumeAluminum
              ? "product-system-v2-letters-volume-open-detail"
              : showLettersBackForex
                ? "product-system-v2-letters-back-open-detail"
                : showLettersLed
                  ? "product-system-v2-letters-led-open-detail"
                  : undefined
        }
      >
        <div className="flex items-center gap-3">
          <div className={`shrink-0 rounded-lg p-2 ${visual.bgColor} ${visual.color} [&>svg]:h-5 [&>svg]:w-5`}>
            {icon}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-[10px] text-wo-text-muted">#{index + 1}</span>
              <span className="text-[11px] font-bold uppercase tracking-wide text-wo-text-primary">
                {typeLabel}
              </span>
              {showLettersFaceProcess ? (
                <CncProcessableBadge
                  size="sm"
                  testId="product-system-v2-letters-face-cnc-row-mark"
                />
              ) : null}
            </div>
            <p className="mt-0.5 truncate text-[13px] font-semibold text-wo-text-primary">
              {displayName || <span className="italic text-wo-text-muted">Fără nume</span>}
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-1.5">
            {opensDetailPage ? (
              <ChevronRight
                className={`h-4 w-4 ${
                  showLettersLed
                    ? "text-yellow-300/80"
                    : showLettersBackForex
                      ? "text-amber-300/80"
                      : showLettersVolumeAluminum
                        ? "text-sky-300/80"
                        : "text-violet-300/80"
                }`}
                aria-hidden
              />
            ) : (
              <>
                <span className="rounded-lg bg-blue-500/10 px-2 py-1 text-[10px] font-semibold text-blue-400">
                  {component.operations.length} op.
                </span>
                <span className="rounded-lg bg-emerald-500/10 px-2 py-1 text-[10px] font-semibold text-emerald-400">
                  {component.materials.length} mat.
                </span>
              </>
            )}
          </div>
        </div>
      </button>
      {showLettersFaceProcess ? <LettersFaceDetailTeaser /> : null}
      {showLettersVolumeAluminum ? <LettersVolumeAluminumDetailTeaser /> : null}
      {showLettersBackForex ? <LettersBackForexDetailTeaser /> : null}
      {showLettersLed ? <LettersLedDetailTeaser /> : null}
    </div>
  );
}

export function ProductSystemStructureReadonlyPanel({
  template,
  testId = "product-system-v2-modules-center",
}: {
  template: ProductTemplateEntity;
  testId?: string;
}) {
  const navigate = useNavigate();
  const components = useMemo(() => {
    const parsed = parseTemplateComponentsWithLegacy(
      template.components_json,
      template.operations_json,
      template.required_materials_json,
    );
    return parsed.filter((c) => c._legacy !== true);
  }, [
    template.components_json,
    template.operations_json,
    template.required_materials_json,
  ]);
  const visibleComponents = useMemo(
    () =>
      components
        .map((component, index) => ({ component, index }))
        .filter(
          ({ component }) =>
            !isHiddenLettersFinisajStructureRow(template.template_code, component),
        ),
    [components, template.template_code],
  );

  const isAcmTeaching = isAcmBoxedMountingTemplate(template.template_code);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(
    isAcmTeaching ? 0 : visibleComponents.length > 0 ? visibleComponents[0]!.index : null,
  );

  const stages = useMemo(() => {
    if (isAcmTeaching) return [];
    const explicit = parseExplicitConstructionStagesFromNotes(template.notes);
    return deriveConstructionStages(components, {
      explicitStages: explicit,
      getStageLabel: (component) => {
        const visual = stageVisual(component.type);
        const typeLabel = getComponentTypeDisplayLabel(
          component,
          template.template_code,
          visual.label,
        );
        return typeLabel || component.name.trim() || component.component_id;
      },
    }).filter((stage) => {
      const component = components[stage.componentIndex];
      return (
        !!component &&
        !isHiddenLettersFinisajStructureRow(template.template_code, component)
      );
    });
  }, [components, isAcmTeaching, template.notes, template.template_code]);

  const getStageStyle = (stage: DerivedConstructionStage): ConstructionStageStyle => {
    const visual = stageVisual(stage.componentType);
    const volIcon = isVolumetricLettersTemplate(template.template_code)
      ? volumetricStageIcon(stage)
      : null;
    return {
      icon: volIcon ?? visual.icon,
      color: visual.color,
      bgColor: visual.bgColor,
      borderColor: visual.borderColor,
    };
  };

  if (isAcmTeaching) {
    return (
      <section className="space-y-4" data-testid={testId}>
        <div className="space-y-3" data-testid="product-system-v2-modules-core">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <Hammer className="h-5 w-5 shrink-0 text-purple-400" />
                <h3
                  className="text-[14px] font-bold text-wo-text-primary"
                  data-testid="product-system-v2-structure-title"
                >
                  Structură produs
                </h3>
                <span className="rounded-full bg-purple-500/10 px-2 py-0.5 text-[10px] font-bold text-purple-400">
                  {ACM_BOXED_STRUCTURE_TEACHING_CARDS.length}
                </span>
              </div>
              <p className="mt-1 pl-7 text-[10px] text-wo-text-muted">
                {ACM_BOXED_STRUCTURE_HELPER_RO} {ACM_BOXED_CARD_NOT_TASK_HELPER_RO}
              </p>
            </div>
          </div>
          <div className="space-y-1" data-testid="product-system-v2-modules-list">
            {ACM_BOXED_STRUCTURE_TEACHING_CARDS.map((card, index) => (
              <ComponentTimelineWrap
                key={card.stepId}
                index={index}
                isLast={index === ACM_BOXED_STRUCTURE_TEACHING_CARDS.length - 1}
              >
                <AcmBoxedTeachingCard
                  templateCode={template.template_code}
                  index={index}
                  typeLabel={card.typeLabel}
                  displayName={card.displayName}
                  teaserRo={card.teaserRo}
                  teaserHintRo={card.teaserHintRo}
                  stepId={card.stepId}
                  selected={selectedIndex === index}
                  onSelect={() => setSelectedIndex(index)}
                />
              </ComponentTimelineWrap>
            ))}
            <LettersAcmConnectionPricesEntryCard templateCode={template.template_code} />
            <LettersAcmComposerEntryCard templateCode={template.template_code} />
          </div>
        </div>
      </section>
    );
  }

  if (visibleComponents.length === 0) {
    return (
      <section className={`${PS_SURFACE_PANEL} px-4 py-4`} data-testid={testId}>
        <div className="flex items-center gap-2">
          <Hammer className="h-5 w-5 shrink-0 text-purple-400" />
          <h3 className="text-[14px] font-bold text-wo-text-primary" data-testid="product-system-v2-structure-title">
            Structură produs
          </h3>
        </div>
        <p className="mt-2 text-[12px] text-wo-text-muted" data-testid="product-system-v2-modules-empty">
          Nicio componentă vizibilă pe acest Product Template.
        </p>
      </section>
    );
  }

  return (
    <section className="space-y-4" data-testid={testId}>
      {stages.length > 0 ? (
        <div
          className="rounded-xl border border-wo-border-subtle bg-wo-surface-raised p-3"
          data-testid="product-system-v2-structure-chips"
        >
          <TemplateConstructionStageRow
            stages={stages}
            selectedIndex={selectedIndex}
            onSelectStage={(componentIndex) => {
              setSelectedIndex(componentIndex);
              const component = components[componentIndex];
              if (!component) return;
              const detailPath = resolveLettersStructureDetailPath(
                template.template_code,
                component,
              );
              if (detailPath) {
                navigate(detailPath);
              }
            }}
            getStageStyle={getStageStyle}
            collapsible={false}
          />
        </div>
      ) : null}

      <div className="space-y-3" data-testid="product-system-v2-modules-core">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <Hammer className="h-5 w-5 shrink-0 text-purple-400" />
              <h3
                className="text-[14px] font-bold text-wo-text-primary"
                data-testid="product-system-v2-structure-title"
              >
                Structură produs
              </h3>
              <span className="rounded-full bg-purple-500/10 px-2 py-0.5 text-[10px] font-bold text-purple-400">
                {visibleComponents.length}
              </span>
            </div>
            <p className="mt-1 pl-7 text-[10px] text-wo-text-muted">
              {isVolumetricLettersTemplate(template.template_code)
                ? `Față · Volum · Spate · LED → pagină detaliu. Finisaj produs ascuns (față/cant pe pașii lor). ${LETTERS_STRUCTURE_CARD_NOT_TASK_HELPER_RO}`
                : "Componente template → selectare pe hartă."}
            </p>
          </div>
        </div>

        <div className="space-y-1" data-testid="product-system-v2-modules-list">
          {visibleComponents.map(({ component, index }, visibleIndex) => (
            <ComponentTimelineWrap
              key={`${component.component_id}_${index}`}
              index={visibleIndex}
              isLast={visibleIndex === visibleComponents.length - 1}
            >
              <ReadonlyStructureCard
                component={component}
                templateCode={template.template_code}
                index={index}
                selected={selectedIndex === index}
                onSelect={() => setSelectedIndex(index)}
              />
            </ComponentTimelineWrap>
          ))}
        </div>
        {isVolumetricLettersTemplate(template.template_code) ? (
          <>
            <LettersAcmConnectionPricesEntryCard templateCode={template.template_code} />
            <LettersAcmComposerEntryCard templateCode={template.template_code} />
          </>
        ) : null}
      </div>
    </section>
  );
}
