import { useState, useMemo, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useBackendData } from "@/hooks/useBackendData";
import {
  listClients,
  getClientFiscalDisplayStatus,
  getClientFiscalDisplayLabel,
  type ClientEntity,
  type ClientFiscalDisplayStatus,
} from "@/lib/api";
import {
  Users,
  Search,
  Building2,
  FileText,
  ClipboardList,
  Inbox,
  ChevronRight,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
} from "lucide-react";

interface ClientSummary {
  name: string;
  entityId?: number;
  contactPerson: string;
  cui?: string;
  address?: string;
  city?: string;
  identityType?: ClientEntity["identity_type"];
  fiscalStatus: ClientFiscalDisplayStatus;
  channel?: string;
  intakeCount: number;
  quoteCount: number;
  orderCount: number;
  activeIntakes: number;
  openQuotes: number;
  activeOrders: number;
  totalRevenue: number;
  lastActivity: string;
  hasFiscalData: boolean;
  entityOnly: boolean;
}

function normalizeClientKey(name: string): string {
  return name.trim().toLowerCase();
}

function formatCurrency(val: number) {
  return val.toLocaleString("ro-RO", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleDateString("ro-RO", { day: "2-digit", month: "short", year: "numeric" });
}

function deriveFiscalStatusFromIntake(
  hasFiscalType: boolean,
  cui?: string
): ClientFiscalDisplayStatus {
  if (hasFiscalType && cui) return "saved";
  if (hasFiscalType && !cui) return "missing_cui";
  return "non_fiscal";
}

function createSummaryFromEntity(entity: ClientEntity): ClientSummary {
  const fiscalStatus = getClientFiscalDisplayStatus(entity);
  return {
    name: entity.name,
    entityId: entity.id,
    contactPerson: entity.contact_person || "—",
    cui: entity.cui,
    address: entity.address,
    city: entity.city,
    identityType: entity.identity_type,
    fiscalStatus,
    channel: undefined,
    intakeCount: 0,
    quoteCount: 0,
    orderCount: 0,
    activeIntakes: 0,
    openQuotes: 0,
    activeOrders: 0,
    totalRevenue: 0,
    lastActivity: entity.updated_at || entity.created_at || new Date(0).toISOString(),
    hasFiscalData: fiscalStatus === "saved",
    entityOnly: true,
  };
}

function FiscalStatusBadge({ status }: { status: ClientFiscalDisplayStatus }) {
  if (status === "saved") {
    return (
      <span className="inline-flex items-center gap-1 rounded border border-emerald-300 bg-emerald-50 px-1.5 py-0.5 text-[9px] font-semibold text-emerald-800 dark:border-emerald-800/30 dark:bg-emerald-900/30 dark:text-emerald-400">
        <CheckCircle2 className="w-2.5 h-2.5" />
        {getClientFiscalDisplayLabel(status)}
      </span>
    );
  }
  if (status === "missing_cui") {
    return (
      <span className="inline-flex items-center gap-1 rounded border border-red-300 bg-red-50 px-1.5 py-0.5 text-[9px] font-semibold text-red-800 dark:border-red-800/30 dark:bg-red-900/30 dark:text-red-400">
        <AlertTriangle className="w-2.5 h-2.5" />
        {getClientFiscalDisplayLabel(status)}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded border border-amber-300 bg-amber-50 px-1.5 py-0.5 text-[9px] font-semibold text-amber-900 dark:border-amber-800/30 dark:bg-amber-900/30 dark:text-amber-400">
      <ShieldAlert className="w-2.5 h-2.5" />
      {getClientFiscalDisplayLabel(status)}
    </span>
  );
}

export default function Clients() {
  const navigate = useNavigate();
  const { intakes, quotes, orders, loading } = useBackendData();
  const [search, setSearch] = useState("");
  const [entities, setEntities] = useState<ClientEntity[]>([]);
  const [entitiesLoading, setEntitiesLoading] = useState(true);
  const [entitiesError, setEntitiesError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setEntitiesLoading(true);
    setEntitiesError(null);
    listClients()
      .then((rows) => {
        if (!cancelled) setEntities(rows);
      })
      .catch(() => {
        if (!cancelled) setEntitiesError("Nu am putut încărca registrul de clienți.");
      })
      .finally(() => {
        if (!cancelled) setEntitiesLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const clients = useMemo(() => {
    const map = new Map<string, ClientSummary>();

    for (const entity of entities) {
      map.set(normalizeClientKey(entity.name), createSummaryFromEntity(entity));
    }

    for (const intake of intakes) {
      const key = normalizeClientKey(intake.client);
      if (!map.has(key)) {
        map.set(key, {
          name: intake.client,
          contactPerson: intake.contactPerson,
          cui: intake.identity?.cui,
          channel: intake.channel,
          fiscalStatus: deriveFiscalStatusFromIntake(
            intake.identity?.type === "fiscal",
            intake.identity?.cui
          ),
          intakeCount: 0,
          quoteCount: 0,
          orderCount: 0,
          activeIntakes: 0,
          openQuotes: 0,
          activeOrders: 0,
          totalRevenue: 0,
          lastActivity: intake.updatedAt || intake.createdAt,
          hasFiscalData:
            intake.identity?.type === "fiscal" && Boolean(intake.identity?.cui),
          entityOnly: false,
        });
      }
      const c = map.get(key)!;
      c.entityOnly = false;
      c.intakeCount++;
      if (["new", "in_review", "needs_info", "ready_for_quote"].includes(intake.status)) {
        c.activeIntakes++;
      }
      if (!c.contactPerson || c.contactPerson === "—") {
        c.contactPerson = intake.contactPerson;
      }
      if (!c.cui && intake.identity?.cui) c.cui = intake.identity.cui;
      if (!c.channel) c.channel = intake.channel;
      if (!c.entityId) {
        c.fiscalStatus = deriveFiscalStatusFromIntake(
          intake.identity?.type === "fiscal" || c.fiscalStatus === "saved",
          c.cui
        );
        c.hasFiscalData = c.fiscalStatus === "saved";
      }
      if (intake.updatedAt && intake.updatedAt > c.lastActivity) c.lastActivity = intake.updatedAt;
    }

    for (const quote of quotes) {
      const key = normalizeClientKey(quote.client);
      if (!map.has(key)) {
        map.set(key, {
          name: quote.client,
          contactPerson: quote.contactPerson,
          fiscalStatus: "non_fiscal",
          intakeCount: 0,
          quoteCount: 0,
          orderCount: 0,
          activeIntakes: 0,
          openQuotes: 0,
          activeOrders: 0,
          totalRevenue: 0,
          lastActivity: quote.createdAt,
          hasFiscalData: false,
          entityOnly: false,
        });
      }
      const c = map.get(key)!;
      c.entityOnly = false;
      c.quoteCount++;
      if (["draft", "priced", "sent", "viewed", "negotiating"].includes(quote.status)) {
        c.openQuotes++;
      }
      if (!c.contactPerson || c.contactPerson === "—") {
        c.contactPerson = quote.contactPerson;
      }
      if (quote.createdAt > c.lastActivity) c.lastActivity = quote.createdAt;
    }

    for (const order of orders) {
      const key = normalizeClientKey(order.client);
      if (!map.has(key)) {
        map.set(key, {
          name: order.client,
          contactPerson: order.contactPerson,
          fiscalStatus: "non_fiscal",
          intakeCount: 0,
          quoteCount: 0,
          orderCount: 0,
          activeIntakes: 0,
          openQuotes: 0,
          activeOrders: 0,
          totalRevenue: 0,
          lastActivity: order.createdAt,
          hasFiscalData: false,
          entityOnly: false,
        });
      }
      const c = map.get(key)!;
      c.entityOnly = false;
      c.orderCount++;
      c.totalRevenue += order.totalAmount;
      if (["created", "confirmed", "locked", "in_execution"].includes(order.status)) {
        c.activeOrders++;
      }
      if (!c.contactPerson || c.contactPerson === "—") {
        c.contactPerson = order.contactPerson;
      }
      if (order.createdAt > c.lastActivity) c.lastActivity = order.createdAt;
    }

    return Array.from(map.values()).sort((a, b) => b.lastActivity.localeCompare(a.lastActivity));
  }, [entities, intakes, quotes, orders]);

  const filtered = useMemo(() => {
    if (!search.trim()) return clients;
    const q = search.toLowerCase();
    return clients.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        c.contactPerson.toLowerCase().includes(q) ||
        (c.cui && c.cui.toLowerCase().includes(q)) ||
        (c.address && c.address.toLowerCase().includes(q)) ||
        (c.city && c.city.toLowerCase().includes(q))
    );
  }, [clients, search]);

  if (loading || entitiesLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-10 w-10 animate-spin rounded-full border-b-2 border-blue-600 dark:border-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-blue-600/10 p-2 dark:bg-blue-600/15">
            <Users className="h-5 w-5 text-blue-700 dark:text-blue-400" />
          </div>
          <div>
            <h1 className="text-[18px] font-bold text-wo-text-primary">Clienți</h1>
            <p className="text-[12px] text-wo-text-muted">
              {clients.length} clienți · {entities.length} în registrul entități
            </p>
          </div>
        </div>
      </div>

      {entitiesError && (
        <div className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-[12px] text-amber-900 dark:border-amber-800/30 dark:bg-amber-900/20 dark:text-amber-300">
          {entitiesError} Lista afișează doar activitatea comercială.
        </div>
      )}

      <div className="flex w-full max-w-md items-center gap-2 rounded-lg border border-wo-border-subtle bg-wo-surface-raised px-3 py-2 focus-within:border-blue-500/50">
        <Search className="h-4 w-4 shrink-0 text-wo-text-muted" />
        <input
          type="text"
          placeholder="Caută client, CUI, adresă, oraș, contact..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-transparent text-[13px] text-wo-text-primary outline-none placeholder:text-wo-text-dim"
        />
      </div>

      <div className="space-y-2">
        {filtered.length === 0 ? (
          <div className="py-12 text-center text-[13px] text-wo-text-muted">
            Nu au fost găsiți clienți.
          </div>
        ) : (
          filtered.map((client) => (
            <div
              key={client.entityId ? `entity-${client.entityId}` : client.name}
              onClick={() => navigate(`/clients/${encodeURIComponent(client.name)}`)}
              className="group cursor-pointer rounded-lg border border-wo-border-subtle bg-wo-surface-raised p-4 transition-all hover:border-blue-600/40 hover:bg-wo-surface-raised"
            >
              <div className="flex items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-wo-surface-inset">
                    <Building2 className="h-4 w-4 text-wo-text-muted" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="truncate text-[14px] font-semibold text-wo-text-primary">{client.name}</span>
                      <FiscalStatusBadge status={client.fiscalStatus} />
                      {client.entityOnly && (
                        <span className="rounded border border-blue-300 bg-blue-50 px-1.5 py-0.5 text-[9px] font-semibold text-blue-800 dark:border-blue-800/30 dark:bg-blue-900/30 dark:text-blue-300">
                          Registru entități
                        </span>
                      )}
                    </div>
                    <div className="mt-0.5 flex flex-wrap items-center gap-3">
                      <span className="text-[11px] text-wo-text-muted">{client.contactPerson}</span>
                      {client.cui && (
                        <span className="font-mono text-[11px] text-wo-text-secondary">CUI: {client.cui}</span>
                      )}
                      {(client.address || client.city) && (
                        <span className="max-w-[280px] truncate text-[11px] text-wo-text-dim">
                          {[client.address, client.city].filter(Boolean).join(", ")}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex shrink-0 items-center gap-4">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1 text-[11px]" title="Cereri">
                      <Inbox className="h-3.5 w-3.5 text-wo-text-muted" />
                      <span className="text-wo-text-secondary">{client.intakeCount}</span>
                      {client.activeIntakes > 0 && (
                        <span className="font-semibold text-blue-700 dark:text-blue-400">({client.activeIntakes})</span>
                      )}
                    </div>
                    <div className="flex items-center gap-1 text-[11px]" title="Oferte">
                      <FileText className="h-3.5 w-3.5 text-wo-text-muted" />
                      <span className="text-wo-text-secondary">{client.quoteCount}</span>
                      {client.openQuotes > 0 && (
                        <span className="font-semibold text-violet-700 dark:text-purple-400">({client.openQuotes})</span>
                      )}
                    </div>
                    <div className="flex items-center gap-1 text-[11px]" title="Comenzi">
                      <ClipboardList className="h-3.5 w-3.5 text-wo-text-muted" />
                      <span className="text-wo-text-secondary">{client.orderCount}</span>
                      {client.activeOrders > 0 && (
                        <span className="font-semibold text-emerald-700 dark:text-emerald-400">({client.activeOrders})</span>
                      )}
                    </div>
                  </div>

                  {client.totalRevenue > 0 && (
                    <div className="text-right">
                      <p className="text-[13px] font-bold text-wo-text-primary">{formatCurrency(client.totalRevenue)} RON</p>
                      <p className="text-[10px] text-wo-text-dim">venit total</p>
                    </div>
                  )}

                  <div className="min-w-[80px] text-right">
                    <p className="text-[11px] text-wo-text-muted">{formatDate(client.lastActivity)}</p>
                  </div>

                  <ChevronRight className="h-4 w-4 text-wo-text-dim transition-colors group-hover:text-blue-700 dark:group-hover:text-blue-400" />
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
