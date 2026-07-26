import { useCallback, useEffect, useMemo, useState } from "react";
import {
  operationalRegistryApi,
  type FieldInstallationTeam,
  type FieldInstallationTeamStatus,
  type OperatorRegistryEmployee,
} from "@/api/operationalRegistry";
import {
  computeFieldInstallationEligibility,
  deriveFieldCapabilities,
  orderInstallationRef,
  suggestRoleOnSite,
  type FieldEligibilityStatus,
} from "@/lib/fieldInstallationEligibility";
import {
  AlertTriangle,
  HardHat,
  Loader2,
  MapPin,
  Plus,
  Trash2,
  Users,
  Play,
  CheckCircle2,
  Camera,
} from "lucide-react";

const TEAM_STATUS_OPTIONS: Array<{ value: FieldInstallationTeamStatus; label: string }> = [
  { value: "draft", label: "Draft" },
  { value: "planned", label: "Planificat" },
  { value: "in_progress", label: "În desfășurare" },
  { value: "completed", label: "Finalizat" },
  { value: "cancelled", label: "Anulat" },
];

const ROLE_OPTIONS = [
  { value: "montator", label: "Montator" },
  { value: "electrician", label: "Electrician" },
  { value: "colantator", label: "Colantator" },
  { value: "asamblare", label: "Ansamblare" },
];

function EligibilityBadge({ status }: { status: FieldEligibilityStatus }) {
  const cfg = {
    authorized: "bg-emerald-900/40 text-emerald-300 border-emerald-700",
    not_authorized: "bg-amber-900/40 text-amber-300 border-amber-700",
    unverified: "bg-slate-800/60 text-slate-400 border-slate-600",
  }[status];
  const label = {
    authorized: "Autorizat teren",
    not_authorized: "Neautorizat teren",
    unverified: "Neconfirmat",
  }[status];
  return (
    <span className={`inline-flex px-2 py-0.5 text-[10px] font-semibold rounded border ${cfg}`}>
      {label}
    </span>
  );
}

interface FieldInstallationTeamPanelProps {
  orderId: number;
  orderCode: string;
  defaultSiteAddress?: string;
  visible?: boolean;
}

export default function FieldInstallationTeamPanel({
  orderId,
  orderCode,
  defaultSiteAddress = "",
  visible = true,
}: FieldInstallationTeamPanelProps) {
  const [team, setTeam] = useState<FieldInstallationTeam | null>(null);
  const [employees, setEmployees] = useState<OperatorRegistryEmployee[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | "">("");
  const [selectedRole, setSelectedRole] = useState("montator");
  const [siteAddress, setSiteAddress] = useState(defaultSiteAddress);
  const [notes, setNotes] = useState("");
  const [clientObservations, setClientObservations] = useState("");
  const [photoUrl, setPhotoUrl] = useState("");
  const [presentMemberIds, setPresentMemberIds] = useState<number[]>([]);
  const [fieldMapping, setFieldMapping] = useState<Awaited<
    ReturnType<typeof operationalRegistryApi.getOperationMapping>
  > | null>(null);

  const installationRef = orderInstallationRef(orderId);
  const memberIds = useMemo(
    () => new Set(team?.members.map((m) => m.employee_id) ?? []),
    [team]
  );

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [teamsRes, empRes, mapping] = await Promise.all([
        operationalRegistryApi.listFieldInstallationTeams({ order_id: orderId }),
        operationalRegistryApi.listActiveEmployees(),
        operationalRegistryApi.getOperationMapping("field_installation").catch(() => null),
      ]);
      setTeam(teamsRes.items[0] ?? null);
      setEmployees(empRes.items);
      setFieldMapping(mapping);
      if (teamsRes.items[0]) {
        const t = teamsRes.items[0];
        setSiteAddress(t.site_address ?? defaultSiteAddress);
        setNotes(t.notes ?? "");
        setClientObservations(t.client_observations ?? "");
        setPresentMemberIds(t.members_present?.map((m) => m.employee_id) ?? []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare încărcare echipă montaj");
    } finally {
      setLoading(false);
    }
  }, [orderId, defaultSiteAddress]);

  useEffect(() => {
    if (visible && orderId > 0) {
      void loadData();
    }
  }, [visible, orderId, loadData]);

  const availableEmployees = useMemo(
    () => employees.filter((e) => !memberIds.has(e.id)),
    [employees, memberIds]
  );

  async function handleCreateTeam() {
    setActionLoading("create");
    setError(null);
    try {
      const created = await operationalRegistryApi.createFieldInstallationTeam({
        installation_ref: installationRef,
        site_address: siteAddress || undefined,
        notes: notes || undefined,
        status: "draft",
      });
      setTeam(created);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nu s-a putut crea echipa");
    } finally {
      setActionLoading(null);
    }
  }

  async function handleSaveMeta() {
    if (!team) return;
    setActionLoading("save");
    setError(null);
    try {
      const updated = await operationalRegistryApi.updateFieldInstallationTeam(team.id, {
        site_address: siteAddress,
        notes,
      });
      setTeam(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare salvare");
    } finally {
      setActionLoading(null);
    }
  }

  async function handleStatusChange(status: FieldInstallationTeamStatus) {
    if (!team) return;
    setActionLoading("status");
    setError(null);
    try {
      const updated = await operationalRegistryApi.updateFieldInstallationTeam(team.id, { status });
      setTeam(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare status");
    } finally {
      setActionLoading(null);
    }
  }

  async function handleAddMember() {
    if (!team || selectedEmployeeId === "") return;
    const emp = employees.find((e) => e.id === selectedEmployeeId);
    if (!emp) return;

    setActionLoading(`add-${selectedEmployeeId}`);
    setError(null);
    try {
      const updated = await operationalRegistryApi.addFieldInstallationTeamMember(team.id, {
        employee_id: selectedEmployeeId,
        role_on_site: selectedRole || suggestRoleOnSite(emp.skill_codes) || undefined,
      });
      setTeam(updated);
      setSelectedEmployeeId("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Angajat invalid sau inactiv");
    } finally {
      setActionLoading(null);
    }
  }

  async function handleStartReporting() {
    if (!team) return;
    setActionLoading("start-reporting");
    setError(null);
    try {
      const updated = await operationalRegistryApi.startFieldInstallationReporting(team.id, {
        started_by_employee_id:
          typeof selectedEmployeeId === "number" ? selectedEmployeeId : undefined,
        members_present: presentMemberIds.length ? presentMemberIds : undefined,
      });
      setTeam(updated);
      if (updated.warnings?.length) {
        setError(`Avertismente: ${updated.warnings.join(", ")}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare start montaj");
    } finally {
      setActionLoading(null);
    }
  }

  async function handleCompleteReporting() {
    if (!team) return;
    setActionLoading("complete-reporting");
    setError(null);
    try {
      const photos = photoUrl.trim()
        ? [...(team.completion_photos ?? []), photoUrl.trim()]
        : team.completion_photos;
      const updated = await operationalRegistryApi.completeFieldInstallationReporting(team.id, {
        client_observations: clientObservations || undefined,
        completion_photos: photos,
        members_present: presentMemberIds.length ? presentMemberIds : undefined,
        completed_by_employee_id:
          typeof selectedEmployeeId === "number" ? selectedEmployeeId : undefined,
      });
      setTeam(updated);
      setPhotoUrl("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare finalizare montaj");
    } finally {
      setActionLoading(null);
    }
  }

  async function handleSaveReportingDraft() {
    if (!team) return;
    setActionLoading("save-reporting");
    setError(null);
    try {
      const photos = photoUrl.trim()
        ? [...(team.completion_photos ?? []), photoUrl.trim()]
        : team.completion_photos;
      const updated = await operationalRegistryApi.updateFieldInstallationReporting(team.id, {
        client_observations: clientObservations,
        completion_photos: photos,
        members_present: presentMemberIds,
      });
      setTeam(updated);
      setPhotoUrl("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare salvare raportare");
    } finally {
      setActionLoading(null);
    }
  }

  function togglePresentMember(employeeId: number) {
    setPresentMemberIds((prev) =>
      prev.includes(employeeId) ? prev.filter((id) => id !== employeeId) : [...prev, employeeId]
    );
  }

  async function handleRemoveMember(employeeId: number) {
    if (!team) return;
    setActionLoading(`remove-${employeeId}`);
    setError(null);
    try {
      const updated = await operationalRegistryApi.removeFieldInstallationTeamMember(
        team.id,
        employeeId
      );
      setTeam(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare eliminare membru");
    } finally {
      setActionLoading(null);
    }
  }

  if (!visible || orderId <= 0) return null;

  return (
    <div className="bg-[#0D1A14] border border-emerald-800/40 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-3">
        <HardHat className="w-4 h-4 text-emerald-400" />
        <p className="text-[12px] text-emerald-300 font-semibold">Montaj teren — Echipă beneficiar</p>
        <span className="ml-auto px-2 py-0.5 text-[10px] font-semibold rounded-full bg-slate-800 text-slate-400 border border-slate-600">
          field_installation
        </span>
      </div>

      <p className="text-[11px] text-slate-500 mb-3">
        Alocare echipă multi-angajat pentru montaj la beneficiar ({orderCode}). Separat de stația
        atelier <span className="text-purple-300">montaj_autocolant</span>.
      </p>

      {loading ? (
        <div className="flex items-center gap-2 text-[12px] text-slate-500 py-4">
          <Loader2 className="w-4 h-4 animate-spin" /> Se încarcă...
        </div>
      ) : (
        <>
          {error && (
            <p className="text-[11px] text-red-400 mb-3 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" /> {error}
            </p>
          )}

          {!team ? (
            <button
              onClick={() => void handleCreateTeam()}
              disabled={actionLoading === "create"}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-emerald-800/40 text-emerald-200 border border-emerald-700/50 hover:bg-emerald-800/60 text-[13px] font-semibold disabled:opacity-50"
            >
              {actionLoading === "create" ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Plus className="w-4 h-4" />
              )}
              Creează echipă montaj teren
            </button>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label
                    className="text-[10px] text-slate-500 uppercase tracking-wide"
                    htmlFor="order-field-team-status"
                  >
                    Status echipă
                  </label>
                  <select
                    id="order-field-team-status"
                    name="field-team-status"
                    value={team.status}
                    onChange={(e) =>
                      void handleStatusChange(e.target.value as FieldInstallationTeamStatus)
                    }
                    disabled={actionLoading === "status"}
                    className="mt-1 w-full bg-wo-surface-raised border border-wo-border-subtle rounded-lg px-3 py-2 text-[13px] text-slate-200"
                  >
                    {TEAM_STATUS_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label
                    className="text-[10px] text-slate-500 uppercase tracking-wide flex items-center gap-1"
                    htmlFor="order-field-site-address"
                  >
                    <MapPin className="w-3 h-3" /> Adresă teren
                  </label>
                  <input
                    id="order-field-site-address"
                    name="field-site-address"
                    value={siteAddress}
                    onChange={(e) => setSiteAddress(e.target.value)}
                    placeholder="Adresa montaj la beneficiar"
                    className="mt-1 w-full bg-wo-surface-raised border border-wo-border-subtle rounded-lg px-3 py-2 text-[13px] text-slate-200"
                  />
                </div>
              </div>

              <div>
                <label
                  className="text-[10px] text-slate-500 uppercase tracking-wide"
                  htmlFor="order-field-installation-notes"
                >
                  Observații montaj
                </label>
                <textarea
                  id="order-field-installation-notes"
                  name="field-installation-notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                  className="mt-1 w-full bg-wo-surface-raised border border-wo-border-subtle rounded-lg px-3 py-2 text-[13px] text-slate-200 resize-none"
                  placeholder="Acces, utilaje necesare, restricții teren..."
                />
              </div>

              <button
                onClick={() => void handleSaveMeta()}
                disabled={actionLoading === "save"}
                className="px-3 py-1.5 text-[11px] font-semibold rounded bg-slate-700 text-slate-200 hover:bg-slate-600 disabled:opacity-50"
              >
                Salvează adresă / observații
              </button>

              <div>
                <h4 className="text-[12px] font-semibold text-slate-300 mb-2 flex items-center gap-2">
                  <Users className="w-4 h-4 text-cyan-400" />
                  Membri echipă ({team.member_count})
                </h4>
                {!(team.members ?? []).length ? (
                  <p className="text-[11px] text-amber-400">
                    Adaugă cel puțin doi angajați pentru echipă de montaj teren.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {(team.members ?? []).map((member) => {
                      const caps = deriveFieldCapabilities(member.skill_codes);
                      return (
                        <div
                          key={member.employee_id}
                          className="flex items-center gap-3 px-3 py-2 rounded-lg bg-wo-surface-raised border border-wo-border-subtle"
                        >
                          <div className="flex-1 min-w-0">
                            <p className="text-[13px] font-semibold text-slate-200">
                              {member.employee_name}
                            </p>
                            <p className="text-[10px] text-slate-500">
                              Rol teren:{" "}
                              {ROLE_OPTIONS.find((r) => r.value === member.role_on_site)?.label ??
                                member.role_on_site ??
                                "—"}
                              {caps.length > 0 && ` · ${caps.join(", ")}`}
                            </p>
                          </div>
                          <button
                            onClick={() => void handleRemoveMember(member.employee_id)}
                            disabled={actionLoading === `remove-${member.employee_id}`}
                            className="p-2 rounded-lg text-red-400 hover:bg-red-900/20 disabled:opacity-50"
                            title="Elimină din echipă"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-3 space-y-2">
                <p className="text-[11px] text-slate-400 font-semibold">Adaugă angajat din registry</p>
                <div className="flex flex-col sm:flex-row gap-2">
                  <select
                    id="order-field-team-member-employee"
                    name="field-team-member-employee"
                    value={selectedEmployeeId}
                    onChange={(e) => {
                      const val = e.target.value ? Number(e.target.value) : "";
                      setSelectedEmployeeId(val);
                      if (typeof val === "number") {
                        const emp = employees.find((x) => x.id === val);
                        const suggested = emp ? suggestRoleOnSite(emp.skill_codes) : null;
                        if (suggested) setSelectedRole(suggested);
                      }
                    }}
                    className="flex-1 bg-wo-surface-inset border border-wo-border-subtle rounded-lg px-3 py-2 text-[13px] text-slate-200"
                  >
                    <option value="">Selectează angajat...</option>
                    {availableEmployees.map((emp) => {
                      const eligibility = computeFieldInstallationEligibility(emp, fieldMapping);
                      const caps = deriveFieldCapabilities(emp.skill_codes);
                      return (
                        <option key={emp.id} value={emp.id}>
                          {emp.name}
                          {caps.length ? ` (${caps.join(", ")})` : ""}
                        </option>
                      );
                    })}
                  </select>
                  <select
                    id="order-field-team-member-role"
                    name="field-team-member-role"
                    value={selectedRole}
                    onChange={(e) => setSelectedRole(e.target.value)}
                    className="bg-wo-surface-inset border border-wo-border-subtle rounded-lg px-3 py-2 text-[13px] text-slate-200"
                  >
                    {ROLE_OPTIONS.map((r) => (
                      <option key={r.value} value={r.value}>
                        {r.label}
                      </option>
                    ))}
                  </select>
                  <button
                    onClick={() => void handleAddMember()}
                    disabled={selectedEmployeeId === "" || actionLoading?.startsWith("add-")}
                    className="px-4 py-2 rounded-lg bg-emerald-700 text-white text-[12px] font-semibold hover:bg-emerald-600 disabled:opacity-50"
                  >
                    Adaugă
                  </button>
                </div>
                {selectedEmployeeId !== "" && (
                  <div className="flex items-center gap-2 flex-wrap">
                    {(() => {
                      const emp = employees.find((e) => e.id === selectedEmployeeId);
                      if (!emp) return null;
                      const eligibility = computeFieldInstallationEligibility(emp, fieldMapping);
                      const caps = deriveFieldCapabilities(emp.skill_codes);
                      return (
                        <>
                          <EligibilityBadge status={eligibility} />
                          {caps.map((cap) => (
                            <span
                              key={cap}
                              className="px-2 py-0.5 text-[10px] rounded bg-slate-800 text-slate-300 border border-slate-600"
                            >
                              {cap}
                            </span>
                          ))}
                        </>
                      );
                    })()}
                  </div>
                )}
              </div>

              <div className="bg-wo-surface-raised border border-emerald-800/30 rounded-lg p-4 space-y-3">
                <h4 className="text-[12px] font-semibold text-emerald-300">Raportare montaj teren</h4>
                {team.reporting_ready && (
                  <p className="text-[11px] text-slate-400">
                    Start: {team.started_at ? new Date(team.started_at).toLocaleString("ro-RO") : "—"}
                    {team.ended_at &&
                      ` · Finalizat: ${new Date(team.ended_at).toLocaleString("ro-RO")}`}
                  </p>
                )}
                {team.warnings?.length > 0 && (
                  <p className="text-[11px] text-amber-400">
                    {team.warnings.join(" · ")}
                  </p>
                )}

                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => void handleStartReporting()}
                    disabled={actionLoading === "start-reporting" || team.status === "in_progress"}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-700 text-white text-[12px] font-semibold disabled:opacity-50"
                  >
                    <Play className="w-4 h-4" /> Start montaj
                  </button>
                  <button
                    onClick={() => void handleCompleteReporting()}
                    disabled={actionLoading === "complete-reporting" || !team.reporting_ready}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg bg-emerald-700 text-white text-[12px] font-semibold disabled:opacity-50"
                  >
                    <CheckCircle2 className="w-4 h-4" /> Marchează finalizat
                  </button>
                </div>

                <div>
                  <label
                    className="text-[10px] text-slate-500 uppercase"
                    htmlFor="order-field-client-observations"
                  >
                    Observații client
                  </label>
                  <textarea
                    id="order-field-client-observations"
                    name="field-client-observations"
                    value={clientObservations}
                    onChange={(e) => setClientObservations(e.target.value)}
                    rows={2}
                    className="mt-1 w-full bg-wo-surface-inset border border-wo-border-subtle rounded-lg px-3 py-2 text-[13px] text-slate-200 resize-none"
                  />
                </div>

                <div>
                  <label
                    className="text-[10px] text-slate-500 uppercase flex items-center gap-1"
                    htmlFor="order-field-completion-photo-url"
                  >
                    <Camera className="w-3 h-3" /> Poze finalizare (URL)
                  </label>
                  <div className="flex gap-2 mt-1">
                    <input
                      id="order-field-completion-photo-url"
                      name="field-completion-photo-url"
                      value={photoUrl}
                      onChange={(e) => setPhotoUrl(e.target.value)}
                      placeholder="https://..."
                      className="flex-1 bg-wo-surface-inset border border-wo-border-subtle rounded-lg px-3 py-2 text-[13px] text-slate-200"
                    />
                    <button
                      onClick={() => void handleSaveReportingDraft()}
                      disabled={actionLoading === "save-reporting"}
                      className="px-3 py-2 rounded-lg bg-slate-700 text-slate-200 text-[11px] disabled:opacity-50"
                    >
                      Salvează
                    </button>
                  </div>
                  {team.completion_photos?.length > 0 && (
                    <ul className="mt-2 space-y-1">
                      {team.completion_photos.map((url, idx) => (
                        <li key={idx} className="text-[10px] text-slate-500 truncate">
                          {url}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                {team.members.length > 0 && (
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase mb-1">Membri prezenți</p>
                    <div className="flex flex-wrap gap-2">
                      {team.members.map((m) => (
                        <button
                          key={m.employee_id}
                          onClick={() => togglePresentMember(m.employee_id)}
                          className={`px-2 py-1 rounded text-[11px] border ${
                            presentMemberIds.includes(m.employee_id)
                              ? "bg-cyan-900/40 border-cyan-600 text-cyan-200"
                              : "bg-slate-800 border-slate-600 text-slate-400"
                          }`}
                        >
                          {m.employee_name}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                <p className="text-[10px] text-slate-600 italic">
                  Colectare observațională — fără cost, fără stock adjustment, fără scheduling.
                </p>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
