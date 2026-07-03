import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import IntakeV6QuoteCommercialSpinePanel from "./IntakeV6QuoteCommercialSpinePanel";

vi.mock("@/lib/intakeV6/intakeV6Api", () => ({
  getIntakeV6CommercialSpineState: vi.fn(),
  getIntakeV6PricedQuoteDryRun: vi.fn(),
  handoffIntakeV6ToOffer: vi.fn(),
  writeIntakeV6PricedQuote: vi.fn(),
  createIntakeV6QuoteSnapshotV2: vi.fn(),
  completeIntakeV6PricingReview: vi.fn(),
  persistIntakeV6OwnerApproval: vi.fn(),
  acceptIntakeV6Quote: vi.fn(),
  convertIntakeV6QuoteToOrder: vi.fn(),
}));

import {
  createIntakeV6QuoteSnapshotV2,
  getIntakeV6CommercialSpineState,
  getIntakeV6PricedQuoteDryRun,
  handoffIntakeV6ToOffer,
  writeIntakeV6PricedQuote,
} from "@/lib/intakeV6/intakeV6Api";

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const mockedSpine = vi.mocked(getIntakeV6CommercialSpineState);
const mockedDryRun = vi.mocked(getIntakeV6PricedQuoteDryRun);
const mockedHandoff = vi.mocked(handoffIntakeV6ToOffer);
const mockedWrite = vi.mocked(writeIntakeV6PricedQuote);
const mockedSnapshot = vi.mocked(createIntakeV6QuoteSnapshotV2);

const workspaceId = "c8dda47f-e2a7-4fea-800c-2dc01b2be5a3";
const quoteId = 6;
const intakeCode = `IV6-${workspaceId}`;

const unpricedSpineState = {
  quote_exists: true,
  is_v6_quote: true,
  quote_id: quoteId,
  quote_code: "Q-V6-IV6-BB8EE3F8-1782910533",
  quote_status: "draft",
  intake_code: intakeCode,
  workspace_id: workspaceId,
  requires_pricing_review: true,
  pricing_review: { completed: false },
  owner_approval: { exists: false, valid: false, stale: false },
  snapshot_v2: { exists: false, snapshot_id: null, accept_allowed: false },
  quote_accepted: false,
  quote_commercial_totals: { available: false, blocker: "QUOTE_NOT_PRICED" },
  v6_order_conversion: { converted: false, blocked_reasons: ["PRICING_REVIEW_REQUIRED"] },
  v6_quote_to_order_enabled: true,
};

const pricedSpineState = {
  ...unpricedSpineState,
  quote_status: "priced",
  quote_commercial_totals: {
    available: true,
    grand_total: 7886.61,
    subtotal: 6517.86,
    vat: 1368.75,
  },
};

const snapshottedSpineState = {
  ...pricedSpineState,
  snapshot_v2: { exists: true, snapshot_id: 99, snapshot_code: "QSN2-2026-0001", status: "frozen", readiness: "ready_for_owner_review", accept_allowed: true },
};

describe("IntakeV6QuoteCommercialSpinePanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows dry-run blockers and unpriced guidance for blocked backend pricing", async () => {
    mockedSpine.mockResolvedValue(unpricedSpineState);
    mockedDryRun.mockResolvedValue({
      pricing_status: "V6_PRICED_DRY_RUN_BLOCKED",
      workspace_id: workspaceId,
      pricing_source: "intake_v6_backend_priced_dry_run",
      commercial_totals: {
        subtotal_net: null,
        vat_rate: 21,
        vat_amount: null,
        total_gross: null,
        currency: "RON",
      },
      blockers: [{ code: "V6_PRICED_DRY_RUN_ZERO_TOTAL", message: "Zero total" }],
      commercial_line_items: [],
    });

    render(
      <IntakeV6QuoteCommercialSpinePanel
        workspaceId={workspaceId}
        quoteId={quoteId}
        intakeCode={intakeCode}
        clientAnalysisHash={null}
      />,
    );

    expect(await screen.findByTestId("intake-v6-priced-quote-bridge")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-dry-run-blockers")).toHaveTextContent(
      /Dry-run V6 a returnat total zero/i,
    );
    expect(screen.getByTestId("intake-v6-spine-pricing-blocker")).toHaveTextContent(
      /Scrie totaluri pe ofertă/i,
    );
    expect(screen.getByTestId("intake-v6-write-priced-quote")).toBeDisabled();
  });

  it("hands off to offer in a single action when dry-run is ready", async () => {
    mockedSpine.mockResolvedValueOnce(unpricedSpineState).mockResolvedValueOnce(pricedSpineState);
    mockedDryRun.mockResolvedValue({
      pricing_status: "V6_PRICED_DRY_RUN_READY",
      workspace_id: workspaceId,
      pricing_source: "intake_v6_backend_priced_dry_run",
      commercial_totals: {
        subtotal_net: 6517.86,
        vat_rate: 21,
        vat_amount: 1368.75,
        total_gross: 7886.61,
        currency: "RON",
      },
      blockers: [],
      commercial_line_items: [{ code: "face", total: 1000 }],
      pricing_hash: "hash-123",
    });
    mockedHandoff.mockResolvedValue({
      status: "V6_PRICED_QUOTE_WRITTEN",
      quote_id: quoteId,
      quote_code: "Q-V6-IV6-BB8EE3F8-1782910533",
      quote_created: false,
      quote_status: "priced",
      source_workspace_id: workspaceId,
      blockers: [],
      can_create_quote_snapshot: true,
      next_route: "/quotes/Q-V6-IV6-BB8EE3F8-1782910533",
    });

    const onSpineUpdated = vi.fn();
    render(
      <IntakeV6QuoteCommercialSpinePanel
        workspaceId={workspaceId}
        quoteId={quoteId}
        intakeCode={intakeCode}
        clientAnalysisHash={"a".repeat(64)}
        onSpineUpdated={onSpineUpdated}
      />,
    );

    const handoffButton = await screen.findByTestId("intake-v6-handoff-to-offer");
    expect(handoffButton).toBeEnabled();
    fireEvent.click(handoffButton);

    await waitFor(() => {
      expect(mockedHandoff).toHaveBeenCalledWith(workspaceId, {
        client_analysis_hash: "a".repeat(64),
        expected_total_gross: 7886.61,
        expected_pricing_hash: "hash-123",
        operator_confirmation: true,
      });
    });
    expect(onSpineUpdated).toHaveBeenCalled();
    expect(mockNavigate).toHaveBeenCalledWith("/quotes/Q-V6-IV6-BB8EE3F8-1782910533");
  });

  it("creates snapshot v2 after quote is priced", async () => {
    mockedSpine.mockResolvedValueOnce(pricedSpineState).mockResolvedValueOnce(snapshottedSpineState);
    mockedDryRun.mockResolvedValue({
      pricing_status: "V6_PRICED_DRY_RUN_READY",
      workspace_id: workspaceId,
      pricing_source: "intake_v6_backend_priced_dry_run",
      commercial_totals: {
        subtotal_net: 6517.86,
        vat_rate: 21,
        vat_amount: 1368.75,
        total_gross: 7886.61,
        currency: "RON",
      },
      blockers: [],
      commercial_line_items: [{ code: "face", total: 1000 }],
    });
    mockedSnapshot.mockResolvedValue({
      status: "V6_QUOTE_SNAPSHOT_V2_CREATED",
      quote_id: quoteId,
      snapshot_id: 99,
      blockers: [],
    });

    render(
      <IntakeV6QuoteCommercialSpinePanel
        workspaceId={workspaceId}
        quoteId={quoteId}
        intakeCode={intakeCode}
        clientAnalysisHash={null}
      />,
    );

    const snapshotButton = await screen.findByTestId("intake-v6-create-snapshot-v2");
    expect(snapshotButton).toBeEnabled();
    fireEvent.click(snapshotButton);

    await waitFor(() => {
      expect(mockedSnapshot).toHaveBeenCalledWith(workspaceId, quoteId, {
        operator_confirmation: true,
        expected_grand_total: 7886.61,
      });
    });
  });

  it("requires snapshot v2 before pricing review", async () => {
    mockedSpine.mockResolvedValue(pricedSpineState);
    mockedDryRun.mockResolvedValue({
      pricing_status: "V6_PRICED_DRY_RUN_READY",
      workspace_id: workspaceId,
      pricing_source: "intake_v6_backend_priced_dry_run",
      commercial_totals: {
        subtotal_net: 6517.86,
        vat_rate: 21,
        vat_amount: 1368.75,
        total_gross: 7886.61,
        currency: "RON",
      },
      blockers: [],
      commercial_line_items: [{ code: "face", total: 1000 }],
    });

    render(
      <IntakeV6QuoteCommercialSpinePanel
        workspaceId={workspaceId}
        quoteId={quoteId}
        intakeCode={intakeCode}
        clientAnalysisHash={null}
      />,
    );

    expect(await screen.findByTestId("intake-v6-create-snapshot-v2")).toBeEnabled();
    expect(screen.getByTestId("intake-v6-snapshot-required-hint")).toHaveTextContent(
      /Creeaza Snapshot V2 inainte de Review si Accept/i,
    );
    expect(screen.queryByTestId("intake-v6-complete-pricing-review")).not.toBeInTheDocument();
  });
});
