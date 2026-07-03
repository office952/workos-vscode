/**
 * BUILD 12 — Order Document Snapshot Reference Section
 *
 * Displays the document snapshot reference linked to an order.
 * Read-only, load-on-demand. No mutations.
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  getOrderDocumentSnapshotReference,
  type OrderDocumentSnapshotReferenceResponse,
} from '@/api/orders';

interface OrderDocumentSnapshotSectionProps {
  orderId: number;
}

export function OrderDocumentSnapshotSection({ orderId }: OrderDocumentSnapshotSectionProps) {
  const [data, setData] = useState<OrderDocumentSnapshotReferenceResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const handleLoad = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getOrderDocumentSnapshotReference(orderId);
      setData(result);
      setLoaded(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load document snapshot reference');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card data-testid="order-document-snapshot-section">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          Referință Document Snapshot
          {loaded && data && (
            <Badge variant={data.has_document_snapshot ? 'default' : 'secondary'}>
              {data.has_document_snapshot ? 'Atașat' : 'Lipsă'}
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {!loaded && !loading && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleLoad}
            data-testid="load-document-snapshot-btn"
          >
            Încarcă referința document
          </Button>
        )}

        {loading && (
          <p className="text-sm text-muted-foreground" data-testid="loading-indicator">
            Se încarcă...
          </p>
        )}

        {error && (
          <p className="text-sm text-destructive" data-testid="error-message">
            Eroare: {error}
          </p>
        )}

        {loaded && data && !data.has_document_snapshot && (
          <p className="text-sm text-muted-foreground" data-testid="no-snapshot-message">
            Comanda a fost creată fără referință la un document snapshot aprobat.
          </p>
        )}

        {loaded && data && data.has_document_snapshot && data.reference && (
          <div className="space-y-2 text-sm" data-testid="snapshot-reference-details">
            <div className="grid grid-cols-2 gap-2">
              <span className="text-muted-foreground">Snapshot Code:</span>
              <span className="font-mono">{data.reference.snapshot_code || '—'}</span>

              <span className="text-muted-foreground">Status la acceptare:</span>
              <Badge variant="outline" className="w-fit">
                {data.reference.snapshot_status_at_acceptance}
              </Badge>

              <span className="text-muted-foreground">Versiune:</span>
              <span>{data.reference.snapshot_version ?? '—'}</span>

              <span className="text-muted-foreground">Content Hash:</span>
              <span className="font-mono text-xs truncate">
                {data.reference.snapshot_content_hash || '—'}
              </span>

              <span className="text-muted-foreground">Governance Status:</span>
              <Badge
                variant={
                  data.reference.governance_status_at_acceptance === 'eligible'
                    ? 'default'
                    : 'secondary'
                }
                className="w-fit"
              >
                {data.reference.governance_status_at_acceptance}
              </Badge>

              <span className="text-muted-foreground">Template:</span>
              <span>{data.reference.source_template_code || '—'}</span>

              <span className="text-muted-foreground">Dossier ID:</span>
              <span>{data.reference.source_dossier_id ?? '—'}</span>

              <span className="text-muted-foreground">Acceptat de:</span>
              <span>{data.reference.accepted_by || '—'}</span>

              <span className="text-muted-foreground">Acceptat la:</span>
              <span>
                {data.reference.accepted_at
                  ? new Date(data.reference.accepted_at).toLocaleString('ro-RO')
                  : '—'}
              </span>
            </div>

            {data.reference.source_trace_json && (
              <details className="mt-2">
                <summary className="text-xs text-muted-foreground cursor-pointer">
                  Trace detalii
                </summary>
                <pre className="mt-1 text-xs bg-muted p-2 rounded overflow-auto max-h-32">
                  {JSON.stringify(data.reference.source_trace_json, null, 2)}
                </pre>
              </details>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}