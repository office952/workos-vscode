import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Calculator, Loader2, ShieldAlert, Info } from 'lucide-react';

import {
  commercialMarkupPoliciesAdminApi,
  type CommercialMarkupDryRunResult,
  type CommercialMarkupPolicy,
  type CommercialMarkupPolicyConfig,
} from '@/api/commercialMarkupPoliciesAdmin';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

function fmtMoney(v?: number | null, currency?: string | null): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  return `${v.toFixed(2)} ${currency ?? ''}`.trim();
}

function emptyConfig(): CommercialMarkupPolicyConfig {
  return {
    scope_types: [],
    markup_types: [],
    rounding_modes: [],
    applies_to: [],
    statuses: [],
    conflict_resolution: '',
    separation_notice: 'Commercial markup policy is separate from Material Registry unit_cost.',
    no_write_notice: 'Dry-run only. No material, ProductSystem, quote, order, or CostEngine state is changed.',
  };
}

function PolicyStatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    active: { label: "Active", cls: "border-emerald-700/50 bg-emerald-900/25 text-emerald-300" },
    draft: { label: "Draft", cls: "border-amber-700/50 bg-amber-900/25 text-amber-300" },
    archived: { label: "Archived", cls: "border-slate-700/50 bg-slate-800/40 text-slate-500" },
  };
  const cfg = map[status] ?? { label: status, cls: "border-slate-700/50 bg-slate-800/40 text-slate-400" };
  return (
    <Badge variant="outline" className={`px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${cfg.cls}`}>
      {cfg.label}
    </Badge>
  );
}

function ScopeBadge({ scopeType }: { scopeType: string }) {
  const map: Record<string, { cls: string }> = {
    global: { cls: "border-blue-700/50 bg-blue-900/25 text-blue-300" },
    category: { cls: "border-violet-700/50 bg-violet-900/25 text-violet-300" },
    material: { cls: "border-cyan-700/50 bg-cyan-900/25 text-cyan-300" },
  };
  const cfg = map[scopeType] ?? { cls: "border-slate-700/50 bg-slate-800/40 text-slate-400" };
  return (
    <Badge variant="outline" className={`px-2 py-0.5 text-[10px] font-medium capitalize ${cfg.cls}`}>
      {scopeType}
    </Badge>
  );
}

export default function CommercialMarkupPolicies() {
  const [policies, setPolicies] = useState<CommercialMarkupPolicy[]>([]);
  const [config, setConfig] = useState<CommercialMarkupPolicyConfig>(emptyConfig());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [materialCode, setMaterialCode] = useState('DEV-SMOKE-LED-MODULE');
  const [quantity, setQuantity] = useState('1');
  const [dryRunLoading, setDryRunLoading] = useState(false);
  const [dryRunError, setDryRunError] = useState<string | null>(null);
  const [dryRunResult, setDryRunResult] = useState<CommercialMarkupDryRunResult | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [cfg, rows] = await Promise.all([
          commercialMarkupPoliciesAdminApi.config(),
          commercialMarkupPoliciesAdminApi.list(),
        ]);
        setConfig(cfg);
        setPolicies(rows);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Eroare la încărcarea politicilor');
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, []);

  const filtered = useMemo(() => {
    if (statusFilter === 'all') return policies;
    return policies.filter((row) => row.status === statusFilter);
  }, [policies, statusFilter]);

  const stats = useMemo(() => {
    const total = policies.length;
    const active = policies.filter((p) => p.status === 'active').length;
    const draft = policies.filter((p) => p.status === 'draft').length;
    const archived = policies.filter((p) => p.status === 'archived').length;
    return { total, active, draft, archived };
  }, [policies]);

  const runDryRun = async () => {
    const parsedQuantity = Number(quantity);
    setDryRunLoading(true);
    setDryRunError(null);
    try {
      const result = await commercialMarkupPoliciesAdminApi.dryRun({
        material_code: materialCode.trim(),
        quantity: Number.isFinite(parsedQuantity) && parsedQuantity > 0 ? parsedQuantity : 1,
      });
      setDryRunResult(result);
    } catch (err) {
      setDryRunError(err instanceof Error ? err.message : 'Eroare dry-run');
      setDryRunResult(null);
    } finally {
      setDryRunLoading(false);
    }
  };

  return (
    <div className="space-y-5 w-full">
      {/* Explanatory panel */}
      <div className="flex items-start gap-3 rounded-xl border border-slate-800/60 bg-slate-900/40 px-5 py-4">
        <ShieldAlert className="mt-0.5 h-4 w-4 text-cyan-400 shrink-0" />
        <div className="space-y-1 text-[12px] text-slate-300">
          <p className="font-medium text-slate-200">{config.separation_notice}</p>
          <p className="text-slate-500">{config.no_write_notice}</p>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-800/40 bg-red-900/15 px-4 py-3 text-[12px] text-red-300 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {[
          { label: 'Total policies', value: stats.total, cls: 'text-slate-100' },
          { label: 'Active', value: stats.active, cls: 'text-emerald-400' },
          { label: 'Draft', value: stats.draft, cls: 'text-amber-400' },
          { label: 'Archived', value: stats.archived, cls: 'text-slate-500' },
        ].map((item) => (
          <Card key={item.label} className="border-slate-800/60 bg-slate-950/70 shadow-none">
            <CardContent className="px-4 py-3">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-600">{item.label}</p>
              <p className={`text-[22px] font-bold mt-1 ${item.cls}`}>{item.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Policies table */}
      <Card className="border-slate-800/60 bg-slate-950/60 shadow-none overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between gap-3 px-5 py-4 border-b border-slate-800/50">
          <div>
            <CardTitle className="text-[14px] font-semibold text-slate-100">Reguli comerciale</CardTitle>
            <CardDescription className="text-[11px] text-slate-500 mt-0.5">
              Ordinea și prioritatea regulilor aplicate peste costul materialului.
            </CardDescription>
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[160px] border-slate-700/60 bg-slate-900/60 text-[12px] text-slate-300 h-8">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Toate statusurile</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="archived">Archived</SelectItem>
            </SelectContent>
          </Select>
        </CardHeader>
        <CardContent className="px-0 pb-0 pt-0">
          {loading ? (
            <div className="flex items-center gap-2 py-10 justify-center text-[12px] text-slate-500">
              <Loader2 className="w-4 h-4 animate-spin" />
              Se încarcă politicile...
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-10 text-slate-500">
              <Info className="w-5 h-5" />
              <p className="text-[12px]">Nicio politică pentru filtrul selectat.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-800/50 hover:bg-transparent">
                    <TableHead className="text-[10px] font-bold uppercase tracking-wider text-slate-600 px-5">Nivel</TableHead>
                    <TableHead className="text-[10px] font-bold uppercase tracking-wider text-slate-600">Target</TableHead>
                    <TableHead className="text-[10px] font-bold uppercase tracking-wider text-slate-600">Markup</TableHead>
                    <TableHead className="text-[10px] font-bold uppercase tracking-wider text-slate-600">Status</TableHead>
                    <TableHead className="text-[10px] font-bold uppercase tracking-wider text-slate-600 text-center">Prioritate</TableHead>
                    <TableHead className="text-[10px] font-bold uppercase tracking-wider text-slate-600">Perioadă validitate</TableHead>
                    <TableHead className="text-[10px] font-bold uppercase tracking-wider text-slate-600">Note</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.map((policy) => (
                    <TableRow key={policy.id} className="border-slate-800/40 hover:bg-slate-900/40 transition-colors">
                      <TableCell className="px-5 py-3">
                        <ScopeBadge scopeType={policy.scope_type} />
                      </TableCell>
                      <TableCell className="py-3">
                        <span className="text-[12px] font-medium text-slate-200">{policy.scope_value}</span>
                      </TableCell>
                      <TableCell className="py-3">
                        <div className="flex items-center gap-1.5">
                          <span className="text-[12px] font-mono text-slate-300">
                            {policy.markup_percent != null ? `${policy.markup_percent}%` : ''}
                            {policy.markup_fixed != null ? `+${policy.markup_fixed}` : ''}
                          </span>
                          <span className="text-[10px] text-slate-600">{policy.markup_type}</span>
                        </div>
                      </TableCell>
                      <TableCell className="py-3">
                        <PolicyStatusBadge status={policy.status} />
                      </TableCell>
                      <TableCell className="py-3 text-center">
                        <span className="text-[12px] font-mono text-slate-400">{policy.priority}</span>
                      </TableCell>
                      <TableCell className="py-3">
                        <div className="text-[11px] text-slate-500 space-y-0.5">
                          <p>{policy.valid_from ?? '—'}</p>
                          <p>{policy.valid_to ?? '—'}</p>
                        </div>
                      </TableCell>
                      <TableCell className="py-3 max-w-[180px]">
                        <p className="text-[11px] text-slate-600 truncate" title={policy.notes ?? undefined}>
                          {policy.notes ?? '—'}
                        </p>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Dry-run simulation */}
      <Card className="border-slate-800/60 bg-slate-950/60 shadow-none">
        <CardHeader className="px-5 py-4 border-b border-slate-800/50">
          <CardTitle className="text-[14px] font-semibold text-slate-100">Simulare markup comercial</CardTitle>
          <CardDescription className="text-[11px] text-slate-500 mt-0.5">
            Testează aplicarea regulilor pe un material. Nu modifică nimic în sistem.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 px-5 pt-4 pb-5">
          <div className="grid grid-cols-1 md:grid-cols-[1fr_120px_auto] gap-3 items-end">
            <div className="space-y-1.5">
              <Label htmlFor="markup_material_code" className="text-[11px] font-medium text-slate-400">Cod material</Label>
              <Input
                id="markup_material_code"
                value={materialCode}
                onChange={(e) => setMaterialCode(e.target.value)}
                className="border-slate-700/60 bg-slate-900/60 text-[12px] text-slate-200 h-9"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="markup_quantity" className="text-[11px] font-medium text-slate-400">Cantitate</Label>
              <Input
                id="markup_quantity"
                type="number"
                min={1}
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                className="border-slate-700/60 bg-slate-900/60 text-[12px] text-slate-200 h-9"
              />
            </div>
            <Button
              onClick={runDryRun}
              disabled={dryRunLoading || !materialCode.trim()}
              className="h-9 bg-slate-800 text-slate-200 hover:bg-slate-700 border border-slate-700/60"
            >
              {dryRunLoading ? <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" /> : <Calculator className="w-3.5 h-3.5 mr-2" />}
              Run dry-run
            </Button>
          </div>

          {dryRunError && (
            <div className="rounded-lg border border-red-800/40 bg-red-900/15 px-4 py-3 text-[12px] text-red-300 flex items-center gap-2">
              <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
              {dryRunError}
            </div>
          )}

          {dryRunResult && (
            <div className="space-y-3 pt-2">
              <div className="grid grid-cols-2 gap-2 md:grid-cols-3 xl:grid-cols-6">
                {[
                  { label: 'Cost unitar', value: fmtMoney(dryRunResult.unit_cost, dryRunResult.currency) },
                  { label: 'Cost total bază', value: fmtMoney(dryRunResult.base_cost_total, dryRunResult.currency) },
                  { label: 'Adaos aplicat', value: fmtMoney(dryRunResult.markup_amount, dryRunResult.currency) },
                  { label: 'Preț unitar (fără TVA)', value: fmtMoney(dryRunResult.commercial_unit_price, dryRunResult.currency) },
                  { label: 'Total comercial', value: fmtMoney(dryRunResult.commercial_total_price, dryRunResult.currency) },
                  { label: 'TVA mode', value: dryRunResult.vat_mode ?? '—' },
                ].map((item) => (
                  <div key={item.label} className="rounded-lg border border-slate-800/50 bg-slate-900/40 px-3 py-2.5">
                    <p className="text-[10px] text-slate-600 uppercase tracking-wide">{item.label}</p>
                    <p className="text-[13px] font-medium text-slate-200 mt-0.5">{item.value}</p>
                  </div>
                ))}
              </div>

              <div className="rounded-lg border border-slate-800/50 bg-slate-900/40 px-4 py-3 text-[12px] text-slate-300">
                <span className="text-slate-500">Politică aplicată: </span>
                {dryRunResult.applied_policy
                  ? `${dryRunResult.applied_policy.scope_type}:${dryRunResult.applied_policy.scope_value} (${dryRunResult.applied_policy.markup_type})`
                  : 'none'}
              </div>

              {dryRunResult.warnings.length > 0 && (
                <div className="rounded-lg border border-amber-800/40 bg-amber-900/15 px-4 py-3 space-y-1.5">
                  <p className="text-[11px] font-semibold text-amber-300 uppercase tracking-wide">Warnings</p>
                  {dryRunResult.warnings.map((warning) => (
                    <div key={`${warning.code}-${warning.message}`} className="flex items-start gap-2 text-[12px] text-amber-200">
                      <AlertTriangle className="w-3 h-3 mt-0.5 shrink-0" />
                      <span>{warning.code}: {warning.message}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}