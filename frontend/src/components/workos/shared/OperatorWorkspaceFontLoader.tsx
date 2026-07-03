import { useEffect } from "react";

const INTER_HREF =
  "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap";

export default function OperatorWorkspaceFontLoader() {
  useEffect(() => {
    const existing = document.querySelector(`link[data-operator-workspace-fonts="true"]`);
    if (existing) return;

    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = INTER_HREF;
    link.setAttribute("data-operator-workspace-fonts", "true");
    document.head.appendChild(link);
  }, []);

  return null;
}