import { useState, useCallback, useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useInventoryData } from "@/hooks/useInventoryData";
import {
  physicalSheets,
  standardSheetFormats,
  isPlateMaterial,
  isRollMaterial,
  getAvailableSheets,
  type InventoryMaterial,
  type StockStatus,
  type PhysicalSheet,
  type SheetType,
  type SheetStatus,
} from "@/lib/mockData";
import {
  onJobCompleted,
  topUpReservoir,
  recalibrateMaterial,
  sendPurchaseDraft,
  checkAndGenerateDraftOrders,
  getInkReservoirs,
  getPurchaseDrafts,
  getEventLog,
  getPendingJobs,
  getCompletedJobs,
  needsRecalibration,
  applyWasteMarkup,
  type EngineEvent,
  type PurchaseDraft,
  type InkReservoir,
  type JobConsumptionRecord,
} from "@/lib/inventoryEngine";
import { SectionHeader } from "@/components/workos/SharedComponents";
import RecalibrationModal from "@/components/workos/RecalibrationModal";
import InventorySheetQualityPanel from "@/components/inventory/InventorySheetQualityPanel";
import StockMovementsPanel from "@/components/inventory/StockMovementsPanel";
import { CncProcessableBadge } from "@/components/workos/CncProcessableBadge";
import { materialCarriesCncProcessableBadge } from "@/lib/cnc/cncProcessableBadge";
import {
  misleadingCodeNoteRo,
  normalizePricingDisplayName,
} from "@/lib/pricing/pricingDisplayNaming";
import { buildSheetQualityMaterialUrl } from "@/utils/inventorySheetQualityLinks";
import {
  Warehouse,
  AlertTriangle,
  Search,
  Package,
  TrendingDown,
  Clock,
  Star,
  Truck,
  ArrowUpDown,
  Layers,
  RectangleHorizontal,
  Scissors,
  ChevronRight,
  Ruler,
  Grid3X3,
  CircleDot,
  Cylinder,
  Droplets,
  Play,
  CheckCircle2,
  FileText,
  Send,
  RotateCcw,
  Activity,
  Beaker,
  ShoppingCart,
  Zap,
  ChevronDown,
  ChevronUp,
  Database,
  Loader2,
  Info,
} from "lucide-react";

// ── Status configs ──────────────────────────────────────────
const stockStatusConfig: Record<StockStatus, { label: string; cls: string; dotCls: string }> = {
  ok: { label: "În stoc", cls: "text-emerald-400", dotCls: "bg-emerald-500" },
  low: { label: "Scăzut", cls: "text-amber-400", dotCls: "bg-amber-500" },
  critical: { label: "Critic", cls: "text-red-400", dotCls: "bg-red-500 animate-pulse" },
  out_of_stock: { label: "Epuizat", cls: "text-red-500", dotCls: "bg-red-600 animate-pulse" },
  untracked: { label: "Stoc neurmărit", cls: "text-slate-400", dotCls: "bg-slate-500" },
};

const sheetTypeConfig: Record<SheetType, { label: string; cls: string; icon: React.ReactNode }> = {
  full_sheet: { label: "Placă întreagă", cls: "bg-blue-900/40 text-blue-300 border-blue-700", icon: <RectangleHorizontal className="w-3 h-3" /> },
  remnant: { label: "Rest / Remnant", cls: "bg-amber-900/40 text-amber-300 border-amber-700", icon: <Scissors className="w-3 h-3" /> },
};

const sheetStatusConfig: Record<SheetStatus, { label: string; cls: string }> = {
  available: { label: "Disponibil", cls: "text-emerald-400" },
  reserved: { label: "Rezervat", cls: "text-amber-400" },
  in_use: { label: "În lucru", cls: "text-blue-400" },
};

// ── Tab type ────────────────────────────────────────────────
type InventoryTab = "all" | "placi" | "role" | "altele" | "cerneala" | "automatizare" | "sheet_quality";

function parseInventoryTabFromUrl(value: string | null): InventoryTab | null {
  if (!value) return null;
  if (value === "sheet-quality") return "sheet_quality";
  const valid: InventoryTab[] = [
    "all",
    "placi",
    "role",
    "altele",
    "cerneala",
    "automatizare",
    "sheet_quality",
  ];
  return valid.includes(value as InventoryTab) ? (value as InventoryTab) : null;
}

function inventoryTabToUrlValue(value: InventoryTab): string {
  if (value === "sheet_quality") return "sheet-quality";
  return value;
}

// ── Helper: material category icon ─────────────────────────
function CategoryIcon({ category }: { category: string }) {
  switch (category) {
    case "Plăci": return <Layers className="w-3.5 h-3.5 text-blue-400" />;
    case "Rolă": return <Cylinder className="w-3.5 h-3.5 text-teal-400" />;
    case "Electric": return <CircleDot className="w-3.5 h-3.5 text-amber-400" />;
    case "Consumabile": return <TrendingDown className="w-3.5 h-3.5 text-purple-400" />;
    case "Metal": return <Grid3X3 className="w-3.5 h-3.5 text-slate-400" />;
    default: return <Package className="w-3.5 h-3.5 text-slate-400" />;
  }
}

// ── Stock bar ───────────────────────────────────────────────
function StockBar({ current, min, max }: { current: number | null; min: number; max: number }) {
  if (current === null || current === undefined) {
    return (
      <div className="relative w-full" title="Stoc neurmărit">
        <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden border border-dashed border-slate-600" />
      </div>
    );
  }
  const safeMax = max > 0 ? max : 1;
  const pct = Math.min((current / safeMax) * 100, 100);
  const minPct = (min / safeMax) * 100;
  const color = current <= 0 ? "bg-red-600" : current <= min ? "bg-red-500" : current <= min * 1.5 ? "bg-amber-500" : "bg-emerald-500";

  return (
    <div className="relative w-full">
      <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
        <div className={`${color} h-2 rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
      </div>
      <div className="absolute top-0 w-px h-2 bg-amber-400/60" style={{ left: `${minPct}%` }} title={`Min: ${min}`} />
    </div>
  );
}

// ── Reservoir bar ───────────────────────────────────────────
function ReservoirBar({ current, capacity }: { current: number; capacity: number }) {
  const pct = Math.min((current / capacity) * 100, 100);
  const color = pct <= 15 ? "bg-red-500" : pct <= 35 ? "bg-amber-500" : "bg-cyan-500";

  return (
    <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
      <div className={`${color} h-3 rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
    </div>
  );
}

// ── Sheet visual (mini rectangle proportional) ──────────────
function SheetVisual({ sheet, maxW }: { sheet: PhysicalSheet; maxW: number }) {
  const scale = 60 / maxW;
  const w = Math.max(sheet.widthMM * scale, 8);
  const h = Math.max(sheet.heightMM * scale, 4);
  const isRemnant = sheet.type === "remnant";

  return (
    <div
      className={`rounded-sm border transition-all ${
        isRemnant
          ? "bg-amber-900/30 border-amber-700/50 border-dashed"
          : "bg-blue-900/30 border-blue-700/50"
      }`}
      style={{ width: `${w}px`, height: `${h}px`, minWidth: "8px", minHeight: "4px" }}
      title={`${sheet.widthMM}×${sheet.heightMM}mm — ${sheetTypeConfig[sheet.type].label}`}
    />
  );
}

// ── Plate detail panel ──────────────────────────────────────
function PlateDetailPanel({ material }: { material: InventoryMaterial }) {
  const sheets = getAvailableSheets(material.id);
  const fullSheets = sheets.filter((s) => s.type === "full_sheet");
  const remnants = sheets.filter((s) => s.type === "remnant");
  const totalAreaM2 = sheets.reduce((sum, s) => sum + (s.widthMM * s.heightMM) / 1_000_000, 0);
  const maxDim = Math.max(...sheets.map((s) => s.widthMM), 1);

  const formats = standardSheetFormats.find((f) => f.materialId === material.id);

  return (
    <div className="space-y-4">
      <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
        <div className="flex items-center gap-2 mb-3">
          <Layers className="w-4 h-4 text-blue-400" />
          <span className="text-[14px] font-bold text-slate-200">
            {normalizePricingDisplayName(material.id, material.name)}
          </span>
          {materialCarriesCncProcessableBadge(material.id) ? (
            <CncProcessableBadge size="sm" testId={`inventory-cnc-badge-detail-${material.id}`} />
          ) : null}
          <span className={`text-[10px] font-semibold ${stockStatusConfig[material.stockStatus].cls}`}>
            ● {stockStatusConfig[material.stockStatus].label}
          </span>
        </div>

        <div className="grid grid-cols-4 gap-3 mb-4">
          <div className="bg-wo-surface-raised rounded-lg p-2 text-center">
            <p className="text-[20px] font-bold text-wo-text-primary">{sheets.length}</p>
            <p className="text-[9px] text-slate-500 uppercase">Plăci Total</p>
          </div>
          <div className="bg-wo-surface-raised rounded-lg p-2 text-center">
            <p className="text-[20px] font-bold text-blue-300">{fullSheets.length}</p>
            <p className="text-[9px] text-slate-500 uppercase">Întregi</p>
          </div>
          <div className="bg-wo-surface-raised rounded-lg p-2 text-center">
            <p className="text-[20px] font-bold text-amber-300">{remnants.length}</p>
            <p className="text-[9px] text-slate-500 uppercase">Resturi</p>
          </div>
          <div className="bg-wo-surface-raised rounded-lg p-2 text-center">
            <p className="text-[20px] font-bold text-wo-text-primary">{totalAreaM2.toFixed(1)}</p>
            <p className="text-[9px] text-slate-500 uppercase">mp Total</p>
          </div>
        </div>

        {formats && (
          <div className="mb-4">
            <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-2">Formate Standard Achiziție</p>
            <div className="flex flex-wrap gap-2">
              {formats.formats.map((f) => (
                <span key={f.label} className="px-2 py-1 text-[11px] bg-slate-800 text-slate-300 rounded border border-slate-700 font-mono">
                  {f.label}
                </span>
              ))}
            </div>
          </div>
        )}

        <div>
          <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-2">Hartă Plăci (proporțional)</p>
          <div className="flex flex-wrap gap-2 items-end p-3 bg-wo-surface-inset rounded-lg border border-wo-border-subtle min-h-[60px]">
            {sheets.map((sheet) => (
              <SheetVisual key={sheet.sheetId} sheet={sheet} maxW={maxDim} />
            ))}
            {sheets.length === 0 && (
              <p className="text-[11px] text-slate-600 italic">Nicio placă disponibilă</p>
            )}
          </div>
          <div className="flex items-center gap-4 mt-2 text-[10px] text-slate-500">
            <span className="flex items-center gap-1">
              <span className="w-3 h-2 bg-blue-900/30 border border-blue-700/50 rounded-sm inline-block" /> Placă întreagă
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-2 bg-amber-900/30 border border-amber-700/50 border-dashed rounded-sm inline-block" /> Rest
            </span>
          </div>
        </div>
      </div>

      <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg overflow-hidden">
        <div className="px-4 py-2.5 border-b border-wo-border-subtle bg-wo-surface-inset">
          <p className="text-[12px] font-semibold text-slate-300">Plăci Individuale ({sheets.length})</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-[12px]">
            <thead>
              <tr className="text-slate-500 text-left border-b border-wo-border-subtle">
                <th className="px-4 py-2 font-medium">ID</th>
                <th className="px-4 py-2 font-medium">Dimensiuni</th>
                <th className="px-4 py-2 font-medium">mp</th>
                <th className="px-4 py-2 font-medium">Tip</th>
                <th className="px-4 py-2 font-medium">Status</th>
                <th className="px-4 py-2 font-medium">Locație</th>
                <th className="px-4 py-2 font-medium">Notă</th>
              </tr>
            </thead>
            <tbody>
              {sheets.map((sheet) => {
                const tCfg = sheetTypeConfig[sheet.type];
                const sCfg = sheetStatusConfig[sheet.status];
                const areaMp = (sheet.widthMM * sheet.heightMM) / 1_000_000;
                return (
                  <tr key={sheet.sheetId} className="border-b border-wo-border-subtle/50 hover:bg-wo-surface-raised/50 transition-colors">
                    <td className="px-4 py-2 font-mono text-slate-400">{sheet.sheetId}</td>
                    <td className="px-4 py-2">
                      <span className="font-mono text-slate-200">{sheet.widthMM}×{sheet.heightMM}</span>
                      <span className="text-slate-500 ml-1">mm</span>
                    </td>
                    <td className="px-4 py-2 text-slate-300 font-mono">{areaMp.toFixed(2)}</td>
                    <td className="px-4 py-2">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-semibold rounded border ${tCfg.cls}`}>
                        {tCfg.icon}
                        {tCfg.label}
                      </span>
                    </td>
                    <td className="px-4 py-2">
                      <span className={`text-[11px] font-medium ${sCfg.cls}`}>● {sCfg.label}</span>
                    </td>
                    <td className="px-4 py-2 text-slate-500">{sheet.location}</td>
                    <td className="px-4 py-2 text-slate-500 text-[11px]">{sheet.label || "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ── Ink Reservoir Card ──────────────────────────────────────
function InkReservoirCard({
  reservoir,
  onTopUp,
  materials,
}: {
  reservoir: InkReservoir;
  onTopUp: (materialId: string) => void;
  materials: InventoryMaterial[];
}) {
  const pct = Math.round((reservoir.currentML / reservoir.capacityML) * 100);
  const material = materials.find((m) => m.id === reservoir.materialId);
  const shelfStock = material?.stockCurrent ?? 0;

  // Color based on ink type
  const inkColors: Record<string, string> = {
    "MAT-014": "cyan",
    "MAT-015": "pink",
    "MAT-016": "yellow",
    "MAT-017": "slate",
  };
  const inkColor = inkColors[reservoir.materialId] || "blue";
  const borderColor = `border-${inkColor}-700/50`;
  const bgColor = pct <= 15 ? "bg-red-900/20" : pct <= 35 ? "bg-amber-900/10" : "bg-wo-surface-raised";

  return (
    <div className={`${bgColor} border border-wo-border-strong rounded-lg p-3`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Droplets className={`w-4 h-4 ${pct <= 15 ? "text-red-400" : pct <= 35 ? "text-amber-400" : "text-cyan-400"}`} />
          <div>
            <p className="text-[12px] font-semibold text-slate-200">{reservoir.materialName.replace("Cerneală solvent ", "")}</p>
            <p className="text-[10px] text-slate-500 font-mono">{reservoir.materialId}</p>
          </div>
        </div>
        <span className={`text-[11px] font-bold ${pct <= 15 ? "text-red-400" : pct <= 35 ? "text-amber-400" : "text-cyan-300"}`}>
          {pct}%
        </span>
      </div>

      <ReservoirBar current={reservoir.currentML} capacity={reservoir.capacityML} />

      <div className="flex items-center justify-between mt-2">
        <div className="text-[10px] text-slate-500">
          <span className="font-mono text-slate-300">{reservoir.currentML}</span> / {reservoir.capacityML} ml
        </div>
        <div className="text-[10px] text-slate-500">
          Raft: <span className="font-mono text-slate-300">{shelfStock}L</span>
        </div>
      </div>

      <button
        onClick={() => onTopUp(reservoir.materialId)}
        disabled={shelfStock < 1}
        className="mt-2 w-full flex items-center justify-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold bg-cyan-900/30 border border-cyan-700/40 text-cyan-300 rounded-lg hover:bg-cyan-900/50 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
      >
        <Beaker className="w-3.5 h-3.5" />
        +1L Bulk
      </button>
    </div>
  );
}

// ── Event Log Item ──────────────────────────────────────────
function EventLogItem({ event }: { event: EngineEvent }) {
  const iconMap: Record<string, React.ReactNode> = {
    stock_deducted: <TrendingDown className="w-3.5 h-3.5 text-red-400" />,
    topup: <Beaker className="w-3.5 h-3.5 text-cyan-400" />,
    recalibration: <RotateCcw className="w-3.5 h-3.5 text-blue-400" />,
    draft_created: <FileText className="w-3.5 h-3.5 text-amber-400" />,
    job_completed: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />,
  };

  return (
    <div className="flex items-start gap-2 px-3 py-2 border-b border-wo-border-subtle/50 last:border-0">
      <div className="mt-0.5 shrink-0">{iconMap[event.type] || <Activity className="w-3.5 h-3.5 text-slate-500" />}</div>
      <div className="flex-1 min-w-0">
        <p className="text-[11px] text-slate-300 leading-relaxed">{event.message}</p>
        <p className="text-[9px] text-slate-600 font-mono mt-0.5">
          {new Date(event.timestamp).toLocaleString("ro-RO")}
        </p>
      </div>
    </div>
  );
}

// ── Purchase Draft Row ──────────────────────────────────────
function PurchaseDraftRow({
  draft,
  onSend,
}: {
  draft: PurchaseDraft;
  onSend: (draftId: string) => void;
}) {
  return (
    <tr className="border-b border-wo-border-subtle/50 hover:bg-wo-surface-raised/50 transition-colors">
      <td className="px-4 py-2.5">
        <span className="font-mono text-[11px] text-slate-400">{draft.id}</span>
      </td>
      <td className="px-4 py-2.5">
        <p className="text-slate-200 text-[12px] font-medium">{draft.materialName}</p>
      </td>
      <td className="px-4 py-2.5 text-[12px] text-slate-300 font-mono">
        {draft.suggestedQuantity} {draft.unit}
      </td>
      <td className="px-4 py-2.5 text-[12px] text-slate-400">{draft.supplierName}</td>
      <td className="px-4 py-2.5 text-[12px] font-mono text-slate-300">
        {draft.estimatedCost.toLocaleString("ro-RO")} RON
      </td>
      <td className="px-4 py-2.5">
        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
          draft.urgency === "urgent"
            ? "bg-red-900/30 text-red-300 border border-red-700/40"
            : "bg-slate-800 text-slate-400 border border-slate-700"
        }`}>
          {draft.urgency === "urgent" ? "⚡ Urgent" : "Normal"}
        </span>
      </td>
      <td className="px-4 py-2.5">
        <span className={`text-[10px] font-semibold ${
          draft.status === "draft" ? "text-amber-400" : draft.status === "sent" ? "text-blue-400" : "text-emerald-400"
        }`}>
          {draft.status === "draft" ? "Draft" : draft.status === "sent" ? "Trimis" : "Confirmat"}
        </span>
      </td>
      <td className="px-4 py-2.5">
        {draft.status === "draft" && (
          <button
            onClick={() => onSend(draft.id)}
            className="flex items-center gap-1 px-2 py-1 text-[10px] font-semibold bg-blue-900/30 border border-blue-700/40 text-blue-300 rounded hover:bg-blue-900/50 transition-colors"
          >
            <Send className="w-3 h-3" />
            Trimite
          </button>
        )}
      </td>
    </tr>
  );
}

// ── Main Inventory Page ─────────────────────────────────────
export default function Inventory() {
  const [searchParams, setSearchParams] = useSearchParams();
  // ── Real data from backend (with mock fallback) ──
  const { materials: inventoryMaterials, suppliers, source: dataSource, loading: dataLoading, error: dataError } = useInventoryData();
  const isMockSource = dataSource === "mock";

  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<InventoryTab>(() => parseInventoryTabFromUrl(searchParams.get("tab")) || "all");
  const [filterStatus, setFilterStatus] = useState<StockStatus | "all">("all");
  const [sortBy, setSortBy] = useState<"name" | "stock" | "days">("days");
  const [selectedPlate, setSelectedPlate] = useState<InventoryMaterial | null>(null);

  // Engine state — force re-render via counter
  const [renderTick, setRenderTick] = useState(0);
  const forceUpdate = useCallback(() => setRenderTick((t) => t + 1), []);

  // Recalibration modal state
  const [recalModal, setRecalModal] = useState<{ materialId: string; materialName: string; currentStock: number; unit: string } | null>(null);

  // Collapsible sections
  const [showEventLog, setShowEventLog] = useState(true);

  const urlTab = parseInventoryTabFromUrl(searchParams.get("tab"));
  useEffect(() => {
    if (urlTab && urlTab !== activeTab) {
      setActiveTab(urlTab);
    }
  }, [activeTab, urlTab]);

  function setInventoryTab(tab: InventoryTab) {
    setActiveTab(tab);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set("tab", inventoryTabToUrlValue(tab));
      return next;
    });
  }

  // Read engine state
  const reservoirs = getInkReservoirs();
  const drafts = getPurchaseDrafts();
  const events = getEventLog();
  const pendingJobs = getPendingJobs();
  const completedJobs = getCompletedJobs();

  // Categorize materials from live category (not obsolete mock IDs).
  const plateMaterials = inventoryMaterials.filter((m) => m.uiTabCategory === "placi");
  const rollMaterials = inventoryMaterials.filter((m) => m.uiTabCategory === "role");
  const inkMaterials = inventoryMaterials.filter((m) => m.uiTabCategory === "cerneala");
  const otherMaterials = inventoryMaterials.filter((m) => m.uiTabCategory === "altele" || !m.uiTabCategory);

  const criticalCount = inventoryMaterials.filter((m) => m.stockStatus === "critical" || m.stockStatus === "out_of_stock").length;
  const lowCount = inventoryMaterials.filter((m) => m.stockStatus === "low").length;
  const untrackedCount = inventoryMaterials.filter((m) => m.stockStatus === "untracked").length;
  const missingPriceCount = inventoryMaterials.filter(
    (m) => m.unitCost === null || m.unitCost === undefined || m.registryStatus === "missing_price"
  ).length;
  const trackedStockValue = inventoryMaterials.reduce((sum, m) => {
    if (m.stockCurrent === null || m.unitCost === null || m.unitCost === undefined) return sum;
    return sum + m.stockCurrent * m.unitCost;
  }, 0);

  const totalSheets = isMockSource ? physicalSheets.filter((s) => s.status === "available").length : 0;
  const totalFullSheets = isMockSource ? physicalSheets.filter((s) => s.status === "available" && s.type === "full_sheet").length : 0;
  const totalRemnants = isMockSource ? physicalSheets.filter((s) => s.status === "available" && s.type === "remnant").length : 0;

  // Filter materials based on tab
  let materialsToShow = inventoryMaterials;
  if (activeTab === "placi") materialsToShow = plateMaterials;
  else if (activeTab === "role") materialsToShow = rollMaterials;
  else if (activeTab === "cerneala") materialsToShow = inkMaterials;
  else if (activeTab === "altele") materialsToShow = otherMaterials;
  else if (activeTab === "automatizare") materialsToShow = isMockSource ? [] : inventoryMaterials;
  else if (activeTab === "sheet_quality") materialsToShow = [];

  let filtered = materialsToShow.filter((m) => {
    if (filterStatus !== "all" && m.stockStatus !== filterStatus) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return m.name.toLowerCase().includes(q) || m.id.toLowerCase().includes(q) || m.supplier.toLowerCase().includes(q);
    }
    return true;
  });

  filtered = [...filtered].sort((a, b) => {
    if (sortBy === "name") return a.name.localeCompare(b.name);
    if (sortBy === "stock") {
      const av = a.stockCurrent;
      const bv = b.stockCurrent;
      if (av === null && bv === null) return 0;
      if (av === null) return 1;
      if (bv === null) return -1;
      return av - bv;
    }
    return a.daysUntilEmpty - b.daysUntilEmpty;
  });

  // ── Handlers ────────────────────────────────────────────
  function handleJobComplete(jobId: string) {
    const result = onJobCompleted(jobId);
    if (!result.success) {
      alert(result.error || "Eroare la finalizare job.");
      return;
    }
    // Check for materials needing recalibration
    inventoryMaterials.forEach((m) => {
      if (needsRecalibration(m.id)) {
        setRecalModal({ materialId: m.id, materialName: m.name, currentStock: m.stockCurrent ?? 0, unit: m.unit });
      }
    });
    forceUpdate();
  }

  function handleTopUp(materialId: string) {
    const result = topUpReservoir(materialId);
    if (!result.success) {
      alert(result.message);
      return;
    }
    forceUpdate();
  }

  function handleSendDraft(draftId: string) {
    const result = sendPurchaseDraft(draftId);
    if (!result.success) {
      alert(result.message);
      return;
    }
    forceUpdate();
  }

  function handleRecalConfirmEmpty() {
    if (!recalModal) return;
    recalibrateMaterial(recalModal.materialId, 0, "Operator");
    setRecalModal(null);
    forceUpdate();
  }

  function handleRecalSetValue(newValue: number) {
    if (!recalModal) return;
    recalibrateMaterial(recalModal.materialId, newValue, "Operator");
    setRecalModal(null);
    forceUpdate();
  }

  // ── Loading state ─────────────────────────────────────────
  if (dataLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 text-cyan-400 animate-spin" />
        <span className="ml-2 text-slate-400 text-sm">Se încarcă inventarul...</span>
      </div>
    );
  }

  // ── Render ────────────────────────────────────────────────
  return (
    <div className="space-y-4">
      {/* Recalibration Modal */}
      {recalModal && (
        <RecalibrationModal
          materialId={recalModal.materialId}
          materialName={recalModal.materialName}
          currentStock={recalModal.currentStock}
          unit={recalModal.unit}
          onConfirmEmpty={handleRecalConfirmEmpty}
          onRecalibrate={handleRecalSetValue}
          onDismiss={() => setRecalModal(null)}
        />
      )}

      {/* Header */}
      <div className="flex items-center gap-2">
        <Warehouse className="w-5 h-5 text-cyan-400" />
        <h1 className="text-[18px] font-bold text-wo-text-primary">Inventar & OC</h1>
        <span className="text-[10px] text-slate-500 bg-slate-800 px-2 py-0.5 rounded-full ml-1">
          {inventoryMaterials.length} materiale{isMockSource ? ` • ${totalSheets} plăci fizice` : ""}
        </span>
        {dataSource === "db" ? (
          <span className="text-[10px] text-emerald-500 bg-emerald-900/20 px-2 py-0.5 rounded-full border border-emerald-800/30 flex items-center gap-1">
            <Database className="w-3 h-3" /> Live DB
          </span>
        ) : (
          <span className="text-[10px] text-amber-500 bg-amber-900/20 px-2 py-0.5 rounded-full border border-amber-800/30">
            Mock Data
          </span>
        )}
        {isMockSource ? (
          <span className="text-[10px] text-emerald-500 bg-emerald-900/20 px-2 py-0.5 rounded-full border border-emerald-800/30">
            <Zap className="w-3 h-3 inline mr-0.5" />
            Motor Automatizare Activ
          </span>
        ) : (
          <span className="text-[10px] text-amber-500 bg-amber-900/20 px-2 py-0.5 rounded-full border border-amber-800/30">
            <AlertTriangle className="w-3 h-3 inline mr-0.5" />
            Automatizare locală dezactivată în live mode
          </span>
        )}
      </div>

      <p className="text-[12px] text-slate-400 -mt-2">
        Inventar &amp; OC = stoc, furnizori, recepții și consum. Prețurile de achiziție de aici sunt operaționale — pentru calculul de ofertă folosiți{" "}
        <Link to="/inventory/pricing" className="text-cyan-400 hover:underline">
          Pricing Registry
        </Link>
        .
      </p>

      {dataError && dataSource !== "mock" && (
        <div className="flex items-center gap-2 px-4 py-2.5 bg-red-900/20 border border-red-800/40 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
          <p className="text-[12px] text-red-300">Eroare backend inventar: {dataError}</p>
        </div>
      )}

      {!isMockSource && (
        <div className="flex items-start gap-2 px-4 py-2.5 bg-amber-900/15 border border-amber-800/30 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
          <p className="text-[12px] text-amber-300/90">
            Preview-ul de plăci fizice, rezervoare și draft-uri automate folosește motor local mock și este blocat în live mode.
          </p>
        </div>
      )}

      {/* Alert Banner — only confirmed critical/zero stock (not untracked). */}
      {criticalCount > 0 && (
        <div className="flex items-center gap-2 px-4 py-2.5 bg-red-900/20 border border-red-800/40 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
          <p className="text-[12px] text-red-300">
            <strong>{criticalCount} material(e) cu stoc confirmat critic / epuizat</strong> — necesită reaprovizionare urgentă.
            {lowCount > 0 && <span className="text-amber-400 ml-2">+ {lowCount} cu stoc scăzut</span>}
          </p>
          {isMockSource && drafts.filter((d) => d.status === "draft").length > 0 && (
            <span className="ml-auto text-[10px] text-amber-300 bg-amber-900/30 px-2 py-0.5 rounded border border-amber-700/40">
              {drafts.filter((d) => d.status === "draft").length} draft(uri) comandă generate
            </span>
          )}
        </div>
      )}
      {(untrackedCount > 0 || missingPriceCount > 0) && (
        <div className="flex items-start gap-2 px-4 py-2.5 bg-slate-900/40 border border-slate-700/50 rounded-lg">
          <Info className="w-4 h-4 text-slate-400 mt-0.5 shrink-0" />
          <p className="text-[12px] text-slate-300">
            {untrackedCount > 0 && (
              <span>
                <strong>{untrackedCount}</strong> cu stoc neurmărit (nu înseamnă epuizat).{" "}
              </span>
            )}
            {missingPriceCount > 0 && (
              <span>
                <strong>{missingPriceCount}</strong> cu cost achiziție lipsă — rămân vizibile / selectabile; calcul comercial blocat separat.
              </span>
            )}
          </p>
        </div>
      )}

      {/* Summary KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div className="bg-wo-surface-raised border border-wo-border-strong border-t-2 border-t-cyan-500 rounded-lg px-4 py-3">
          <p className="text-[10px] text-slate-400 uppercase tracking-wide">Total Materiale</p>
          <p className="text-[20px] font-bold text-wo-text-primary mt-1">{inventoryMaterials.length}</p>
        </div>
        <div className="bg-wo-surface-raised border border-wo-border-strong border-t-2 border-t-blue-500 rounded-lg px-4 py-3">
          <p className="text-[10px] text-slate-400 uppercase tracking-wide">Plăci Fizice</p>
          <div className="flex items-baseline gap-2 mt-1">
            <p className="text-[20px] font-bold text-blue-300">{totalFullSheets}</p>
            <p className="text-[11px] text-amber-400">+{totalRemnants} resturi</p>
          </div>
        </div>
        <div className="bg-wo-surface-raised border border-wo-border-strong border-t-2 border-t-red-500 rounded-lg px-4 py-3">
          <p className="text-[10px] text-slate-400 uppercase tracking-wide">Critice / Epuizate</p>
          <p className="text-[20px] font-bold text-red-400 mt-1">{criticalCount}</p>
        </div>
        <div className="bg-wo-surface-raised border border-wo-border-strong border-t-2 border-t-amber-500 rounded-lg px-4 py-3">
          <p className="text-[10px] text-slate-400 uppercase tracking-wide">Stoc Scăzut</p>
          <p className="text-[20px] font-bold text-amber-400 mt-1">{lowCount}</p>
        </div>
        <div className="bg-wo-surface-raised border border-wo-border-strong border-t-2 border-t-emerald-500 rounded-lg px-4 py-3">
          <p className="text-[10px] text-slate-400 uppercase tracking-wide">Valoare Stoc (urmărit)</p>
          <p className="text-[16px] font-bold text-emerald-400 mt-1">
            {trackedStockValue.toLocaleString("ro-RO")} RON
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-1 w-fit flex-wrap">
        {([
          { key: "all" as InventoryTab, label: "Toate", count: inventoryMaterials.length, icon: <Package className="w-3.5 h-3.5" /> },
          { key: "placi" as InventoryTab, label: "Plăci", count: plateMaterials.length, icon: <Layers className="w-3.5 h-3.5" /> },
          { key: "role" as InventoryTab, label: "Role", count: rollMaterials.length, icon: <Cylinder className="w-3.5 h-3.5" /> },
          { key: "cerneala" as InventoryTab, label: "Cerneală", count: inkMaterials.length, icon: <Droplets className="w-3.5 h-3.5" /> },
          { key: "altele" as InventoryTab, label: "Altele", count: otherMaterials.length, icon: <Grid3X3 className="w-3.5 h-3.5" /> },
          { key: "sheet_quality" as InventoryTab, label: "Sheet Quality", count: 0, icon: <FileText className="w-3.5 h-3.5" /> },
            { key: "automatizare" as InventoryTab, label: "Automatizare", count: pendingJobs.length, icon: <Zap className="w-3.5 h-3.5" />, disabled: !isMockSource, tooltip: "Disponibil doar în modul mock" },
        ] as { key: InventoryTab; label: string; count: number; icon: React.ReactNode; disabled?: boolean; tooltip?: string }[]).map((tab) => (
          <button
            key={tab.key}
            onClick={() => {
              if (!tab.disabled) {
                setInventoryTab(tab.key);
                setSelectedPlate(null);
              }
            }}
            disabled={tab.disabled}
            title={tab.tooltip}
            className={`px-3 py-1.5 rounded-md text-[12px] font-semibold transition-colors flex items-center gap-1.5 ${
              tab.disabled
                ? "text-slate-600 cursor-not-allowed opacity-50"
                : activeTab === tab.key
                  ? "bg-blue-600/20 text-blue-400"
                  : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {tab.icon}
            {tab.label}
            <span className="text-[10px] opacity-60">({tab.count})</span>
            {tab.disabled && (
              <span className="text-[8px] uppercase tracking-wider bg-slate-800 text-slate-500 px-1.5 py-0.5 rounded ml-0.5">Draft</span>
            )}
          </button>
        ))}
      </div>

      {/* ═══ AUTOMATION TAB ═══ */}
      {activeTab === "automatizare" && isMockSource && (
        <div className="space-y-4">
          {/* Ink Reservoirs */}
          <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
            <SectionHeader title="Rezervoare Cerneală (Printer)" count={reservoirs.length} icon={<Droplets className="w-4 h-4" />} />
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
              {reservoirs.map((r) => (
                <InkReservoirCard key={r.materialId} reservoir={r} onTopUp={handleTopUp} materials={inventoryMaterials} />
              ))}
            </div>
          </div>

          {/* Pending Jobs — Simulate Completion */}
          <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
            <SectionHeader title="Job-uri în Așteptare (Simulare ColorGate)" count={pendingJobs.length} icon={<Play className="w-4 h-4" />} />
            {pendingJobs.length === 0 ? (
              <p className="text-[12px] text-slate-500 italic">Toate job-urile au fost finalizate.</p>
            ) : (
              <div className="space-y-2">
                {pendingJobs.map((job) => (
                  <div key={job.jobId} className="flex items-center gap-3 bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[12px] text-blue-300 font-semibold">{job.jobId}</span>
                        <span className="text-[11px] text-slate-400">•</span>
                        <span className="text-[12px] text-slate-300">{job.client}</span>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-0.5">{job.product}</p>
                      <div className="flex flex-wrap gap-2 mt-1.5">
                        {job.consumptions.map((c, i) => {
                          const mat = inventoryMaterials.find((m) => m.id === c.materialId);
                          const actual = applyWasteMarkup(c.quantityUsed, c.materialId);
                          const hasMarkup = isPlateMaterial(c.materialId) || isRollMaterial(c.materialId);
                          return (
                            <span key={i} className="text-[10px] px-1.5 py-0.5 bg-slate-800 text-slate-400 rounded border border-slate-700 font-mono">
                              {mat?.name.substring(0, 20) || c.materialId}: -{actual.toFixed(2)} {c.unit}
                              {hasMarkup && <span className="text-amber-500 ml-0.5">(+10%)</span>}
                            </span>
                          );
                        })}
                      </div>
                    </div>
                    <button
                      onClick={() => handleJobComplete(job.jobId)}
                      className="shrink-0 flex items-center gap-1.5 px-3 py-2 text-[11px] font-semibold bg-emerald-900/30 border border-emerald-700/40 text-emerald-300 rounded-lg hover:bg-emerald-900/50 transition-colors"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      Finalizează Job
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Completed Jobs */}
          {completedJobs.length > 0 && (
            <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
              <SectionHeader title="Job-uri Finalizate" count={completedJobs.length} icon={<CheckCircle2 className="w-4 h-4" />} />
              <div className="space-y-1.5">
                {completedJobs.map((job) => (
                  <div key={job.jobId} className="flex items-center gap-3 px-3 py-2 bg-emerald-900/10 border border-emerald-800/20 rounded-lg">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                    <span className="font-mono text-[11px] text-emerald-300">{job.jobId}</span>
                    <span className="text-[11px] text-slate-400">{job.client} — {job.product}</span>
                    <span className="ml-auto text-[9px] text-slate-600 font-mono">
                      {job.completedAt ? new Date(job.completedAt).toLocaleString("ro-RO") : ""}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Purchase Drafts */}
          <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
            <SectionHeader title="Draft Comenzi Aprovizionare" count={drafts.length} icon={<ShoppingCart className="w-4 h-4" />} />
            {drafts.length === 0 ? (
              <p className="text-[12px] text-slate-500 italic">Nu există draft-uri de comenzi. Stocurile sunt suficiente.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-[12px]">
                  <thead>
                    <tr className="text-slate-500 text-left border-b border-wo-border-subtle">
                      <th className="px-4 py-2 font-medium">ID</th>
                      <th className="px-4 py-2 font-medium">Material</th>
                      <th className="px-4 py-2 font-medium">Cantitate</th>
                      <th className="px-4 py-2 font-medium">Furnizor</th>
                      <th className="px-4 py-2 font-medium">Cost Est.</th>
                      <th className="px-4 py-2 font-medium">Urgență</th>
                      <th className="px-4 py-2 font-medium">Status</th>
                      <th className="px-4 py-2 font-medium w-24"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {drafts.map((draft) => (
                      <PurchaseDraftRow key={draft.id} draft={draft} onSend={handleSendDraft} />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Event Log */}
          <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg">
            <button
              onClick={() => setShowEventLog(!showEventLog)}
              className="w-full flex items-center justify-between px-4 py-3 text-left"
            >
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-slate-400" />
                <span className="text-[13px] font-semibold text-slate-300">Jurnal Evenimente Motor</span>
                <span className="text-[10px] text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded">{events.length}</span>
              </div>
              {showEventLog ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
            </button>
            {showEventLog && (
              <div className="border-t border-wo-border-subtle max-h-64 overflow-y-auto">
                {events.length === 0 ? (
                  <p className="px-4 py-3 text-[12px] text-slate-500 italic">Niciun eveniment încă. Finalizați un job pentru a vedea activitatea.</p>
                ) : (
                  events.slice(0, 30).map((evt) => <EventLogItem key={evt.id} event={evt} />)
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ═══ INVENTORY SHEET QUALITY TAB ═══ */}
      {activeTab === "sheet_quality" && <InventorySheetQualityPanel />}

      {/* ═══ STANDARD INVENTORY TABS ═══ */}
      {activeTab !== "automatizare" && activeTab !== "sheet_quality" && (
        <>
          {/* Filters */}
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-2 bg-wo-surface-raised border border-wo-border-subtle rounded-lg px-3 py-2 flex-1 max-w-sm focus-within:border-blue-500/50">
              <Search className="w-4 h-4 text-slate-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Caută material, furnizor..."
                className="bg-transparent text-[13px] text-slate-200 placeholder:text-slate-600 outline-none w-full"
              />
            </div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as StockStatus | "all")}
              className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg px-3 py-2 text-[12px] text-slate-300 outline-none"
            >
              <option value="all">Toate statusurile</option>
              <option value="ok">OK</option>
              <option value="low">Scăzut</option>
              <option value="critical">Critic</option>
              <option value="out_of_stock">Epuizat</option>
              <option value="untracked">Stoc neurmărit</option>
            </select>
            <button
              onClick={() => setSortBy(sortBy === "days" ? "stock" : sortBy === "stock" ? "name" : "days")}
              className="flex items-center gap-1 px-3 py-2 bg-wo-surface-raised border border-wo-border-subtle rounded-lg text-[12px] text-slate-400 hover:text-slate-200 transition-colors"
            >
              <ArrowUpDown className="w-3.5 h-3.5" />
              {sortBy === "days" ? "Zile rămase" : sortBy === "stock" ? "Stoc curent" : "Nume"}
            </button>
            <span className="text-[11px] text-slate-500 ml-auto">{filtered.length} rezultate</span>
          </div>

          {/* Ink Reservoirs (shown on cerneala tab) */}
          {activeTab === "cerneala" && isMockSource && (
            <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
              <SectionHeader title="Rezervoare Cerneală (Printer)" count={reservoirs.length} icon={<Droplets className="w-4 h-4" />} />
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
                {reservoirs.map((r) => (
                  <InkReservoirCard key={r.materialId} reservoir={r} onTopUp={handleTopUp} materials={inventoryMaterials} />
                ))}
              </div>
            </div>
          )}

          {/* Main content area */}
          <div className={`grid gap-4 ${isMockSource && (activeTab === "placi" || (activeTab === "all" && selectedPlate)) ? "grid-cols-1 lg:grid-cols-3" : "grid-cols-1"}`}>
            {/* Materials Table */}
            <div className={`${isMockSource && (activeTab === "placi" || (activeTab === "all" && selectedPlate)) ? "lg:col-span-2" : ""}`}>
              <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-[12px]">
                    <thead>
                      <tr className="text-slate-500 text-left border-b border-wo-border-subtle bg-wo-surface-inset">
                        <th className="px-4 py-2.5 font-medium">Status</th>
                        <th className="px-4 py-2.5 font-medium">Material</th>
                        <th className="px-4 py-2.5 font-medium">Tip</th>
                        <th className="px-4 py-2.5 font-medium">Stoc</th>
                        <th className="px-4 py-2.5 font-medium w-28">Nivel</th>
                        <th className="px-4 py-2.5 font-medium">Zile</th>
                        <th className="px-4 py-2.5 font-medium">Furnizor</th>
                        {isMockSource && (activeTab === "placi" || activeTab === "all") && (
                          <th className="px-4 py-2.5 font-medium">Plăci</th>
                        )}
                        <th className="px-4 py-2.5 font-medium w-44">Acțiuni</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filtered.map((mat) => {
                        const sCfg = stockStatusConfig[mat.stockStatus];
                        const isPlate = mat.uiTabCategory === "placi" || isPlateMaterial(mat.id);
                        const isRoll = mat.uiTabCategory === "role" || isRollMaterial(mat.id);
                        const isInk = mat.uiTabCategory === "cerneala";
                        const sheets = isMockSource && isPlateMaterial(mat.id) ? getAvailableSheets(mat.id) : [];
                        const fullCount = sheets.filter((s) => s.type === "full_sheet").length;
                        const remnantCount = sheets.filter((s) => s.type === "remnant").length;
                        const isSelected = selectedPlate?.id === mat.id;
                        const needsRecal = needsRecalibration(mat.id);
                        const missingPrice =
                          mat.unitCost === null ||
                          mat.unitCost === undefined ||
                          mat.registryStatus === "missing_price";

                        return (
                          <tr
                            key={mat.id}
                            onClick={() => isMockSource && isPlateMaterial(mat.id) ? setSelectedPlate(isSelected ? null : mat) : undefined}
                            className={`border-b border-wo-border-subtle/50 transition-colors ${
                              isMockSource && isPlateMaterial(mat.id) ? "cursor-pointer" : ""
                            } ${isSelected ? "bg-blue-900/20 border-blue-800/30" : "hover:bg-wo-surface-raised/50"}`}
                          >
                            <td className="px-4 py-2.5">
                              <div className="flex flex-col gap-1">
                                <div className="flex items-center gap-1.5">
                                  <span className={`w-2 h-2 rounded-full ${sCfg.dotCls}`} />
                                  <span className={`text-[11px] font-semibold ${sCfg.cls}`}>{sCfg.label}</span>
                                </div>
                                {missingPrice && (
                                  <span className="text-[10px] text-amber-300/90">Preț lipsă</span>
                                )}
                              </div>
                            </td>
                            <td className="px-4 py-2.5">
                              <div className="flex flex-wrap items-center gap-1.5">
                                <p className="text-slate-200 font-medium">
                                  {normalizePricingDisplayName(mat.id, mat.name)}
                                </p>
                                {materialCarriesCncProcessableBadge(mat.id) ? (
                                  <CncProcessableBadge
                                    size="sm"
                                    testId={`inventory-cnc-badge-${mat.id}`}
                                  />
                                ) : null}
                              </div>
                              <p className="text-[10px] text-slate-500 font-mono">{mat.id}</p>
                              {misleadingCodeNoteRo(mat.id) ? (
                                <p className="mt-0.5 max-w-md text-[10px] leading-snug text-amber-500/80">
                                  {misleadingCodeNoteRo(mat.id)}
                                </p>
                              ) : null}
                            </td>
                            <td className="px-4 py-2.5">
                              <div className="flex items-center gap-1">
                                <CategoryIcon category={mat.category} />
                                <span className="text-[11px] text-slate-400">{mat.category}</span>
                              </div>
                            </td>
                            <td className="px-4 py-2.5">
                              {mat.stockCurrent === null || mat.stockCurrent === undefined ? (
                                <>
                                  <span className={`font-semibold ${sCfg.cls}`}>—</span>
                                  <span className="text-slate-500"> {mat.unit} (neurmărit)</span>
                                </>
                              ) : (
                                <>
                                  <span className={`font-semibold ${sCfg.cls}`}>{mat.stockCurrent}</span>
                                  <span className="text-slate-500"> / {mat.stockMax} {mat.unit}</span>
                                </>
                              )}
                            </td>
                            <td className="px-4 py-2.5">
                              <StockBar current={mat.stockCurrent} min={mat.stockMin} max={mat.stockMax} />
                            </td>
                            <td className="px-4 py-2.5">
                              <span className={`font-semibold ${mat.daysUntilEmpty <= 3 ? "text-red-400" : mat.daysUntilEmpty <= 7 ? "text-amber-400" : "text-slate-300"}`}>
                                {mat.daysUntilEmpty}d
                              </span>
                            </td>
                            <td className="px-4 py-2.5 text-slate-400">{mat.supplier}</td>
                            {isMockSource && (activeTab === "placi" || activeTab === "all") && (
                              <td className="px-4 py-2.5">
                                {isPlate ? (
                                  <div className="flex items-center gap-2">
                                    <span className="flex items-center gap-1 text-[11px]">
                                      <RectangleHorizontal className="w-3 h-3 text-blue-400" />
                                      <span className="text-blue-300 font-semibold">{fullCount}</span>
                                    </span>
                                    {remnantCount > 0 && (
                                      <span className="flex items-center gap-1 text-[11px]">
                                        <Scissors className="w-3 h-3 text-amber-400" />
                                        <span className="text-amber-300 font-semibold">{remnantCount}</span>
                                      </span>
                                    )}
                                  </div>
                                ) : isRoll ? (
                                  <span className="text-[10px] text-teal-400 flex items-center gap-1">
                                    <Cylinder className="w-3 h-3" /> rolă
                                  </span>
                                ) : (
                                  <span className="text-[10px] text-slate-600">—</span>
                                )}
                              </td>
                            )}
                            <td className="px-4 py-2.5">
                              <div className="flex items-center gap-1">
                                <Link
                                  to={buildSheetQualityMaterialUrl(mat.id)}
                                  onClick={(e) => e.stopPropagation()}
                                  className="inline-flex items-center px-2 py-1 text-[10px] font-semibold rounded border border-blue-700/50 text-blue-300 hover:bg-blue-900/30"
                                  title="Deschide Inventory Sheet Quality pentru acest material"
                                >
                                  Sheet Quality
                                </Link>
                                {isPlate && (
                                  <ChevronRight className={`w-4 h-4 transition-transform ${isSelected ? "text-blue-400 rotate-90" : "text-slate-600"}`} />
                                )}
                                {isMockSource && needsRecal && (
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setRecalModal({ materialId: mat.id, materialName: mat.name, currentStock: mat.stockCurrent ?? 0, unit: mat.unit });
                                    }}
                                    className="p-1 text-amber-400 hover:text-amber-300 transition-colors"
                                    title="Recalibrare necesară"
                                  >
                                    <RotateCcw className="w-3.5 h-3.5" />
                                  </button>
                                )}
                                {isMockSource && isInk && (
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleTopUp(mat.id);
                                    }}
                                    className="p-1 text-cyan-400 hover:text-cyan-300 transition-colors"
                                    title="Alimentare +1L Bulk"
                                  >
                                    <Beaker className="w-3.5 h-3.5" />
                                  </button>
                                )}
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Plate Detail Panel */}
            {isMockSource && (activeTab === "placi" || activeTab === "all") && selectedPlate && isPlateMaterial(selectedPlate.id) && (
              <div className="lg:col-span-1">
                <PlateDetailPanel material={selectedPlate} />
              </div>
            )}
          </div>

          {/* Purchase Drafts (shown on all tabs when drafts exist) */}
          {isMockSource && drafts.length > 0 && activeTab !== "cerneala" && (
            <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
              <SectionHeader title="Draft Comenzi Aprovizionare" count={drafts.length} icon={<ShoppingCart className="w-4 h-4" />} />
              <div className="overflow-x-auto">
                <table className="w-full text-[12px]">
                  <thead>
                    <tr className="text-slate-500 text-left border-b border-wo-border-subtle">
                      <th className="px-4 py-2 font-medium">ID</th>
                      <th className="px-4 py-2 font-medium">Material</th>
                      <th className="px-4 py-2 font-medium">Cantitate</th>
                      <th className="px-4 py-2 font-medium">Furnizor</th>
                      <th className="px-4 py-2 font-medium">Cost Est.</th>
                      <th className="px-4 py-2 font-medium">Urgență</th>
                      <th className="px-4 py-2 font-medium">Status</th>
                      <th className="px-4 py-2 font-medium w-24"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {drafts.map((draft) => (
                      <PurchaseDraftRow key={draft.id} draft={draft} onSend={handleSendDraft} />
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Suppliers */}
          <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
            <SectionHeader title="Furnizori" count={suppliers.length} icon={<Truck className="w-4 h-4" />} />
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
              {suppliers.map((sup) => (
                <div key={sup.id} className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-[13px] font-semibold text-slate-200">{sup.name}</p>
                    <div className="flex items-center gap-0.5">
                      {Array.from({ length: 5 }).map((_, i) => (
                        <Star key={i} className={`w-3 h-3 ${i < sup.rating ? "text-amber-400 fill-amber-400" : "text-slate-600"}`} />
                      ))}
                    </div>
                  </div>
                  <p className="text-[11px] text-slate-400">{sup.category}</p>
                  <div className="flex items-center gap-3 mt-2 text-[10px] text-slate-500">
                    <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> Lead: {sup.leadTimeDays}d</span>
                    <span className="flex items-center gap-1"><Package className="w-3 h-3" /> {sup.activeOrders} active</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Stock Movements (BUILD 16) */}
          <StockMovementsPanel />
        </>
      )}
    </div>
  );
}