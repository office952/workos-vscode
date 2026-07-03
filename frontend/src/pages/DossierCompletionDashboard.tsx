/**
 * BUILD 7 — Dossier Completion Dashboard (read-only).
 *
 * Displays descriptive dossier progress from entity JSON fields (local
 * non-empty checks). Does NOT evaluate canonical product-readiness or
 * quote gates — use Blueprint Dossier Studio for that.
 *
 * Rules:
 *   - Read-only display.
 *   - No canonical readiness / quote-gate truth on this page.
 *   - No editing from dashboard.
 *   - No auto-fixing missing fields.
 *   - No creating output blocks automatically.
 *   - No mutating ProductTemplate, Dossier, Quote, or Order.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { blueprintDossierApi, type BlueprintDossierEntity } from "@/api/blueprintDossier";
import { isMockEnabled } from "@/lib/mockGuard";

// ============================================================
// Types
// ============================================================

interface DossierSummary {
  id: number;
  template_id: number;
  template_code: string;
  dossier_version: number;
  status: string;
  sections_completed: number;
  sections_total: number;
  missing_sections: string[];
  owner_role: string | null;
  reviewer_role: string | null;
  reviewed_at: string | null;
}

// ============================================================
// Helpers
// ============================================================

const DOSSIER_SECTIONS_KEYS = [
  "sections_json",
  "variants_json",
  "layers_json",
  "task_rules_json",
  "time_assumptions_json",
  "costengine_mapping_json",
  "quote_readiness_json",
  "output_blocks_json",
  "visual_prompt_blocks_json",
  "production_notes_json",
  "qc_checkpoints_json",
  "risks_json",
  "completion_state_json",
] as const satisfies readonly (keyof BlueprintDossierEntity)[];

/**
 * Display-only descriptive progress: counts non-empty *_json fields.
 * Not canonical readiness. Backend GET /api/v1/product-readiness/blueprints/{id}
 * remains the authority for quote gates (see Blueprint Dossier Studio).
 */
function computeDossierSummary(dossier: BlueprintDossierEntity): DossierSummary {
  const total = DOSSIER_SECTIONS_KEYS.length;
  let completed = 0;
  const missing: string[] = [];

  for (const key of DOSSIER_SECTIONS_KEYS) {
    const value = dossier[key];
    if (value && value !== "null" && value !== "[]" && value !== "{}") {
      completed++;
    } else {
      missing.push(key.replace("_json", ""));
    }
  }

  return {
    id: dossier.id,
    template_id: dossier.template_id,
    template_code: dossier.template_code,
    dossier_version: dossier.dossier_version,
    status: dossier.status,
    sections_completed: completed,
    sections_total: total,
    missing_sections: missing,
    owner_role: dossier.owner_role,
    reviewer_role: dossier.reviewer_role,
    reviewed_at: dossier.reviewed_at,
  };
}

function getStatusColor(status: string): string {
  switch (status) {
    case "approved":
      return "bg-green-500/20 text-green-400 border-green-500/30";
    case "needs_review":
      return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
    case "draft":
      return "bg-slate-500/20 text-slate-400 border-slate-500/30";
    case "blocked":
      return "bg-red-500/20 text-red-400 border-red-500/30";
    case "deprecated":
      return "bg-gray-500/20 text-gray-400 border-gray-500/30";
    default:
      return "bg-slate-500/20 text-slate-400 border-slate-500/30";
  }
}

function getCompletionColor(completed: number, total: number): string {
  const pct = total > 0 ? completed / total : 0;
  if (pct >= 0.8) return "text-green-400";
  if (pct >= 0.5) return "text-yellow-400";
  return "text-red-400";
}

// ============================================================
// Component
// ============================================================

export default function DossierCompletionDashboard() {
  const [summaries, setSummaries] = useState<DossierSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadDossiers() {
      try {
        setLoading(true);
        setError(null);

        const response = await blueprintDossierApi.list({ skip: 0, limit: 100 });
        const items = response?.items ?? [];

        if (!cancelled) {
          const computed = items.map(computeDossierSummary);
          setSummaries(computed);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Eroare la incarcarea dossierelor"
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadDossiers();
    return () => {
      cancelled = true;
    };
  }, []);

  // --- Stats ---
  const totalDossiers = summaries.length;
  const approvedCount = summaries.filter((s) => s.status === "approved").length;
  const draftCount = summaries.filter((s) => s.status === "draft").length;
  const blockedCount = summaries.filter((s) => s.status === "blocked").length;
  const avgCompletion =
    totalDossiers > 0
      ? Math.round(
          summaries.reduce(
            (acc, s) => acc + (s.sections_completed / s.sections_total) * 100,
            0
          ) / totalDossiers
        )
      : 0;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">
            Progres descriptiv dosar
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Vizualizare read-only — secțiuni completate local (câmpuri JSON populate).
            Readiness oficială: vezi Blueprint Dossier Studio.
          </p>
        </div>
        {isMockEnabled() && (
          <Badge variant="outline" className="border-amber-500/50 text-amber-400">
            MOCK
          </Badge>
        )}
      </div>

      <p className="text-xs text-slate-500 border border-slate-700 rounded-lg px-3 py-2 bg-slate-900/60">
        Necesită verificare readiness în Studio pentru gate-uri ofertare. Procentele de mai jos
        nu înlocuiesc evaluarea backend product-readiness.
      </p>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-slate-900 border-slate-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-slate-400">Total Dossiere</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-white">{totalDossiers}</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-900 border-slate-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-slate-400">Status dossier: aprobate</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-green-400">{approvedCount}</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-900 border-slate-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-slate-400">Draft / Blocate</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-yellow-400">
              {draftCount} / <span className="text-red-400">{blockedCount}</span>
            </p>
          </CardContent>
        </Card>
        <Card className="bg-slate-900 border-slate-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-slate-400">
              Progres descriptiv mediu (local)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-blue-400">{avgCompletion}%</p>
          </CardContent>
        </Card>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="space-y-3">
          <Skeleton className="h-12 w-full bg-slate-800" />
          <Skeleton className="h-12 w-full bg-slate-800" />
          <Skeleton className="h-12 w-full bg-slate-800" />
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <Card className="bg-red-900/20 border-red-500/30">
          <CardContent className="p-4">
            <p className="text-red-400">Eroare: {error}</p>
            <p className="text-sm text-slate-400 mt-1">
              Datele nu pot fi incarcate. Verificati conexiunea la backend.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!loading && !error && summaries.length === 0 && (
        <Card className="bg-slate-900 border-slate-700">
          <CardContent className="p-8 text-center">
            <p className="text-slate-400">
              Nu exista Blueprint Dossiere inregistrate.
            </p>
            <p className="text-sm text-slate-500 mt-1">
              Creati un dossier din ProductSystem pentru a vedea progresul descriptiv local.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Table */}
      {!loading && !error && summaries.length > 0 && (
        <Card className="bg-slate-900 border-slate-700">
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow className="border-slate-700 hover:bg-slate-800/50">
                  <TableHead className="text-slate-400">Template Code</TableHead>
                  <TableHead className="text-slate-400">Status dossier</TableHead>
                  <TableHead className="text-slate-400">Versiune</TableHead>
                  <TableHead className="text-slate-400">Secțiuni completate (local)</TableHead>
                  <TableHead className="text-slate-400">Secțiuni lipsă (local)</TableHead>
                  <TableHead className="text-slate-400">Owner</TableHead>
                  <TableHead className="text-slate-400">Reviewer</TableHead>
                  <TableHead className="text-slate-400">Reviewed At</TableHead>
                  <TableHead className="text-slate-400">Actiuni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {summaries.map((s) => (
                  <TableRow
                    key={s.id}
                    className="border-slate-700 hover:bg-slate-800/50"
                  >
                    <TableCell className="font-mono text-sm text-white">
                      {s.template_code}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={getStatusColor(s.status)}
                      >
                        {s.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-300">
                      v{s.dossier_version}
                    </TableCell>
                    <TableCell>
                      <span
                        className={`font-semibold ${getCompletionColor(
                          s.sections_completed,
                          s.sections_total
                        )}`}
                      >
                        {s.sections_completed}/{s.sections_total}
                      </span>
                      <span className="text-slate-500 ml-1 text-xs">
                        ({Math.round((s.sections_completed / s.sections_total) * 100)}
                        %)
                      </span>
                    </TableCell>
                    <TableCell>
                      {s.missing_sections.length > 0 ? (
                        <span className="text-xs text-slate-400">
                          {s.missing_sections.length} lipsa
                        </span>
                      ) : (
                        <span className="text-xs text-green-400" title="Toate câmpurile JSON verificate sunt populate — nu implică readiness ofertare">
                          Populate local
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-slate-300">
                      {s.owner_role || "—"}
                    </TableCell>
                    <TableCell className="text-sm text-slate-300">
                      {s.reviewer_role || "—"}
                    </TableCell>
                    <TableCell className="text-sm text-slate-400">
                      {s.reviewed_at
                        ? new Date(s.reviewed_at).toLocaleDateString("ro-RO")
                        : "—"}
                    </TableCell>
                    <TableCell>
                      <Link
                        to="/product-system/blueprint-dossier"
                        className="text-xs text-blue-400 hover:text-blue-300 underline"
                        title="Readiness oficială și gate-uri ofertare"
                      >
                        Studio — readiness
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}