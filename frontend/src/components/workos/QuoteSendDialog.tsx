import { useCallback, useEffect, useMemo, useState } from "react";

import { type Quote } from "@/lib/mockData";

import {

  generateQuotePDF,

  buildMailtoLink,

  buildWhatsAppLink,

  buildSmsLink,

  buildQuoteSummaryText,

} from "@/lib/quotePdfGenerator";
import { generateQuotePdf, downloadLatestPdf } from "@/api/quotePdf";
import { DEFAULT_QUOTE_CURRENCY, formatQuoteMoney } from "@/lib/quoteCurrency";

import { postQuoteSendLog, QuotePricingError, type QuoteSendLogResponse } from "@/api/quotes";

import {

  formatSendChannelLabel,

  QUOTE_SEND_ASSISTED_NOTICE,

  QUOTE_SEND_CHANNEL_LABELS,

  QUOTE_SEND_CHANNELS,

  QUOTE_SEND_SUCCESS_MESSAGE,

  validateSendLogForm,

  type QuoteSendChannel,

} from "@/lib/quoteSendLog";

import {

  X,

  FileDown,

  Mail,

  MessageCircle,

  Smartphone,

  Link2,

  Check,

  Send,

  AlertCircle,

  CheckCircle2,

  Loader2,

} from "lucide-react";



interface QuoteSendDialogProps {

  quote: Quote;

  open: boolean;

  onClose: () => void;

  onRegistered?: (result: QuoteSendLogResponse) => void | Promise<void>;

}



export default function QuoteSendDialog({

  quote,

  open,

  onClose,

  onRegistered,

}: QuoteSendDialogProps) {

  const [channel, setChannel] = useState<QuoteSendChannel>("email_manual");

  const [recipient, setRecipient] = useState(quote.contactPerson ?? "");

  const [note, setNote] = useState("");

  const [documentRef, setDocumentRef] = useState("");

  const [copied, setCopied] = useState(false);

  const [pdfGenerating, setPdfGenerating] = useState(false);

  const [submitting, setSubmitting] = useState(false);

  const [submitError, setSubmitError] = useState<string | null>(null);

  const [success, setSuccess] = useState<QuoteSendLogResponse | null>(null);



  useEffect(() => {

    if (!open) return;

    setChannel("email_manual");

    setRecipient(quote.contactPerson ?? "");

    setNote("");

    setDocumentRef("");

    setSubmitError(null);

    setSuccess(null);

  }, [open, quote.id, quote.contactPerson]);



  const formValidation = useMemo(

    () => validateSendLogForm({ channel, recipient, note }),

    [channel, recipient, note]

  );



  const canSubmit = !submitting && !formValidation && quote.dbId != null;



  const handleDownloadPDF = useCallback(async () => {

    setPdfGenerating(true);

    try {

      if (quote.dbId) {

        await generateQuotePdf(quote.dbId);

        await downloadLatestPdf(quote.dbId);

        setDocumentRef(`oferta_${quote.id}.pdf`);

        setChannel("print");

        return;

      }

      const { url, filename } = generateQuotePDF(quote);

      const a = document.createElement("a");

      a.href = url;

      a.download = filename;

      document.body.appendChild(a);

      a.click();

      document.body.removeChild(a);

      URL.revokeObjectURL(url);

      setDocumentRef(filename);

      setChannel("print");

    } catch (err) {

      console.error("PDF generation failed:", err);

    } finally {

      setPdfGenerating(false);

    }

  }, [quote]);



  const handleEmail = useCallback(() => {

    window.open(buildMailtoLink(quote), "_blank");

    setChannel("email_manual");

  }, [quote]);



  const handleWhatsApp = useCallback(() => {

    window.open(buildWhatsAppLink(quote), "_blank");

    setChannel("whatsapp");

  }, [quote]);



  const handleSMS = useCallback(() => {

    window.open(buildSmsLink(quote), "_blank");

    setChannel("phone");

  }, [quote]);



  const handleCopyLink = useCallback(async () => {

    const text = buildQuoteSummaryText(quote);

    try {

      await navigator.clipboard.writeText(text);

    } catch {

      const ta = document.createElement("textarea");

      ta.value = text;

      document.body.appendChild(ta);

      ta.select();

      document.execCommand("copy");

      document.body.removeChild(ta);

    }

    setCopied(true);

    setTimeout(() => setCopied(false), 2000);

  }, [quote]);



  async function handleConfirmSend() {

    if (!quote.dbId || formValidation) return;

    setSubmitting(true);

    setSubmitError(null);

    try {

      const result = await postQuoteSendLog(quote.dbId, {

        channel,

        recipient: recipient.trim() || undefined,

        note: note.trim() || undefined,

        document_ref: documentRef.trim() || undefined,

      });

      setSuccess(result);

      await onRegistered?.(result);

    } catch (err) {

      setSubmitError(

        err instanceof QuotePricingError

          ? err.message

          : err instanceof Error

            ? err.message

            : "Trimiterea asistată nu a putut fi înregistrată."

      );

    } finally {

      setSubmitting(false);

    }

  }



  if (!open) return null;



  const currency = quote.currency ?? DEFAULT_QUOTE_CURRENCY;



  return (

    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">

      <div

        className="bg-[#111827] border border-[#1E293B] rounded-xl shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto"

        data-testid="quote-send-dialog"

      >

        <div className="flex items-center justify-between p-4 border-b border-[#1E293B]">

          <div className="flex items-center gap-2">

            <Send className="w-4 h-4 text-blue-400" />

            <h2 className="text-[14px] font-bold text-slate-100">Trimitere asistată</h2>

          </div>

          <button

            type="button"

            onClick={onClose}

            className="p-1 rounded-lg hover:bg-slate-700/50 text-slate-400 hover:text-slate-200 transition-colors"

          >

            <X className="w-4 h-4" />

          </button>

        </div>



        <div

          className="mx-4 mt-4 flex items-start gap-2 px-3 py-2 bg-amber-950/20 border border-amber-900/30 rounded-lg"

          data-testid="quote-send-assisted-notice"

        >

          <AlertCircle className="w-3.5 h-3.5 text-amber-400 mt-0.5 shrink-0" />

          <div className="text-[10px] text-amber-200/90 leading-relaxed space-y-1">

            <p>{QUOTE_SEND_ASSISTED_NOTICE}</p>

            {(quote.status === "draft" || quote.status === "priced") && (

              <p data-testid="quote-send-status-notice">

                La confirmare, statusul ofertei va fi marcat ca{" "}

                <span className="font-semibold">trimisă</span> în sistem.

              </p>

            )}

          </div>

        </div>



        <div className="p-4 border-b border-[#1E293B] bg-[#0D1321]">

          <div className="flex items-center justify-between">

            <div>

              <span className="text-[12px] font-mono text-blue-400">{quote.id}</span>

              <span className="text-[10px] text-slate-500 ml-2">v{quote.version}</span>

            </div>

            <span className="text-[16px] font-bold text-slate-100">

              {formatQuoteMoney(quote.grandTotal, currency)}

            </span>

          </div>

          <p className="text-[12px] text-slate-300 mt-1">{quote.client}</p>

          <p className="text-[11px] text-slate-500">{quote.contactPerson}</p>

        </div>



        <div className="p-4 space-y-3 border-b border-[#1E293B]">

          <p className="text-[11px] text-slate-400 uppercase tracking-wide">

            Instrumente operator (nu înregistrează automat)

          </p>

          <div className="grid grid-cols-2 gap-2">

            <button

              type="button"

              onClick={() => void handleDownloadPDF()}

              disabled={pdfGenerating}

              className="flex items-center gap-2 px-3 py-2 bg-[#1A2236] border border-[#2A3548] rounded-lg text-[11px] text-slate-200"

            >

              <FileDown className="w-3.5 h-3.5 text-red-400" /> PDF

            </button>

            <button

              type="button"

              onClick={handleEmail}

              className="flex items-center gap-2 px-3 py-2 bg-[#1A2236] border border-[#2A3548] rounded-lg text-[11px] text-slate-200"

            >

              <Mail className="w-3.5 h-3.5 text-blue-400" /> Email

            </button>

            <button

              type="button"

              onClick={handleWhatsApp}

              className="flex items-center gap-2 px-3 py-2 bg-[#1A2236] border border-[#2A3548] rounded-lg text-[11px] text-slate-200"

            >

              <MessageCircle className="w-3.5 h-3.5 text-emerald-400" /> WhatsApp

            </button>

            <button

              type="button"

              onClick={handleCopyLink}

              className="flex items-center gap-2 px-3 py-2 bg-[#1A2236] border border-[#2A3548] rounded-lg text-[11px] text-slate-200"

            >

              {copied ? (

                <Check className="w-3.5 h-3.5 text-emerald-400" />

              ) : (

                <Link2 className="w-3.5 h-3.5 text-amber-400" />

              )}

              Copiere

            </button>

          </div>

        </div>



        <div className="p-4 space-y-3">

          <p className="text-[11px] text-slate-400 uppercase tracking-wide">

            Confirmare trimitere asistată

          </p>



          <div>

            <label htmlFor="quote-send-channel" className="text-[11px] text-slate-400 block mb-1">

              Canal *

            </label>

            <select

              id="quote-send-channel"

              data-testid="quote-send-channel-select"

              value={channel}

              onChange={(e) => setChannel(e.target.value as QuoteSendChannel)}

              className="w-full px-3 py-2 rounded-lg border border-[#2A3548] bg-[#0f1524] text-slate-100 text-[13px]"

            >

              {QUOTE_SEND_CHANNELS.map((value) => (

                <option key={value} value={value}>

                  {QUOTE_SEND_CHANNEL_LABELS[value]}

                </option>

              ))}

            </select>

          </div>



          <div>

            <label htmlFor="quote-send-recipient" className="text-[11px] text-slate-400 block mb-1">

              Destinatar (opțional)

            </label>

            <input

              id="quote-send-recipient"

              data-testid="quote-send-recipient-input"

              value={recipient}

              onChange={(e) => setRecipient(e.target.value)}

              className="w-full px-3 py-2 rounded-lg border border-[#2A3548] bg-[#0f1524] text-slate-100 text-[13px]"

            />

          </div>



          <div>

            <label htmlFor="quote-send-note" className="text-[11px] text-slate-400 block mb-1">

              Notiță (opțional)

            </label>

            <textarea

              id="quote-send-note"

              data-testid="quote-send-note-input"

              value={note}

              onChange={(e) => setNote(e.target.value)}

              rows={2}

              className="w-full px-3 py-2 rounded-lg border border-[#2A3548] bg-[#0f1524] text-slate-100 text-[13px]"

            />

          </div>



          <div>

            <label htmlFor="quote-send-document-ref" className="text-[11px] text-slate-400 block mb-1">

              Referință document / PDF (opțional)

            </label>

            <input

              id="quote-send-document-ref"

              data-testid="quote-send-document-ref-input"

              value={documentRef}

              onChange={(e) => setDocumentRef(e.target.value)}

              className="w-full px-3 py-2 rounded-lg border border-[#2A3548] bg-[#0f1524] text-slate-100 text-[13px]"

            />

          </div>



          {formValidation && (

            <p className="text-[10px] text-red-400" data-testid="quote-send-form-error">

              {formValidation}

            </p>

          )}



          {submitError && (

            <div

              className="flex items-start gap-2 rounded-lg border border-red-900/40 bg-red-950/20 px-3 py-2"

              data-testid="quote-send-submit-error"

            >

              <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />

              <p className="text-[11px] text-red-300">{submitError}</p>

            </div>

          )}



          {success && (

            <div

              className="flex items-start gap-2 rounded-lg border border-emerald-900/40 bg-emerald-950/20 px-3 py-2"

              data-testid="quote-send-success"

            >

              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />

              <p className="text-[11px] text-emerald-300" data-testid="quote-send-success-message">

                {QUOTE_SEND_SUCCESS_MESSAGE}{" "}

                {formatSendChannelLabel(success.log_entry.channel)} · v

                {success.quote_version}

              </p>

            </div>

          )}



          {!quote.dbId && (

            <p className="text-[10px] text-amber-400">

              Trimiterea persistentă necesită ofertă din baza de date live.

            </p>

          )}

        </div>



        <div className="flex items-center justify-end gap-2 p-4 border-t border-[#1E293B]">

          <button

            type="button"

            onClick={onClose}

            className="px-3 py-1.5 text-[12px] rounded border border-[#2A3548] text-slate-400 hover:text-slate-200"

          >

            Închide

          </button>

          <button

            type="button"

            data-testid="quote-send-confirm-action"

            disabled={!canSubmit}

            onClick={() => void handleConfirmSend()}

            className="px-4 py-1.5 text-[12px] font-semibold rounded bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-40"

          >

            {submitting ? (

              <span className="inline-flex items-center gap-2">

                <Loader2 className="w-3.5 h-3.5 animate-spin" /> Se înregistrează…

              </span>

            ) : (

              "Confirmă trimiterea asistată"

            )}

          </button>

        </div>

      </div>

    </div>

  );

}


