import type { QuoteCommercialDeliveryLogEntry, QuoteStatus } from "@/lib/mockData";

import { isTerminalClosedQuoteStatus } from "@/lib/commercialSpineNavigation";

export const QUOTE_SEND_CHANNELS = [
  "email_manual",
  "whatsapp",
  "phone",
  "print",
  "other",
] as const;

export type QuoteSendChannel = (typeof QUOTE_SEND_CHANNELS)[number];

export const QUOTE_SEND_CHANNEL_LABELS: Record<QuoteSendChannel, string> = {
  email_manual: "Email manual",
  whatsapp: "WhatsApp",
  phone: "Telefon",
  print: "Print / predare fizică",
  other: "Alt canal manual",
};

export const QUOTE_SEND_ASSISTED_NOTICE =
  "Această acțiune nu trimite email automat. Se salvează doar faptul că operatorul a trimis/predat oferta prin canalul ales.";

export const QUOTE_SEND_SUCCESS_MESSAGE =
  "Trimiterea asistată a fost înregistrată.";

/** Mirrors backend QUOTE_SEND_LOG_ALLOWED_STATUSES (minus terminal closed). */
export const QUOTE_SEND_LOG_ELIGIBLE_STATUSES: QuoteStatus[] = [
  "draft",
  "priced",
  "sent",
  "viewed",
  "negotiating",
  "accepted",
];

export function isQuoteSendLogEligible(status: QuoteStatus): boolean {
  if (isTerminalClosedQuoteStatus(status)) return false;
  return QUOTE_SEND_LOG_ELIGIBLE_STATUSES.includes(status);
}

export function extractCommercialDeliveryLog(
  lineItemsRaw?: string | null
): QuoteCommercialDeliveryLogEntry[] {
  if (!lineItemsRaw?.trim()) return [];
  try {
    const parsed = JSON.parse(lineItemsRaw) as Record<string, unknown>;
    const logs = parsed.commercial_delivery_log;
    if (!Array.isArray(logs)) return [];
    return logs
      .filter((entry): entry is QuoteCommercialDeliveryLogEntry => {
        return !!entry && typeof entry === "object" && "channel" in entry;
      })
      .slice()
      .sort((a, b) => String(b.sent_at).localeCompare(String(a.sent_at)));
  } catch {
    return [];
  }
}

export function getLatestCommercialDeliveryLog(
  lineItemsRaw?: string | null
): QuoteCommercialDeliveryLogEntry | null {
  const logs = extractCommercialDeliveryLog(lineItemsRaw);
  return logs[0] ?? null;
}

export function formatSendChannelLabel(channel: string): string {
  if (channel in QUOTE_SEND_CHANNEL_LABELS) {
    return QUOTE_SEND_CHANNEL_LABELS[channel as QuoteSendChannel];
  }
  return channel;
}

export function validateSendLogForm(input: {
  channel: string;
  recipient?: string;
  note?: string;
}): string | null {
  if (!input.channel.trim()) return "Selectează canalul de trimitere.";
  if (!QUOTE_SEND_CHANNELS.includes(input.channel as QuoteSendChannel)) {
    return "Canalul selectat nu este valid.";
  }
  if (input.note && input.note.length > 500) {
    return "Notița depășește 500 de caractere.";
  }
  if (input.recipient && input.recipient.length > 200) {
    return "Destinatarul depășește 200 de caractere.";
  }
  return null;
}
