/**
 * Read-only review surface for external artwork analysis (desktop → WorkOS).
 * Does not parse files; does not confirm Product Truth.
 */

import type { ArtworkAnalysisReviewSurfaceV1 } from "@/lib/artworkAnalysis/artworkAnalysisContractV1";

export type ArtworkAnalysisReviewPanelProps = {
  surface?: ArtworkAnalysisReviewSurfaceV1 | null;
  emptyHint?: string;
};

export function ArtworkAnalysisReviewPanel({
  surface = null,
  emptyHint = "Nicio analiză externă încărcată. Analiza fișierelor (SVG/DWG/DXF) aparține aplicației desktop.",
}: ArtworkAnalysisReviewPanelProps) {
  return (
    <section
      data-testid="artwork-analysis-review-panel"
      aria-label="Revizuire analiză artwork externă"
      style={{
        border: "1px solid var(--border, #d0d5dd)",
        borderRadius: 8,
        padding: "12px 14px",
        display: "grid",
        gap: 8,
        background: "var(--surface, #fafafa)",
      }}
    >
      <header style={{ display: "grid", gap: 4 }}>
        <strong style={{ fontSize: 14 }}>Analiză artwork (externă)</strong>
        <span style={{ fontSize: 12, opacity: 0.8 }}>
          Observed / proposed din desktop · confirmarea Product Truth rămâne la operator
        </span>
      </header>

      {!surface ? (
        <p data-testid="artwork-analysis-review-empty" style={{ margin: 0, fontSize: 13 }}>
          {emptyHint}
        </p>
      ) : (
        <dl
          data-testid="artwork-analysis-review-surface"
          style={{
            margin: 0,
            display: "grid",
            gridTemplateColumns: "auto 1fr",
            gap: "4px 12px",
            fontSize: 13,
          }}
        >
          <dt>analysis_id</dt>
          <dd style={{ margin: 0 }}>{surface.analysis_id}</dd>
          <dt>contract</dt>
          <dd style={{ margin: 0 }}>{surface.contract_version}</dd>
          <dt>sursă</dt>
          <dd style={{ margin: 0 }}>
            {surface.source_file_name || "—"}
            {surface.source_file_hash ? ` · ${surface.source_file_hash}` : ""}
          </dd>
          <dt>entități / grupuri</dt>
          <dd style={{ margin: 0 }}>
            {surface.entity_count} / {surface.group_count}
          </dd>
          <dt>măsurători / observații</dt>
          <dd style={{ margin: 0 }}>
            {surface.measurement_count} / {surface.observation_count}
            {surface.unconfirmed_observation_count > 0
              ? ` (${surface.unconfirmed_observation_count} neconfirmate)`
              : ""}
          </dd>
          <dt>binding-uri propuse</dt>
          <dd style={{ margin: 0 }}>
            {surface.suggested_binding_count}
            {surface.all_bindings_proposed ? " · toate proposed" : " · ATENȚIE: status invalid"}
          </dd>
          <dt>transport</dt>
          <dd style={{ margin: 0 }}>{surface.transport}</dd>
          <dt>adapter → Product Truth</dt>
          <dd style={{ margin: 0 }}>
            {surface.product_truth_writable_from_adapter
              ? "SCARIE: writable"
              : "blocat (consume-only)"}
          </dd>
        </dl>
      )}

      {surface?.notes?.length ? (
        <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, opacity: 0.85 }}>
          {surface.notes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
