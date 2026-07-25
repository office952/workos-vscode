import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import IntakeV6ReviewWorkbenchLayout from "./IntakeV6ReviewWorkbenchLayout";

describe("IntakeV6ReviewWorkbenchLayout", () => {
  it("composes strip, domain nav, form body, and offer rail", () => {
    render(
      <IntakeV6ReviewWorkbenchLayout
        productStrip={<span>strip</span>}
        domainNav={<nav>domains</nav>}
        attention={<span>!</span>}
        formBody={<p>fields</p>}
        formFooter={<footer>save</footer>}
        offerRail={<aside>offer</aside>}
      />,
    );

    expect(screen.getByTestId("intake-v6-review-workbench")).toHaveAttribute(
      "data-workbench-variant",
      "b",
    );
    expect(screen.getByTestId("intake-v6-review-product-strip")).toHaveTextContent("strip");
    expect(screen.getByTestId("intake-v6-review-domain-nav-shell")).toHaveTextContent("domains");
    expect(screen.getByTestId("intake-v6-review-domain-nav-shell")).toHaveAttribute(
      "data-domain-nav-placement",
      "top",
    );
    expect(screen.getByTestId("intake-v6-review-form-body")).toHaveTextContent("fields");
    expect(screen.getByTestId("intake-v6-live-calculation-sticky-shell")).toHaveTextContent("offer");
    expect(screen.getByTestId("intake-v6-review-attention-slot")).toHaveTextContent("!");
  });

  it("omits product strip when Configurare hides identity chrome", () => {
    render(
      <IntakeV6ReviewWorkbenchLayout
        domainNav={<nav>domains</nav>}
        formBody={<p>fields</p>}
        offerRail={<aside>offer</aside>}
      />,
    );

    expect(screen.queryByTestId("intake-v6-review-product-strip")).not.toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-review-domain-nav-shell")).toHaveTextContent("domains");
    expect(screen.getByTestId("intake-v6-review-form-chrome")).toHaveAttribute(
      "data-domain-nav-placement",
      "top",
    );
  });
});
