import { useEffect, useState, useCallback, useMemo, useRef } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import {
  productTemplatesApi,
  productTemplateAvailabilityApi,
  materialsApi,
  parseTemplateComponentsWithLegacy,
  validateTemplateComponentsStrict,
  PRODUCT_COMPONENT_TYPES,
  type ProductTemplateEntity,
  type ProductTemplateAvailabilityItem,
  type ProductTemplateComponent,
  type ProductComponentType,
  type ProductTemplateOperation,
  type ProductTemplateMaterial,
  type InventoryMaterialEntity,
} from "@/lib/api";
import { getRoutingForOperation, getWorkstation } from "@/lib/workstationRouting";
import {
  productFamiliesApi,
  type ProductFamily,
} from "@/api/productFamilies";
import { isMockEnabled } from "@/lib/mockGuard";
import { mockTemplatesToEntities, mockProductFamilies } from "@/lib/mockData";
import {
  formatMaterialSourceNotes,
  getMaterialRegistryStatusBadges,
  getMaterialRegistryUnknownLabel,
  hasMaterialSourceNotes,
} from "@/features/product-system/materialRegistryDisplay";
import {
  getComponentTypeDisplayLabel,
  getComponentTypeSelectOptionLabel,
} from "@/features/product-system/componentTypeDisplay";
import { MaterialRegistryPicker } from "@/features/product-system/MaterialRegistryPicker";
import { formatMaterialRegistryShortName } from "@/features/product-system/materialRegistryDisplay";
import { isVolumetricLettersTemplate } from "@/features/product-system/componentTypeDisplay";
import {
  VolumetricCantProductionModulesPanel,
  VolumetricComponentProductionHint,
} from "@/features/product-system/VolumetricProductionGuidance";
import { TemplateGeneralTabPanel } from "@/features/product-system/TemplateGeneralTabPanel";
import { ProductE2EReadinessPanel } from "@/features/product-system/ProductE2EReadinessPanel";
import { ProductTemplatePublicationPanel } from "@/features/product-system/ProductTemplatePublicationPanel";
import { ComponentContractUsedByPanel } from "@/features/product-system/ComponentContractUsedByPanel";
import { getTemplateArchivePolicy } from "@/features/product-system/templateArchivePolicy";
import {
  deriveConstructionStages,
  parseExplicitConstructionStagesFromNotes,
} from "@/features/product-system/templateConstructionStages";
import {
  CALIBRATION_DURATION_TOOLTIP,
  formatComponentDisplayName,
  formatInternalTemplateHours,
  formatOperationCalibrationLabel,
} from "@/features/product-system/templateCalibrationDisplay";
import {
  TemplateEditorCommandBar,
  ComponentDetailInsightPanel,
  TemplateConstructionStageRow,
  ComponentTimelineWrap,
  type ConstructionStageStyle,
} from "@/features/product-system/templateStudioPanels";
import {
  TemplateOperationMappingPanel,
  type TemplateOperationRef,
} from "@/features/operational-registry/TemplateOperationMappingPanel";
import {
  filterActiveTemplatesForQuote,
  filterArchivedExperimentalTemplates,
} from "@/lib/activeTemplateScope";
import { TemplateSelectorSheet } from "@/features/product-system/TemplateSelectorSheet";
import {
  ProductAggregateOverviewPanel,
  ProductAggregateStructureList,
} from "@/features/product-system/ProductAggregateOverviewPanel";
import { FormSystemAdminPanel } from "@/features/product-system/FormSystemAdminPanel";
import { OwnerReadonlyVolumetricProofPanel } from "@/features/product-system/OwnerReadonlyVolumetricProofPanel";
import { useProductAggregate } from "@/features/product-system/useProductAggregate";
import {
  isSyntheticAutoComponent,
  resolveDisplayCounts,
  shouldPreferAggregateDisplay,
} from "@/features/product-system/productAggregateDisplay";
import { buildReturnCantReadonlyContainerModel } from "@/features/product-system/returnCantReadonlyContainerModel";
import { ProductCompilerDisplayShell } from "@/features/product-system/ProductCompilerDisplayShell";
import {
  MODULE_PRODUS_BOUNDARY_LABEL,
  MUST_OWN_ON_MODULE_LABEL,
  PRODUCT_COMPILER_GRAPH_STAGE_LABEL,
  PRODUCT_COMPILER_LABEL,
  PRODUCT_TEMPLATE_COMPOSES_HELP,
  PRODUCT_TEMPLATE_COMPOSER_ONLY_HELP,
  RETURN_CANT_MOVE_TRUTH_HELP,
  MODULE_PRODUS_SHARED_SINGULAR_LABEL,
  SHARED_FOUNDATION_HELP,
  displayModuleSourceTypeLabel,
  displayModuleTemplateWireLabel,
  equalModulesHintRo,
} from "@/features/product-system/productTemplateModulesVocabulary";
import {
  assessCandidateModuleProdusLiveCompleteness,
  CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE,
} from "@/features/product-system/candidateModuleProdusReadonlyCompleteness";
import { buildCandidateModuleProdusReadonlySetModel } from "@/features/product-system/candidateModuleProdusReadonlySetModel";
import { CandidateModuleProdusPanel } from "@/features/product-system/CandidateModuleProdusPanel";
import { ProductSystemCanonicalCatalog } from "@/features/product-system/ProductSystemCanonicalCatalog";
import { ProductSystemV2Workspace } from "@/features/product-system/ProductSystemV2Workspace";
import { ProductSystemSpineBand } from "@/features/product-system/ProductSystemSpineBand";
import { isPsLegacyCatalogEnabled } from "@/features/product-system/productSystemV2WorkspaceModel";
import { parseRequestedTemplateCode } from "@/features/product-system/productSystemTemplateQuerySync";
import {
  buildProductSystemProductDetailPath,
  resolveRequestedTemplateCode,
} from "@/features/product-system/productSystemRouteSync";
import { useProductSystemShell } from "@/features/product-system/ProductSystemShellContext";
import {
  getInitialProductSystemScreen,
  isTemplateEditableForQuote,
  shouldShowEditorScreen,
  shouldShowLibraryScreen,
  type ProductSystemScreen,
} from "@/features/product-system/productSystemNavigation";
import {
  recordTemplateOpened,
} from "@/features/product-system/templateSelectionStorage";
import {
  Package,
  Plus,
  Trash2,
  X,
  Clock,
  Layers,
  Cog,
  Box,
  CheckCircle2,
  AlertTriangle,
  ChevronRight,
  ChevronDown,
  ArrowLeft,
  Lightbulb,
  Frame,
  Paintbrush,
  Sparkles,
  LayoutGrid,
  GripVertical,
  Info,
  Hammer,
  RefreshCw,
  ScanLine,
  MoreHorizontal,
  Search,
} from "lucide-react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { SourceBadge, StatusBadge } from "@/components/workos/design-system";
import type { SourceState } from "@/components/workos/design-system";

// ============================================================
// COMPONENT TYPE CONFIG — icons, colors, descriptions, emoji
// ============================================================
const COMPONENT_TYPE_CONFIG: Record<
  ProductComponentType,
  {
    icon: React.ReactNode;
    color: string;
    bgColor: string;
    borderColor: string;
    label: string;
    description: string;
    emoji: string;
  }
> = {
  STRUCTURA: {
    icon: <Frame className="w-5 h-5" />,
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/30",
    label: "Structură Metalică",
    description: "Cadrul principal — profile sudate, debitate CNC",
    emoji: "ðŸ—ï¸",
  },
  FATA_ACP_ROUTATA: {
    icon: <LayoutGrid className="w-5 h-5" />,
    color: "text-amber-400",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/30",
    label: "Față ACP Routată",
    description: "Panoul frontal din aluminiu compozit, routat CNC",
    emoji: "ðŸŽ¨",
  },
  DIFUZIE_PLEXI: {
    icon: <Sparkles className="w-5 h-5" />,
    color: "text-cyan-400",
    bgColor: "bg-cyan-500/10",
    borderColor: "border-cyan-500/30",
    label: "Difuzie Plexiglas",
    description: "Placa de difuzie din plexiglas opal pentru iluminare uniformă",
    emoji: "ðŸ’Ž",
  },
  ILUMINARE: {
    icon: <Lightbulb className="w-5 h-5" />,
    color: "text-yellow-400",
    bgColor: "bg-yellow-500/10",
    borderColor: "border-yellow-500/30",
    label: "Iluminare LED",
    description: "Module LED, drivere, cablaj electric",
    emoji: "ðŸ’¡",
  },
  RELIEF_PLEXI_10MM: {
    icon: <Box className="w-5 h-5" />,
    color: "text-purple-400",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/30",
    label: "Relief Plexiglas 10mm",
    description: "Litere/forme 3D din plexiglas de 10mm, tăiate laser",
    emoji: "âœ¨",
  },
  FINISAJ: {
    icon: <Paintbrush className="w-5 h-5" />,
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/30",
    label: "Finisaj",
    description: "Vopsire, lăcuire, aplicare folii, asamblare finală",
    emoji: "ðŸŽ¯",
  },
  // BUILD 4: Advertising production types
  PRINT_SUBSTRATE: {
    icon: <Layers className="w-5 h-5" />,
    color: "text-rose-400",
    bgColor: "bg-rose-500/10",
    borderColor: "border-rose-500/30",
    label: "Substrat Print",
    description: "Banner, mesh, PVC — suprafața de imprimare",
    emoji: "ðŸ–¨ï¸",
  },
  VINYL_APPLICATION: {
    icon: <Layers className="w-5 h-5" />,
    color: "text-pink-400",
    bgColor: "bg-pink-500/10",
    borderColor: "border-pink-500/30",
    label: "Aplicare Vinyl",
    description: "Autocolant, sticker, folie — aplicare și tăiere",
    emoji: "ðŸ“‹",
  },
  PLEXI_PANEL: {
    icon: <Box className="w-5 h-5" />,
    color: "text-sky-400",
    bgColor: "bg-sky-500/10",
    borderColor: "border-sky-500/30",
    label: "Panou Plexiglas",
    description: "Placă plexiglas — tăiere, gravare, montaj",
    emoji: "ðŸªŸ",
  },
  FRAME_PROFILE: {
    icon: <Frame className="w-5 h-5" />,
    color: "text-orange-400",
    bgColor: "bg-orange-500/10",
    borderColor: "border-orange-500/30",
    label: "Profil Cadru",
    description: "Profil aluminiu pentru casetă luminoasă",
    emoji: "ðŸ”²",
  },
  LITERE_3D: {
    icon: <Box className="w-5 h-5" />,
    color: "text-violet-400",
    bgColor: "bg-violet-500/10",
    borderColor: "border-violet-500/30",
    label: "Litere 3D",
    description: "Litere volumetrice — față plexiglas 3mm PMMA - opal, bordură aluminiu, spate Forex 10 mm, LED pe spate",
    emoji: "ðŸ”¤",
  },
  ELECTRIC_LED: {
    icon: <Lightbulb className="w-5 h-5" />,
    color: "text-amber-400",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/30",
    label: "Sistem LED",
    description: "Module LED, surse, cablaj pentru iluminare",
    emoji: "âš¡",
  },
  EXTERNALIZARE: {
    icon: <RefreshCw className="w-5 h-5" />,
    color: "text-red-400",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/30",
    label: "Externalizare",
    description: "Producție externalizată la furnizor",
    emoji: "ðŸ­",
  },
  TAIERE_CNC_LASER: {
    icon: <Cog className="w-5 h-5" />,
    color: "text-teal-400",
    bgColor: "bg-teal-500/10",
    borderColor: "border-teal-500/30",
    label: "Tăiere CNC/Laser",
    description: "Operații de debitare CNC sau laser",
    emoji: "âš™ï¸",
  },
  LAMINARE: {
    icon: <Layers className="w-5 h-5" />,
    color: "text-lime-400",
    bgColor: "bg-lime-500/10",
    borderColor: "border-lime-500/30",
    label: "Laminare",
    description: "Laminare protecție UV, mat sau lucios",
    emoji: "ðŸ›¡ï¸",
  },
};

function getVolumetricStageIcon(stage: { code: string; label: string }): React.ReactNode | null {
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

function getBlueprintComponentIcon(
  component: Pick<ProductTemplateComponent, "component_id" | "name">,
  templateCode: string,
  fallback: React.ReactNode
): React.ReactNode {
  if (!isVolumetricLettersTemplate(templateCode)) {
    return fallback;
  }
  return (
    getVolumetricStageIcon({
      code: component.component_id,
      label: component.name,
    }) ?? fallback
  );
}

// ============================================================
// TOOLTIP COMPONENT
// ============================================================
function OperationRoutingBadge({ opCode }: { opCode: string }) {
  const routing = getRoutingForOperation(opCode.toLowerCase().replace(/[-\s]/g, "_"));
  if (!routing) {
    if (!opCode.trim()) return null;
    return (
      <span className="px-1.5 py-0.5 text-[8px] font-semibold rounded bg-wo-surface-inset text-wo-text-dim border border-wo-border-strong whitespace-nowrap" title="Routing lipsă — operație necunoscută">
        ! Routing lipsă
      </span>
    );
  }
  const ws = getWorkstation(routing.workstationId);
  if (!ws) return null;
  return (
    <span
      className={`px-1.5 py-0.5 text-[8px] font-semibold rounded bg-wo-surface-inset border border-wo-border-strong whitespace-nowrap ${ws.color}`}
      title={`Stație: ${ws.name} Â· Skill: ${routing.skillLabel} Â· Tablet-ready âœ“`}
    >
      {ws.icon} {ws.shortName}
    </span>
  );
}

function Tooltip({ text, children }: { text: string; children: React.ReactNode }) {
  const [show, setShow] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  return (
    <div
      className="relative inline-flex"
      ref={ref}
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      {show && (
        <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-wo-surface-raised border border-wo-border-strong rounded-lg shadow-xl text-[11px] text-wo-text-primary whitespace-nowrap pointer-events-none">
          {text}
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-px w-2 h-2 bg-wo-surface-raised border-r border-b border-wo-border-strong rotate-45" />
        </div>
      )}
    </div>
  );
}

// ============================================================
// DRAFT SHAPE — Sprint #15
// ============================================================
interface DraftTemplate {
  id?: number;
  template_code: string;
  family_id: string;
  family_name: string;
  description: string;
  components: ProductTemplateComponent[];
  estimated_hours: number;
  base_labor_rate: number;
  base_margin_pct: number;
  active: boolean;
  notes: string;
}


function entityToDraft(e: ProductTemplateEntity): DraftTemplate {
  const components = parseTemplateComponentsWithLegacy(
    e.components_json,
    e.operations_json,
    e.required_materials_json
  );
  return {
    id: e.id,
    template_code: e.template_code,
    family_id: e.family_id ?? "",
    family_name: e.family_name,
    description: e.description ?? "",
    components,
    estimated_hours: e.estimated_hours ?? 0,
    base_labor_rate: e.base_labor_rate ?? 0,
    base_margin_pct: e.base_margin_pct ?? 0,
    active: e.active ?? true,
    notes: e.notes ?? "",
  };
}

function emptyDraft(): DraftTemplate {
  return {
    template_code: "",
    family_id: "",
    family_name: "",
    description: "",
    components: [],
    estimated_hours: 0,
    base_labor_rate: 0,
    base_margin_pct: 0,
    active: true,
    notes: "",
  };
}

// ============================================================
// SERIALIZATION — Sprint #15/#27 dual representation
// ============================================================
function serializeOperation(
  op: ProductTemplateOperation,
  componentId: string
): Record<string, unknown> {
  const extras = op._extras ?? {};
  const out: Record<string, unknown> = {
    ...extras,
    code: op.code,
    name: op.name,
    workcenter: op.workcenter,
    estimatedMinutes: op.estimatedMinutes,
    estimated_minutes: op.estimated_minutes ?? op.estimatedMinutes,
    sequence: op.sequence,
    component_ref: componentId,
  };
  if (op.calculation_type) out.calculation_type = op.calculation_type;
  if (op.formula_id) out.formula_id = op.formula_id;
  if (op.formula_params) out.formula_params = op.formula_params;
  if (op.requires_quote_input) out.requires_quote_input = op.requires_quote_input;
  return out;
}

function serializeMaterial(
  m: ProductTemplateMaterial,
  componentId: string
): Record<string, unknown> {
  const extras = m._extras ?? {};
  const out: Record<string, unknown> = {
    ...extras,
    materialCode: m.materialCode,
    material_code: m.material_code ?? m.materialCode,
    name: m.name,
    quantity: m.quantity,
    unit: m.unit,
    component_ref: componentId,
  };
  if (m.calculation_type) out.calculation_type = m.calculation_type;
  if (m.formula_id) out.formula_id = m.formula_id;
  if (m.formula_params) out.formula_params = m.formula_params;
  if (m.requires_quote_input) out.requires_quote_input = m.requires_quote_input;
  return out;
}

function draftToPayload(d: DraftTemplate): Partial<ProductTemplateEntity> {
  const componentsSerialized: Array<Record<string, unknown>> = d.components.map((c) => ({
    component_id: c.component_id,
    type: c.type,
    name: c.name,
    operations: c.operations.map((op) => serializeOperation(op, c.component_id)),
    materials: c.materials.map((m) => serializeMaterial(m, c.component_id)),
  }));

  const flatOps: Array<Record<string, unknown>> = [];
  const flatMats: Array<Record<string, unknown>> = [];
  d.components.forEach((c) => {
    c.operations.forEach((op) => flatOps.push(serializeOperation(op, c.component_id)));
    c.materials.forEach((m) => flatMats.push(serializeMaterial(m, c.component_id)));
  });

  return {
    template_code: d.template_code,
    family_id: d.family_id || undefined,
    family_name: d.family_name,
    description: d.description || undefined,
    components_json: JSON.stringify(componentsSerialized),
    operations_json: JSON.stringify(flatOps),
    required_materials_json: JSON.stringify(flatMats),
    estimated_hours: d.estimated_hours,
    base_labor_rate: d.base_labor_rate,
    base_margin_pct: d.base_margin_pct,
    active: d.active,
    notes: d.notes || undefined,
  };
}

// ============================================================
// VALIDATION
// ============================================================
interface ValidationRule {
  key: string;
  label: string;
  ok: boolean;
}

function computeValidation(
  draft: DraftTemplate,
  families: ProductFamily[],
  materialsByCode: Map<string, InventoryMaterialEntity>
): ValidationRule[] {
  const componentsAllTyped =
    draft.components.length > 0 &&
    draft.components.every(
      (c) =>
        c._legacy !== true &&
        (PRODUCT_COMPONENT_TYPES as string[]).includes(c.type) &&
        c.name.trim().length > 0 &&
        c.component_id.trim().length > 0
    );
  const eachHasOp =
    draft.components.length > 0 &&
    draft.components.every(
      (c) =>
        c.operations.length > 0 &&
        c.operations.every(
          (op) => op.code.trim().length > 0 && op.name.trim().length > 0
        )
    );
  const eachHasMat =
    draft.components.length > 0 &&
    draft.components.every(
      (c) =>
        c.materials.length > 0 &&
        c.materials.every(
          (m) => m.materialCode.trim().length > 0 && materialsByCode.has(m.materialCode)
        )
    );
  // Family is valid if: (a) registry loaded and family_id matches, OR (b) registry empty but family_id+family_name present from template
  const familyKnown =
    draft.family_id.trim().length > 0 &&
    (families.length === 0
      ? draft.family_name.trim().length > 0  // registry not loaded — trust template data
      : families.some((f) => f.family_id === draft.family_id));

  return [
    { key: "template_code", label: "Cod șablon completat", ok: draft.template_code.trim().length > 0 },
    { key: "family", label: "Familie produs selectată", ok: familyKnown },
    { key: "components_min_1", label: "Minim o componentă", ok: draft.components.length > 0 },
    { key: "components_typed", label: "Componente cu tip valid", ok: componentsAllTyped },
    { key: "each_component_has_operation", label: "Fiecare componentă are operații", ok: eachHasOp },
    { key: "each_component_has_material", label: "Fiecare componentă are materiale", ok: eachHasMat },
  ];
}

// ============================================================
// PREVIEW DISPLAY HELPERS (display-only; no new business semantics)
// ============================================================
function getDraftDisplayCounts(draft: DraftTemplate) {
  const totalOps = draft.components.reduce((a, c) => a + c.operations.length, 0);
  const totalMats = draft.components.reduce((a, c) => a + c.materials.length, 0);
  const totalMinutes = draft.components.reduce(
    (a, c) => a + c.operations.reduce((b, op) => b + (op.estimatedMinutes || 0), 0),
    0
  );
  const operationHours =
    totalMinutes > 0 ? `${Math.round((totalMinutes / 60) * 10) / 10}h` : "—";
  const internalCalibrationHours =
    (draft.estimated_hours ?? 0) > 0
      ? `${draft.estimated_hours}h`
      : operationHours;

  return {
    components: draft.components.length,
    operations: totalOps,
    materials: totalMats,
    internalCalibrationHours,
  };
}

// ============================================================
// VISUAL PRODUCT ILLUSTRATION — SVG totem/sign (orientative only)
// ============================================================
function ProductIllustration({ components }: { components: ProductTemplateComponent[] }) {
  const hasType = (t: ProductComponentType) => components.some((c) => c.type === t);

  if (components.length === 0) {
    return (
      <div className="text-center py-8 px-3 border border-dashed border-wo-border-strong rounded-lg bg-wo-surface-inset">
        <Package className="w-10 h-10 text-wo-text-dim mx-auto mb-2" />
        <p className="text-[11px] text-wo-text-muted font-medium leading-relaxed">
          Previzualizare indisponibilă — șablonul nu are componente definite.
        </p>
      </div>
    );
  }

  return (
    <div className="relative w-full max-w-[280px] mx-auto">
      <svg viewBox="0 0 200 300" className="w-full h-auto">
        {/* Base/ground */}
        <ellipse cx="100" cy="285" rx="70" ry="8" fill="#1E293B" opacity="0.5" />

        {/* Pole/structure */}
        <rect
          x="85" y="100" width="30" height="180"
          rx="2"
          fill={hasType("STRUCTURA") ? "#3B82F6" : "#334155"}
          opacity={hasType("STRUCTURA") ? 0.8 : 0.3}
          className="transition-all duration-500"
        />

        {/* Sign body - ACP face */}
        <rect
          x="20" y="10" width="160" height="100"
          rx="6"
          fill={hasType("FATA_ACP_ROUTATA") ? "#F59E0B" : "#334155"}
          opacity={hasType("FATA_ACP_ROUTATA") ? 0.7 : 0.2}
          className="transition-all duration-500"
        />

        {/* Diffusion layer */}
        <rect
          x="30" y="20" width="140" height="80"
          rx="4"
          fill={hasType("DIFUZIE_PLEXI") ? "#06B6D4" : "#334155"}
          opacity={hasType("DIFUZIE_PLEXI") ? 0.5 : 0.15}
          className="transition-all duration-500"
        />

        {/* LED glow */}
        {hasType("ILUMINARE") && (
          <>
            <rect x="35" y="25" width="130" height="70" rx="3" fill="#FDE047" opacity="0.15">
              <animate attributeName="opacity" values="0.1;0.2;0.1" dur="2s" repeatCount="indefinite" />
            </rect>
            {/* LED dots */}
            {[45, 70, 95, 120, 145].map((cx) => (
              <circle key={cx} cx={cx} cy="60" r="2" fill="#FDE047" opacity="0.8">
                <animate attributeName="opacity" values="0.5;1;0.5" dur="1.5s" repeatCount="indefinite" begin={`${(cx - 45) * 0.1}s`} />
              </circle>
            ))}
          </>
        )}

        {/* Relief text */}
        {hasType("RELIEF_PLEXI_10MM") && (
          <text
            x="100" y="68"
            textAnchor="middle"
            fill="#A78BFA"
            fontSize="18"
            fontWeight="bold"
            opacity="0.9"
            className="select-none"
          >
            LOGO
          </text>
        )}

        {/* Finish shine effect */}
        {hasType("FINISAJ") && (
          <rect x="20" y="10" width="160" height="100" rx="6" fill="url(#shine)" opacity="0.3">
            <animate attributeName="opacity" values="0.1;0.35;0.1" dur="3s" repeatCount="indefinite" />
          </rect>
        )}

        <defs>
          <linearGradient id="shine" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="white" stopOpacity="0" />
            <stop offset="50%" stopColor="white" stopOpacity="0.4" />
            <stop offset="100%" stopColor="white" stopOpacity="0" />
          </linearGradient>
        </defs>
      </svg>

      <p className="text-[9px] text-wo-text-dim text-center mt-2 italic">
        Stratificare orientativă (tipuri principale)
      </p>
    </div>
  );
}

// ============================================================
// PRODUCT PREVIEW PANEL — operator-facing visual summary
// ============================================================
function ProductPreviewPanel({
  draft,
  compact = false,
}: {
  draft: DraftTemplate;
  compact?: boolean;
}) {
  const hasComponents = draft.components.length > 0;

  return (
    <div
      className={
        compact
          ? "flex flex-col gap-3"
          : "bg-wo-surface-raised border border-wo-border-subtle rounded-xl p-4 flex flex-col gap-3"
      }
    >
      {!compact && (
        <div className="space-y-1">
          <h3 className="text-[11px] font-bold text-wo-text-primary uppercase tracking-wide">
            Previzualizare orientativă
          </h3>
          <p className="text-[10px] text-wo-text-muted leading-relaxed">
            Vizualizare orientativă Â· date din șablon
          </p>
          <p className="text-[9px] text-wo-text-dim italic">
            Nu reprezintă randare tehnică finală
          </p>
        </div>
      )}
      {compact && (
        <p className="text-[9px] text-wo-text-dim italic leading-relaxed">
          Vizualizare orientativă Â· nu e randare tehnică finală
        </p>
      )}

      <ProductIllustration components={draft.components} />

      {hasComponents && (
        <div className="space-y-1.5 pt-1 border-t border-wo-border-subtle">
          <p className="text-[9px] text-wo-text-dim uppercase tracking-wide font-bold">
            Etape / componente
          </p>
          <ol className="space-y-1 max-h-[200px] overflow-y-auto scrollbar-thin pr-0.5">
            {draft.components.map((c, index) => {
              const cfg = COMPONENT_TYPE_CONFIG[c.type] || COMPONENT_TYPE_CONFIG.STRUCTURA;
              const componentIcon = getBlueprintComponentIcon(c, draft.template_code, cfg.icon);
              const typeLabel = getComponentTypeDisplayLabel(
                c,
                draft.template_code,
                cfg.label
              );
              const opCount = c.operations.length;
              const matCount = c.materials.length;
              return (
                <li
                  key={c.component_id + "_" + index}
                  className={`flex items-start gap-2 rounded-lg border px-2 py-1.5 ${cfg.bgColor} ${cfg.borderColor}`}
                >
                  <span className={`mt-0.5 flex h-4 w-4 items-center justify-center shrink-0 ${cfg.color} [&>svg]:h-3.5 [&>svg]:w-3.5`}>
                    {componentIcon}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-[9px] font-bold uppercase tracking-wide text-wo-text-primary">
                      {index + 1}. {typeLabel}
                    </p>
                    <p className="text-[10px] text-wo-text-secondary truncate">
                      {formatComponentDisplayName(c.name) || "Fără denumire"}
                    </p>
                    <p className="text-[8px] text-wo-text-muted mt-0.5">
                      {opCount} op. Â· {matCount} mat.
                    </p>
                  </div>
                </li>
              );
            })}
          </ol>
        </div>
      )}
    </div>
  );
}

// ============================================================
// FORMULA / DYNAMIC LINE METADATA (read-only display)
// ============================================================
type FormulaLineLike = ProductTemplateOperation | ProductTemplateMaterial;

function hasFormulaLineMetadata(row: FormulaLineLike): boolean {
  if (row.calculation_type === "formula_based") return true;
  if (row.calculation_type && row.calculation_type !== "static") return true;
  if ((row.formula_id || "").trim().length > 0) return true;
  const params = row.formula_params;
  if (params && typeof params === "object" && Object.keys(params).length > 0) return true;
  const quoteInput = row.requires_quote_input;
  if (Array.isArray(quoteInput) && quoteInput.length > 0) return true;
  const extras = row._extras;
  if (extras && typeof extras === "object" && Object.keys(extras).length > 0) return true;
  return false;
}

function formatFormulaParamsJson(params: Record<string, unknown> | undefined): string | null {
  if (!params || typeof params !== "object" || Object.keys(params).length === 0) return null;
  try {
    return JSON.stringify(params, null, 2);
  } catch {
    return null;
  }
}

function formatExtrasJson(extras: Record<string, unknown> | undefined): string | null {
  if (!extras || typeof extras !== "object" || Object.keys(extras).length === 0) return null;
  try {
    return JSON.stringify(extras, null, 2);
  } catch {
    return null;
  }
}

function materialRegistryBadgeStatusKey(badgeKey: string): string {
  switch (badgeKey) {
    case "in-registry":
      return "configured";
    case "no-price":
      return "missing_price";
    case "needs-owner":
      return "needs_owner_review";
    case "commercial-active":
      return "active";
    case "price-inactive":
      return "unconfigured";
    case "archived":
      return "archived";
    case "owner-confirmed":
      return "owner_confirmed";
    case "review-needed":
      return "needs_review";
    case "source-missing":
      return "missing_source";
    case "source-stale":
      return "stale";
    default:
      return badgeKey;
  }
}

function MaterialRegistryStatusReadonly({
  registryRow,
  materialCode,
}: {
  registryRow: InventoryMaterialEntity | undefined;
  materialCode: string;
}) {
  if (!materialCode.trim()) return null;

  if (!registryRow) {
    return (
      <div className="mx-2 mb-1.5 px-2 py-1.5 rounded border border-red-800/30 bg-red-950/20">
        <StatusBadge
          domain="pricing"
          status="missing"
          label={getMaterialRegistryUnknownLabel()}
          className="text-[8px] uppercase"
          title="Codul nu există în registrul de materiale încărcat pe această pagină"
        />
      </div>
    );
  }

  const badges = getMaterialRegistryStatusBadges(registryRow);
  const sourceNotes = formatMaterialSourceNotes(registryRow);

  return (
    <div className="mx-2 mb-1.5 px-2 py-1.5 rounded border border-wo-border-subtle bg-wo-surface-inset">
      <div className="flex flex-wrap items-center gap-1 mb-1">
        {badges.map((b) => (
          <StatusBadge
            key={b.key}
            domain="pricing"
            status={materialRegistryBadgeStatusKey(b.key)}
            label={b.label}
            className="text-[8px] uppercase whitespace-nowrap"
            title={b.title}
          />
        ))}
      </div>
      {hasMaterialSourceNotes(registryRow) && sourceNotes ? (
        <div className="mt-1 border-t border-wo-border-subtle pt-1">
          <p className="text-[9px] text-wo-text-muted uppercase tracking-wide font-bold mb-0.5">
            Note sursă (referință, nu alias runtime)
          </p>
          <p className="text-[9px] text-wo-text-muted leading-snug whitespace-pre-wrap break-words max-h-20 overflow-y-auto scrollbar-thin">
            {sourceNotes}
          </p>
        </div>
      ) : null}
    </div>
  );
}

function FormulaLineMetadataReadonly({ row, kind }: { row: FormulaLineLike; kind: "operation" | "material" }) {
  if (!hasFormulaLineMetadata(row)) return null;

  const paramsText = formatFormulaParamsJson(row.formula_params);
  const extrasText = formatExtrasJson(row._extras);
  const quoteInputs = Array.isArray(row.requires_quote_input)
    ? row.requires_quote_input.filter((x) => String(x).trim().length > 0)
    : [];
  const isFormulaBased = row.calculation_type === "formula_based";
  const borderTone =
    kind === "operation" ? "border-cyan-800/40 bg-cyan-950/15" : "border-violet-800/40 bg-violet-950/15";

  return (
    <div className={`mt-1.5 mx-2 mb-2 px-2.5 py-2 rounded-lg border ${borderTone}`}>
      <div className="flex flex-wrap items-center gap-1.5 mb-1.5">
        <span className="px-1.5 py-0.5 text-[8px] font-bold uppercase tracking-wide rounded bg-cyan-900/40 text-cyan-300 border border-cyan-700/40">
          Dinamic
        </span>
        {(isFormulaBased || quoteInputs.length > 0) && (
          <span className="px-1.5 py-0.5 text-[8px] font-bold uppercase tracking-wide rounded bg-amber-900/30 text-amber-300 border border-amber-700/40">
            Depinde de ofertă
          </span>
        )}
        {row.calculation_type ? (
          <span className="text-[9px] text-wo-text-muted font-mono">{row.calculation_type}</span>
        ) : null}
      </div>
      {(row.formula_id || "").trim() ? (
        <p className="text-[10px] text-wo-text-secondary font-mono mb-1">
          Formula: <span className="text-cyan-300">{(row.formula_id || "").trim()}</span>
        </p>
      ) : null}
      {paramsText ? (
        <div className="mb-1">
          <p className="text-[9px] text-wo-text-muted uppercase tracking-wide font-bold mb-0.5">
            Parametri formulă
          </p>
          <pre className="text-[9px] text-wo-text-muted font-mono whitespace-pre-wrap break-all max-h-24 overflow-y-auto scrollbar-thin bg-wo-surface-inset rounded px-2 py-1 border border-wo-border-subtle">
            {paramsText}
          </pre>
        </div>
      ) : null}
      {quoteInputs.length > 0 ? (
        <p className="text-[9px] text-wo-text-muted mb-1">
          Input ofertă:{" "}
          <span className="text-amber-300/90 font-mono">{quoteInputs.join(", ")}</span>
        </p>
      ) : null}
      {extrasText ? (
        <div>
          <p className="text-[9px] text-wo-text-muted uppercase tracking-wide font-bold mb-0.5">
            Metadate păstrate din șablon
          </p>
          <pre className="text-[9px] text-wo-text-muted font-mono whitespace-pre-wrap break-all max-h-20 overflow-y-auto scrollbar-thin bg-wo-surface-inset rounded px-2 py-1 border border-wo-border-subtle">
            {extrasText}
          </pre>
        </div>
      ) : null}
    </div>
  );
}

// ============================================================
// COLLAPSIBLE COMPONENT CARD — the main redesign
// ============================================================
function CollapsibleComponentCard({
  component,
  allComponents,
  index,
  templateCode,
  selected,
  expanded,
  onSelect,
  onToggleExpand,
  onUpdate,
  onRemove,
  materials,
  materialsByCode,
  readOnly = false,
}: {
  component: ProductTemplateComponent;
  allComponents: ProductTemplateComponent[];
  index: number;
  templateCode: string;
  selected: boolean;
  expanded: boolean;
  onSelect: () => void;
  onToggleExpand: () => void;
  onUpdate: (next: ProductTemplateComponent) => void;
  onRemove: () => void;
  materials: InventoryMaterialEntity[];
  materialsByCode: Map<string, InventoryMaterialEntity>;
  readOnly?: boolean;
}) {
  const cfg = COMPONENT_TYPE_CONFIG[component.type] || COMPONENT_TYPE_CONFIG.STRUCTURA;
  const componentIcon = getBlueprintComponentIcon(component, templateCode, cfg.icon);
  const typeDisplayLabel = getComponentTypeDisplayLabel(
    component,
    templateCode,
    cfg.label
  );

  const patch = (p: Partial<ProductTemplateComponent>) => {
    const merged: ProductTemplateComponent = { ...component, ...p };
    if (merged._legacy && (p.type !== undefined || p.name !== undefined)) {
      merged._legacy = false;
    }
    onUpdate(merged);
  };

  // Operations helpers
  const addOp = () => {
    const nextSeq =
      component.operations.length > 0
        ? Math.max(...component.operations.map((o) => o.sequence)) + 1
        : 1;
    onUpdate({
      ...component,
      operations: [
        ...component.operations,
        {
          code: "",
          name: "",
          workcenter: "",
          estimatedMinutes: 30,
          sequence: nextSeq,
          component_ref: component.component_id,
        },
      ],
    });
  };
  const updateOp = (i: number, next: ProductTemplateOperation) => {
    const arr = [...component.operations];
    arr[i] = { ...next, component_ref: component.component_id };
    onUpdate({ ...component, operations: arr });
  };
  const removeOp = (i: number) => {
    onUpdate({ ...component, operations: component.operations.filter((_, idx) => idx !== i) });
  };

  // Materials helpers
  const addMat = () => {
    onUpdate({
      ...component,
      materials: [
        ...component.materials,
        { materialCode: "", name: "", quantity: 1, unit: "", component_ref: component.component_id },
      ],
    });
  };
  const selectMat = (i: number, code: string) => {
    const row = materialsByCode.get(code);
    const arr = [...component.materials];
    arr[i] = row
      ? { ...arr[i], materialCode: row.code, name: row.name, unit: row.unit, component_ref: component.component_id }
      : { ...arr[i], materialCode: code, name: "", unit: "", component_ref: component.component_id };
    onUpdate({ ...component, materials: arr });
  };
  const updateMatQty = (i: number, qty: number) => {
    const arr = [...component.materials];
    arr[i] = { ...arr[i], quantity: qty };
    onUpdate({ ...component, materials: arr });
  };
  const removeMat = (i: number) => {
    onUpdate({ ...component, materials: component.materials.filter((_, idx) => idx !== i) });
  };

  const hasWarning = component._legacy === true || component._needs_review === true;
  const displayName = formatComponentDisplayName(component.name);
  const materialsRegistryEmpty = materials.length === 0;

  return (
    <div
      data-component-index={index}
      className={`rounded-xl border transition-all duration-300 overflow-hidden ${
        hasWarning
          ? "border-amber-500/40 bg-amber-950/5"
          : selected
          ? "border-purple-500/50 bg-purple-500/[0.06] ring-1 ring-purple-500/25"
          : expanded
          ? `${cfg.borderColor} ${cfg.bgColor}`
          : "border-wo-border-subtle bg-wo-surface-raised hover:border-slate-600"
      }`}
    >
      {/* Collapsed header — always visible */}
      <div className="w-full text-left px-4 py-3 flex items-center gap-3">
        <button
          type="button"
          onClick={onSelect}
          className="flex flex-1 min-w-0 items-center gap-3 text-left"
        >
        <div className={`p-2 rounded-lg ${cfg.bgColor} ${cfg.color} shrink-0 [&>svg]:h-5 [&>svg]:w-5`}>
          {componentIcon}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-wo-text-muted">#{index + 1}</span>
            <span className="text-[11px] font-bold uppercase tracking-wide text-wo-text-primary">
              {typeDisplayLabel}
            </span>
            {hasWarning && (
              <span className="px-1.5 py-0.5 text-[9px] font-bold bg-amber-900/40 text-amber-400 border border-amber-700 rounded">
                REVIZUIRE
              </span>
            )}
          </div>
          <p className="text-[13px] font-semibold text-wo-text-primary truncate mt-0.5">
            {displayName || <span className="text-wo-text-muted italic">Fără nume</span>}
          </p>
        </div>

        {/* Summary chips */}
        <div className="flex items-center gap-1.5 shrink-0">
          <span className="px-2 py-1 bg-blue-500/10 text-blue-400 rounded-lg text-[10px] font-semibold">
            {component.operations.length} op.
          </span>
          <span className="px-2 py-1 bg-emerald-500/10 text-emerald-400 rounded-lg text-[10px] font-semibold">
            {component.materials.length} mat.
          </span>
        </div>
        </button>
        {!readOnly ? (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onToggleExpand();
            }}
            aria-label={expanded ? "ÃŽnchide editarea componentei" : "Deschide editarea componentei"}
            aria-expanded={expanded}
            className={`w-8 h-8 rounded-lg border flex items-center justify-center shrink-0 transition-colors ${
              expanded
                ? "bg-purple-500/15 border-purple-500/40 text-purple-300"
                : "bg-wo-surface-inset border-wo-border-strong text-wo-text-muted hover:text-wo-text-secondary hover:border-slate-600"
            }`}
          >
            <ChevronDown
              className={`w-4 h-4 transition-transform ${expanded ? "rotate-180" : ""}`}
            />
          </button>
        ) : null}
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-wo-border-subtle">
          {isVolumetricLettersTemplate(templateCode) ? (
            <>
              <VolumetricComponentProductionHint componentId={component.component_id} />
              <VolumetricCantProductionModulesPanel component={component} components={allComponents} />
            </>
          ) : null}
          {/* Component identity fields */}
          <div className="grid grid-cols-3 gap-3 pt-3">
            <div>
              <label className="flex items-center gap-1 text-[10px] text-wo-text-muted uppercase tracking-wide mb-1">
                ID Componentă
                <Tooltip text="Identificator unic intern (ex: comp_1, cadru_principal)">
                  <Info className="w-3 h-3 text-wo-text-dim cursor-help" />
                </Tooltip>
              </label>
              <input
                type="text"
                value={component.component_id}
                onChange={(e) => patch({ component_id: e.target.value.trim() })}
                placeholder="comp_1"
                className="w-full bg-wo-surface-inset border border-wo-border-strong rounded-lg px-3 py-2 text-[12px] text-wo-text-primary font-mono outline-none focus:border-purple-500/50"
              />
            </div>
            <div>
              <label className="flex items-center gap-1 text-[10px] text-wo-text-muted uppercase tracking-wide mb-1">
                Tip Componentă
                <Tooltip text="Categoria componentei — determină fluxul de producție">
                  <Info className="w-3 h-3 text-wo-text-dim cursor-help" />
                </Tooltip>
              </label>
              <select
                value={component.type}
                onChange={(e) => patch({ type: e.target.value as ProductComponentType })}
                className="w-full bg-wo-surface-inset border border-wo-border-strong rounded-lg px-3 py-2 text-[12px] text-wo-text-primary outline-none focus:border-purple-500/50"
              >
                {PRODUCT_COMPONENT_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {COMPONENT_TYPE_CONFIG[t].emoji}{" "}
                    {getComponentTypeSelectOptionLabel(
                      t,
                      templateCode,
                      COMPONENT_TYPE_CONFIG[t].label
                    )}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="flex items-center gap-1 text-[10px] text-wo-text-muted uppercase tracking-wide mb-1">
                Nume Componentă
                <Tooltip text="Denumirea descriptivă (ex: Cadru metalic sudat 2x1m)">
                  <Info className="w-3 h-3 text-wo-text-dim cursor-help" />
                </Tooltip>
              </label>
              <input
                type="text"
                value={component.name}
                onChange={(e) => patch({ name: e.target.value })}
                placeholder="ex: Cadru metalic sudat"
                className="w-full bg-wo-surface-inset border border-wo-border-strong rounded-lg px-3 py-2 text-[12px] text-wo-text-primary outline-none focus:border-purple-500/50"
              />
            </div>
          </div>

          {/* Description hint */}
          <div className={`flex items-start gap-2 px-3 py-2 rounded-lg ${cfg.bgColor} border ${cfg.borderColor}`}>
            <Info className={`w-3.5 h-3.5 ${cfg.color} mt-0.5 shrink-0`} />
            <p className="text-[11px] text-wo-text-secondary">{cfg.description}</p>
          </div>

          {hasWarning && (
            <div className="flex items-start gap-2 px-3 py-2 bg-amber-900/15 border border-amber-700/30 rounded-lg">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400 mt-0.5 shrink-0" />
              <p className="text-[11px] text-amber-300">
                {component._legacy
                  ? "Componentă migrată din forma veche. Confirmă tipul și salvează."
                  : "Operații/materiale vechi atașate aici. Revizuiește și redistribuie dacă e cazul."}
              </p>
            </div>
          )}

          <div className="px-3 py-2.5 rounded-lg border border-wo-border-strong bg-wo-surface-inset space-y-1.5">
            <p className="text-[10px] text-wo-text-muted leading-relaxed">
              Câmpurile dinamice sunt afișate informativ. Editarea formulelor se va trata într-un pas separat.
            </p>
            <p className="text-[10px] text-wo-text-secondary leading-relaxed">
              Parametrii configurabili ai produsului — text, font, înălțime, adâncime, tip iluminare, RAL,
              montaj — nu se editează aici ca reguli de șablon. Ei trebuie colectați în Intake / Dossier /
              Ofertă și folosiți de formulele dinamice.
            </p>
            <p className="text-[10px] text-wo-text-muted italic leading-relaxed">
              Șablonul definește structura produsului; valorile concrete vin din cererea clientului și
              ofertare.
            </p>
          </div>

          {/* OPERATIONS */}
          <div className="bg-wo-surface-inset border border-wo-border-subtle rounded-xl p-3">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Cog className="w-4 h-4 text-blue-400" />
                <span className="text-[12px] font-bold text-wo-text-primary">
                  Operații de Producție
                </span>
                <span className="text-[10px] text-blue-400 bg-blue-500/10 px-1.5 py-0.5 rounded-full font-bold">
                  {component.operations.length}
                </span>
              </div>
              <button
                onClick={addOp}
                className="flex items-center gap-1 px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-[10px] font-bold transition-colors"
              >
                <Plus className="w-3 h-3" /> Adaugă Operație
              </button>
            </div>

            {component.operations.length === 0 ? (
              <div className="flex items-center gap-2 px-3 py-3 bg-red-900/10 border border-red-800/20 rounded-lg">
                <AlertTriangle className="w-4 h-4 text-red-400" />
                <p className="text-[11px] text-red-300">Nicio operație definită — necesară minim 1 pentru salvare.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {component.operations.map((op, i) => {
                  const invalid = op.code.trim().length === 0 || op.name.trim().length === 0;
                  const dynamicMeta = hasFormulaLineMetadata(op);
                  return (
                    <div
                      key={i}
                      className={`rounded-lg transition-all ${
                        invalid
                          ? "bg-red-900/10 border border-red-800/20"
                          : dynamicMeta
                            ? "bg-wo-surface-raised border border-cyan-800/30"
                            : "bg-wo-surface-raised border border-wo-border-subtle"
                      }`}
                    >
                      <div className="flex items-center gap-2 p-2">
                        <GripVertical className="w-3 h-3 text-wo-text-dim shrink-0" />
                        <span className="text-[10px] text-wo-text-muted font-mono w-6 text-center shrink-0">
                          {op.sequence}
                        </span>
                        {dynamicMeta ? (
                          <span
                            className="shrink-0 px-1 py-0.5 text-[8px] font-bold uppercase rounded bg-cyan-900/40 text-cyan-300 border border-cyan-700/40"
                            title="Linie dinamică — metadate formule mai jos"
                          >
                            Dinamic
                          </span>
                        ) : null}
                        <input
                          type="text"
                          value={op.code}
                          onChange={(e) => updateOp(i, { ...op, code: e.target.value })}
                          placeholder="CNC_CUT"
                          className="flex-1 bg-transparent border-b border-wo-border-strong px-1 py-1 text-[11px] text-wo-text-primary font-mono outline-none focus:border-blue-500/50"
                        />
                        <input
                          type="text"
                          value={op.name}
                          onChange={(e) => updateOp(i, { ...op, name: e.target.value })}
                          placeholder="Debitare CNC"
                          className="flex-[2] bg-transparent border-b border-wo-border-strong px-1 py-1 text-[11px] text-wo-text-primary outline-none focus:border-blue-500/50"
                        />
                        <Tooltip text="Centrul de lucru (ex: CNC, Sudură, Vopsitorie)">
                          <input
                            type="text"
                            value={op.workcenter}
                            onChange={(e) => updateOp(i, { ...op, workcenter: e.target.value })}
                            placeholder="CNC"
                            className="w-20 bg-transparent border-b border-wo-border-strong px-1 py-1 text-[11px] text-wo-text-primary font-mono outline-none focus:border-blue-500/50"
                          />
                        </Tooltip>
                        <OperationRoutingBadge opCode={op.code} />
                        <Tooltip text={CALIBRATION_DURATION_TOOLTIP}>
                          <div className="flex flex-col items-end w-24 shrink-0">
                            <span className="text-[8px] text-wo-text-dim uppercase tracking-wide">
                              calibrare
                            </span>
                            <div className="flex items-center gap-1 w-full">
                              <input
                                type="number"
                                min="0"
                                value={op.estimatedMinutes}
                                onChange={(e) =>
                                  updateOp(i, {
                                    ...op,
                                    estimatedMinutes: Number(e.target.value) || 0,
                                  })
                                }
                                className="w-full bg-transparent border-b border-wo-border-strong px-1 py-1 text-[11px] text-wo-text-primary font-mono text-right outline-none focus:border-blue-500/50"
                              />
                              <span className="text-[9px] text-wo-text-dim">min</span>
                            </div>
                            <span className="text-[8px] text-wo-text-dim mt-0.5 truncate max-w-full">
                              {formatOperationCalibrationLabel(op)}
                            </span>
                          </div>
                        </Tooltip>
                        <button
                          onClick={() => removeOp(i)}
                          className="p-1 text-wo-text-dim hover:text-red-400 transition-colors shrink-0"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                      <FormulaLineMetadataReadonly row={op} kind="operation" />
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* MATERIALS */}
          <div className="bg-wo-surface-inset border border-wo-border-subtle rounded-xl p-3">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Box className="w-4 h-4 text-emerald-400" />
                <span className="text-[12px] font-bold text-wo-text-primary">
                  Materiale Necesare
                </span>
                <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded-full font-bold">
                  {component.materials.length}
                </span>
              </div>
              <button
                onClick={addMat}
                disabled={materialsRegistryEmpty}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] font-bold transition-colors ${
                  materialsRegistryEmpty
                    ? "bg-slate-700/60 text-wo-text-muted cursor-not-allowed"
                    : "bg-emerald-600 hover:bg-emerald-500 text-white"
                }`}
              >
                <Plus className="w-3 h-3" /> Adaugă Material
              </button>
            </div>

            {materialsRegistryEmpty && (
              <div className="flex items-center gap-2 px-3 py-3 bg-amber-900/10 border border-amber-800/20 rounded-lg">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <p className="text-[11px] text-amber-300">
                  Registrul de materiale nu este încărcat. Materialele din șablon sunt afișate direct.{" "}
                  <Link to="/inventory" className="underline hover:text-amber-200">Inventar</Link>
                </p>
              </div>
            )}
            {component.materials.length === 0 ? (
              <div className="flex items-center gap-2 px-3 py-3 bg-red-900/10 border border-red-800/20 rounded-lg">
                <AlertTriangle className="w-4 h-4 text-red-400" />
                <p className="text-[11px] text-red-300">Niciun material — necesar minim 1 din registru.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {component.materials.map((m, i) => {
                  const row = materialsByCode.get(m.materialCode);
                  const invalid = !row;
                  const dynamicMeta = hasFormulaLineMetadata(m);
                  return (
                    <div
                      key={i}
                      className={`rounded-lg transition-all ${
                        invalid
                          ? "bg-red-900/10 border border-red-800/20"
                          : dynamicMeta
                            ? "bg-wo-surface-raised border border-violet-800/30"
                            : "bg-wo-surface-raised border border-wo-border-subtle"
                      }`}
                    >
                      <div className="flex items-center gap-2 p-2">
                        {dynamicMeta ? (
                          <span
                            className="shrink-0 px-1 py-0.5 text-[8px] font-bold uppercase rounded bg-violet-900/40 text-violet-300 border border-violet-700/40"
                            title="Linie dinamică — metadate formule mai jos"
                          >
                            Dinamic
                          </span>
                        ) : null}
                        <MaterialRegistryPicker
                          materials={materials}
                          value={m.materialCode}
                          onValueChange={(code) => selectMat(i, code)}
                          componentId={component.component_id}
                          templateCode={templateCode}
                          unknownCode={m.materialCode}
                          disabled={materialsRegistryEmpty}
                          className="flex-[2] min-w-[140px]"
                        />
                        <span
                          className="flex-[2] text-[11px] text-wo-text-muted truncate hidden sm:block"
                          title={row ? row.name : m.name}
                        >
                          {row
                            ? formatMaterialRegistryShortName(row.name)
                            : m.name
                              ? formatMaterialRegistryShortName(m.name)
                              : "—"}
                        </span>
                        <Tooltip
                          text={
                            dynamicMeta
                              ? "Cantitate calculată la ofertare din formulă și unități (mp, ml, buc)"
                              : "Cantitate statică de referință per unitate de produs"
                          }
                        >
                          <input
                            type="number"
                            step="0.01"
                            min="0"
                            value={m.quantity}
                            onChange={(e) => updateMatQty(i, Number(e.target.value) || 0)}
                            className="w-16 bg-transparent border-b border-wo-border-strong px-1 py-1 text-[11px] text-wo-text-primary font-mono text-right outline-none focus:border-emerald-500/50"
                          />
                        </Tooltip>
                        <span className="text-[10px] text-wo-text-muted font-mono w-10">
                          {row ? row.unit : m.unit || "—"}
                        </span>
                        <button
                          onClick={() => removeMat(i)}
                          className="p-1 text-wo-text-dim hover:text-red-400 transition-colors shrink-0"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                      <MaterialRegistryStatusReadonly
                        registryRow={row}
                        materialCode={m.materialCode}
                      />
                      <FormulaLineMetadataReadonly row={m} kind="material" />
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Delete component */}
          <div className="flex justify-end">
            <button
              onClick={onRemove}
              className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] text-red-400 hover:text-red-300 hover:bg-red-900/20 rounded-lg transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" /> Șterge Componenta
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================
// EDITOR PANEL — Redesigned with visual components
// ============================================================
const SHARED_VOLUMETRIC_EDITOR_MODULES: Record<string, string> = {
  volumetric_face: "TPL-VOLUMETRIC-FACE_v1",
  volumetric_back: "TPL-VOLUMETRIC-BACK_v1",
  volumetric_return_side: "TPL-VOLUM-ALUMINIU_v1",
  volumetric_surface_finish: "TPL-VOLUMETRIC-FINISH_v1",
  volumetric_mounting_interface: "TPL-METAL-PREMOUNT-STRUCTURE_v1",
  volumetric_lighting: "TPL-VOLUMETRIC-LED_v1",
};

type OwnershipFieldAudit = {
  key: string;
  productTruthPath: string;
  sourceState: string;
  warning: string;
};

type SharedComponentOwnershipAudit = {
  componentKey: string;
  label: string;
  primaryTemplateCode: string;
  separateCalculationStatus: "read_only_contract" | "partial_ready" | "calculation_blocked";
  separateCalculationLabel: string;
  shouldOwn: string[];
  gaps: string[];
  fields: OwnershipFieldAudit[];
  note: string;
};

type ReturnCantSourcePathAudit = {
  key:
    | "material_profile"
    | "return_depth_mm"
    | "return_finish_type"
    | "letter_perimeter_m"
    | "operation_modelare_cant"
    | "operation_bonding"
    | "finish_source"
    | "resources_tools"
    | "separate_calculation_readiness";
  label: string;
  canonicalTarget: string;
  currentSource: string;
  currentSourcePath: string;
  sourceStatus:
    | "component-owned template only"
    | "form system only"
    | "parent aggregate only"
    | "separate finish component"
    | "operation registry missing"
    | "component-owned source missing"
    | "blocked";
  blocker: string;
  note: string;
};

type ReturnCantTruthContainerFieldAudit = {
  key:
    | "instance_id"
    | "component_template_code"
    | "component_id"
    | "layer_group_ids"
    | "source_face_component_id"
    | "source_face_perimeter_ref"
    | "perimeter_source"
    | "confirmed_perimeter_m"
    | "material_profile"
    | "depth_mm"
    | "finish_type"
    | "color_source"
    | "operation_modelare_cant_ref"
    | "operation_bonding_ref"
    | "resource_requirements_ref"
    | "confirmation_state"
    | "blockers";
  label: string;
  sourceType:
    | "component truth"
    | "Form System capture"
    | "root geometry context"
    | "parent aggregate support"
    | "legacy alias"
    | "component template / registry"
    | "missing";
  currentSource: string;
  targetPath: string;
  note: string;
};

type ProductCompositionReadModelEntry = {
  key: string;
  label: string;
  componentType: "structural" | "functional";
  componentTemplateCode: string;
  componentId: string;
  requiredInLetters: boolean;
  currentWiring: "wired" | "partial" | "missing";
  currentSourceType:
    | "module produs"
    | "component template"
    | "parent aggregate"
    | "dossier"
    | "shared contract"
    | "missing";
  productTruthTarget: string;
  formSystemFields: string[];
  geometryDependency: string;
  materialSource: string;
  operationSource: string;
  calculationReadiness: "ready" | "partial" | "blocked";
  blockers: string[];
  recommendation: string;
};

const SHARED_COMPONENT_OWNERSHIP_AUDIT: Record<string, SharedComponentOwnershipAudit> = {
  volumetric_face: {
    componentKey: "volumetric_face",
    label: "Face / front",
    primaryTemplateCode: "TPL-VOLUMETRIC-FACE_v1",
    separateCalculationStatus: "partial_ready",
    separateCalculationLabel: "partial_ready",
    shouldOwn: ["selected_layer_refs", "material", "thickness_mm", "finish_target"],
    gaps: ["material still falls back in product-root flow", "selected layer ownership still needs explicit confirmation"],
    fields: [
      {
        key: "selected_layer_refs",
        productTruthPath: "components.face.selected_layer_refs",
        sourceState: "product context only",
        warning: "source not wired yet for component-owned confirmation",
      },
      {
        key: "material",
        productTruthPath: "components.face.material",
        sourceState: "component-owned pending",
        warning: "component-owned source missing confirmation",
      },
      {
        key: "finish_target",
        productTruthPath: "components.finish.target",
        sourceState: "component-owned pending",
        warning: "shared finish target still crosses product/root context",
      },
    ],
    note: "Face truth exists directionally, but Product Template still carries fallback/hydrated context for material and finish alignment.",
  },
  volumetric_back: {
    componentKey: "volumetric_back",
    label: "Back / spate",
    primaryTemplateCode: "TPL-VOLUMETRIC-BACK_v1",
    separateCalculationStatus: "calculation_blocked",
    separateCalculationLabel: "calculation blocked",
    shouldOwn: ["backing_mode", "material", "bevel_enabled"],
    gaps: ["back material remains too implicit", "back confirmation path is not explicit enough"],
    fields: [
      {
        key: "backing_mode",
        productTruthPath: "components.back.backing_mode",
        sourceState: "component-owned fallback",
        warning: "hydrated default is not final truth",
      },
      {
        key: "material",
        productTruthPath: "components.back.material",
        sourceState: "component-owned pending",
        warning: "source not wired yet for explicit back material ownership",
      },
    ],
    note: "Back remains component-shaped, but not ready for honest separate calculation without explicit owner-confirmed material truth.",
  },
  volumetric_return_side: {
    componentKey: "volumetric_return_side",
    label: "CANT / VOLUM DIN ALUMINIU",
    primaryTemplateCode: "TPL-VOLUM-ALUMINIU_v1",
    separateCalculationStatus: "partial_ready",
    separateCalculationLabel:
      "contract preview ready · confirmed perimeter required · publication blocked",
    shouldOwn: [
      "return_depth_mm",
      "perimeter_source",
      "confirmed_perimeter_m",
      "material_profile",
      "finish_type",
      "color_target",
      "layer_group_ids",
      "confirmation_state",
    ],
    gaps: [
      "publication/activation remain blocked (required inactive child)",
      "operator must confirm perimeter — evidence-only quote_geometry cannot drive separate calc",
      "dual id documented: BOM comp_volum_aluminiu_module vs pricing stub comp_lateral_litere",
    ],
    fields: [
      {
        key: "return_depth_mm",
        productTruthPath: "components.return_cant.instances[].material_profile.width_mm",
        sourceState: "component-owned gate 30/60/80/100",
        warning: "depth must match material profile gate",
      },
      {
        key: "perimeter_source",
        productTruthPath: "components.return_cant.instances[].geometry.perimeter_source",
        sourceState: "component-owned provenance",
        warning: "evidence_only cannot confirm; operator_confirmed required for calc",
      },
      {
        key: "confirmed_perimeter_m",
        productTruthPath: "components.return_cant.instances[].geometry.confirmed_perimeter_m",
        sourceState: "operator confirm → product truth",
        warning: "required input for separate-calculation-preview",
      },
      {
        key: "material_profile",
        productTruthPath: "components.return_cant.instances[].material_profile",
        sourceState: "component-owned from return_depth_mm",
        warning: "width_mm maps to MAT-PROFIL-LATERAL-LITERE-*",
      },
      {
        key: "finish_type",
        productTruthPath: "components.return_cant.instances[].finish_variant",
        sourceState: "component-owned (stock / Oracal / RAL)",
        warning: "finish + pricing_keys emitted by return_cant bridge",
      },
      {
        key: "color_target",
        productTruthPath: "components.return_cant.instances[].finish_variant",
        sourceState: "component-owned via finish_variant",
        warning: "RAL / Oracal codes live on finish_variant + pricing_keys",
      },
      {
        key: "layer_group_ids",
        productTruthPath: "components.return_cant.instances[].layer_group_ids",
        sourceState: "component-owned from confirmed layer roles",
        warning: "required for confirmation; missing ids keep state blocked",
      },
      {
        key: "confirmation_state",
        productTruthPath: "components.return_cant.instances[].confirmation_state",
        sourceState: "component-owned (requires confirmed_perimeter_m)",
        warning: "evidence-only perimeter cannot set confirmed",
      },
    ],
    note:
      "Separate-calc preview: POST .../TPL-VOLUM-ALUMINIU_v1/separate-calculation-preview. Publication/activation stay blocked until dedicated owner GO.",
  },
  volumetric_surface_finish: {
    componentKey: "volumetric_surface_finish",
    label: "Finish / artwork",
    primaryTemplateCode: "TPL-VOLUMETRIC-FINISH_v1",
    separateCalculationStatus: "calculation_blocked",
    separateCalculationLabel: "calculation blocked",
    shouldOwn: ["finish_target", "print_required", "lamination_required"],
    gaps: ["finish family boundaries remain mixed", "artwork-derived consequences still need a cleaner owner split"],
    fields: [
      {
        key: "finish_target",
        productTruthPath: "components.finish.target",
        sourceState: "component-owned pending",
        warning: "source not wired yet as one canonical finish path",
      },
      {
        key: "print_required",
        productTruthPath: "components.finish.print_required",
        sourceState: "component-owned pending",
        warning: "derived consequence still depends on artwork decisions",
      },
    ],
    note: "Finish is a real component boundary, but the current system should keep it read-only until the field ownership split is cleaner.",
  },
  volumetric_mounting_interface: {
    componentKey: "volumetric_mounting_interface",
    label: "Mounting / support",
    primaryTemplateCode: "TPL-METAL-PREMOUNT-STRUCTURE_v1",
    separateCalculationStatus: "calculation_blocked",
    separateCalculationLabel: "calculation blocked",
    shouldOwn: ["mounting_system", "support_required"],
    gaps: ["support_required is still missing as first-class component truth", "metal_support_required remains downstream-only"],
    fields: [
      {
        key: "mounting_system",
        productTruthPath: "components.mounting.system",
        sourceState: "component-owned fallback",
        warning: "hydrated/default mounting system is not final component truth",
      },
      {
        key: "support_required",
        productTruthPath: "components.support.support_required",
        sourceState: "missing component truth",
        warning: "component-owned source missing",
      },
    ],
    note: "Mounting stays component-owned directionally, but support truth is still downstream-derived instead of first-class component input.",
  },
  volumetric_lighting: {
    componentKey: "volumetric_lighting",
    label: "Lighting",
    primaryTemplateCode: "TPL-VOLUMETRIC-LED_v1",
    separateCalculationStatus: "read_only_contract",
    separateCalculationLabel: "read-only contract",
    shouldOwn: ["illumination_type", "led_module_count", "strategy_profile"],
    gaps: ["strategy exists, but primary lighting truth is still partial", "operator-confirmed lighting state is not component-complete"],
    fields: [
      {
        key: "illumination_type",
        productTruthPath: "components.lighting.illumination_type",
        sourceState: "component-owned fallback",
        warning: "current lighting mode is still hydrated or defaulted",
      },
      {
        key: "led_module_count",
        productTruthPath: "components.lighting.led_module_count",
        sourceState: "component-owned pending",
        warning: "source not wired yet for operator-confirmed LED count",
      },
      {
        key: "strategy_profile",
        productTruthPath: "components.lighting.strategy_profile",
        sourceState: "product context only",
        warning: "strategy/profile is not the primary shared component truth",
      },
    ],
    note: "Lighting is valid as a shared component, but separate calculation must remain read-only until owner-confirmed lighting truth is explicit.",
  },
};

const SHARED_COMPONENT_OWNERSHIP_ORDER = [
  "volumetric_face",
  "volumetric_back",
  "volumetric_return_side",
  "volumetric_surface_finish",
  "volumetric_mounting_interface",
  "volumetric_lighting",
] as const;

function ownershipStatusClass(status: SharedComponentOwnershipAudit["separateCalculationStatus"]) {
  switch (status) {
    case "partial_ready":
      return "border-amber-700/40 bg-amber-900/20 text-amber-300";
    case "read_only_contract":
      return "border-cyan-700/40 bg-cyan-950/30 text-cyan-200";
    default:
      return "border-red-700/40 bg-red-900/20 text-red-300";
  }
}

const RETURN_CANT_SEPARATE_SOURCE_PATHS: ReturnCantSourcePathAudit[] = [
  {
    key: "material_profile",
    label: "material cant / profil aluminiu",
    canonicalTarget: "components.return_cant.material_profile",
    currentSource: "Module produs catalog gate",
    currentSourcePath: "TPL-VOLUM-ALUMINIU_v1.required_materials_json[*] gate return_depth_mm",
    sourceStatus: "component-owned source missing",
    blocker: "RETURN_CANT_MATERIAL_MISSING",
    note: "Profiles 30/60/80/100 mm exist in the Module produs catalog, but no confirmed module-owned Product Truth field exists yet.",
  },
  {
    key: "return_depth_mm",
    label: "return_depth_mm",
    canonicalTarget: "components.return_cant.depth_mm",
    currentSource: "Form System + legacy Product Truth alias",
    currentSourcePath: "finish_setup.return_depth_mm; legacy components.return.depth_mm / components.returnCant.depthMm",
    sourceStatus: "form system only",
    blocker: "RETURN_CANT_HEIGHT_CONFIRMATION_REQUIRED",
    note: "Depth exists today as hydrated or fallback review input, not as confirmed component-owned truth.",
  },
  {
    key: "return_finish_type",
    label: "return_finish_type",
    canonicalTarget: "components.return_cant.finish_type",
    currentSource: "Form System + legacy Product Truth alias",
    currentSourcePath: "finish_setup.return_finish_type; legacy components.returnCant.finishType",
    sourceStatus: "form system only",
    blocker: "RETURN_CANT_FINISH_MISSING",
    note: "Finish intent exists in review payload, but the canonical component-owned path is still not confirmed.",
  },
  {
    key: "letter_perimeter_m",
    label: "letter_perimeter_m / perimeter dependency",
    canonicalTarget: "components.return_cant.perimeter_source -> components.face.confirmed_perimeter",
    currentSource: "Root geometry dependency",
    currentSourcePath: "quote_geometry.letter_perimeter_m; future dependency target components.face.confirmed_perimeter",
    sourceStatus: "parent aggregate only",
    blocker: "RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED",
    note: "Perimeter still comes from root geometry context, not from an explicit confirmed dependency owned on the component boundary.",
  },
  {
    key: "operation_modelare_cant",
    label: "operation: modelare_cant",
    canonicalTarget: "TPL-VOLUM-ALUMINIU_v1.operations_json[RETURN_PROFILE_MACHINE_FORMING]",
    currentSource: "Module produs operation",
    currentSourcePath: "Module produs operation + aggregate outputs operations.linked_module[TPL-VOLUM-ALUMINIU_v1]",
    sourceStatus: "component-owned template only",
    blocker: "RETURN_CANT_DEPTH_MISSING",
    note: "The operation exists on the Module produs and registry, but separate calculation is still blocked until module-owned inputs are explicit.",
  },
  {
    key: "operation_bonding",
    label: "operation: bonding / lipire cant",
    canonicalTarget: "TPL-VOLUM-ALUMINIU_v1.operations_json[RETURN_PROFILE_FACE_BONDING]",
    currentSource: "Module produs operation",
    currentSourcePath: "Module produs operation + aggregate outputs operations.linked_module[TPL-VOLUM-ALUMINIU_v1]",
    sourceStatus: "component-owned template only",
    blocker: "RETURN_CANT_MATERIAL_MISSING",
    note: "Bonding is already modeled as a Module produs operation, but it still depends on missing material/profile truth and perimeter dependency confirmation.",
  },
  {
    key: "finish_source",
    label: "finish source",
    canonicalTarget: "components.return_cant.finish_type + components.return_cant.color_target.*",
    currentSource: "Form System + separate finish component",
    currentSourcePath: "finish_setup.return_finish_type / return_oracal_code + TPL-VOLUMETRIC-FINISH_v1 boundary",
    sourceStatus: "separate finish component",
    blocker: "RETURN_CANT_FINISH_MISSING",
    note: "Cant finish still crosses review setup and the separate finish component boundary, so it is not yet clean component-owned truth.",
  },
  {
    key: "resources_tools",
    label: "resources / tools",
    canonicalTarget: "operation_resource_requirements + Module produs workcenters",
    currentSource: "Workcenter hints only",
    currentSourcePath: "WC_FORMING, WC_ASSEMBLY, WC_PAINT; operation_resource_requirements not surfaced in this panel",
    sourceStatus: "operation registry missing",
    blocker: "RETURN_CANT_OPERATION_RESOURCE_MAPPING_MISSING",
    note: "Workcenters are present on Module produs operations, but explicit machine/resource authorization is still an operational registry concern, not a module-owned truth field.",
  },
  {
    key: "separate_calculation_readiness",
    label: "separate calculation readiness",
    canonicalTarget: "component-owned truth + confirmed dependency + explicit confirmation",
    currentSource: "Read-only ownership audit",
    currentSourcePath: "Product System ownership panel + return_cant readonly mapper",
    sourceStatus: "blocked",
    blocker: "RETURN_CANT_MATERIAL_MISSING + RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED + RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED",
    note: "What we can calculate today is diagnostic only. Separate calculation remains blocked until the missing component-owned fields move out of parent/root context.",
  },
];

const RETURN_CANT_TRUTH_CONTAINER_FIELDS: ReturnCantTruthContainerFieldAudit[] = [
  {
    key: "instance_id",
    label: "instance_id",
    sourceType: "missing",
    currentSource: "not stabilized; readonly rows still keyed by group/artwork source rows",
    targetPath: "components.return_cant.instances[].instance_id",
    note: "Container target is canonical, but stable instance ids are not yet first-class runtime truth.",
  },
  {
    key: "component_template_code",
    label: displayModuleTemplateWireLabel("component_template_code"),
    sourceType: "component template / registry",
    currentSource: "TPL-VOLUM-ALUMINIU_v1",
    targetPath: "components.return_cant.instances[].component_template_code",
    note: "The structural boundary is already real at the Module produs (child Product Template) level.",
  },
  {
    key: "component_id",
    label: "component_id",
    sourceType: "component template / registry",
    currentSource: "comp_lateral_litere",
    targetPath: "components.return_cant.instances[].component_id",
    note: "The structural component id is stable in seed, dossier, and ProductAggregate mapping.",
  },
  {
    key: "layer_group_ids",
    label: "layer_group_ids",
    sourceType: "missing",
    currentSource: "selected_layer_refs and layer confirmations exist, but are not mapped as component truth",
    targetPath: "components.return_cant.instances[].layer_group_ids",
    note: "Still blocked until layer-group selection is component-scoped.",
  },
  {
    key: "source_face_component_id",
    label: "source_face_component_id",
    sourceType: "parent aggregate support",
    currentSource: "implied by comp_face_litere in composition/read-model",
    targetPath: "components.return_cant.instances[].source_face_component_id",
    note: "The dependency owner exists conceptually, but is not yet written as explicit instance truth.",
  },
  {
    key: "source_face_perimeter_ref",
    label: "source_face_perimeter_ref",
    sourceType: "missing",
    currentSource: "components.face.confirmed_perimeter is target language, not yet explicit reference wiring",
    targetPath: "components.return_cant.instances[].source_face_perimeter_ref",
    note: "Return/cant must reference face perimeter, not invent its own perimeter source.",
  },
  {
    key: "perimeter_source",
    label: "perimeter_source",
    sourceType: "root geometry context",
    currentSource: "quote_geometry.letter_perimeter_m",
    targetPath: "components.return_cant.instances[].perimeter_source",
    note: "Current root geometry evidence is context only; dependency remains blocked until face-confirmed perimeter is explicit.",
  },
  {
    key: "confirmed_perimeter_m",
    label: "confirmed_perimeter_m",
    sourceType: "missing",
    currentSource: "letter_perimeter_m exists, but not as component-owned confirmed_perimeter_m for return_cant",
    targetPath: "components.return_cant.instances[].confirmed_perimeter_m",
    note: "This must come from the face dependency, not from aggregate hydration.",
  },
  {
    key: "material_profile",
    label: "material_profile",
    sourceType: "component template / registry",
    currentSource: "profile width/material gates in TPL-VOLUM-ALUMINIU_v1",
    targetPath: "components.return_cant.instances[].material_profile",
    note: "The material family exists on the Module produs (child Product Template), but the selected truth field is still missing.",
  },
  {
    key: "depth_mm",
    label: "depth_mm",
    sourceType: "Form System capture",
    currentSource: "finish_setup.return_depth_mm",
    targetPath: "components.return_cant.instances[].depth_mm",
    note: "Current depth is still capture/hydration, not confirmed component truth.",
  },
  {
    key: "finish_type",
    label: "finish_type",
    sourceType: "Form System capture",
    currentSource: "finish_setup.return_finish_type",
    targetPath: "components.return_cant.instances[].finish_type",
    note: "Current finish token is still capture/hydration, not a completed component-owned field.",
  },
  {
    key: "color_source",
    label: "color_source",
    sourceType: "Form System capture",
    currentSource: "return_oracal_code / finish_setup + reusable finish interpretation",
    targetPath: "components.return_cant.instances[].color_source",
    note: "Color remains coupled to finish capture and catalog interpretation.",
  },
  {
    key: "operation_modelare_cant_ref",
    label: "operation_modelare_cant_ref",
    sourceType: "component template / registry",
    currentSource: "RETURN_PROFILE_MACHINE_FORMING / modelare_cant",
    targetPath: "components.return_cant.instances[].operation_modelare_cant_ref",
    note: "Operation exists already; truth inputs are what remain incomplete.",
  },
  {
    key: "operation_bonding_ref",
    label: "operation_bonding_ref",
    sourceType: "component template / registry",
    currentSource: "RETURN_PROFILE_FACE_BONDING",
    targetPath: "components.return_cant.instances[].operation_bonding_ref",
    note: "Bonding reference exists as operation identity, not yet as instance-bound truth.",
  },
  {
    key: "resource_requirements_ref",
    label: "resource_requirements_ref",
    sourceType: "parent aggregate support",
    currentSource: "operation_resource_requirements remains external operational registry boundary",
    targetPath: "components.return_cant.instances[].resource_requirements_ref",
    note: "Read-only only; do not treat workcenter hints as component truth.",
  },
  {
    key: "confirmation_state",
    label: "confirmation_state",
    sourceType: "missing",
    currentSource: "workflow/global confirmations only",
    targetPath: "components.return_cant.instances[].confirmation_state",
    note: "No row/global confirmation can be treated as final component confirmation.",
  },
  {
    key: "blockers",
    label: "blockers",
    sourceType: "component truth",
    currentSource: "readonly mapper blockers",
    targetPath: "components.return_cant.instances[].blockers[]",
    note: "Blockers are already explicit and should stay visible until source paths are real.",
  },
];

const STRUCTURAL_COMPOSITION_READ_MODEL: ProductCompositionReadModelEntry[] = [
  {
    key: "face",
    label: "FACE / FATA",
    componentType: "structural",
    componentTemplateCode: "TPL-VOLUMETRIC-FACE_v1",
    componentId: "comp_face_litere",
    requiredInLetters: true,
    currentWiring: "partial",
    currentSourceType: "shared contract",
    productTruthTarget: "components.face.*",
    formSystemFields: ["face_finish_type", "letter_face_area_m2", "letter_perimeter_m"],
    geometryDependency: "selected_layer_refs + face area + perimeter",
    materialSource: "fallback / partial face material",
    operationSource: "debitare_fata / face_cnc_cut",
    calculationReadiness: "partial",
    blockers: ["FACE_MATERIAL_MISSING", "SELECTED_FACE_LAYER_MISSING", "FACE_FINISH_TARGET_MISSING"],
    recommendation: "Promote explicit face material, thickness, and confirmed perimeter onto component-owned truth.",
  },
  {
    key: "back",
    label: "BACK / SPATE",
    componentType: "structural",
    componentTemplateCode: "TPL-VOLUMETRIC-BACK_v1",
    componentId: "comp_spate_litere",
    requiredInLetters: true,
    currentWiring: "partial",
    currentSourceType: "shared contract",
    productTruthTarget: "components.back.*",
    formSystemFields: ["backing_mode", "back_bevel_enabled"],
    geometryDependency: "follows face geometry and area",
    materialSource: "implicit from backing mode / parent flow",
    operationSource: "debitare_spate / back_cut",
    calculationReadiness: "blocked",
    blockers: ["BACK_MATERIAL_MISSING", "BACKING_MODE_CONFIRMATION_REQUIRED"],
    recommendation: "Make back material explicit before calling the backing component separately calculable.",
  },
  {
    key: "return_cant",
    label: "RETURN_CANT / VOLUM",
    componentType: "structural",
    componentTemplateCode: "TPL-VOLUM-ALUMINIU_v1",
    componentId: "comp_lateral_litere",
    requiredInLetters: true,
    currentWiring: "partial",
    currentSourceType: "module produs",
    productTruthTarget: "components.return_cant.*",
    formSystemFields: ["return_depth_mm", "return_finish_type", "volum_aluminum_module_template_code", "letter_perimeter_m"],
    geometryDependency: "depends on face confirmed perimeter",
    materialSource: "Module produs profile gate only",
    operationSource: "modelare_cant / RETURN_PROFILE_MACHINE_FORMING / RETURN_PROFILE_FACE_BONDING",
    calculationReadiness: "blocked",
    blockers: [
      "RETURN_CANT_MATERIAL_MISSING",
      "RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED",
      "RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED",
    ],
    recommendation: "Align return/cant truth container before any separate calculation or delete/move work.",
  },
];

const FUNCTIONAL_COMPOSITION_READ_MODEL: ProductCompositionReadModelEntry[] = [
  {
    key: "lighting",
    label: "LIGHTING / LED",
    componentType: "functional",
    componentTemplateCode: "TPL-VOLUMETRIC-LED_v1",
    componentId: "comp_led_litere",
    requiredInLetters: false,
    currentWiring: "partial",
    currentSourceType: "shared contract",
    productTruthTarget: "components.lighting.*",
    formSystemFields: ["lighting_system_type", "led_module_count", "selected_psu_watts"],
    geometryDependency: "depends on face area and whole product geometry",
    materialSource: "LED modules + PSU config",
    operationSource: "sistem_led",
    calculationReadiness: "partial",
    blockers: ["LIGHTING_MODE_CONFIRMATION_REQUIRED", "LIGHTING_LED_COUNT_MISSING"],
    recommendation: "Keep as functional boundary until zones/circuits/service-access truth is explicit.",
  },
  {
    key: "finish",
    label: "FINISH / FINISAJ",
    componentType: "functional",
    componentTemplateCode: "TPL-VOLUMETRIC-FINISH_v1",
    componentId: "comp_finisaj_litere",
    requiredInLetters: true,
    currentWiring: "partial",
    currentSourceType: "shared contract",
    productTruthTarget: "components.finish.*",
    formSystemFields: ["letter_group_finishes", "mounting_template_enabled", "mounting_template_area_m2"],
    geometryDependency: "depends on face/return/artwork scope",
    materialSource: "review payload + finish family rules",
    operationSource: "finisaje",
    calculationReadiness: "blocked",
    blockers: ["FINISH_TARGET_MISSING", "PRINT_REQUIRED_UNKNOWN"],
    recommendation: "Separate finish, artwork, and cant ownership before claiming finish as complete component truth.",
  },
  {
    key: "mounting",
    label: "SUPPORT / MOUNTING",
    componentType: "functional",
    componentTemplateCode: "TPL-METAL-PREMOUNT-STRUCTURE_v1",
    componentId: "comp_premount_bars",
    requiredInLetters: false,
    currentWiring: "partial",
    currentSourceType: "module produs",
    productTruthTarget: "components.mounting.* / components.support.*",
    formSystemFields: ["mounting_system", "metal_support_required", "premount_bar_length_ml"],
    geometryDependency: "depends on width and installation strategy",
    materialSource: "Module produs + derived support bridge",
    operationSource: "structura_suport",
    calculationReadiness: "blocked",
    blockers: ["TRIGGER_FIELD_MISMATCH", "SUPPORT_REQUIRED_UNKNOWN"],
    recommendation: "Do not treat derived metal_support_required as primary component truth.",
  },
];

function ownershipFieldStateClass(sourceState: string) {
  if (sourceState.includes("missing")) {
    return "border-red-700/30 bg-red-950/20 text-red-200";
  }
  if (sourceState.includes("fallback") || sourceState.includes("pending")) {
    return "border-amber-700/30 bg-amber-950/20 text-amber-200";
  }
  if (sourceState.includes("dependency")) {
    return "border-cyan-700/30 bg-cyan-950/20 text-cyan-200";
  }
  return "border-slate-700 bg-slate-900 text-wo-text-secondary";
}

function returnCantSourceStatusClass(status: ReturnCantSourcePathAudit["sourceStatus"]) {
  switch (status) {
    case "component-owned template only":
      return "border-cyan-700/30 bg-cyan-950/20 text-cyan-200";
    case "form system only":
    case "separate finish component":
      return "border-amber-700/30 bg-amber-950/20 text-amber-200";
    case "parent aggregate only":
      return "border-slate-700 bg-slate-900 text-wo-text-secondary";
    case "operation registry missing":
    case "component-owned source missing":
    case "blocked":
      return "border-red-700/30 bg-red-950/20 text-red-200";
    default:
      return "border-slate-700 bg-slate-900 text-wo-text-secondary";
  }
}

function returnCantTruthSourceClass(sourceType: ReturnCantTruthContainerFieldAudit["sourceType"]) {
  switch (sourceType) {
    case "component truth":
      return "border-emerald-700/40 bg-emerald-900/20 text-emerald-300";
    case "component dependency anchor":
      return "border-cyan-700/40 bg-cyan-950/30 text-cyan-200";
    case "Form System capture":
      return "border-amber-700/40 bg-amber-900/20 text-amber-300";
    case "root geometry context":
    case "parent aggregate support":
      return "border-slate-700 bg-slate-900 text-wo-text-secondary";
    case "legacy alias":
      return "border-fuchsia-700/40 bg-fuchsia-950/20 text-fuchsia-200";
    case "component template / registry":
      return "border-cyan-700/40 bg-cyan-950/20 text-cyan-200";
    default:
      return "border-red-700/40 bg-red-950/20 text-red-200";
  }
}

function ReturnCantTruthContainerPanel() {
  const model = buildReturnCantReadonlyContainerModel();

  return (
    <section
      data-testid="product-system-return-cant-truth-container"
      className="mt-3 rounded-lg border border-fuchsia-800/40 bg-fuchsia-950/10 p-3"
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h4 className="text-[11px] font-bold uppercase tracking-wide text-fuchsia-100">Return/Cant truth container</h4>
          <p className="mt-0.5 text-[10px] text-fuchsia-300/80">
            Target readonly container alignment for return/cant. This does not write Product Truth. It only aligns the language used by Product System, the readonly mapper, and the composition model.
          </p>
        </div>
        <div className="flex flex-wrap gap-1.5 text-[9px] font-bold">
          <span className="rounded border border-fuchsia-700/40 bg-fuchsia-950/30 px-1.5 py-0.5 text-fuchsia-200">target: {model.targetContainerPath}</span>
          <span className="rounded border border-slate-700 bg-slate-900 px-1.5 py-0.5 text-wo-text-secondary">status: {model.readiness.toUpperCase()}</span>
        </div>
      </div>

      <div className="mt-2 rounded-lg border border-cyan-800/40 bg-cyan-950/15 px-3 py-2 text-[10px] text-cyan-200" data-testid="product-system-return-cant-face-dependency">
        FACE -&gt; RETURN_CANT dependency: target upstream is `{model.upstreamDependencies[0]?.canonicalPath}`. Until that dependency is explicit and confirmed, return/cant stays blocked and must not invent its own perimeter truth from aggregate/root context.
      </div>

      <div className="mt-2 rounded-lg border border-fuchsia-800/40 bg-fuchsia-950/15 px-3 py-2 text-[10px] text-fuchsia-200" data-testid="product-system-return-cant-legacy-alias">
        Legacy alias still present: `{model.legacyAliasPaths.join(", ")}` is diagnostic/compatibility language only. Canonical target remains `{model.targetContainerPath}`.
      </div>

      <div className="mt-2 rounded-lg border border-slate-800/90 bg-wo-surface-inset px-3 py-2 text-[10px] text-wo-text-secondary" data-testid="product-system-return-cant-aggregate-boundary">
        {model.productAggregateBoundaryNote}
      </div>

      <div className="mt-3 overflow-hidden rounded-lg border border-slate-800/90 bg-wo-surface-inset">
        <div className="grid grid-cols-[minmax(0,0.9fr)_minmax(0,0.85fr)_minmax(0,1fr)_minmax(0,1fr)] gap-2 border-b border-slate-800 px-3 py-2 text-[9px] font-bold uppercase tracking-wide text-wo-text-muted">
          <span>Field</span>
          <span>Source type</span>
          <span>Current source</span>
          <span>Target path</span>
        </div>
        <div className="divide-y divide-slate-800/80">
          {model.sourceTypeRows.map((field) => (
            <div key={field.key} data-testid={`product-system-return-cant-truth-field-${field.key}`} className="px-3 py-2 text-[10px]">
              <div className="grid grid-cols-[minmax(0,0.9fr)_minmax(0,0.85fr)_minmax(0,1fr)_minmax(0,1fr)] gap-2">
                <div>
                  <p className="font-bold text-wo-text-primary">{field.label}</p>
                  <p className="mt-0.5 text-[9px] text-wo-text-muted">{field.note}</p>
                </div>
                <div>
                  <span className={`inline-flex rounded border px-1.5 py-0.5 text-[9px] font-bold ${returnCantTruthSourceClass(field.sourceType)}`}>{displayModuleSourceTypeLabel(field.sourceType)}</span>
                </div>
                <p className="font-mono text-wo-text-secondary">{field.currentSource}</p>
                <p className="font-mono text-cyan-200/85">{field.targetPath}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function compositionWiringClass(status: ProductCompositionReadModelEntry["currentWiring"]) {
  switch (status) {
    case "wired":
      return "border-emerald-700/40 bg-emerald-900/20 text-emerald-300";
    case "partial":
      return "border-amber-700/40 bg-amber-900/20 text-amber-300";
    default:
      return "border-red-700/40 bg-red-900/20 text-red-300";
  }
}

function compositionReadinessClass(status: ProductCompositionReadModelEntry["calculationReadiness"]) {
  switch (status) {
    case "ready":
      return "border-emerald-700/40 bg-emerald-900/20 text-emerald-300";
    case "partial":
      return "border-amber-700/40 bg-amber-900/20 text-amber-300";
    default:
      return "border-red-700/40 bg-red-900/20 text-red-300";
  }
}

function CompositionReadModelTable({
  title,
  entries,
  testId,
}: {
  title: string;
  entries: ProductCompositionReadModelEntry[];
  testId: string;
}) {
  return (
    <section data-testid={testId} className="mt-3 rounded-lg border border-violet-800/40 bg-violet-950/10 p-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h4 className="text-[11px] font-bold uppercase tracking-wide text-violet-100">{title}</h4>
          <p className="mt-0.5 text-[10px] text-violet-300/80">
            {PRODUCT_TEMPLATE_COMPOSES_HELP} {equalModulesHintRo()}
          </p>
        </div>
        <span className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-[9px] font-bold text-wo-text-secondary">Overall status: PARTIAL</span>
      </div>

      <div className="mt-2 rounded-lg border border-slate-800/90 bg-wo-surface-inset px-3 py-2 text-[10px] text-wo-text-secondary" data-testid={`${testId}-aggregate-boundary`}>
        ProductAggregate is derived read model. If a row compensates for missing component truth, treat it as support/diagnostic output, not as the primary truth source.
      </div>

      <div className="mt-3 overflow-hidden rounded-lg border border-slate-800/90 bg-wo-surface-inset">
        <div className="grid grid-cols-[minmax(0,0.9fr)_minmax(0,0.9fr)_minmax(0,0.9fr)_minmax(0,1.1fr)_minmax(0,0.8fr)_minmax(0,1fr)] gap-2 border-b border-slate-800 px-3 py-2 text-[9px] font-bold uppercase tracking-wide text-wo-text-muted">
          <span>Module</span>
          <span>Module / id</span>
          <span>Current source</span>
          <span>Truth target / dependencies</span>
          <span>Status</span>
          <span>Blockers</span>
        </div>
        <div className="divide-y divide-slate-800/80">
          {entries.map((entry) => (
            <div key={entry.key} data-testid={`${testId}-${entry.key}`} className="px-3 py-2 text-[10px]">
              <div className="grid grid-cols-[minmax(0,0.9fr)_minmax(0,0.9fr)_minmax(0,0.9fr)_minmax(0,1.1fr)_minmax(0,0.8fr)_minmax(0,1fr)] gap-2">
                <div>
                  <p className="font-bold text-wo-text-primary">{entry.label}</p>
                  <p className="mt-0.5 text-[9px] text-wo-text-muted">{entry.componentType === "structural" ? "Module produs (structural)" : "Module produs (functional)"}</p>
                </div>
                <div>
                  <p className="font-mono text-cyan-200/85">{entry.componentTemplateCode}</p>
                  <p className="mt-0.5 font-mono text-[9px] text-wo-text-muted">{entry.componentId}</p>
                </div>
                <div>
                  <span className={`inline-flex rounded border px-1.5 py-0.5 text-[9px] font-bold ${compositionWiringClass(entry.currentWiring)}`}>{entry.currentWiring}</span>
                  <p className="mt-1 text-[9px] text-wo-text-muted">source: {displayModuleSourceTypeLabel(entry.currentSourceType)}</p>
                </div>
                <div>
                  <p className="font-mono text-cyan-200/85">{entry.productTruthTarget}</p>
                  <p className="mt-0.5 text-wo-text-muted">geometry: {entry.geometryDependency}</p>
                  <p className="mt-0.5 text-wo-text-muted">material: {entry.materialSource}</p>
                  <p className="mt-0.5 text-wo-text-muted">operation: {entry.operationSource}</p>
                </div>
                <div>
                  <span className={`inline-flex rounded border px-1.5 py-0.5 text-[9px] font-bold ${compositionReadinessClass(entry.calculationReadiness)}`}>{entry.calculationReadiness}</span>
                  <p className="mt-1 text-[9px] text-wo-text-muted">required: {entry.requiredInLetters ? "yes" : "conditional"}</p>
                </div>
                <div>
                  <p className="font-mono text-amber-200/85">{entry.blockers.join(", ")}</p>
                  <p className="mt-0.5 text-wo-text-muted">{entry.recommendation}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function ReturnCantSeparateCalculationSourcePaths({
  sharedWithProductCodes,
}: {
  sharedWithProductCodes: string[];
}) {
  const logoReuse = sharedWithProductCodes.includes("TPL-VOLUMETRIC-LOGO_v1");

  return (
    <section
      data-testid="product-system-return-cant-source-paths"
      className="mt-3 rounded-lg border border-cyan-800/40 bg-cyan-950/10 p-3"
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h4 className="text-[11px] font-bold uppercase tracking-wide text-cyan-100">Separate calculation source paths</h4>
          <p className="mt-0.5 text-[10px] text-cyan-300/80">
            {RETURN_CANT_MOVE_TRUTH_HELP}
          </p>
        </div>
        <div className="flex flex-wrap gap-1.5 text-[9px] font-bold">
          <span className="rounded border border-cyan-700/40 bg-cyan-950/30 px-1.5 py-0.5 text-cyan-200">Module TPL-VOLUM-ALUMINIU_v1</span>
          <span className="rounded border border-cyan-700/40 bg-cyan-950/30 px-1.5 py-0.5 text-cyan-200">Component comp_lateral_litere</span>
        </div>
      </div>

      <div className="mt-2 grid gap-2 md:grid-cols-3">
        <div className="rounded-lg border border-slate-800/90 bg-wo-surface-inset px-3 py-2">
          <p className="text-[9px] font-bold uppercase tracking-wide text-wo-text-muted">We can read now</p>
          <p className="mt-1 text-[10px] text-wo-text-primary">Depth gate, finish token, component operations, component material variants, and workcenter hints.</p>
        </div>
        <div className="rounded-lg border border-slate-800/90 bg-wo-surface-inset px-3 py-2">
          <p className="text-[9px] font-bold uppercase tracking-wide text-wo-text-muted">Still parent aggregate only</p>
          <p className="mt-1 text-[10px] text-wo-text-primary">`quote_geometry.letter_perimeter_m`, linked aggregate operation traces, and global review setup hydration.</p>
        </div>
        <div className="rounded-lg border border-slate-800/90 bg-wo-surface-inset px-3 py-2">
          <p className="text-[9px] font-bold uppercase tracking-wide text-wo-text-muted">{MUST_OWN_ON_MODULE_LABEL}</p>
          <p className="mt-1 text-[10px] text-wo-text-primary">`material_profile`, `perimeter_source`, `layer_group_ids`, and `confirmation_state`.</p>
        </div>
      </div>

      {logoReuse ? (
        <div className="mt-2 rounded-lg border border-amber-800/40 bg-amber-950/20 px-3 py-2 text-[10px] text-amber-200" data-testid="product-system-return-cant-logo-reuse-note">
          Reusable component check: `TPL-VOLUMETRIC-LOGO_v1` also points at this cant component boundary, so the missing source paths should be solved once for Letters and Logo. Logo remains candidate / read-only.
        </div>
      ) : null}

      <div className="mt-3 overflow-hidden rounded-lg border border-slate-800/90 bg-wo-surface-inset">
        <div className="grid grid-cols-[minmax(0,0.9fr)_minmax(0,1fr)_minmax(0,1.15fr)_minmax(0,0.85fr)_minmax(0,0.95fr)] gap-2 border-b border-slate-800 px-3 py-2 text-[9px] font-bold uppercase tracking-wide text-wo-text-muted">
          <span>Source key</span>
          <span>Canonical target</span>
          <span>Current source path</span>
          <span>Source status</span>
          <span>Blocker</span>
        </div>
        <div className="divide-y divide-slate-800/80">
          {RETURN_CANT_SEPARATE_SOURCE_PATHS.map((entry) => (
            <div key={entry.key} data-testid={`product-system-return-cant-source-${entry.key}`} className="px-3 py-2 text-[10px]">
              <div className="grid grid-cols-[minmax(0,0.9fr)_minmax(0,1fr)_minmax(0,1.15fr)_minmax(0,0.85fr)_minmax(0,0.95fr)] gap-2">
                <div>
                  <p className="font-bold text-wo-text-primary">{entry.label}</p>
                  <p className="mt-0.5 text-[9px] text-wo-text-muted">{entry.currentSource}</p>
                </div>
                <p className="font-mono text-cyan-200/85">{entry.canonicalTarget}</p>
                <p className="font-mono text-wo-text-secondary">{entry.currentSourcePath}</p>
                <span className={`h-fit rounded border px-1.5 py-0.5 text-[9px] font-bold ${returnCantSourceStatusClass(entry.sourceStatus)}`}>{entry.sourceStatus}</span>
                <p className="font-mono text-amber-200/85">{entry.blocker}</p>
              </div>
              <p className="mt-1 text-[10px] text-wo-text-muted">{entry.note}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function ComponentCalculationOwnershipPanel({
  availability,
}: {
  availability?: ProductTemplateAvailabilityItem | null;
}) {
  const contracts = availability?.shared_component_contracts ?? [];
  if (contracts.length === 0) {
    return null;
  }

  const contractsByKey = new Map(contracts.map((contract) => [contract.component_key, contract]));
  const rows = SHARED_COMPONENT_OWNERSHIP_ORDER
    .map((componentKey) => {
      const audit = SHARED_COMPONENT_OWNERSHIP_AUDIT[componentKey];
      const contract = contractsByKey.get(componentKey);
      if (!audit || !contract) {
        return null;
      }
      return { audit, contract };
    })
    .filter((row): row is { audit: SharedComponentOwnershipAudit; contract: NonNullable<typeof contracts[number]> } => Boolean(row));

  if (rows.length === 0) {
    return null;
  }

  const isLogoCandidate =
    availability?.template_code === "TPL-VOLUMETRIC-LOGO_v1" ||
    contracts.some((contract) => contract.profile_key === "logo");
  const profileLabel = Array.from(new Set(contracts.map((contract) => contract.profile_key))).join(" + ");

  return (
    <section
      data-testid="product-system-component-ownership-panel"
      className="rounded-xl border border-amber-800/40 bg-amber-950/10 p-3"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-[13px] font-bold text-amber-100">Module calculation ownership</h3>
          <p className="mt-0.5 text-[11px] text-amber-200/75">
            {PRODUCT_TEMPLATE_COMPOSER_ONLY_HELP}
          </p>
        </div>
        <div className="flex flex-wrap gap-1.5 text-[10px] font-bold">
          <span className="rounded border border-wo-warning/40 bg-wo-warning-muted px-2 py-0.5 text-wo-warning">Read-only</span>
          <span className="rounded border border-wo-warning/40 bg-wo-warning-muted px-2 py-0.5 text-wo-warning" data-testid="product-system-ownership-composer-badge">Product Template = composer</span>
          <span className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-wo-text-secondary">No component root</span>
          <span className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-wo-text-secondary">No component quote</span>
          <span className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-wo-text-secondary">No promote</span>
          <span className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-wo-text-secondary">No mutation call</span>
          <span className="rounded border border-cyan-700/40 bg-cyan-950/30 px-2 py-0.5 text-cyan-200">Profile {profileLabel}</span>
        </div>
      </div>

      <div
        className="mt-3 rounded-lg border border-red-800/40 bg-red-950/15 px-3 py-2 text-[11px] text-red-200"
        data-testid="product-system-ownership-product-template-warning"
      >
        Product Template still carries component-owned defaults, hydrated values, or dependencies in the product-root flow. Treat this page as ownership audit only until component-owned sources are wired.
      </div>

      <CompositionReadModelTable
        title="Structural composition map"
        entries={STRUCTURAL_COMPOSITION_READ_MODEL}
        testId="product-system-structural-composition-map"
      />

      <CompositionReadModelTable
        title="Functional composition map"
        entries={FUNCTIONAL_COMPOSITION_READ_MODEL}
        testId="product-system-functional-composition-map"
      />

      {isLogoCandidate ? (
        <div
          className="mt-2 rounded-lg border border-amber-800/40 bg-amber-950/20 px-3 py-2 text-[11px] text-amber-200"
          data-testid="product-system-ownership-logo-candidate"
        >
          <p className="font-bold">TPL-VOLUMETRIC-LOGO_v1 remains candidate / read-only / linked child.</p>
          <p className="mt-0.5 text-amber-200/75">Do not activate it as Work Intake root or commercial root from this surface.</p>
        </div>
      ) : null}

      <div className="mt-3 grid gap-3 xl:grid-cols-2">
        {rows.map(({ audit, contract }) => {
          const moduleCode =
            contract.shared_module_template_code ??
            contract.module_template_code ??
            audit.primaryTemplateCode;
          return (
            <article
              key={audit.componentKey}
              data-testid={`product-system-ownership-component-${audit.componentKey}`}
              className="rounded-lg border border-slate-800 bg-slate-950/40 p-3"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="text-[12px] font-bold text-wo-text-primary">{audit.label}</p>
                  <p className="mt-0.5 font-mono text-[10px] text-cyan-200">{moduleCode}</p>
                  <p className="mt-0.5 text-[10px] text-wo-text-muted">{MODULE_PRODUS_BOUNDARY_LABEL}</p>
                </div>
                <span
                  className={`rounded border px-2 py-0.5 text-[9px] font-bold ${ownershipStatusClass(audit.separateCalculationStatus)}`}
                  data-testid={`product-system-ownership-status-${audit.componentKey}`}
                >
                  {audit.separateCalculationLabel}
                </span>
              </div>

              <div className="mt-2 flex flex-wrap gap-1.5 text-[10px]">
                <span className="rounded border border-slate-700 bg-slate-900 px-1.5 py-0.5 text-wo-text-secondary">Confidence {contract.confidence}</span>
                <span className="rounded border border-slate-700 bg-slate-900 px-1.5 py-0.5 text-wo-text-secondary">Owner decision {contract.owner_decision}</span>
              </div>

              <div className="mt-3 rounded-lg border border-slate-800/90 bg-wo-surface-inset px-3 py-2">
                <p className="text-[10px] font-bold uppercase tracking-wide text-wo-text-muted">Should own</p>
                <p className="mt-1 font-mono text-[10px] text-wo-text-primary">{audit.shouldOwn.join(", ")}</p>
              </div>

              <div className="mt-2 rounded-lg border border-slate-800/90 bg-wo-surface-inset px-3 py-2">
                <p className="text-[10px] font-bold uppercase tracking-wide text-wo-text-muted">Current gaps</p>
                <div className="mt-1 space-y-1 text-[10px] text-amber-200/85">
                  {audit.gaps.map((gap) => (
                    <p key={gap}>{gap}</p>
                  ))}
                </div>
              </div>

              <div className="mt-2 overflow-hidden rounded-lg border border-slate-800/90 bg-wo-surface-inset">
                <div className="grid grid-cols-[minmax(0,0.95fr)_minmax(0,1.2fr)_minmax(0,0.9fr)_minmax(0,1fr)] gap-2 border-b border-slate-800 px-3 py-2 text-[9px] font-bold uppercase tracking-wide text-wo-text-muted">
                  <span>Canonical field key</span>
                  <span>Product Truth path</span>
                  <span>Source/state</span>
                  <span>Warning</span>
                </div>
                <div className="divide-y divide-slate-800/80">
                  {audit.fields.map((field) => (
                    <div key={field.key} className="grid grid-cols-[minmax(0,0.95fr)_minmax(0,1.2fr)_minmax(0,0.9fr)_minmax(0,1fr)] gap-2 px-3 py-2 text-[10px]">
                      <p className="font-mono font-bold text-wo-text-primary">{field.key}</p>
                      <p className="font-mono text-cyan-200/85">{field.productTruthPath}</p>
                      <span className={`h-fit rounded border px-1.5 py-0.5 text-[9px] font-bold ${ownershipFieldStateClass(field.sourceState)}`}>{field.sourceState}</span>
                      <p className="text-amber-200/85">{field.warning}</p>
                    </div>
                  ))}
                </div>
              </div>

              {audit.componentKey === "volumetric_return_side" ? (
                <>
                  <ReturnCantTruthContainerPanel />
                  <ReturnCantSeparateCalculationSourcePaths
                    sharedWithProductCodes={availability?.shared_with_product_codes ?? []}
                  />
                </>
              ) : null}

              <p className="mt-2 text-[10px] text-wo-text-muted">{audit.note}</p>
            </article>
          );
        })}
      </div>

      <p className="mt-3 text-[10px] text-wo-text-muted">
        Canonical field bindings stay read-only. Use the Form System tab for the backing field-binding map; do not treat ProductAggregate or ProductDefinition as primary owners.
      </p>
    </section>
  );
}

function SharedVolumetricFoundationPanel({
  availability,
}: {
  availability?: ProductTemplateAvailabilityItem | null;
}) {
  const contracts = availability?.shared_component_contracts ?? [];
  if (contracts.length === 0) return null;

  const profiles = Array.from(new Set(contracts.map((contract) => contract.profile_key))).join(" + ");
  const lighting = contracts.find((contract) => contract.component_key === "volumetric_lighting");
  const isCandidate = availability?.product_system_role === "candidate_product";
  const isLogoProfile = contracts.some((contract) => contract.profile_key === "logo");
  const runtimeStatusFor = (contract: (typeof contracts)[number]) => {
    if (contract.component_key === "volumetric_lighting" && contract.strategy_status) {
      return contract.strategy_status;
    }
    if (contract.component_key === "volumetric_lighting" && contract.profile_key === "logo") {
      return "NEEDS_LED_CALCULATION_STRATEGY";
    }
    if (contract.component_key === "volumetric_lighting" && contract.profile_key === "letters") {
      return "current LED strategy";
    }
    return availability?.quote_offerable ? "offerable binding" : "candidate / linked child binding";
  };

  return (
    <section data-testid="product-system-editor-shared-foundation" className="rounded-xl border border-cyan-800/40 bg-cyan-950/10 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-[13px] font-bold text-cyan-100">Shared component foundation</h3>
          <p className="mt-0.5 text-[11px] text-cyan-300/70">{SHARED_FOUNDATION_HELP}</p>
        </div>
        <div className="flex flex-wrap gap-1.5 text-[10px] font-bold">
          <span className="rounded border border-cyan-700/40 bg-cyan-950/40 px-2 py-0.5 text-cyan-200">Read-only</span>
          <span className="rounded border border-cyan-700/40 bg-cyan-950/40 px-2 py-0.5 text-cyan-200">Profile {profiles}</span>
          <span className="rounded border border-slate-700 bg-slate-900 px-2 py-0.5 text-wo-text-secondary">Contracts {contracts.length}</span>
          {lighting?.confidence === "PARTIAL" ? <span className="rounded border border-amber-700/40 bg-amber-900/20 px-2 py-0.5 text-amber-300">Lighting PARTIAL</span> : null}
        </div>
      </div>
      {isCandidate && isLogoProfile ? (
        <div className="mt-2 rounded-lg border border-amber-800/40 bg-amber-950/15 px-2.5 py-2 text-[10px] text-amber-200" data-testid="product-system-editor-logo-candidate-readiness">
          <p className="font-bold">Candidate / linked child only Â· Not Work Intake</p>
          <p className="mt-0.5 text-amber-200/75">Offerability requires Product Truth + Modular Form + ProductDefinition + Pricing readiness.</p>
        </div>
      ) : null}
      <div className="mt-2 grid gap-1.5 md:grid-cols-2 xl:grid-cols-3">
        {contracts.map((contract) => (
          <div key={contract.component_key} className="rounded-lg border border-slate-800 bg-slate-950/40 px-2.5 py-1.5">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <p className="text-[11px] font-bold text-wo-text-primary">{contract.display_name}</p>
                <p className="mt-0.5 font-mono text-[10px] font-bold text-cyan-200">{contract.component_key}</p>
              </div>
              <span className={`rounded border px-1.5 py-0.5 text-[9px] font-bold ${contract.confidence === "PARTIAL" ? "border-amber-700/40 bg-amber-900/20 text-amber-300" : "border-slate-700 bg-slate-900 text-wo-text-secondary"}`}>{contract.confidence}</span>
            </div>
            <p className="mt-1 text-[10px] text-wo-text-muted">Profile: {contract.profile_key}</p>
            <p className="mt-0.5 truncate font-mono text-[10px] text-cyan-200">{MODULE_PRODUS_SHARED_SINGULAR_LABEL}: {SHARED_VOLUMETRIC_EDITOR_MODULES[contract.component_key] ?? contract.shared_module_template_code ?? contract.module_template_code}</p>
            {contract.component_key === "volumetric_lighting" && contract.shared_module_template_code ? (
              <p className="mt-0.5 truncate font-mono text-[10px] text-cyan-200">{MODULE_PRODUS_SHARED_SINGULAR_LABEL}: {contract.shared_module_template_code}</p>
            ) : null}
            {contract.component_key === "volumetric_lighting" && contract.strategy_source_template_code ? (
              <p className="mt-0.5 truncate font-mono text-[10px] text-cyan-200">Strategy source: {contract.strategy_source_template_code}</p>
            ) : null}
            {contract.component_key === "volumetric_lighting" && contract.calculation_strategy_key ? (
              <p className="mt-0.5 truncate font-mono text-[10px] text-amber-300">Strategy: {contract.calculation_strategy_key}</p>
            ) : null}
            <p className="mt-1 text-[10px] text-wo-text-muted">Owner decision: {contract.owner_decision}</p>
            <p className="mt-0.5 text-[10px] font-bold text-wo-text-secondary">Runtime status: {runtimeStatusFor(contract)}</p>
            {contract.component_key === "volumetric_lighting" && contract.strategy_meaning ? (
              <p className="mt-0.5 text-[9px] text-wo-text-muted">{contract.strategy_meaning}</p>
            ) : null}
            {contract.component_key === "volumetric_lighting" && contract.reserved_module_template_code ? (
              <p className="mt-0.5 truncate font-mono text-[9px] text-wo-text-muted">Logo lighting strategy/profile source: {contract.reserved_module_template_code}</p>
            ) : null}
            <p className="mt-0.5 text-[9px] text-wo-text-dim">No pricing / no runtime activation.</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function TemplateEditor({
  draft,
  isNew,
  onChange,
  onSave,
  onCancel,
  onArchive,
  archivePolicy,
  onChangeTemplate,
  onBackToLibrary,
  readOnly = false,
  saving,
  families,
  materials,
  availability,
  allTemplates,
  availabilityItems,
  ownerProofWorkspaceId = null,
}: {
  draft: DraftTemplate;
  isNew: boolean;
  onChange: (next: DraftTemplate) => void;
  onSave: () => void;
  onCancel: () => void;
  onArchive?: () => void;
  archivePolicy: {
    isArchivedForQuote: boolean;
    canArchive: boolean;
    blockReason: string | null;
  };
  onChangeTemplate?: () => void;
  onBackToLibrary?: () => void;
  readOnly?: boolean;
  saving: boolean;
  families: ProductFamily[];
  materials: InventoryMaterialEntity[];
  availability?: ProductTemplateAvailabilityItem | null;
  allTemplates: ProductTemplateEntity[];
  availabilityItems: ProductTemplateAvailabilityItem[];
  /** When set with volumetric template, shows owner read-only chain proof. */
  ownerProofWorkspaceId?: string | null;
}) {
  const [studioTab, setStudioTab] = useState<"structure" | "general" | "operational" | "form-system">("structure");
  const [selectedComponentIndex, setSelectedComponentIndex] = useState<number | null>(null);
  const [expandedComponentIndex, setExpandedComponentIndex] = useState<number | null>(null);
  const familyList: ProductFamily[] = Array.isArray(families) ? families : [];
  const materialList: InventoryMaterialEntity[] = Array.isArray(materials) ? materials : [];
  const materialsByCode = useMemo(() => {
    const m = new Map<string, InventoryMaterialEntity>();
    materialList.forEach((row) => m.set(row.code, row));
    return m;
  }, [materialList]);

  const { aggregate, usingFallback, fallbackReason, isLoading: aggregateLoading } = useProductAggregate(
    isNew ? null : draft.template_code
  );
  const preferAggregateDisplay = shouldPreferAggregateDisplay(draft.components, aggregate);

  const templateOperations = useMemo((): TemplateOperationRef[] => {
    const ops: TemplateOperationRef[] = [];
    for (const component of draft.components) {
      for (const op of component.operations) {
        ops.push({
          code: op.code,
          label: op.name || op.code,
          workcenter: op.workcenter ?? null,
        });
      }
    }
    return ops;
  }, [draft.components]);

  const applyChange = readOnly ? () => {} : onChange;
  const update = <K extends keyof DraftTemplate>(key: K, value: DraftTemplate[K]) =>
    applyChange({ ...draft, [key]: value });

  const nextComponentId = (): string => {
    const used = new Set(draft.components.map((c) => c.component_id));
    let i = draft.components.length + 1;
    while (used.has(`comp_${i}`)) i += 1;
    return `comp_${i}`;
  };
  const addComponent = () =>
    update("components", [
      ...draft.components,
      {
        component_id: nextComponentId(),
        type: "STRUCTURA",
        name: "",
        operations: [],
        materials: [],
      },
    ]);
  const updateComponent = (i: number, next: ProductTemplateComponent) => {
    const arr = [...draft.components];
    arr[i] = next;
    update("components", arr);
  };
  const removeComponent = (i: number) => {
    update("components", draft.components.filter((_, idx) => idx !== i));
    setSelectedComponentIndex((prev) => {
      if (prev === null) return null;
      if (prev === i) return null;
      if (prev > i) return prev - 1;
      return prev;
    });
    setExpandedComponentIndex((prev) => {
      if (prev === null) return null;
      if (prev === i) return null;
      if (prev > i) return prev - 1;
      return prev;
    });
  };

  useEffect(() => {
    if (draft.components.length === 0) {
      setSelectedComponentIndex(null);
      setExpandedComponentIndex(null);
      return;
    }
    setSelectedComponentIndex((prev) =>
      prev !== null && prev >= draft.components.length ? null : prev
    );
    setExpandedComponentIndex((prev) =>
      prev !== null && prev >= draft.components.length ? null : prev
    );
  }, [draft.components.length]);

  const validation = useMemo(
    () => computeValidation(draft, familyList, materialsByCode),
    [draft, familyList, materialsByCode]
  );
  const canSave = validation.every((v) => v.ok);
  const passedCount = validation.filter((v) => v.ok).length;
  const displayCounts = resolveDisplayCounts(
    getDraftDisplayCounts(draft),
    aggregate,
    preferAggregateDisplay
  );

  const constructionStages = useMemo(() => {
    const explicit = parseExplicitConstructionStagesFromNotes(draft.notes);
    return deriveConstructionStages(draft.components, {
      explicitStages: explicit,
      getStageLabel: (component) => {
        const cfg =
          COMPONENT_TYPE_CONFIG[component.type] || COMPONENT_TYPE_CONFIG.STRUCTURA;
        const typeLabel = getComponentTypeDisplayLabel(
          component,
          draft.template_code,
          cfg.label
        );
        return typeLabel || component.name.trim() || component.component_id;
      },
    });
  }, [draft.components, draft.notes, draft.template_code]);

  const getConstructionStageStyle = useCallback(
    (stage: { code: string; label: string; componentType: ProductComponentType }): ConstructionStageStyle => {
      const cfg =
        COMPONENT_TYPE_CONFIG[stage.componentType] || COMPONENT_TYPE_CONFIG.STRUCTURA;
      return {
        icon: isVolumetricLettersTemplate(draft.template_code)
          ? getVolumetricStageIcon(stage) ?? cfg.icon
          : cfg.icon,
        color: cfg.color,
        bgColor: cfg.bgColor,
        borderColor: cfg.borderColor,
      };
    },
    [draft.template_code]
  );

  const selectComponent = useCallback((index: number) => {
    setSelectedComponentIndex(index);
    requestAnimationFrame(() => {
      const row = document.querySelector(`[data-component-index="${index}"]`);
      row?.scrollIntoView({ block: "nearest", behavior: "smooth" });
    });
  }, []);

  const toggleComponentExpand = useCallback((index: number) => {
    if (readOnly) return;
    setSelectedComponentIndex(index);
    setExpandedComponentIndex((prev) => (prev === index ? null : index));
  }, [readOnly]);

  const selectedComponent =
    selectedComponentIndex !== null ? draft.components[selectedComponentIndex] ?? null : null;
  const selectedTypeLabel =
    selectedComponent !== null
      ? getComponentTypeDisplayLabel(
          selectedComponent,
          draft.template_code,
          (COMPONENT_TYPE_CONFIG[selectedComponent.type] || COMPONENT_TYPE_CONFIG.STRUCTURA).label
        )
      : "";

  const templateDisplayName =
    draft.family_name.trim() ||
    draft.description.trim().split("\n")[0]?.slice(0, 80) ||
    "";

  const internalHoursLabel = formatInternalTemplateHours(draft.estimated_hours);
  const isLogoSharedProfile = availability?.shared_component_contracts?.some(
    (contract) => contract.profile_key === "logo"
  ) ?? false;

  const candidateModuleProdusReadonlyPanel = (
    <CandidateModuleProdusPanel
      templates={allTemplates}
      availabilityItems={availabilityItems}
      selectedTemplateCode={draft.template_code}
      variant="inline"
    />
  );

  const generalTabPanel = (
    <div className="space-y-3">
      {candidateModuleProdusReadonlyPanel}
      <TemplateGeneralTabPanel
        draft={draft}
        readOnly={readOnly}
        saving={saving}
        isNew={isNew}
        familyList={familyList}
        internalHoursLabel={internalHoursLabel}
        componentCount={displayCounts.components}
        operationCount={displayCounts.operations}
        materialCount={displayCounts.materials}
        isArchivedForQuote={archivePolicy.isArchivedForQuote}
        canArchive={archivePolicy.canArchive}
        archiveBlockReason={archivePolicy.blockReason}
        onNotesChange={(value) => update("notes", value)}
        onDescriptionChange={(value) => update("description", value)}
        onArchive={readOnly ? undefined : onArchive}
      />
      <SharedVolumetricFoundationPanel availability={availability} />
      {draft.template_code ? (
        <>
          <ProductTemplatePublicationPanel templateCode={draft.template_code} />
          <ComponentContractUsedByPanel templateCode={draft.template_code} />
          <ProductE2EReadinessPanel templateCode={draft.template_code} />
        </>
      ) : null}
    </div>
  );

  const structurePanel = (
    <div className="space-y-4">
      <ProductCompilerDisplayShell stage="both" />
      {candidateModuleProdusReadonlyPanel}

      <ComponentCalculationOwnershipPanel availability={availability} />

      {aggregateLoading ? (
        <div className="text-[11px] text-wo-text-muted">Se încarcă {PRODUCT_COMPILER_LABEL}…</div>
      ) : isLogoSharedProfile ? (
        <SharedVolumetricFoundationPanel availability={availability} />
      ) : (
        <ProductAggregateOverviewPanel
          aggregate={aggregate}
          fallbackMessage={usingFallback ? fallbackReason : null}
          showLegacyFallbackNote={usingFallback}
        />
      )}

      {preferAggregateDisplay && aggregate && !isLogoSharedProfile ? (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Hammer className="w-5 h-5 text-purple-400 shrink-0" />
            <h3 className="text-[14px] font-bold text-wo-text-primary">{PRODUCT_COMPILER_GRAPH_STAGE_LABEL}</h3>
            <span className="text-[10px] text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded-full font-bold">
              {aggregate.components.length}
            </span>
          </div>
          <ProductAggregateStructureList aggregate={aggregate} />
          {draft.components.some(isSyntheticAutoComponent) ? (
            <div className="rounded-lg border border-amber-700/40 bg-amber-900/10 px-3 py-2 text-[10px] text-amber-200">
              Legacy parent row conține componentă sintetică (comp_auto_1) — folosită doar pentru compatibilitate edit, nu ca adevăr structural.
            </div>
          ) : null}
        </div>
      ) : (
        <>
      {constructionStages.length > 0 ? (
        <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-xl p-3">
          <TemplateConstructionStageRow
            stages={constructionStages}
            selectedIndex={selectedComponentIndex}
            onSelectStage={selectComponent}
            getStageStyle={getConstructionStageStyle}
            collapsible={false}
          />
        </div>
      ) : null}

      <div className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <Hammer className="w-5 h-5 text-purple-400 shrink-0" />
              <h3 className="text-[14px] font-bold text-wo-text-primary">Structură produs</h3>
              <span className="text-[10px] text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded-full font-bold">
                {draft.components.length}
              </span>
            </div>
            <p className="text-[10px] text-wo-text-muted mt-1 pl-7">
              Apasă pe o componentă pentru detalii în panoul din dreapta. Folosește săgeata pentru
              editare inline.
            </p>
          </div>
          {!readOnly ? (
            <button
              type="button"
              onClick={addComponent}
              className="flex items-center gap-1.5 px-3 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-[11px] font-bold transition-colors shadow-lg shadow-purple-900/20"
            >
              <Plus className="w-3.5 h-3.5" /> Adaugă componentă
            </button>
          ) : null}
        </div>

        {draft.components.length === 0 ? (
          <div className="bg-wo-surface-raised border border-wo-border-subtle border-dashed rounded-xl p-8 text-center">
            <Layers className="w-10 h-10 text-wo-text-dim mx-auto mb-3" />
            <p className="text-[13px] text-wo-text-muted font-semibold mb-1">Nicio componentă definită</p>
            <p className="text-[11px] text-wo-text-muted mb-4">
              Adaugă componentele care definesc structura produsului.
            </p>
            {!readOnly ? (
              <button
                type="button"
                onClick={addComponent}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-[12px] font-bold transition-colors"
              >
                <Plus className="w-3.5 h-3.5" /> Prima componentă
              </button>
            ) : null}
          </div>
        ) : (
          <div className="space-y-1">
            {draft.components.map((c, i) => (
              <ComponentTimelineWrap
                key={c.component_id + "_" + i}
                index={i}
                isLast={i === draft.components.length - 1}
              >
                <CollapsibleComponentCard
                  component={c}
                  allComponents={draft.components}
                  index={i}
                  templateCode={draft.template_code}
                  selected={selectedComponentIndex === i}
                  expanded={expandedComponentIndex === i}
                  onSelect={() => selectComponent(i)}
                  onToggleExpand={() => toggleComponentExpand(i)}
                  onUpdate={(next) => updateComponent(i, next)}
                  onRemove={() => removeComponent(i)}
                  materials={materialList}
                  materialsByCode={materialsByCode}
                  readOnly={readOnly}
                />
              </ComponentTimelineWrap>
            ))}
          </div>
        )}
      </div>
        </>
      )}
    </div>
  );

  return (
    <div className="flex flex-col w-full min-h-[min(720px,calc(100vh-240px))] max-h-[calc(100vh-200px)] border border-wo-border-subtle rounded-xl overflow-hidden bg-wo-surface-inset">
      <TemplateEditorCommandBar
        templateCode={draft.template_code}
        displayName={templateDisplayName}
        active={draft.active}
        isNew={isNew}
        counts={displayCounts}
        passedCount={passedCount}
        totalValidation={validation.length}
        canSave={canSave}
        saving={saving}
        onSave={onSave}
        onCancel={onCancel}
        onChangeTemplate={onChangeTemplate}
        onBackToLibrary={onBackToLibrary}
        pricingHref={!isNew && draft.active ? `/inventory/pricing?template=${encodeURIComponent(draft.template_code)}` : undefined}
        changeTemplateLabel={isNew ? "Alege template" : "Schimbă template"}
        readOnly={readOnly}
      />

      {ownerProofWorkspaceId && isVolumetricLettersTemplate(draft.template_code) ? (
        <div className="shrink-0 border-b border-wo-border-subtle px-3 py-2 overflow-y-auto max-h-[42vh]">
          <OwnerReadonlyVolumetricProofPanel
            templateCode={draft.template_code}
            workspaceId={ownerProofWorkspaceId}
          />
        </div>
      ) : null}

      {readOnly ? (
        <div className="flex items-center gap-2 px-4 py-2 bg-amber-900/15 border-b border-amber-800/30 text-[11px] text-amber-300 shrink-0">
          <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
          Șablon arhivat — vizualizare read-only. Nu este activ pentru ofertă sau Pricing.
        </div>
      ) : null}

      <div className="flex flex-1 min-h-0 flex-col xl:flex-row">
        <div
          className={`flex flex-col min-w-0 min-h-0 ${
            studioTab === "structure"
              ? "xl:flex-[7] xl:border-r border-wo-border-subtle"
              : studioTab === "operational" || studioTab === "form-system"
                ? "flex-1"
                : "flex-1"
          }`}
        >
          <div className="flex items-center justify-between px-4 py-2 bg-wo-surface-raised border-b border-wo-border-subtle shrink-0">
            <div className="flex gap-1 bg-wo-surface-inset p-1 rounded-lg border border-wo-border-subtle">
              <button
                type="button"
                onClick={() => setStudioTab("structure")}
                className={`px-3 py-1.5 rounded-md text-[11px] font-bold transition-colors ${
                  studioTab === "structure"
                    ? "bg-purple-600/30 text-purple-200"
                    : "text-wo-text-muted hover:text-wo-text-secondary"
                }`}
                data-testid="product-system-studio-tab-compiler"
              >
                {PRODUCT_COMPILER_LABEL}
              </button>
              <button
                type="button"
                onClick={() => setStudioTab("operational")}
                className={`px-3 py-1.5 rounded-md text-[11px] font-bold transition-colors ${
                  studioTab === "operational"
                    ? "bg-violet-600/30 text-violet-200"
                    : "text-wo-text-muted hover:text-wo-text-secondary"
                }`}
              >
                Resurse operaționale
              </button>
              <button
                type="button"
                onClick={() => setStudioTab("form-system")}
                className={`px-3 py-1.5 rounded-md text-[11px] font-bold transition-colors ${
                  studioTab === "form-system"
                    ? "bg-sky-600/30 text-sky-200"
                    : "text-wo-text-muted hover:text-wo-text-secondary"
                }`}
                data-testid="product-system-form-system-tab"
              >
                Form System
              </button>
              <button
                type="button"
                onClick={() => setStudioTab("general")}
                className={`px-3 py-1.5 rounded-md text-[11px] font-bold transition-colors ${
                  studioTab === "general"
                    ? "bg-purple-600/30 text-purple-200"
                    : "text-wo-text-muted hover:text-wo-text-secondary"
                }`}
              >
                Informații generale
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-4 scrollbar-thin">
            {studioTab === "structure"
              ? structurePanel
              : studioTab === "operational"
                ? (
                    <TemplateOperationMappingPanel operations={templateOperations} />
                  )
                : studioTab === "form-system"
                  ? (
                      isNew ? (
                        <div className="text-[11px] text-wo-text-muted">
                          Form System este disponibil după salvarea template-ului.
                        </div>
                      ) : (
                        <FormSystemAdminPanel templateCode={draft.template_code} />
                      )
                    )
                  : generalTabPanel}
          </div>
        </div>

        {studioTab === "structure" ? (
          <div className="flex flex-col min-h-0 min-w-0 flex-1 xl:flex-[3] xl:min-w-[300px] xl:max-w-[38%] border-t xl:border-t-0 border-wo-border-subtle">
            <ComponentDetailInsightPanel
              selectedComponent={selectedComponent}
              selectedIndex={selectedComponentIndex}
              typeDisplayLabel={selectedTypeLabel}
              templateCode={draft.template_code}
              validation={validation}
              preview={<ProductPreviewPanel draft={draft} compact />}
              materialsByCode={materialsByCode}
            />
          </div>
        ) : null}
      </div>
    </div>
  );
}

function loadModeChipLabel(mode: "api" | "mock" | "empty_real" | "auth_required" | "error") {
  switch (mode) {
    case "mock":
      return "DEV MOCK";
    case "api":
    case "empty_real":
      return "Live DB";
    default:
      return "API indisponibil";
  }
}

function productSystemLoadModeToSource(
  mode: "api" | "mock" | "empty_real" | "auth_required" | "error",
): SourceState {
  switch (mode) {
    case "api":
      return "db";
    case "empty_real":
      return "empty";
    case "mock":
      return "mock";
    case "auth_required":
    case "error":
      return "error";
    default:
      return "error";
  }
}

function ProductSystemLibraryMoreMenu({
  onCreateTemplate,
  readOnly = false,
}: {
  onCreateTemplate: () => void;
  readOnly?: boolean;
}) {
  const [open, setOpen] = useState(false);
  if (readOnly) return null;

  return (
    <div className="relative">
      <button
        type="button"
        data-testid="product-system-library-more-menu"
        aria-label="More catalog actions"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
        className="rounded border border-wo-border-strong bg-wo-surface-inset p-1.5 text-wo-text-secondary transition-colors hover:bg-wo-hover"
      >
        <MoreHorizontal className="h-3.5 w-3.5" />
      </button>
      {open ? (
        <div className="absolute right-0 top-full z-20 mt-0.5 min-w-[12rem] rounded border border-slate-800 bg-wo-surface-inset p-1 shadow-lg">
          <p className="px-2 py-1 text-[9px] font-semibold uppercase tracking-wide text-wo-text-muted">
            Design-time (admin)
          </p>
          <button
            type="button"
            data-testid="product-system-library-create-template"
            onClick={() => {
              onCreateTemplate();
              setOpen(false);
            }}
            className="block w-full rounded px-2 py-1 text-left text-[11px] text-wo-text-primary hover:bg-wo-hover"
          >
            Șablon nou
          </button>
          <p
            data-testid="product-system-library-design-time-note"
            className="px-2 pb-1 text-[10px] leading-snug text-wo-text-muted"
          >
            Admin design-time only — not operator quoting
          </p>
          <div className="my-1 border-t border-slate-800" />
          <Link
            to="/product-system/blueprint-dossier"
            data-testid="product-system-library-blueprint-link"
            className="block rounded px-2 py-1 text-[11px] text-wo-text-primary hover:bg-wo-hover"
            onClick={() => setOpen(false)}
          >
            Blueprint Dossier
          </Link>
        </div>
      ) : null}
    </div>
  );
}

function ProductSystemInfoPopover({
  loadMode,
  catalogCounts = {
    activeProducts: 0,
    candidateProducts: 0,
    internalModules: 0,
    sharedComponents: 0,
    archivedExperimental: 0,
  },
  compact = false,
}: {
  loadMode: "api" | "mock" | "empty_real" | "auth_required" | "error";
  catalogCounts?: {
    activeProducts: number;
    candidateProducts: number;
    internalModules: number;
    sharedComponents: number;
    archivedExperimental: number;
  };
  compact?: boolean;
}) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className={
            compact
              ? "rounded border border-wo-border-strong bg-wo-surface-inset p-1.5 text-wo-text-secondary transition-colors hover:bg-wo-hover"
              : "flex items-center gap-1.5 px-3 py-2 bg-wo-surface-inset hover:bg-wo-hover text-wo-text-secondary border border-wo-border-strong rounded-lg text-[12px] font-semibold transition-colors"
          }
          aria-label="Informații ProductSystem"
        >
          <Info className="w-3.5 h-3.5" /> {compact ? null : "Info"}
        </button>
      </PopoverTrigger>
      <PopoverContent
        align="end"
        className="w-[min(22rem,calc(100vw-2rem))] border-slate-700 bg-wo-surface-raised p-4 text-wo-text-primary shadow-xl"
      >
        <p className="text-[12px] font-bold text-wo-text-primary mb-2">Cum funcționează?</p>
        <ul className="space-y-2 text-[11px] text-wo-text-muted leading-relaxed list-disc pl-4">
          <li>
            Fiecare produs este definit ca un <strong className="text-purple-300">șablon</strong>{" "}
            format din <strong className="text-blue-300">componente</strong>.
          </li>
          <li>
            Componentele conțin <strong className="text-blue-300">operații</strong> și{" "}
            <strong className="text-emerald-300">materiale</strong> necesare producției.
          </li>
          <li>
            Șablonul este folosit în{" "}
            <Link
              to="/intake-v6/operator"
              data-testid="product-system-page-intake-v6-link"
              className="text-purple-300 underline underline-offset-2 hover:text-purple-200"
            >
              Intake V6
            </Link>{" "}
            (downstream) — Oferta client nu se formează aici.
          </li>
          <li>
            Validarea completă a șablonului se face în pașii următori (ofertare, comenzi, prețuri).
          </li>
          <li>
            ProductSystem este zona de <strong className="text-amber-300/90">configurare șablon</strong>{" "}
            — structură produs, materiale și operații.
          </li>
          <li>
            Șabloanele nu se șterg din interfață; se <strong className="text-wo-text-secondary">arhivează</strong>{" "}
            pentru a păstra istoricul.
          </li>
        </ul>
        <p className="mt-3 text-[10px] text-wo-text-muted border-t border-slate-700/80 pt-3">
          Prețurile și ofertele folosesc aceste șabloane în modulele dedicate — fără modificarea datelor
          istorice.
        </p>
        <p className="mt-2 text-[10px] text-wo-text-dim">
          Sursă date: <span className="text-wo-text-muted">{loadModeChipLabel(loadMode)}</span>
          {" Â· "}
          {catalogCounts.activeProducts} produse ofertabile Â· {catalogCounts.candidateProducts} in pregatire Â· {catalogCounts.internalModules} module interne
        </p>
      </PopoverContent>
    </Popover>
  );
}

// ============================================================
// MAIN PAGE
// ============================================================
export default function ProductSystem() {
  type TemplateLoadMode = "api" | "mock" | "empty_real" | "auth_required" | "error";
  const navigate = useNavigate();
  const { templateCode: routeTemplateCode } = useParams<{ templateCode?: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const { operatorReadOnly, shellMode } = useProductSystemShell();
  const requestedTemplateCode = resolveRequestedTemplateCode({
    pathTemplateCode: routeTemplateCode,
    queryTemplateCode: searchParams.get("template"),
  });
  const [templates, setTemplates] = useState<ProductTemplateEntity[]>([]);
  const [availabilityItems, setAvailabilityItems] = useState<ProductTemplateAvailabilityItem[]>([]);
  const [families, setFamilies] = useState<ProductFamily[]>([]);
  const [materials, setMaterials] = useState<InventoryMaterialEntity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const [loadMode, setLoadMode] = useState<TemplateLoadMode>("api");
  const [screen, setScreen] = useState<ProductSystemScreen>(getInitialProductSystemScreen);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [draft, setDraft] = useState<DraftTemplate | null>(null);
  const [isNew, setIsNew] = useState(false);
  const [saving, setSaving] = useState(false);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [catalogSearch, setCatalogSearch] = useState("");

  const useLegacyCatalog = isPsLegacyCatalogEnabled(searchParams);

  const handleRequestedTemplateCodeChange = useCallback(
    (templateCode: string | null) => {
      if (shellMode) {
        const legacySuffix = useLegacyCatalog ? "?ps_legacy=1" : "";
        if (templateCode) {
          navigate(
            `${buildProductSystemProductDetailPath(templateCode)}${legacySuffix}`,
            { replace: false },
          );
        } else {
          navigate(`/product-system/products${legacySuffix}`, { replace: false });
        }
        return;
      }
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          if (templateCode) {
            next.set("template", templateCode);
          } else {
            next.delete("template");
          }
          if (useLegacyCatalog) {
            next.set("ps_legacy", "1");
          }
          return next;
        },
        { replace: false },
      );
    },
    [navigate, setSearchParams, shellMode, useLegacyCatalog],
  );

  const loadTemplates = useCallback(async (): Promise<ProductTemplateEntity[]> => {
    setLoading(true);
    setError(null);
    setWarning(null);
    setLoadMode("api");

    const useMock = isMockEnabled();
    let loaded: ProductTemplateEntity[] = [];

    try {
      const [templateResult, famRes, matRes, availabilityRes] = await Promise.allSettled([
        productTemplatesApi.list(),
        productFamiliesApi.list({ limit: 500, sort: "label" }),
        materialsApi.list({}, { limit: 500, sort: "code" }),
        productTemplateAvailabilityApi.list({
          offerable_only: false,
          include_runtime_modules: true,
          include_archived: true,
        }),
      ]);

      // Handle families (non-critical) — fall back to mock if API fails
      const famItems = famRes.status === "fulfilled"
        ? Array.isArray(famRes.value?.items) ? famRes.value.items : []
        : [];
      if (famItems.length > 0) {
        setFamilies(famItems);
      } else if (useMock) {
        setFamilies(mockProductFamilies() as unknown as ProductFamily[]);
      } else {
        setFamilies([]);
      }

      // Handle materials (non-critical)
      if (matRes.status === "fulfilled") {
        setMaterials(Array.isArray(matRes.value) ? matRes.value : []);
      } else {
        setMaterials([]);
      }

      if (availabilityRes.status === "fulfilled") {
        setAvailabilityItems(Array.isArray(availabilityRes.value.items) ? availabilityRes.value.items : []);
      } else {
        setAvailabilityItems([]);
      }

      // Handle templates (critical)
      if (templateResult.status === "fulfilled") {
        const apiTemplates = templateResult.value;
        if (apiTemplates.length > 0) {
          loaded = apiTemplates;
          setTemplates(apiTemplates);
          setLoadMode("api");
        } else if (useMock) {
          // API responded successfully with an empty list — keep true empty state.
          loaded = [];
          setTemplates([]);
          setLoadMode("empty_real");
        } else {
          loaded = [];
          setTemplates([]);
          setLoadMode("empty_real");
        }
      } else {
        const err = templateResult.reason;
        const errMsg = err instanceof Error ? err.message : String(err);
        const isAuthError = /40[13]/.test(errMsg) || /unauthorized|forbidden|permisiune/i.test(errMsg);
        if (useMock) {
          // Mock enabled — always fall back to mock data on API failure
          loaded = mockTemplatesToEntities() as unknown as ProductTemplateEntity[];
          setTemplates(loaded);
          setWarning("DEV MOCK DATA — aceste date nu vin din API real.");
          setLoadMode("mock");
        } else if (isAuthError) {
          loaded = [];
          setTemplates([]);
          setError("Nu ai permisiune să accesezi șabloanele. Autentifică-te și reîncearcă.");
          setLoadMode("auth_required");
        } else {
          console.error("Failed to load product templates", err);
          loaded = [];
          setTemplates([]);
          setError("Nu s-au putut încărca șabloanele. Verifică conexiunea la backend.");
          setLoadMode("error");
        }
      }
    } catch (e) {
      // Fallback for unexpected errors
      const errMsg = e instanceof Error ? e.message : String(e);
      const isAuthError = /40[13]/.test(errMsg) || /unauthorized|forbidden|permisiune/i.test(errMsg);

      if (useMock) {
        loaded = mockTemplatesToEntities() as unknown as ProductTemplateEntity[];
        setTemplates(loaded);
        setFamilies(mockProductFamilies() as unknown as ProductFamily[]);
        setMaterials([]);
        setAvailabilityItems([]);
        setWarning("DEV MOCK DATA — aceste date nu vin din API real.");
        setLoadMode("mock");
      } else if (isAuthError) {
        loaded = [];
        setTemplates([]);
        setFamilies([]);
        setMaterials([]);
        setAvailabilityItems([]);
        setWarning("Lipsă sesiune / autentificare necesară pentru API real.");
        setLoadMode("auth_required");
      } else {
        console.error("Failed to load product templates", e);
        loaded = [];
        setTemplates([]);
        setAvailabilityItems([]);
        setError("Nu s-au putut încărca șabloanele. Verifică conexiunea la backend.");
        setLoadMode("error");
      }
    } finally {
      setLoading(false);
    }
    return loaded;
  }, []);

  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  useEffect(() => {
    if (!message) return;
    const t = setTimeout(() => setMessage(null), 3000);
    return () => clearTimeout(t);
  }, [message]);

  const activeOwnerCount = filterActiveTemplatesForQuote(templates).length;
  const archivedCount = filterArchivedExperimentalTemplates(templates).length;
  const catalogCounts = useMemo(
    () => ({
      activeProducts: availabilityItems.filter((item) => item.display_group === "active_products").length,
      candidateProducts: availabilityItems.filter((item) => item.display_group === "candidate_products").length,
      internalModules: availabilityItems.filter((item) => item.display_group === "internal_modules").length,
      sharedComponents: availabilityItems.filter((item) => item.display_group === "shared_components").length,
      archivedExperimental: availabilityItems.filter((item) => item.display_group === "archived_experimental").length,
    }),
    [availabilityItems]
  );
  const selectedAvailability = draft
    ? availabilityItems.find((item) => item.template_code.trim().toUpperCase() === draft.template_code.trim().toUpperCase()) ?? null
    : null;

  const materialsByCode = useMemo(() => {
    const m = new Map<string, InventoryMaterialEntity>();
    materials.forEach((row) => m.set(row.code, row));
    return m;
  }, [materials]);

  const hasCandidateModuleProdusCandidate = useMemo(
    () =>
      buildCandidateModuleProdusReadonlySetModel(templates, availabilityItems, CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE) !=
      null,
    [templates, availabilityItems],
  );

  const ownerDecisionRequiredCount = useMemo(
    () => availabilityItems.filter((item) => item.owner_decision_required).length,
    [availabilityItems],
  );

  const candidateModuleProdusCompleteness = useMemo(
    () => assessCandidateModuleProdusLiveCompleteness(templates),
    [templates],
  );

  const editorReadOnly = useMemo(() => {
    if (operatorReadOnly) return true;
    if (isNew || !selectedId) return false;
    const entity = templates.find((t) => t.id === selectedId);
    return entity ? !isTemplateEditableForQuote(entity) : false;
  }, [isNew, operatorReadOnly, selectedId, templates]);

  const handleBackToLibrary = useCallback(() => {
    setScreen("library");
    setDraft(null);
    setSelectedId(null);
    setIsNew(false);
    setPickerOpen(false);
  }, []);

  const handleOpenEditor = useCallback((t: ProductTemplateEntity) => {
    if (operatorReadOnly) return;
    recordTemplateOpened(t.id);
    setSelectedId(t.id);
    setDraft(entityToDraft(t));
    setIsNew(false);
    setScreen("editor");
    setPickerOpen(false);
  }, [operatorReadOnly]);

  const handleNew = () => {
    if (operatorReadOnly) return;
    setSelectedId(null);
    setDraft(emptyDraft());
    setIsNew(true);
    setScreen("editor");
  };

  const handleCancel = () => {
    if (!isNew && selectedId) {
      const t = templates.find((x) => x.id === selectedId);
      if (t) {
        setDraft(entityToDraft(t));
        return;
      }
    }
    if (isNew) {
      handleBackToLibrary();
      return;
    }
    handleBackToLibrary();
  };

  const handleSave = async () => {
    if (!draft) return;
    const structuralErrors = validateTemplateComponentsStrict(draft.components);
    if (structuralErrors.length > 0) {
      console.warn("Strict validation errors (save blocked):", structuralErrors);
      setMessage({
        type: "error",
        text:
          `Salvarea blocată — ${structuralErrors.length} eroare(i) structurale: ` +
          structuralErrors
            .slice(0, 3)
            .map((e) => `${e.path} [${e.code}]`)
            .join("; ") +
          (structuralErrors.length > 3 ? "..." : ""),
      });
      return;
    }
    setSaving(true);
    try {
      const payload = draftToPayload(draft);
      let savedId: number | null = null;
      if (isNew) {
        const created = await productTemplatesApi.create(payload);
        savedId = created.id;
        setMessage({ type: "success", text: `Șablon creat: ${created.template_code}` });
      } else if (draft.id) {
        await productTemplatesApi.update(draft.id, payload);
        savedId = draft.id;
        setMessage({ type: "success", text: `Șablon actualizat: ${draft.template_code}` });
      }
      const list = await loadTemplates();
      const refreshed = savedId != null ? list.find((t) => t.id === savedId) : null;
      if (refreshed) {
        handleOpenEditor(refreshed);
      } else {
        handleBackToLibrary();
      }
    } catch (e) {
      console.error("Save failed", e);
      setMessage({ type: "error", text: "Salvarea a eșuat. Verifică consola pentru detalii." });
    } finally {
      setSaving(false);
    }
  };

  const handleArchive = async () => {
    if (!draft?.id) return;
    const entity = templates.find((t) => t.id === draft.id);
    if (!entity) return;
    const policy = getTemplateArchivePolicy(entity, activeOwnerCount);
    if (!policy.canArchive) {
      setMessage({
        type: "error",
        text: policy.blockReason ?? "Arhivarea nu este permisă pentru acest șablon.",
      });
      return;
    }
    if (
      !confirm(
        `Arhivezi șablonul ${draft.template_code}?\n\nȘablonul va fi mutat în Arhivate și nu va mai apărea în fluxurile active de ofertare. Datele rămân păstrate.`
      )
    ) {
      return;
    }
    setSaving(true);
    try {
      const payload = draftToPayload({ ...draft, active: false });
      await productTemplatesApi.update(draft.id, payload);
      setMessage({ type: "success", text: `Șablon arhivat: ${draft.template_code}` });
      await loadTemplates();
      handleBackToLibrary();
    } catch (e) {
      console.error("Archive failed", e);
      setMessage({ type: "error", text: "Arhivarea a eșuat. Verifică consola pentru detalii." });
    } finally {
      setSaving(false);
    }
  };

  const editorArchivePolicy = useMemo(() => {
    if (!draft?.id) {
      return { isArchivedForQuote: false, canArchive: false, blockReason: null };
    }
    const entity = templates.find((t) => t.id === draft.id);
    if (!entity) {
      return { isArchivedForQuote: false, canArchive: false, blockReason: null };
    }
    return getTemplateArchivePolicy(entity, activeOwnerCount);
  }, [draft?.id, templates, activeOwnerCount]);

  return (
    <div
      className="space-y-4"
      data-testid="product-system-products-page"
      data-canonical-template-code={routeTemplateCode ?? undefined}
    >
      {shouldShowLibraryScreen(screen) && useLegacyCatalog ? (
        <div className="space-y-2 rounded-xl border border-slate-800/60 bg-slate-950/20 p-3" data-testid="product-system-library-header">
          <div className="flex flex-wrap items-center gap-2 lg:flex-nowrap">
            <div className="flex min-w-0 items-center gap-2">
              {!shellMode ? (
                <Link
                  to="/dashboard"
                  className="shrink-0 rounded-md border border-slate-800 p-2 text-wo-text-muted transition-colors hover:border-slate-700 hover:text-wo-text-secondary"
                  aria-label="Înapoi la Dashboard"
                >
                  <ArrowLeft className="h-4 w-4" />
                </Link>
              ) : null}
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  {shellMode ? (
                    <h2
                      className="truncate text-sm font-semibold leading-tight text-wo-text-primary"
                      data-testid="product-system-products-title"
                    >
                      Catalog vechi (intern)
                    </h2>
                  ) : (
                    <h1 className="truncate text-base font-bold leading-tight text-wo-text-primary">Produse și șabloane</h1>
                  )}
                  <SourceBadge source={productSystemLoadModeToSource(loadMode)} />
                  <span
                    className="rounded border border-amber-800/40 bg-amber-950/20 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-200/90"
                    data-testid="product-system-legacy-catalog-badge"
                  >
                    Legacy
                  </span>
                </div>
              </div>
            </div>

            <div className="flex min-w-[12rem] flex-1 items-center gap-2 rounded-md border border-wo-border-subtle bg-wo-surface-inset px-2.5 py-1.5 lg:max-w-md">
              <Search className="h-3.5 w-3.5 shrink-0 text-wo-text-muted" />
              <input
                type="text"
                value={catalogSearch}
                onChange={(event) => setCatalogSearch(event.target.value)}
                placeholder="Caută cod, familie, descriere…"
                data-testid="product-system-unified-search"
                className="w-full bg-transparent text-sm text-wo-text-primary outline-none placeholder:text-wo-text-muted"
              />
            </div>

            <div className="flex shrink-0 items-center gap-1.5">
              <Link
                to="/product-system/products"
                data-testid="product-system-return-v2-link"
                className="rounded-md border border-sky-800/50 px-2 py-1.5 text-[11px] font-medium text-sky-200 hover:bg-sky-950/30"
              >
                Înapoi la V2
              </Link>
              <button
                onClick={loadTemplates}
                disabled={loading}
                aria-label="Reîncarcă"
                data-testid="product-system-reload-icon"
                className="rounded-md border border-wo-border-strong bg-wo-surface-inset p-2 text-wo-text-secondary transition-colors hover:bg-wo-hover disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              </button>
              <ProductSystemInfoPopover loadMode={loadMode} catalogCounts={catalogCounts} compact />
              <ProductSystemLibraryMoreMenu onCreateTemplate={handleNew} readOnly={operatorReadOnly} />
            </div>
          </div>
          <ProductSystemSpineBand testId="product-system-catalog-overview" />
          {loadMode === "mock" || loadMode === "auth_required" || loadMode === "error" ? (
            <p className="rounded-lg border border-amber-800/30 bg-amber-950/15 px-3 py-2 text-sm text-amber-300/90">
              {loadMode === "mock"
                ? "Mod previzualizare — date mock, nu API live."
                : loadMode === "auth_required"
                  ? "Autentificare necesară pentru șabloane reale."
                  : "Încărcarea șabloanelor a eșuat — reîncarcă sau verifică backend-ul."}
            </p>
          ) : null}
        </div>
      ) : shouldShowLibraryScreen(screen) && !useLegacyCatalog ? (
        <div
          className="flex flex-wrap items-center justify-end gap-2"
          data-testid="product-system-v2-page-toolbar"
        >
          {/* No second title here — shell owns "Product System"; workspace owns the spine once. */}
          <span className="sr-only" data-testid="product-system-products-title">
            Product System workspace
          </span>
          <SourceBadge source={productSystemLoadModeToSource(loadMode)} />
          <button
            onClick={loadTemplates}
            disabled={loading}
            aria-label="Reîncarcă"
            data-testid="product-system-reload-icon"
            className="rounded-md border border-wo-border-strong bg-wo-surface-inset p-2 text-wo-text-secondary transition-colors hover:bg-wo-hover disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <ProductSystemInfoPopover loadMode={loadMode} catalogCounts={catalogCounts} compact />
          {!operatorReadOnly ? (
            <ProductSystemLibraryMoreMenu onCreateTemplate={handleNew} readOnly={operatorReadOnly} />
          ) : null}
          {loadMode === "mock" || loadMode === "auth_required" || loadMode === "error" ? (
            <p className="w-full rounded-lg border border-amber-800/30 bg-amber-950/15 px-3 py-2 text-sm text-amber-300/90">
              {loadMode === "mock"
                ? "Mod previzualizare — date mock, nu API live."
                : loadMode === "auth_required"
                  ? "Autentificare necesară pentru șabloane reale."
                  : "Încărcarea șabloanelor a eșuat — reîncarcă sau verifică backend-ul."}
            </p>
          ) : null}
        </div>
      ) : (
        <>
          <div className="flex items-center gap-2 text-[10px] text-wo-text-muted">
            <Link
              to="/dashboard"
              className="flex items-center gap-1 hover:text-wo-text-secondary transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" /> Dashboard
            </Link>
            <ChevronRight className="w-3 h-3" />
            <span className="text-wo-text-secondary">
              {shouldShowEditorScreen(screen, draft)
                ? "ProductSystem / Editor șablon"
                : "ProductSystem / Șabloane"}
              </span>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <div className="p-1.5 bg-purple-500/10 rounded-lg shrink-0">
                <Package className="w-5 h-5 text-purple-400" />
              </div>
              <div className="min-w-0">
                <h1 className="text-[16px] font-bold text-wo-text-primary leading-tight">
                  {shouldShowEditorScreen(screen, draft)
                    ? "ProductSystem / Editor șablon"
                    : "Catalog produse și șabloane"}
                </h1>
                {shouldShowEditorScreen(screen, draft) ? (
                  <p className="text-[10px] text-wo-text-muted mt-0.5">Editor pentru structura șablonului selectat.</p>
                ) : null}
                {loadMode === "mock" || loadMode === "auth_required" || loadMode === "error" ? (
                  <p className="text-[10px] text-amber-400/90 mt-0.5">
                    {loadMode === "mock"
                      ? "Mod previzualizare — date mock, nu API live."
                      : loadMode === "auth_required"
                        ? "Autentificare necesară pentru șabloane reale."
                        : "Încărcarea șabloanelor a eșuat — reîncarcă sau verifică backend."}
                  </p>
                ) : null}
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-1.5 shrink-0">
              <SourceBadge source={productSystemLoadModeToSource(loadMode)} />
              <ProductSystemInfoPopover
                loadMode={loadMode}
                catalogCounts={catalogCounts}
              />
              {!operatorReadOnly ? (
                <Link
                  to="/product-system/blueprint-dossier"
                  className="flex items-center gap-1.5 px-3 py-2 bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 rounded-lg text-[12px] font-bold transition-colors"
                >
                  <Layers className="w-3.5 h-3.5" /> Blueprint Dossier
                </Link>
              ) : null}
              <button
                onClick={loadTemplates}
                disabled={loading}
                className="flex items-center gap-1.5 px-3 py-2 border border-wo-border-strong bg-wo-surface-raised hover:bg-wo-hover text-wo-text-primary rounded-lg text-[12px] font-semibold transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} /> Reîncarcă
              </button>
              {!operatorReadOnly ? (
              <button
                onClick={handleNew}
                className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-[12px] font-bold transition-colors shadow-lg shadow-emerald-900/20"
              >
                <Plus className="w-3.5 h-3.5" /> Șablon Nou
              </button>
              ) : null}
            </div>
          </div>
        </>
      )}

      {/* Message toast */}
      {message && (
        <div
          className={`flex items-center gap-2 px-4 py-3 rounded-xl border transition-all ${
            message.type === "success"
              ? "bg-emerald-900/20 border-emerald-800/40 text-emerald-300"
              : "bg-red-900/20 border-red-800/40 text-red-300"
          }`}
        >
          {message.type === "success" ? <CheckCircle2 className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
          <span className="text-[12px] font-semibold">{message.text}</span>
        </div>
      )}

      {/* Warning state (dev/preview mode) */}
      {warning && !loading && (
        <div className="flex items-center gap-2 px-4 py-3 bg-amber-900/15 border border-amber-800/30 rounded-xl">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          <p className="text-[12px] text-amber-300">{warning}</p>
          <button
            onClick={loadTemplates}
            className="ml-auto text-[11px] text-amber-300 hover:text-amber-200 underline"
          >
            Reîncarcă
          </button>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="flex items-center gap-2 px-4 py-3 bg-red-900/15 border border-red-800/30 rounded-xl">
          <AlertTriangle className="w-4 h-4 text-red-400" />
          <p className="text-[12px] text-red-300">{error}</p>
          <button
            onClick={loadTemplates}
            className="ml-auto text-[11px] text-red-300 hover:text-red-200 underline"
          >
            Reîncarcă
          </button>
        </div>
      )}

      <div className="min-h-0 min-w-0 w-full xl:max-h-[calc(100vh-132px)]">
        {shouldShowEditorScreen(screen, draft) && draft ? (
          <TemplateEditor
            key={selectedId ?? (isNew ? "new" : draft.template_code)}
            draft={draft}
            isNew={isNew}
            onChange={setDraft}
            onSave={handleSave}
            onCancel={handleCancel}
            onArchive={isNew || editorReadOnly ? undefined : handleArchive}
            archivePolicy={editorArchivePolicy}
            onChangeTemplate={() => setPickerOpen(true)}
            onBackToLibrary={handleBackToLibrary}
            readOnly={editorReadOnly}
            saving={saving}
            families={families}
            materials={materials}
            availability={selectedAvailability}
            allTemplates={templates}
            availabilityItems={availabilityItems}
            ownerProofWorkspaceId={
              searchParams.get("owner_proof") === "1" ? searchParams.get("workspace_id") : null
            }
          />
        ) : loadMode === "auth_required" && !loading ? (
          <div className="bg-wo-surface-raised border border-amber-800/30 rounded-xl p-12 text-center">
            <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto mb-2" />
            <p className="text-[12px] text-amber-300 font-semibold">
              Lipsă sesiune / autentificare necesară pentru API real.
            </p>
            <p className="text-[11px] text-amber-400/80 mt-1">
              Product System nu poate valida șabloanele reale fără autentificare.
            </p>
          </div>
        ) : shouldShowLibraryScreen(screen) && useLegacyCatalog ? (
          <ProductSystemCanonicalCatalog
            templates={templates}
            availabilityItems={availabilityItems}
            loading={loading}
            search={catalogSearch}
            onSearchChange={setCatalogSearch}
            requestedTemplateCode={requestedTemplateCode}
            onRequestedTemplateCodeChange={handleRequestedTemplateCodeChange}
            onOpenTemplate={handleOpenEditor}
          />
        ) : shouldShowLibraryScreen(screen) ? (
          <ProductSystemV2Workspace
            templates={templates}
            availabilityItems={availabilityItems}
            loading={loading}
            search={catalogSearch}
            onSearchChange={setCatalogSearch}
            requestedTemplateCode={requestedTemplateCode}
            onRequestedTemplateCodeChange={handleRequestedTemplateCodeChange}
            onOpenTemplate={operatorReadOnly ? undefined : handleOpenEditor}
          />
        ) : null}
      </div>

      <TemplateSelectorSheet
        open={pickerOpen}
        onOpenChange={setPickerOpen}
        templates={templates}
        selectedId={selectedId}
        onSelect={handleOpenEditor}
      />
    </div>
  );
}
