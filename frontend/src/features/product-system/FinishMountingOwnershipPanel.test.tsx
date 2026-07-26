import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { FinishMountingOwnershipPanel } from "./FinishMountingOwnershipPanel";

describe("FinishMountingOwnershipPanel", () => {
  it("renders precise responsibilities and approved narrowing gates", () => {
    render(
      <MemoryRouter>
        <FinishMountingOwnershipPanel />
      </MemoryRouter>,
    );

    expect(screen.getByTestId("finish-mounting-ownership-panel")).toBeInTheDocument();
    expect(screen.getByTestId("finish-ownership-summary")).toHaveTextContent(/Activare neaprobată/);
    expect(screen.getByTestId("finish-ownership-summary")).toHaveTextContent(/SURFACE_FINISH/);
    expect(screen.getByTestId("template-ownership-summary")).toHaveTextContent(/sablon_montaj/);
    expect(screen.getByTestId("packaging-ownership-summary")).toHaveTextContent(/ambalare_livrare_montaj/);
    expect(screen.getByTestId("mounting-ownership-summary")).toHaveTextContent(/structura_suport/);
    expect(screen.getByTestId("mounting-ownership-summary")).toHaveTextContent(/sablon_montaj/);
    expect(screen.getByTestId("legacy-compatibility-block")).toHaveTextContent(
      /Alias agregat legacy/,
    );
    expect(screen.getByTestId("ownership-gate-MOUNTING_MAP_NARROWING_OWNER_GATE")).toHaveTextContent(
      /APPROVED/,
    );
    expect(screen.getByTestId("ownership-gate-MINI_MODULE_SPLIT_OWNER_GATE")).toHaveTextContent(
      /APPROVED/,
    );
    expect(screen.getByTestId("ownership-gate-SOLD_CHIP_ACTIVATION_OWNER_GATE")).toHaveTextContent(
      /NOT APPROVED/,
    );
    expect(screen.getByTestId("ownership-row-mounting.alias")).toHaveTextContent(/COMPATIBILITY_ALIAS/);
    expect(screen.getByTestId("ownership-action-links")).toBeInTheDocument();
  });
});
