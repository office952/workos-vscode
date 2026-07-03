import { useState } from "react";
import {
  Plus,
  Trash2,
  Save,
  Package,
  Edit2,
  X,
  Loader2,
} from "lucide-react";

export interface MaterialRow {
  material_id: string | null;
  material_name: string;
  quantity: number;
  unit: string;
  task_id: string | null;
  added_at?: string;
  reported_by_employee_id?: number | null;
  reported_by_employee_name?: string | null;
  consumption_notes?: string | null;
  reported_at?: string;
}

interface MaterialsCaptureProps {
  orderId: number;
  taskId?: string;
  materials: MaterialRow[];
  onAdd: (materials: MaterialRow[]) => Promise<boolean>;
  onUpdate: (index: number, material: MaterialRow) => Promise<boolean>;
  onRemove: (index: number) => Promise<boolean>;
  disabled?: boolean;
  reporterEmployeeId?: number | null;
  reporterEmployeeName?: string | null;
}

const VALID_UNITS = [
  "buc", "m", "m2", "m3", "kg", "g", "l", "ml", "set", "role", "coli", "placi",
];

const EMPTY_ROW: MaterialRow = {
  material_id: null,
  material_name: "",
  quantity: 0,
  unit: "buc",
  task_id: null,
};

export function MaterialsCapturePanel({
  orderId,
  taskId,
  materials,
  onAdd,
  onUpdate,
  onRemove,
  disabled = false,
  reporterEmployeeId = null,
  reporterEmployeeName = null,
}: MaterialsCaptureProps) {
  const [pendingRows, setPendingRows] = useState<MaterialRow[]>([]);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editRow, setEditRow] = useState<MaterialRow>(EMPTY_ROW);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function addPendingRow() {
    setPendingRows((prev) => [
      ...prev,
      { ...EMPTY_ROW, task_id: taskId || null },
    ]);
  }

  function updatePendingRow(idx: number, field: keyof MaterialRow, value: string | number | null) {
    setPendingRows((prev) =>
      prev.map((r, i) => (i === idx ? { ...r, [field]: value } : r))
    );
  }

  function removePendingRow(idx: number) {
    setPendingRows((prev) => prev.filter((_, i) => i !== idx));
  }

  function validateRow(row: MaterialRow): string | null {
    if (!row.material_name || row.material_name.trim() === "") {
      return "Numele materialului este obligatoriu";
    }
    if (!row.quantity || row.quantity <= 0) {
      return "Cantitatea trebuie să fie > 0";
    }
    if (!row.unit || !VALID_UNITS.includes(row.unit)) {
      return `Unitate invalidă. Valide: ${VALID_UNITS.join(", ")}`;
    }
    return null;
  }

  async function handleSavePending() {
    setError(null);
    // Validate all pending rows
    for (let i = 0; i < pendingRows.length; i++) {
      const err = validateRow(pendingRows[i]);
      if (err) {
        setError(`Rând ${i + 1}: ${err}`);
        return;
      }
    }
    if (pendingRows.length === 0) {
      setError("Adăugați cel puțin un material");
      return;
    }

    setSaving(true);
    const enriched = pendingRows.map((row) => ({
      ...row,
      task_id: row.task_id ?? taskId ?? null,
      reported_by_employee_id: reporterEmployeeId ?? row.reported_by_employee_id ?? null,
      reported_by_employee_name: reporterEmployeeName ?? row.reported_by_employee_name ?? null,
      reported_at: row.reported_at ?? new Date().toISOString(),
    }));
    const success = await onAdd(enriched);
    setSaving(false);
    if (success) {
      setPendingRows([]);
    } else {
      setError("Eroare la salvare. Verificați conexiunea.");
    }
  }

  function startEdit(idx: number) {
    setEditingIndex(idx);
    setEditRow({ ...materials[idx] });
  }

  function cancelEdit() {
    setEditingIndex(null);
    setEditRow(EMPTY_ROW);
  }

  async function handleSaveEdit() {
    if (editingIndex === null) return;
    const err = validateRow(editRow);
    if (err) {
      setError(err);
      return;
    }
    setError(null);
    setSaving(true);
    const success = await onUpdate(editingIndex, editRow);
    setSaving(false);
    if (success) {
      setEditingIndex(null);
      setEditRow(EMPTY_ROW);
    } else {
      setError("Eroare la actualizare.");
    }
  }

  async function handleRemove(idx: number) {
    setSaving(true);
    setError(null);
    const success = await onRemove(idx);
    setSaving(false);
    if (!success) {
      setError("Eroare la ștergere.");
    }
  }

  return (
    <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Package className="w-4 h-4 text-blue-400" />
          <span className="text-[13px] font-semibold text-slate-200">
            Materiale Consumate
          </span>
          <span className="text-[11px] text-slate-500">
            (Order #{orderId})
          </span>
        </div>
        <span className="text-[10px] text-slate-500 italic">
          Observațional — nu actualizează stocul
        </span>
      </div>

      {/* Saved materials list */}
      {materials.length > 0 && (
        <div className="space-y-1">
          <p className="text-[10px] text-slate-500 uppercase tracking-wide">Salvate</p>
          {materials.map((mat, idx) => (
            <div
              key={idx}
              className="flex items-center gap-2 bg-[#1A2236] border border-[#2A3548] rounded px-3 py-2"
            >
              {editingIndex === idx ? (
                /* Inline edit mode */
                <>
                  <input
                    type="text"
                    value={editRow.material_name}
                    onChange={(e) => setEditRow({ ...editRow, material_name: e.target.value })}
                    className="flex-1 bg-[#0F172A] border border-slate-600 rounded px-2 py-1 text-[12px] text-slate-200"
                    placeholder="Nume material"
                  />
                  <input
                    type="number"
                    value={editRow.quantity || ""}
                    onChange={(e) => setEditRow({ ...editRow, quantity: parseFloat(e.target.value) || 0 })}
                    className="w-20 bg-[#0F172A] border border-slate-600 rounded px-2 py-1 text-[12px] text-slate-200"
                    placeholder="Cant."
                    step="0.01"
                    min="0.01"
                  />
                  <select
                    value={editRow.unit}
                    onChange={(e) => setEditRow({ ...editRow, unit: e.target.value })}
                    className="w-20 bg-[#0F172A] border border-slate-600 rounded px-2 py-1 text-[12px] text-slate-200"
                  >
                    {VALID_UNITS.map((u) => (
                      <option key={u} value={u}>{u}</option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={handleSaveEdit}
                    disabled={saving}
                    className="p-1 text-emerald-400 hover:text-emerald-300"
                  >
                    {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                  </button>
                  <button
                    type="button"
                    onClick={cancelEdit}
                    className="p-1 text-slate-400 hover:text-slate-300"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </>
              ) : (
                /* Display mode */
                <>
                  <span className="flex-1 text-[12px] text-slate-200 font-medium">
                    {mat.material_name || mat.material_id || "—"}
                  </span>
                  <span className="text-[12px] text-emerald-400 font-mono">
                    {mat.quantity} {mat.unit}
                  </span>
                  {mat.task_id && (
                    <span className="text-[10px] text-slate-500 font-mono">
                      task:{mat.task_id}
                    </span>
                  )}
                  {!disabled && (
                    <>
                      <button
                        type="button"
                        onClick={() => startEdit(idx)}
                        className="p-1 text-slate-400 hover:text-blue-400"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleRemove(idx)}
                        disabled={saving}
                        className="p-1 text-slate-400 hover:text-red-400"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </>
                  )}
                </>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Pending rows (not yet saved) */}
      {!disabled && (
        <div className="space-y-2">
          {pendingRows.length > 0 && (
            <p className="text-[10px] text-amber-400 uppercase tracking-wide">
              Nesalvate ({pendingRows.length})
            </p>
          )}
          {pendingRows.map((row, idx) => (
            <div
              key={idx}
              className="flex items-center gap-2 bg-amber-900/10 border border-amber-700/30 rounded px-3 py-2"
            >
              <input
                type="text"
                value={row.material_name}
                onChange={(e) => updatePendingRow(idx, "material_name", e.target.value)}
                className="flex-1 bg-[#0F172A] border border-slate-600 rounded px-2 py-1 text-[12px] text-slate-200"
                placeholder="Nume material *"
              />
              <input
                type="number"
                value={row.quantity || ""}
                onChange={(e) => updatePendingRow(idx, "quantity", parseFloat(e.target.value) || 0)}
                className="w-20 bg-[#0F172A] border border-slate-600 rounded px-2 py-1 text-[12px] text-slate-200"
                placeholder="Cant. *"
                step="0.01"
                min="0.01"
              />
              <select
                value={row.unit}
                onChange={(e) => updatePendingRow(idx, "unit", e.target.value)}
                className="w-20 bg-[#0F172A] border border-slate-600 rounded px-2 py-1 text-[12px] text-slate-200"
              >
                {VALID_UNITS.map((u) => (
                  <option key={u} value={u}>{u}</option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => removePendingRow(idx)}
                className="p-1 text-slate-400 hover:text-red-400"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}

          {/* Action buttons */}
          <div className="flex items-center gap-2 pt-1">
            <button
              type="button"
              onClick={addPendingRow}
              className="flex items-center gap-1 px-3 py-1.5 rounded text-[11px] font-semibold bg-blue-600 hover:bg-blue-500 text-white transition-colors"
            >
              <Plus className="w-3 h-3" />
              Adaugă Material
            </button>
            {pendingRows.length > 0 && (
              <button
                type="button"
                onClick={handleSavePending}
                disabled={saving}
                className="flex items-center gap-1 px-3 py-1.5 rounded text-[11px] font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition-colors"
              >
                {saving ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <Save className="w-3 h-3" />
                )}
                Salvează ({pendingRows.length})
              </button>
            )}
          </div>
        </div>
      )}

      {/* Error display */}
      {error && (
        <p className="text-[11px] text-red-400 bg-red-900/20 border border-red-700/30 rounded px-3 py-1.5">
          {error}
        </p>
      )}
    </div>
  );
}