/**
 * inventoryEngine.ts — Motor central de logică pentru inventarul automatizat.
 *
 * Conține funcții pure care calculează consumul, aplică markup-ul,
 * gestionează top-up-ul și generează alertele de aprovizionare.
 */

import {
  inventoryMaterials,
  suppliers,
  isPlateMaterial,
  isRollMaterial,
  type InventoryMaterial,
  type StockStatus,
} from "./mockData";

// ── Types ───────────────────────────────────────────────────

export interface MaterialConsumption {
  materialId: string;
  quantityUsed: number;
  unit: string;
  source: "colorgate_rip" | "manual" | "operator";
}

export interface JobConsumptionRecord {
  jobId: string;
  client: string;
  product: string;
  consumptions: MaterialConsumption[];
  completedAt: string | null;
}

export interface InkReservoir {
  materialId: string;
  materialName: string;
  currentML: number;
  capacityML: number;
  lastTopUp: string;
}

export type PurchaseDraftStatus = "draft" | "sent" | "confirmed";
export type PurchaseUrgency = "urgent" | "normal";

export interface PurchaseDraft {
  id: string;
  materialId: string;
  materialName: string;
  supplierId: string;
  supplierName: string;
  suggestedQuantity: number;
  unit: string;
  estimatedCost: number;
  urgency: PurchaseUrgency;
  createdAt: string;
  status: PurchaseDraftStatus;
}

export interface RecalibrationEntry {
  materialId: string;
  oldValue: number;
  newValue: number;
  operator: string;
  timestamp: string;
}

export interface EngineEvent {
  id: string;
  type: "stock_deducted" | "topup" | "recalibration" | "draft_created" | "job_completed";
  message: string;
  timestamp: string;
  materialId?: string;
  jobId?: string;
}

// ── Constants ───────────────────────────────────────────────

const PRODUCTION_MARKUP = 1.10; // +10% pierderi tehnice

// ── State (in-memory, simulated) ────────────────────────────

/** Ink reservoirs — virtual tanks inside printers */
const inkReservoirs: InkReservoir[] = [
  { materialId: "MAT-014", materialName: "Cerneală solvent Cyan", currentML: 620, capacityML: 1500, lastTopUp: "2026-04-05T14:00:00" },
  { materialId: "MAT-015", materialName: "Cerneală solvent Magenta", currentML: 880, capacityML: 1500, lastTopUp: "2026-04-04T10:00:00" },
  { materialId: "MAT-016", materialName: "Cerneală solvent Yellow", currentML: 750, capacityML: 1500, lastTopUp: "2026-04-04T10:00:00" },
  { materialId: "MAT-017", materialName: "Cerneală solvent Black", currentML: 340, capacityML: 1500, lastTopUp: "2026-04-06T09:00:00" },
];

/** Job consumption records — simulated ColorGate RIP data */
const jobConsumptions: JobConsumptionRecord[] = [
  {
    jobId: "JOB-0042", client: "Emag", product: "Print autocolant 8mp + laminare",
    completedAt: null,
    consumptions: [
      { materialId: "MAT-014", quantityUsed: 0.35, unit: "litru", source: "colorgate_rip" },
      { materialId: "MAT-015", quantityUsed: 0.28, unit: "litru", source: "colorgate_rip" },
      { materialId: "MAT-016", quantityUsed: 0.30, unit: "litru", source: "colorgate_rip" },
      { materialId: "MAT-017", quantityUsed: 0.42, unit: "litru", source: "colorgate_rip" },
      { materialId: "MAT-005", quantityUsed: 8.0, unit: "ml", source: "manual" },
      { materialId: "MAT-006", quantityUsed: 8.0, unit: "ml", source: "manual" },
    ],
  },
  {
    jobId: "JOB-0039", client: "Penny", product: "Banner mesh 6x3m",
    completedAt: null,
    consumptions: [
      { materialId: "MAT-014", quantityUsed: 0.22, unit: "litru", source: "colorgate_rip" },
      { materialId: "MAT-015", quantityUsed: 0.18, unit: "litru", source: "colorgate_rip" },
      { materialId: "MAT-016", quantityUsed: 0.20, unit: "litru", source: "colorgate_rip" },
      { materialId: "MAT-017", quantityUsed: 0.30, unit: "litru", source: "colorgate_rip" },
      { materialId: "MAT-008", quantityUsed: 18.0, unit: "ml", source: "manual" },
    ],
  },
  {
    jobId: "JOB-0038", client: "Lidl", product: "Colant vitrină 12mp",
    completedAt: null,
    consumptions: [
      { materialId: "MAT-014", quantityUsed: 0.40, unit: "litru", source: "colorgate_rip" },
      { materialId: "MAT-015", quantityUsed: 0.32, unit: "litru", source: "colorgate_rip" },
      { materialId: "MAT-016", quantityUsed: 0.35, unit: "litru", source: "colorgate_rip" },
      { materialId: "MAT-017", quantityUsed: 0.50, unit: "litru", source: "colorgate_rip" },
      { materialId: "MAT-005", quantityUsed: 12.0, unit: "ml", source: "manual" },
      { materialId: "MAT-006", quantityUsed: 12.0, unit: "ml", source: "manual" },
    ],
  },
  {
    jobId: "JOB-0036", client: "Profi", product: "Panou ACP casetat 4x1.5m",
    completedAt: null,
    consumptions: [
      { materialId: "MAT-001", quantityUsed: 6.0, unit: "mp", source: "manual" },
    ],
  },
  {
    jobId: "JOB-0035", client: "OMV", product: "Totem preț carburanți 5m",
    completedAt: null,
    consumptions: [
      { materialId: "MAT-012", quantityUsed: 18.0, unit: "ml", source: "manual" },
      { materialId: "MAT-011", quantityUsed: 12.0, unit: "ml", source: "manual" },
    ],
  },
];

/** Purchase drafts */
const purchaseDrafts: PurchaseDraft[] = [];

/** Event log */
const eventLog: EngineEvent[] = [];

/** Recalibration history */
const recalibrationLog: RecalibrationEntry[] = [];

// ── Helpers ─────────────────────────────────────────────────

let eventCounter = 0;
function nextEventId(): string {
  eventCounter++;
  return `EVT-${String(eventCounter).padStart(4, "0")}`;
}

let draftCounter = 0;
function nextDraftId(): string {
  draftCounter++;
  return `PO-DRAFT-${String(draftCounter).padStart(3, "0")}`;
}

function nowISO(): string {
  return new Date().toISOString();
}

function recalcStatus(mat: InventoryMaterial): void {
  if (mat.stockCurrent <= 0) {
    mat.stockStatus = "out_of_stock";
    mat.daysUntilEmpty = 0;
  } else if (mat.stockCurrent <= mat.stockMin * 0.5) {
    mat.stockStatus = "critical";
    mat.daysUntilEmpty = mat.consumptionRate > 0 ? Math.round(mat.stockCurrent / mat.consumptionRate) : 999;
  } else if (mat.stockCurrent <= mat.stockMin) {
    mat.stockStatus = "low";
    mat.daysUntilEmpty = mat.consumptionRate > 0 ? Math.round(mat.stockCurrent / mat.consumptionRate) : 999;
  } else {
    mat.stockStatus = "ok";
    mat.daysUntilEmpty = mat.consumptionRate > 0 ? Math.round(mat.stockCurrent / mat.consumptionRate) : 999;
  }
}

// ── Core Functions ──────────────────────────────────────────

/**
 * Apply waste markup (+10%) for materials that have technical losses.
 * Plates and rolls get markup; consumables, electric, metal do not.
 */
export function applyWasteMarkup(baseConsumption: number, materialId: string): number {
  if (isPlateMaterial(materialId) || isRollMaterial(materialId)) {
    return baseConsumption * PRODUCTION_MARKUP;
  }
  return baseConsumption;
}

/**
 * Main "brain" function: called when a job is completed.
 * Deducts stock for all consumed materials, applies markup, checks alerts.
 */
export function onJobCompleted(jobId: string): { success: boolean; events: EngineEvent[]; error?: string } {
  const record = jobConsumptions.find((j) => j.jobId === jobId);
  if (!record) {
    return { success: false, events: [], error: `Job ${jobId} nu are date de consum asociate.` };
  }
  if (record.completedAt) {
    return { success: false, events: [], error: `Job ${jobId} a fost deja finalizat la ${record.completedAt}.` };
  }

  const newEvents: EngineEvent[] = [];

  record.consumptions.forEach((consumption) => {
    const material = inventoryMaterials.find((m) => m.id === consumption.materialId);
    if (!material) return;

    // Apply markup for plates/rolls
    const actualQuantity = applyWasteMarkup(consumption.quantityUsed, consumption.materialId);

    // For ink (consumabile litru), deduct from reservoir first
    const isInk = material.category === "Consumabile" && material.unit === "litru";
    if (isInk) {
      const reservoir = inkReservoirs.find((r) => r.materialId === consumption.materialId);
      if (reservoir) {
        const deductML = actualQuantity * 1000; // convert litri to ml
        reservoir.currentML = Math.max(0, reservoir.currentML - deductML);
      }
    }

    // Deduct from main stock
    const oldStock = material.stockCurrent;
    material.stockCurrent = Math.max(0, +(material.stockCurrent - actualQuantity).toFixed(2));
    recalcStatus(material);

    newEvents.push({
      id: nextEventId(),
      type: "stock_deducted",
      message: `${material.name}: -${actualQuantity.toFixed(2)} ${material.unit} (bază: ${consumption.quantityUsed}, markup: ${isPlateMaterial(consumption.materialId) || isRollMaterial(consumption.materialId) ? "+10%" : "0%"})`,
      timestamp: nowISO(),
      materialId: consumption.materialId,
      jobId,
    });
  });

  record.completedAt = nowISO();

  // Job completed event
  newEvents.push({
    id: nextEventId(),
    type: "job_completed",
    message: `Job ${jobId} (${record.client} — ${record.product}) finalizat. Stocuri actualizate.`,
    timestamp: nowISO(),
    jobId,
  });

  // Check for purchase drafts
  const draftEvents = checkAndGenerateDraftOrders();
  newEvents.push(...draftEvents);

  eventLog.push(...newEvents);
  return { success: true, events: newEvents };
}

/**
 * Top-up ink reservoir from bulk stock (shelf bidon → printer tank).
 */
export function topUpReservoir(
  materialId: string,
  amountML: number = 1000
): { success: boolean; message: string; event?: EngineEvent } {
  const material = inventoryMaterials.find((m) => m.id === materialId);
  if (!material) return { success: false, message: "Material negăsit." };

  if (material.stockCurrent < 1) {
    return { success: false, message: `Stoc insuficient pe raft pentru ${material.name}. Stoc curent: ${material.stockCurrent}L.` };
  }

  const reservoir = inkReservoirs.find((r) => r.materialId === materialId);
  if (!reservoir) return { success: false, message: "Rezervor negăsit pentru acest material." };

  if (reservoir.currentML + amountML > reservoir.capacityML) {
    return { success: false, message: `Rezervorul este aproape plin (${reservoir.currentML}/${reservoir.capacityML}ml). Nu se poate adăuga ${amountML}ml.` };
  }

  // Deduct 1L from shelf stock
  material.stockCurrent = +(material.stockCurrent - 1).toFixed(2);
  recalcStatus(material);

  // Add to reservoir
  reservoir.currentML += amountML;
  reservoir.lastTopUp = nowISO();

  const evt: EngineEvent = {
    id: nextEventId(),
    type: "topup",
    message: `${material.name}: +${amountML}ml în rezervor (din bidon raft). Stoc raft: ${material.stockCurrent}L.`,
    timestamp: nowISO(),
    materialId,
  };
  eventLog.push(evt);

  // Check if we need to reorder
  const draftEvents = checkAndGenerateDraftOrders();
  eventLog.push(...draftEvents);

  return { success: true, message: `Alimentare reușită: +${amountML}ml în rezervor. Stoc raft rămas: ${material.stockCurrent}L.`, event: evt };
}

/**
 * Recalibrate material stock — operator enters visual count.
 */
export function recalibrateMaterial(
  materialId: string,
  newValue: number,
  operatorName: string = "Operator"
): { success: boolean; message: string; event?: EngineEvent } {
  const material = inventoryMaterials.find((m) => m.id === materialId);
  if (!material) return { success: false, message: "Material negăsit." };

  const oldValue = material.stockCurrent;
  material.stockCurrent = +newValue.toFixed(2);
  recalcStatus(material);

  recalibrationLog.push({
    materialId,
    oldValue,
    newValue,
    operator: operatorName,
    timestamp: nowISO(),
  });

  const evt: EngineEvent = {
    id: nextEventId(),
    type: "recalibration",
    message: `${material.name}: recalibrat de ${operatorName} — ${oldValue} → ${newValue} ${material.unit}.`,
    timestamp: nowISO(),
    materialId,
  };
  eventLog.push(evt);

  return { success: true, message: `Stoc recalibrat: ${oldValue} → ${newValue} ${material.unit}.`, event: evt };
}

/**
 * Check all materials and generate purchase drafts for those with < 3 days stock.
 */
export function checkAndGenerateDraftOrders(): EngineEvent[] {
  const newEvents: EngineEvent[] = [];

  inventoryMaterials.forEach((material) => {
    if (material.daysUntilEmpty >= 3) return;
    if (material.stockStatus === "ok") return;

    // Check if draft already exists for this material
    const existingDraft = purchaseDrafts.find(
      (d) => d.materialId === material.id && (d.status === "draft" || d.status === "sent")
    );
    if (existingDraft) return;

    // Find supplier
    const supplier = suppliers.find((s) => s.name === material.supplier);
    const suggestedQty = +(material.stockMax - material.stockCurrent).toFixed(2);
    const estimatedCost = +(suggestedQty * material.unitCost).toFixed(2);

    const draft: PurchaseDraft = {
      id: nextDraftId(),
      materialId: material.id,
      materialName: material.name,
      supplierId: supplier?.id || "SUP-??",
      supplierName: material.supplier,
      suggestedQuantity: suggestedQty,
      unit: material.unit,
      estimatedCost,
      urgency: material.daysUntilEmpty <= 1 ? "urgent" : "normal",
      createdAt: nowISO(),
      status: "draft",
    };

    purchaseDrafts.push(draft);

    const evt: EngineEvent = {
      id: nextEventId(),
      type: "draft_created",
      message: `Draft comandă ${draft.id} generat: ${material.name} — ${suggestedQty} ${material.unit} de la ${material.supplier} (~${estimatedCost} RON).`,
      timestamp: nowISO(),
      materialId: material.id,
    };
    newEvents.push(evt);
  });

  return newEvents;
}

/**
 * Mark a purchase draft as "sent" (simulated).
 */
export function sendPurchaseDraft(draftId: string): { success: boolean; message: string } {
  const draft = purchaseDrafts.find((d) => d.id === draftId);
  if (!draft) return { success: false, message: "Draft negăsit." };
  if (draft.status !== "draft") return { success: false, message: `Draft-ul este deja în status: ${draft.status}.` };

  draft.status = "sent";
  eventLog.push({
    id: nextEventId(),
    type: "draft_created",
    message: `Comanda ${draft.id} trimisă la ${draft.supplierName}.`,
    timestamp: nowISO(),
    materialId: draft.materialId,
  });

  return { success: true, message: `Comanda ${draft.id} a fost trimisă la ${draft.supplierName}.` };
}

// ── Getters (read-only access) ──────────────────────────────

export function getInkReservoirs(): InkReservoir[] {
  return [...inkReservoirs];
}

export function getPurchaseDrafts(): PurchaseDraft[] {
  return [...purchaseDrafts];
}

export function getEventLog(): EngineEvent[] {
  return [...eventLog].reverse(); // newest first
}

export function getRecalibrationLog(): RecalibrationEntry[] {
  return [...recalibrationLog];
}

export function getJobConsumptions(): JobConsumptionRecord[] {
  return jobConsumptions.map((j) => ({ ...j, consumptions: [...j.consumptions] }));
}

export function getPendingJobs(): JobConsumptionRecord[] {
  return jobConsumptions.filter((j) => !j.completedAt);
}

export function getCompletedJobs(): JobConsumptionRecord[] {
  return jobConsumptions.filter((j) => j.completedAt !== null);
}

/**
 * Check if a material needs recalibration (stock ≤ 0 but not confirmed by operator).
 */
export function needsRecalibration(materialId: string): boolean {
  const material = inventoryMaterials.find((m) => m.id === materialId);
  if (!material) return false;
  if (material.stockCurrent > 0) return false;

  // Check if recently recalibrated (within last hour)
  const recent = recalibrationLog.find(
    (r) => r.materialId === materialId && Date.now() - new Date(r.timestamp).getTime() < 3600000
  );
  return !recent;
}

// ── Initialize: generate initial drafts for critical materials ──
checkAndGenerateDraftOrders();