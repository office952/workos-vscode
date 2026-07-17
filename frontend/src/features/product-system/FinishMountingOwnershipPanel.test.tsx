import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { FinishMountingOwnershipPanel } from "./FinishMountingOwnershipPanel";

describe("FinishMountingOwnershipPanel", () => {
  it("renders CURRENT vs TARGET separation and blocked sold modules", () => {
    render(
      <MemoryRouter>
        <FinishMountingOwnershipPanel />
      </MemoryRouter>,
    );

    expect(screen.getByTestId("finish-mounting-ownership-panel")).toBeInTheDocument();
    expect(screen.getByTestId("finish-ownership-summary")).toHaveTextContent(/Activare neaprobată/);
    expect(screen.getByTestId("finish-ownership-summary")).toHaveTextContent(/Proprietar țintă: modul FINISH/);
    expect(screen.getByTestId("finish-ownership-summary")).toHaveTextContent(/Cataloage conflictuale/);
    expect(screen.getByTestId("mounting-ownership-summary")).toHaveTextContent(/Suport legat: parțial/);
    expect(screen.getByTestId("mounting-ownership-summary")).toHaveTextContent(/mounting_system/);
    expect(screen.getByTestId("mounting-ownership-summary")).toHaveTextContent(/metal_support_required/);
    expect(screen.getByTestId("ownership-gate-MOUNTING_MAP_NARROWING_OWNER_GATE")).toHaveTextContent(
      /NOT APPROVED/,
    );
    expect(screen.getByTestId("ownership-gate-MINI_MODULE_SPLIT_OWNER_GATE")).toHaveTextContent(
      /NOT APPROVED/,
    );
    expect(screen.getByTestId("ownership-gate-SOLD_CHIP_ACTIVATION_OWNER_GATE")).toHaveTextContent(
      /NOT APPROVED/,
    );
    expect(screen.getByTestId("ownership-row-finish.face_intent")).toHaveTextContent(/ȚINTĂ/);
    expect(screen.getByTestId("ownership-row-mounting.alias")).toHaveTextContent(/COMPATIBILITY_ALIAS/);
  });
});
