import { useState } from "react";
import { AlertTriangle, X } from "lucide-react";

interface ReadinessWarningAcknowledgementModalProps {
  isOpen: boolean;
  warnings: unknown[];
  readinessResult?: Record<string, unknown>;
  quoteId: string;
  onConfirm: (reason: string) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

export default function ReadinessWarningAcknowledgementModal({
  isOpen,
  warnings,
  readinessResult,
  quoteId,
  onConfirm,
  onCancel,
  isLoading = false,
}: ReadinessWarningAcknowledgementModalProps) {
  const [isChecked, setIsChecked] = useState(false);
  const [reason, setReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!isChecked || !reason.trim()) {
      return;
    }
    setIsSubmitting(true);
    try {
      await onConfirm(reason);
      // Clear state on success
      setIsChecked(false);
      setReason("");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    // Clear state on cancel
    setIsChecked(false);
    setReason("");
    onCancel();
  };

  if (!isOpen) return null;

  const canSubmit = isChecked && reason.trim().length > 0 && !isSubmitting && !isLoading;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-[#111827] border border-[#1E293B] rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1E293B]">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <h2 className="text-[14px] font-bold text-slate-100">Readiness Warnings</h2>
          </div>
          <button
            onClick={handleCancel}
            disabled={isSubmitting || isLoading}
            className="p-1 hover:bg-slate-700 rounded transition-colors disabled:opacity-50"
          >
            <X className="w-4 h-4 text-slate-400" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-4 space-y-4">
          <p className="text-[12px] text-slate-400">
            This quote can be converted to an order only after acknowledging the readiness warnings below.
          </p>

          {/* Warnings List */}
          <div className="bg-[#1A2236] border border-amber-800/30 rounded-lg p-3 space-y-2 max-h-48 overflow-y-auto">
            {warnings && warnings.length > 0 ? (
              warnings.map((warning, idx) => {
                const warningText =
                  typeof warning === "string"
                    ? warning
                    : typeof warning === "object" && warning !== null && "message" in warning
                      ? (warning as { message?: string }).message
                      : typeof warning === "object" && warning !== null && "code" in warning
                        ? (warning as { code?: string }).code
                        : String(warning);
                return (
                  <div key={idx} className="flex items-start gap-2">
                    <span className="text-amber-400 text-[11px] font-semibold mt-0.5">•</span>
                    <p className="text-[11px] text-amber-300">{warningText}</p>
                  </div>
                );
              })
            ) : (
              <p className="text-[11px] text-slate-400 italic">No warnings details available.</p>
            )}
          </div>

          {/* Readiness Result Summary (Optional) */}
          {readinessResult && typeof readinessResult === "object" && "overall_status" in readinessResult && (
            <div className="bg-[#1A2236] rounded-lg p-3">
              <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Status</p>
              <p className="text-[12px] text-slate-300 font-semibold">
                {String((readinessResult as Record<string, unknown>).overall_status)}
              </p>
            </div>
          )}

          {/* Acknowledgement Checkbox */}
          <div className="flex items-start gap-2">
            <input
              type="checkbox"
              id="acknowledge_warnings"
              checked={isChecked}
              onChange={(e) => setIsChecked(e.target.checked)}
              disabled={isSubmitting || isLoading}
              className="w-4 h-4 rounded border-[#2A3548] bg-[#1A2236] accent-blue-600 mt-1 cursor-pointer disabled:opacity-50"
            />
            <label htmlFor="acknowledge_warnings" className="text-[11px] text-slate-300 cursor-pointer flex-1">
              I have reviewed and acknowledge these readiness warnings.
            </label>
          </div>

          {/* Reason Textarea */}
          <div>
            <label htmlFor="reason" className="block text-[11px] text-slate-400 uppercase tracking-wide mb-1.5">
              Acknowledgement Reason *
            </label>
            <textarea
              id="reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              disabled={isSubmitting || isLoading}
              placeholder="Explain why you are acknowledging these warnings (required)"
              className="w-full px-3 py-2 bg-[#1A2236] border border-[#2A3548] rounded text-[11px] text-slate-300 placeholder-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/50 resize-none disabled:opacity-50"
              rows={3}
            />
            <p className="text-[10px] text-slate-500 mt-1">Minimum 5 characters required.</p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center gap-2 px-6 py-3 border-t border-[#1E293B] bg-[#0D1117]">
          <button
            onClick={handleCancel}
            disabled={isSubmitting || isLoading}
            className="flex-1 px-3 py-2 text-[11px] font-semibold rounded bg-slate-700 text-slate-300 hover:bg-slate-600 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className={`flex-1 px-3 py-2 text-[11px] font-semibold rounded transition-colors ${
              canSubmit
                ? "bg-blue-600 text-white hover:bg-blue-500"
                : "bg-slate-700 text-slate-500 cursor-not-allowed"
            }`}
          >
            {isSubmitting || isLoading ? "Processing..." : "Create Order with Acknowledgement"}
          </button>
        </div>

        {/* Reason validation helper text */}
        {reason.length < 5 && reason.length > 0 && (
          <div className="px-6 py-2 bg-red-900/20 border-t border-red-800/30 text-[10px] text-red-300">
            Reason must be at least 5 characters. ({reason.length}/5)
          </div>
        )}
      </div>
    </div>
  );
}
