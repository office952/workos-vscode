import { describe, expect, it, beforeEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { ThemeProvider, useTheme } from "./ThemeContext";

function Probe() {
  const { theme, resolvedTheme, setTheme, toggleTheme } = useTheme();
  return (
    <div>
      <span data-testid="theme">{theme}</span>
      <span data-testid="resolved">{resolvedTheme}</span>
      <button type="button" onClick={() => setTheme("dark")}>
        set-dark
      </button>
      <button type="button" onClick={() => setTheme("light")}>
        set-light
      </button>
      <button type="button" onClick={toggleTheme}>
        toggle
      </button>
    </div>
  );
}

describe("ThemeContext WorkOS authority", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove("light", "dark");
    delete document.documentElement.dataset.theme;
  });

  it("applies html.light and data-theme=light for default light", () => {
    render(
      <ThemeProvider defaultTheme="light">
        <Probe />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("resolved").textContent).toBe("light");
    expect(document.documentElement.classList.contains("light")).toBe(true);
    expect(document.documentElement.dataset.theme).toBe("light");
    expect(localStorage.getItem("workos-theme")).toBeNull();
  });

  it("persists dark to workos-theme and applies html.dark", () => {
    render(
      <ThemeProvider defaultTheme="light">
        <Probe />
      </ThemeProvider>,
    );
    act(() => {
      screen.getByRole("button", { name: "set-dark" }).click();
    });
    expect(localStorage.getItem("workos-theme")).toBe("dark");
    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(screen.getByTestId("resolved").textContent).toBe("dark");
  });

  it("toggleTheme flips resolved light/dark", () => {
    render(
      <ThemeProvider defaultTheme="light">
        <Probe />
      </ThemeProvider>,
    );
    act(() => {
      screen.getByRole("button", { name: "toggle" }).click();
    });
    expect(screen.getByTestId("resolved").textContent).toBe("dark");
    act(() => {
      screen.getByRole("button", { name: "toggle" }).click();
    });
    expect(screen.getByTestId("resolved").textContent).toBe("light");
  });
});
