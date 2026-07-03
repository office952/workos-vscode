import jsPDF from "jspdf";
import { type Quote, type CompanySettings, companySettings } from "./mockData";
import {
  DEFAULT_QUOTE_CURRENCY,
  formatQuoteMoney,
} from "./quoteCurrency";

function quoteDisplayCurrency(quote: Quote): string {
  return quote.currency ?? DEFAULT_QUOTE_CURRENCY;
}

function formatAmount(val: number): string {
  return val.toLocaleString("ro-RO", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/**
 * Generate a professional PDF for a quote.
 * Returns a Blob URL for download or sharing.
 *
 * Fallback path when backend PDF is unavailable (no dbId).
 * Uses quote.currency from snapshot when mapped by dataStore.
 */
export function generateQuotePDF(
  quote: Quote,
  company: CompanySettings = companySettings
): { blob: Blob; url: string; filename: string } {
  const currency = quoteDisplayCurrency(quote);
  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const pageW = doc.internal.pageSize.getWidth();
  const margin = 15;
  let y = 20;

  // ── Header ──
  doc.setFontSize(18);
  doc.setFont("helvetica", "bold");
  doc.text(company.name, margin, y);
  y += 7;

  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");
  doc.setTextColor(100);
  doc.text(`CUI: ${company.cui} | Reg.Com: ${company.regCom}`, margin, y);
  y += 4;
  doc.text(`${company.address}, ${company.city}, ${company.county} ${company.postalCode}`, margin, y);
  y += 4;
  doc.text(`Tel: ${company.phone} | Email: ${company.email}`, margin, y);
  y += 4;
  doc.text(`IBAN: ${company.iban} — ${company.bankName}`, margin, y);
  y += 8;

  // ── Separator ──
  doc.setDrawColor(59, 130, 246);
  doc.setLineWidth(0.5);
  doc.line(margin, y, pageW - margin, y);
  y += 8;

  // ── Quote Title ──
  doc.setTextColor(0);
  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");
  doc.text(`OFERTĂ ${quote.id}`, margin, y);

  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");
  doc.setTextColor(100);
  doc.text(`Versiunea ${quote.version} | Valabilă până: ${quote.validUntil}`, pageW - margin, y, { align: "right" });
  y += 10;

  // ── Client Info ──
  doc.setTextColor(0);
  doc.setFontSize(10);
  doc.setFont("helvetica", "bold");
  doc.text("Client:", margin, y);
  doc.setFont("helvetica", "normal");
  doc.text(quote.client, margin + 18, y);
  y += 5;
  doc.setFontSize(9);
  doc.text(`Contact: ${quote.contactPerson}`, margin, y);
  y += 8;

  // ── Line Items Table ──
  doc.setFontSize(10);
  doc.setFont("helvetica", "bold");
  doc.text("Produse / Servicii", margin, y);
  y += 6;

  // Table header
  const colX = [margin, margin + 10, margin + 80, margin + 100, margin + 125, margin + 150];
  doc.setFillColor(241, 245, 249);
  doc.rect(margin, y - 4, pageW - 2 * margin, 7, "F");
  doc.setFontSize(8);
  doc.setFont("helvetica", "bold");
  doc.setTextColor(60);
  doc.text("#", colX[0], y);
  doc.text("Descriere", colX[1], y);
  doc.text("Cant.", colX[2], y);
  doc.text("Preț unit.", colX[3], y);
  doc.text("Total", colX[4], y);
  y += 6;

  // Table rows
  doc.setFont("helvetica", "normal");
  doc.setTextColor(0);
  doc.setFontSize(8);

  quote.lineItems.forEach((li, idx) => {
    if (y > 260) {
      doc.addPage();
      y = 20;
    }
    doc.text(`${idx + 1}`, colX[0], y);
    const desc = li.description.length > 40 ? li.description.slice(0, 40) + "..." : li.description;
    doc.text(desc, colX[1], y);
    doc.text(`${li.quantity}`, colX[2], y);
    doc.text(formatQuoteMoney(li.unitPrice, currency), colX[3], y);
    doc.text(formatQuoteMoney(li.total, currency), colX[4], y);
    y += 5;
  });

  y += 4;
  doc.setDrawColor(200);
  doc.line(margin, y, pageW - margin, y);
  y += 6;

  // ── Totals ──
  const totalsX = pageW - margin - 60;
  doc.setFontSize(9);
  doc.setFont("helvetica", "normal");

  doc.text("Subtotal:", totalsX, y);
  doc.text(formatQuoteMoney(quote.subtotal, currency), pageW - margin, y, { align: "right" });
  y += 5;

  if (quote.discountPct > 0) {
    doc.setTextColor(220, 38, 38);
    doc.text(`Discount (${quote.discountPct}%):`, totalsX, y);
    doc.text(`-${formatQuoteMoney(quote.discount, currency)}`, pageW - margin, y, { align: "right" });
    y += 5;
    doc.setTextColor(0);
  }

  doc.text("Total fără TVA:", totalsX, y);
  doc.text(formatQuoteMoney(quote.totalBeforeVAT, currency), pageW - margin, y, { align: "right" });
  y += 5;

  doc.text("TVA (19%):", totalsX, y);
  doc.text(formatQuoteMoney(quote.vat, currency), pageW - margin, y, { align: "right" });
  y += 6;

  doc.setFont("helvetica", "bold");
  doc.setFontSize(11);
  doc.setTextColor(59, 130, 246);
  doc.text("TOTAL:", totalsX, y);
  doc.text(formatQuoteMoney(quote.grandTotal, currency), pageW - margin, y, { align: "right" });
  y += 10;

  // ── Notes ──
  if (quote.notes) {
    doc.setTextColor(0);
    doc.setFontSize(9);
    doc.setFont("helvetica", "bold");
    doc.text("Observații:", margin, y);
    y += 5;
    doc.setFont("helvetica", "normal");
    doc.setTextColor(80);
    const lines = doc.splitTextToSize(quote.notes, pageW - 2 * margin);
    doc.text(lines, margin, y);
    y += lines.length * 4 + 4;
  }

  // ── Footer ──
  doc.setTextColor(150);
  doc.setFontSize(7);
  doc.text(
    `Generat automat de ${company.name} WorkOS — ${new Date().toLocaleDateString("ro-RO")}`,
    pageW / 2,
    285,
    { align: "center" }
  );

  const blob = doc.output("blob");
  const url = URL.createObjectURL(blob);
  const filename = `Oferta_${quote.id}_v${quote.version}.pdf`;

  return { blob, url, filename };
}

/**
 * Build a plain-text summary for sharing via WhatsApp/SMS/Email body.
 */
export function buildQuoteSummaryText(quote: Quote, company: CompanySettings = companySettings): string {
  const currency = quoteDisplayCurrency(quote);
  const lines = [
    `📋 Ofertă ${quote.id} — ${company.name}`,
    `Client: ${quote.client}`,
    `Contact: ${quote.contactPerson}`,
    ``,
    `Produse:`,
    ...quote.lineItems.map(
      (li, i) =>
        `  ${i + 1}. ${li.description} — ${li.quantity} buc × ${formatQuoteMoney(li.unitPrice, currency)} = ${formatQuoteMoney(li.total, currency)}`
    ),
    ``,
    `Subtotal: ${formatQuoteMoney(quote.subtotal, currency)}`,
    ...(quote.discountPct > 0
      ? [`Discount: -${quote.discountPct}% (${formatQuoteMoney(quote.discount, currency)})`]
      : []),
    `Total fără TVA: ${formatQuoteMoney(quote.totalBeforeVAT, currency)}`,
    `TVA (19%): ${formatQuoteMoney(quote.vat, currency)}`,
    `💰 TOTAL: ${formatQuoteMoney(quote.grandTotal, currency)}`,
    ``,
    `Valabilă până: ${quote.validUntil}`,
    ``,
    `— ${company.name} | ${company.phone} | ${company.email}`,
  ];
  return lines.join("\n");
}

/**
 * Build mailto: link with pre-filled subject and body.
 */
export function buildMailtoLink(quote: Quote, company: CompanySettings = companySettings): string {
  const subject = encodeURIComponent(`Ofertă ${quote.id} — ${company.name}`);
  const body = encodeURIComponent(buildQuoteSummaryText(quote, company));
  return `mailto:?subject=${subject}&body=${body}`;
}

/**
 * Build WhatsApp share link.
 */
export function buildWhatsAppLink(quote: Quote, company: CompanySettings = companySettings): string {
  const text = encodeURIComponent(buildQuoteSummaryText(quote, company));
  return `https://wa.me/?text=${text}`;
}

/**
 * Build SMS share link.
 */
export function buildSmsLink(quote: Quote, company: CompanySettings = companySettings): string {
  const currency = quoteDisplayCurrency(quote);
  const shortText = `Ofertă ${quote.id} de la ${company.name}: ${formatQuoteMoney(quote.grandTotal, currency)}. Contact: ${company.phone}`;
  return `sms:?body=${encodeURIComponent(shortText)}`;
}
