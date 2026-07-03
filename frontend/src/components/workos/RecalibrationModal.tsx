import { useState } from "react";
import { AlertTriangle, Ruler, X, Check, SkipForward } from "lucide-react";

interface RecalibrationModalProps {
  materialId: string;
  materialName: string;
  currentStock: number;
  unit: string;
  onConfirmEmpty: () => void;
  onRecalibrate: (newValue: number) => void;
  onDismiss: () => void;
}

export default function RecalibrationModal({
  materialId,
  materialName,
  currentStock,
  unit,
  onConfirmEmpty,
  onRecalibrate,
  onDismiss,
}: RecalibrationModalProps) {
  const [manualValue, setManualValue] = useState<string>("");
  const [mode, setMode] = useState<"choose" | "manual">("choose");

  function handleRecalibrate() {
    const val = parseFloat(manualValue);
    if (isNaN(val) || val < 0) return;
    onRecalibrate(val);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-[#111827] border border-[#1E293B] rounded-xl shadow-2xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#1E293B]">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <h3 className="text-[15px] font-bold text-slate-100">Recalibrare Stoc</h3>
          </div>
          <button onClick={onDismiss} className="text-slate-500 hover:text-slate-300 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-4 space-y-4">
          <div className="bg-amber-900/20 border border-amber-800/40 rounded-lg p-3">
            <p className="text-[13px] text-amber-200">
              Sistemul indică stoc <strong className="text-amber-100">{currentStock} {unit}</strong> pentru:
            </p>
            <p className="text-[14px] font-bold text-slate-100 mt-1">{materialName}</p>
            <p className="text-[10px] text-slate-500 font-mono mt-0.5">{materialId}</p>
          </div>

          <p className="text-[13px] text-slate-300">
            Confirmați vizual starea materialului:
          </p>

          {mode === "choose" ? (
            <div className="space-y-2">
              {/* Confirm empty */}
              <button
                onClick={onConfirmEmpty}
                className="w-full flex items-center gap-3 px-4 py-3 bg-red-900/20 border border-red-800/40 rounded-lg hover:bg-red-900/30 transition-colors text-left"
              >
                <Check className="w-5 h-5 text-red-400 shrink-0" />
                <div>
                  <p className="text-[13px] font-semibold text-red-300">Confirm epuizat</p>
                  <p className="text-[11px] text-slate-500">Materialul este într-adevăr terminat</p>
                </div>
              </button>

              {/* Enter manual value */}
              <button
                onClick={() => setMode("manual")}
                className="w-full flex items-center gap-3 px-4 py-3 bg-blue-900/20 border border-blue-800/40 rounded-lg hover:bg-blue-900/30 transition-colors text-left"
              >
                <Ruler className="w-5 h-5 text-blue-400 shrink-0" />
                <div>
                  <p className="text-[13px] font-semibold text-blue-300">Introduc stoc real</p>
                  <p className="text-[11px] text-slate-500">Am verificat vizual și mai am material</p>
                </div>
              </button>

              {/* Dismiss */}
              <button
                onClick={onDismiss}
                className="w-full flex items-center gap-3 px-4 py-3 bg-slate-800/50 border border-slate-700/40 rounded-lg hover:bg-slate-800 transition-colors text-left"
              >
                <SkipForward className="w-5 h-5 text-slate-400 shrink-0" />
                <div>
                  <p className="text-[13px] font-semibold text-slate-300">Amân</p>
                  <p className="text-[11px] text-slate-500">Voi verifica mai târziu</p>
                </div>
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <label className="block">
                <span className="text-[12px] text-slate-400 mb-1 block">Cantitate reală ({unit})</span>
                <input
                  type="number"
                  min="0"
                  step="0.1"
                  value={manualValue}
                  onChange={(e) => setManualValue(e.target.value)}
                  placeholder={`ex: 5.5 ${unit}`}
                  className="w-full bg-[#0D1321] border border-[#2A3548] rounded-lg px-3 py-2.5 text-[14px] text-slate-200 placeholder:text-slate-600 outline-none focus:border-blue-500/50"
                  autoFocus
                />
              </label>
              <div className="flex gap-2">
                <button
                  onClick={() => setMode("choose")}
                  className="flex-1 px-4 py-2 text-[12px] font-semibold text-slate-400 bg-slate-800 border border-slate-700 rounded-lg hover:text-slate-200 transition-colors"
                >
                  Înapoi
                </button>
                <button
                  onClick={handleRecalibrate}
                  disabled={!manualValue || parseFloat(manualValue) < 0}
                  className="flex-1 px-4 py-2 text-[12px] font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-500 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Salvează
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}