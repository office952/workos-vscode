import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { render } from "@testing-library/react";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { Toaster } from "./sonner";

describe("Sonner toast host theme authority", () => {
  it("does not import next-themes", () => {
    const src = readFileSync(resolve(__dirname, "sonner.tsx"), "utf8");
    expect(src).not.toMatch(/from ['"]next-themes['"]/);
    expect(src).toMatch(/@\/contexts\/ThemeContext/);
  });

  it("renders under ThemeProvider without throwing", () => {
    expect(() =>
      render(
        <ThemeProvider defaultTheme="light">
          <Toaster />
        </ThemeProvider>,
      ),
    ).not.toThrow();
  });
});
