import { describe, expect, it } from "vitest";
import {
  extractCommercialDeliveryLog,
  formatSendChannelLabel,
  isQuoteSendLogEligible,
  validateSendLogForm,
} from "./quoteSendLog";

describe("quoteSendLog", () => {
  it("extracts commercial delivery log from line_items wrapper", () => {
    const raw = JSON.stringify({
      line_items: { status: "priced" },
      commercial_delivery_log: [
        {
          channel: "email_manual",
          sent_at: "2026-06-08T10:00:00Z",
          quote_version: 2,
          recipient: "a@b.com",
        },
        {
          channel: "whatsapp",
          sent_at: "2026-06-07T10:00:00Z",
          quote_version: 1,
        },
      ],
    });
    const logs = extractCommercialDeliveryLog(raw);
    expect(logs).toHaveLength(2);
    expect(logs[0].channel).toBe("email_manual");
  });

  it("validates channel as required", () => {
    expect(validateSendLogForm({ channel: "" })).toMatch(/canal/i);
    expect(validateSendLogForm({ channel: "email_manual" })).toBeNull();
  });

  it("formats channel labels in Romanian", () => {
    expect(formatSendChannelLabel("email_manual")).toMatch(/Email manual/i);
    expect(formatSendChannelLabel("print")).toMatch(/Print/i);
  });

  it("allows send-log on priced, sent, viewed, negotiating and draft", () => {
    expect(isQuoteSendLogEligible("priced")).toBe(true);
    expect(isQuoteSendLogEligible("sent")).toBe(true);
    expect(isQuoteSendLogEligible("viewed")).toBe(true);
    expect(isQuoteSendLogEligible("negotiating")).toBe(true);
    expect(isQuoteSendLogEligible("draft")).toBe(true);
  });

  it("blocks send-log on terminal closed statuses", () => {
    expect(isQuoteSendLogEligible("rejected")).toBe(false);
    expect(isQuoteSendLogEligible("expired")).toBe(false);
  });
});
