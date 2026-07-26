/**
 * Dry-run remediation inventory — NO writes.
 * Criteria for suspect workspaces (forward-fix build only).
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BACKEND = process.env.PW_BACKEND_URL ?? "http://127.0.0.1:8001";

async function listSuspectFromKnownIds() {
  // Probe known audit workspaces + recent create probe; full list API may not exist.
  const known = [
    "319c706e-fd7d-407a-9903-67f5c560085b", // IV6-87B98425 prior audit
    "ebfed730-eaf9-4e90-ad9e-aa949a061c7d", // IV6-3A52D29C prior audit
  ];

  // Also try listing via a lightweight scan if endpoint exists
  const suspects = [];

  for (const id of known) {
    try {
      const r = await fetch(`${BACKEND}/api/v1/intake-v6/workspaces/${id}`);
      if (!r.ok) {
        suspects.push({ id, error: r.status, note: "unavailable" });
        continue;
      }
      const ws = await r.json();
      const roles = ws.payload?.layer_role_setup?.layers || [];
      const artwork = ws.payload?.finish_setup?.artwork_finishes || [];
      const seg = ws.payload?.finish_setup?.segmented_background;
      const analysis = ws.payload?.svg_analysis_json;
      const fileName = analysis?.sourceFileName || ws.payload?.svg_source?.file_name;

      const logoAsSupport = roles.filter(
        (l) =>
          /logo/i.test(String(l.layer_key || l.layer_name || "")) &&
          l.confirmed_role === "support_panel",
      );
      const supportConfirmed = roles.some((l) => l.confirmed_role === "support_panel");
      const missingSeg = supportConfirmed && !seg?.status;
      const phantomArtwork =
        Array.isArray(artwork) &&
        artwork.length > 0 &&
        supportConfirmed &&
        !roles.some((l) => l.confirmed_role === "printed_artwork" || l.confirmed_role === "logo");

      const flags = [];
      if (logoAsSupport.length) flags.push("P2_logo_as_support");
      if (missingSeg) flags.push("P1_missing_segmented");
      if (phantomArtwork) flags.push("P3_phantom_artwork");

      suspects.push({
        id: ws.id,
        workspace_code: ws.workspace_code,
        title: ws.title,
        fileName,
        flags,
        impact: {
          composition: flags.includes("P2_logo_as_support") || flags.includes("P1_missing_segmented"),
          pricing: flags.includes("P2_logo_as_support") || flags.includes("P3_phantom_artwork"),
          offerOrderUnknown: true,
        },
        recommendation:
          flags.length === 0
            ? "No action (or already forward-fixed path unused)"
            : "Owner-gated remediation: re-open Straturi, re-confirm roles, clear phantom artwork_finishes, re-propose segmented if support confirmed. Do NOT auto-rewrite offers/orders.",
      });
    } catch (e) {
      suspects.push({ id, error: String(e) });
    }
  }

  return suspects;
}

async function main() {
  const suspects = await listSuspectFromKnownIds();
  const flagged = suspects.filter((s) => (s.flags || []).length > 0);
  const report = {
    at: new Date().toISOString(),
    mode: "dry-run",
    selectionCriteria: [
      "logo_* layer confirmed as support_panel",
      "support_panel confirmed but segmented_background null/absent",
      "artwork_finishes present without printed_artwork/logo confirmed roles",
    ],
    scannedKnownAuditWorkspaces: suspects.length,
    suspectCount: flagged.length,
    workspaces: suspects,
    note: "No historical data modified. Expand scan via DB SQL in a dedicated remediation build after owner GO.",
  };
  fs.writeFileSync(path.join(__dirname, "dry-run-remediation.json"), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
