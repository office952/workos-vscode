/**
 * BUILD 12 — Quote Acceptance Guard Indicator
 *
 * Displays readiness indicator for quote → order conversion.
 * Shows document snapshot eligibility and product readiness status.
 * Read-only, load-on-demand. No mutations.
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  getQuoteAcceptanceGuard,
  type QuoteAcceptanceGuardResponse,
  type QuoteAcceptanceGuardItem,
} from '@/api/orders';

interface QuoteAcceptanceGuardIndicatorProps {
  quoteId: number;
}

function getOverallStatusBadge(status: string) {
  switch (status) {
    case 'eligible':
      return <Badge variant="default" className="bg-green-600">Eligibil</Badge>;
    case 'blocked':
      return <Badge variant="destructive">Blocat</Badge>;
    case 'needs_acknowledgement':
      return <Badge variant="secondary" className="bg-yellow-600 text-white">Necesită confirmare</Badge>;
    default:
      return <Badge variant="outline">{status}</Badge>;
  }
}

function getGuardStatusIcon(status: string) {
  switch (status) {
    case 'eligible':
      return '✓';
    case 'blocked':
      return '✗';
    case 'warning':
      return '⚠';
    case 'info':
      return 'ℹ';
    default:
      return '?';
  }
}

function getGuardStatusColor(status: string) {
  switch (status) {
    case 'eligible':
      return 'text-green-600';
    case 'blocked':
      return 'text-red-600';
    case 'warning':
      return 'text-yellow-600';
    case 'info':
      return 'text-blue-600';
    default:
      return 'text-muted-foreground';
  }
}

function GuardItemRow({ item }: { item: QuoteAcceptanceGuardItem }) {
  return (
    <div className="flex items-start gap-2 py-1" data-testid={`guard-item-${item.guard}`}>
      <span className={`font-bold ${getGuardStatusColor(item.status)}`}>
        {getGuardStatusIcon(item.status)}
      </span>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium capitalize">
            {item.guard.replace(/_/g, ' ')}
          </span>
          <Badge variant="outline" className="text-xs">
            {item.status}
          </Badge>
        </div>
        <p className="text-xs text-muted-foreground mt-0.5">{item.detail}</p>
        {item.requires_acknowledgement && (
          <p className="text-xs text-yellow-600 mt-0.5">
            Necesită confirmare explicită la conversie
          </p>
        )}
      </div>
    </div>
  );
}

export function QuoteAcceptanceGuardIndicator({ quoteId }: QuoteAcceptanceGuardIndicatorProps) {
  const [data, setData] = useState<QuoteAcceptanceGuardResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const handleLoad = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getQuoteAcceptanceGuard(quoteId);
      setData(result);
      setLoaded(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to evaluate acceptance guard');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card data-testid="quote-acceptance-guard-section">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          Guard Acceptare Comandă
          {loaded && data && getOverallStatusBadge(data.overall_status)}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {!loaded && !loading && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleLoad}
            data-testid="load-acceptance-guard-btn"
          >
            Verifică eligibilitate conversie
          </Button>
        )}

        {loading && (
          <p className="text-sm text-muted-foreground" data-testid="loading-indicator">
            Se evaluează...
          </p>
        )}

        {error && (
          <p className="text-sm text-destructive" data-testid="error-message">
            Eroare: {error}
          </p>
        )}

        {loaded && data && (
          <div className="space-y-1" data-testid="guard-results">
            {data.guards.map((item) => (
              <GuardItemRow key={item.guard} item={item} />
            ))}
            {data.guards.length === 0 && (
              <p className="text-sm text-muted-foreground">
                Nu au fost evaluate guard-uri.
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}