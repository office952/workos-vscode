/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useEffect } from "react";
import { X, Plus, Search, UserPlus, CheckCircle2, AlertTriangle } from "lucide-react";
import { clientsApi, intakesApi, type ClientEntity, type IntakeRequestEntity } from "@/lib/api";
import { productFamiliesApi, type ProductFamily } from "@/api/productFamilies";
import IntakeWorkTypePicker from "@/components/workos/IntakeWorkTypePicker";
import InfoHint from "@/components/workos/templateIntakeWorkspace/InfoHint";
import {
  formatMissingRequirementsMessage,
  getQuickStartMissingRequirements,
  resolveWorkTypeFamilyId,
} from "@/lib/intakeQuickStartWorkTypes";
import { INTAKE_DELIVERY_OPTIONS } from "@/lib/intakeDeliverySemantics";
import { formatApiErrorFromUnknown, canCreateIntakeRequest } from "@/lib/apiError";
import { useAuth } from "@/contexts/AuthContext";

interface NewIntakeDialogProps {
  open: boolean;
  onClose: () => void;
  onCreated: (intakeCode: string, productFamily?: string | null) => void;
}

type Step = "client" | "details";

type ClientMode = "existing" | "new_temp" | "new_fiscal";

const CHANNELS = [
  { value: "email", label: "Email" },
  { value: "phone", label: "Telefon" },
  { value: "walk_in", label: "Walk-in" },
  { value: "web_form", label: "Formular Web" },
];

const PRIORITIES = [
  { value: "low", label: "Scăzută" },
  { value: "normal", label: "Normală" },
  { value: "high", label: "Ridicată" },
  { value: "urgent", label: "Urgentă" },
];

type IntakeCreateForm = {
  description: string;
  channel: string;
  priority: IntakeRequestEntity["priority"];
  delivery_type: string;
};

export default function NewIntakeDialog({ open, onClose, onCreated }: NewIntakeDialogProps) {
  const { user } = useAuth();
  const canCreateIntake = canCreateIntakeRequest(
    typeof user?.role === "string" ? user.role : undefined
  );
  const [step, setStep] = useState<Step>("client");
  const [mode, setMode] = useState<ClientMode>("existing");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [clients, setClients] = useState<ClientEntity[]>([]);
  const [clientSearch, setClientSearch] = useState("");
  const [selectedClient, setSelectedClient] = useState<ClientEntity | null>(null);
  const [loadingClients, setLoadingClients] = useState(false);
  const [productFamilies, setProductFamilies] = useState<ProductFamily[]>([]);
  const [loadingFamilies, setLoadingFamilies] = useState(false);
  const [familyLoadError, setFamilyLoadError] = useState<string | null>(null);
  const [selectedWorkTypeId, setSelectedWorkTypeId] = useState<string | null>(null);

  const [newClient, setNewClient] = useState({
    name: "",
    cui: "",
    contact_person: "",
    phone: "",
    email: "",
    address: "",
    city: "",
  });

  const [intake, setIntake] = useState<IntakeCreateForm>({
    description: "",
    channel: "email",
    priority: "normal",
    delivery_type: "delivery_standard",
  });

  useEffect(() => {
    if (!open) return;
    setLoadingClients(true);
    clientsApi
      .list({}, { sort: "-created_at", limit: 200 })
      .then((rows) => setClients(rows))
      .catch((err) => {
        console.warn("[NewIntakeDialog] failed to load clients", err);
        setClients([]);
      })
      .finally(() => setLoadingClients(false));
  }, [open]);

  useEffect(() => {
    if (!open) return;
    setLoadingFamilies(true);
    setFamilyLoadError(null);
    productFamiliesApi
      .list({ query: { active: true }, limit: 500, sort: "label" })
      .then((response) => {
        const activeFamilies = response.items.filter((family) => family.active);
        setProductFamilies(activeFamilies);
      })
      .catch((err) => {
        console.warn("[NewIntakeDialog] failed to load product families", err);
        setProductFamilies([]);
        setFamilyLoadError(
          "Familiile de produs active nu au putut fi încărcate. Cererea nu poate fi creată până la rezolvarea sursei backend."
        );
      })
      .finally(() => setLoadingFamilies(false));
  }, [open]);

  useEffect(() => {
    if (!open) {
      setTimeout(() => {
        setStep("client");
        setMode("existing");
        setSelectedClient(null);
        setClientSearch("");
        setSelectedWorkTypeId(null);
        setError(null);
        setSubmitting(false);
        setNewClient({
          name: "",
          cui: "",
          contact_person: "",
          phone: "",
          email: "",
          address: "",
          city: "",
        });
        setIntake({
          description: "",
          channel: "email",
          priority: "normal",
          delivery_type: "delivery_standard",
        });
      }, 200);
    }
  }, [open]);

  if (!open) return null;

  const filteredClients = clientSearch.trim()
    ? clients.filter((c) => {
        const q = clientSearch.toLowerCase();
        return (
          c.name.toLowerCase().includes(q) ||
          (c.cui ?? "").toLowerCase().includes(q) ||
          (c.contact_person ?? "").toLowerCase().includes(q)
        );
      })
    : clients.slice(0, 20);

  const canProceedFromClient = () => {
    if (mode === "existing") return !!selectedClient;
    if (mode === "new_fiscal") return newClient.name.trim().length > 0 && newClient.cui.trim().length > 0;
    if (mode === "new_temp") return newClient.name.trim().length > 0;
    return false;
  };

  const missingRequirements = getQuickStartMissingRequirements({
    workTypeId: selectedWorkTypeId,
    description: intake.description,
    channel: intake.channel,
    registry: productFamilies,
    registryLoading: loadingFamilies,
    registryError: familyLoadError,
  });

  const missingRequirementsMessage = formatMissingRequirementsMessage(missingRequirements);
  const canSubmit = () => canProceedFromClient() && missingRequirements.length === 0;

  const resolvedFamilyId = resolveWorkTypeFamilyId(selectedWorkTypeId, productFamilies);

  const clientDisplayName =
    mode === "existing" ? selectedClient?.name : newClient.name.trim() || "—";

  const handleSubmit = async () => {
    if (!canSubmit()) return;
    if (!canCreateIntake) {
      setError(
        "Contul curent nu poate crea cereri Work Intake. Deschide aplicația operator/comercial pe http://127.0.0.1:3001."
      );
      return;
    }
    if (resolvedFamilyId === null) {
      setError("Selectează tipul de lucrare înainte de a crea cererea.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      let clientEntity: ClientEntity;
      if (mode === "existing" && selectedClient) {
        clientEntity = selectedClient;
      } else {
        const identity_type = mode === "new_fiscal" ? "fiscal" : "temp";
        const temp_ref = mode === "new_temp" ? `TEMP-${Date.now().toString(36).toUpperCase()}` : undefined;
        clientEntity = await clientsApi.create({
          name: newClient.name.trim(),
          identity_type,
          temp_ref,
          cui: mode === "new_fiscal" ? newClient.cui.trim() : undefined,
          contact_person: newClient.contact_person.trim() || undefined,
          phone: newClient.phone.trim() || undefined,
          email: newClient.email.trim() || undefined,
          address: newClient.address.trim() || undefined,
          city: newClient.city.trim() || undefined,
        });
      }

      const code = `IR-${Date.now().toString(36).toUpperCase()}`;

      await intakesApi.create({
        code,
        client_id: clientEntity.id,
        client_name: clientEntity.name,
        contact_person: clientEntity.contact_person ?? "—",
        channel: intake.channel,
        product_family: resolvedFamilyId,
        description: intake.description.trim(),
        dimensions: "—",
        quantity: 1,
        status: "new",
        assigned_to: "—",
        notes: "",
        priority: intake.priority,
        delivery_type: intake.delivery_type,
      });

      onCreated(code, resolvedFamilyId);
      onClose();
    } catch (err: unknown) {
      console.error("[NewIntakeDialog] submit failed", err);
      const message = formatApiErrorFromUnknown(err, "Eroare la crearea cererii. Încearcă din nou.");
      if (message.includes("Invalid product_family/family_id")) {
        setError(`Tipul de lucrare selectat nu mai este valid în registry-ul backend: ${message}`);
      } else {
        setError(message);
      }
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-[#0D1321] border border-[#2A3548] rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b border-[#2A3548]">
          <div className="flex items-center gap-2">
            <Plus className="w-4 h-4 text-emerald-400" />
            <h2 className="text-[14px] font-bold text-slate-100">Cerere Nouă</h2>
            <span className="text-[10px] text-slate-500 bg-slate-800/60 px-2 py-0.5 rounded">
              Pas {step === "client" ? "1" : "2"}/2
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-slate-500 hover:text-slate-200 transition-colors"
            aria-label="Închide"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          {step === "client" && (
            <div className="space-y-4">
              <p className="text-[12px] text-slate-400">
                Alege un client existent sau creează unul nou.
                <InfoHint label="Despre client temporar">
                  Clientul temporar poate fi convertit ulterior la identitate fiscală (CUI) înainte de acceptarea
                  ofertei.
                </InfoHint>
              </p>

              <div className="grid grid-cols-3 gap-2">
                {(
                  [
                    { v: "existing" as const, label: "Client Existent", icon: <Search className="w-3.5 h-3.5" /> },
                    { v: "new_temp" as const, label: "Client Temporar", icon: <UserPlus className="w-3.5 h-3.5" /> },
                    { v: "new_fiscal" as const, label: "Client Fiscal (CUI)", icon: <UserPlus className="w-3.5 h-3.5" /> },
                  ]
                ).map((m) => (
                  <button
                    key={m.v}
                    onClick={() => {
                      setMode(m.v);
                      setSelectedClient(null);
                    }}
                    className={`flex items-center justify-center gap-1.5 px-3 py-2 text-[11px] font-semibold rounded-lg border transition-colors ${
                      mode === m.v
                        ? "bg-blue-600/20 text-blue-300 border-blue-500/50"
                        : "bg-[#1A2236] text-slate-400 border-[#2A3548] hover:border-slate-500"
                    }`}
                  >
                    {m.icon}
                    {m.label}
                  </button>
                ))}
              </div>

              {mode === "existing" && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 bg-[#1A2236] border border-[#2A3548] rounded-lg px-3 py-2 focus-within:border-blue-500/50">
                    <Search className="w-4 h-4 text-slate-500" />
                    <input
                      id="new-intake-client-search"
                      name="new-intake-client-search"
                      type="text"
                      value={clientSearch}
                      onChange={(e) => setClientSearch(e.target.value)}
                      placeholder="Caută după nume, CUI, persoană contact..."
                      className="bg-transparent text-[12px] text-slate-200 placeholder:text-slate-600 outline-none w-full"
                    />
                  </div>
                  <div className="max-h-60 overflow-y-auto border border-[#2A3548] rounded-lg bg-[#1A2236]">
                    {loadingClients ? (
                      <p className="text-[11px] text-slate-500 p-4 text-center">Se încarcă clienții...</p>
                    ) : filteredClients.length === 0 ? (
                      <div className="p-4 text-center">
                        <p className="text-[11px] text-slate-500">
                          {clients.length === 0
                            ? "Nu există clienți în baza de date. Alege „Client Temporar\" pentru a crea unul rapid."
                            : "Niciun client găsit."}
                        </p>
                      </div>
                    ) : (
                      <ul>
                        {filteredClients.map((c) => (
                          <li key={c.id}>
                            <button
                              onClick={() => setSelectedClient(c)}
                              className={`w-full text-left px-3 py-2 border-b border-[#2A3548] last:border-b-0 transition-colors ${
                                selectedClient?.id === c.id
                                  ? "bg-blue-600/15"
                                  : "hover:bg-slate-800/40"
                              }`}
                            >
                              <div className="flex items-center justify-between">
                                <div>
                                  <p className="text-[12px] font-semibold text-slate-200">{c.name}</p>
                                  <p className="text-[10px] text-slate-500">
                                    {c.identity_type === "fiscal" ? `CUI: ${c.cui ?? "—"}` : `TEMP: ${c.temp_ref ?? "—"}`}
                                    {c.contact_person ? ` · ${c.contact_person}` : ""}
                                  </p>
                                </div>
                                {selectedClient?.id === c.id && (
                                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                                )}
                              </div>
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              )}

              {(mode === "new_temp" || mode === "new_fiscal") && (
                <div className="space-y-3">
                  <div>
                    <label
                      className="text-[10px] text-slate-500 uppercase tracking-wide block mb-1"
                      htmlFor="new-intake-client-name"
                    >
                      Nume Client <span className="text-red-400">*</span>
                    </label>
                    <input
                      id="new-intake-client-name"
                      name="new-intake-client-name"
                      value={newClient.name}
                      onChange={(e) => setNewClient({ ...newClient, name: e.target.value })}
                      placeholder="SC Exemplu SRL sau Ion Popescu"
                      className="w-full bg-[#1A2236] border border-[#2A3548] rounded-lg px-3 py-2 text-[12px] text-slate-200 placeholder:text-slate-600 outline-none focus:border-blue-500/50"
                    />
                  </div>
                  {mode === "new_fiscal" && (
                    <div>
                      <label
                        className="text-[10px] text-slate-500 uppercase tracking-wide block mb-1"
                        htmlFor="new-intake-client-cui"
                      >
                        CUI <span className="text-red-400">*</span>
                      </label>
                      <input
                        id="new-intake-client-cui"
                        name="new-intake-client-cui"
                        value={newClient.cui}
                        onChange={(e) => setNewClient({ ...newClient, cui: e.target.value })}
                        placeholder="RO12345678"
                        className="w-full bg-[#1A2236] border border-[#2A3548] rounded-lg px-3 py-2 text-[12px] text-slate-200 placeholder:text-slate-600 outline-none focus:border-blue-500/50"
                      />
                    </div>
                  )}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label
                        className="text-[10px] text-slate-500 uppercase tracking-wide block mb-1"
                        htmlFor="new-intake-client-contact"
                      >
                        Persoană Contact
                      </label>
                      <input
                        id="new-intake-client-contact"
                        name="new-intake-client-contact"
                        value={newClient.contact_person}
                        onChange={(e) => setNewClient({ ...newClient, contact_person: e.target.value })}
                        placeholder="Numele persoanei"
                        className="w-full bg-[#1A2236] border border-[#2A3548] rounded-lg px-3 py-2 text-[12px] text-slate-200 placeholder:text-slate-600 outline-none focus:border-blue-500/50"
                      />
                    </div>
                    <div>
                      <label
                        className="text-[10px] text-slate-500 uppercase tracking-wide block mb-1"
                        htmlFor="new-intake-client-phone"
                      >
                        Telefon
                      </label>
                      <input
                        id="new-intake-client-phone"
                        name="new-intake-client-phone"
                        value={newClient.phone}
                        onChange={(e) => setNewClient({ ...newClient, phone: e.target.value })}
                        placeholder="07xx xxx xxx"
                        className="w-full bg-[#1A2236] border border-[#2A3548] rounded-lg px-3 py-2 text-[12px] text-slate-200 placeholder:text-slate-600 outline-none focus:border-blue-500/50"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {step === "details" && (
            <div className="space-y-5">
              <div className="flex items-center justify-between gap-3 bg-[#1A2236] border border-[#2A3548] rounded-lg px-3 py-2.5">
                <div className="min-w-0">
                  <p className="text-[10px] text-slate-500 uppercase tracking-wide">Client</p>
                  <p className="text-[13px] font-semibold text-slate-200 truncate">{clientDisplayName}</p>
                  <p className="text-[10px] text-slate-500 mt-0.5 truncate">
                    {mode === "existing"
                      ? selectedClient?.identity_type === "fiscal"
                        ? `CUI: ${selectedClient?.cui}`
                        : `Temporar: ${selectedClient?.temp_ref}`
                      : mode === "new_fiscal"
                        ? `CUI: ${newClient.cui}`
                        : "Client temporar (va fi creat)"}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setStep("client")}
                  className="shrink-0 text-[11px] font-semibold text-blue-400 hover:text-blue-300"
                >
                  Schimbă client
                </button>
              </div>

              <section className="space-y-2">
                <div className="flex items-center gap-1.5">
                  <h3 className="text-[12px] font-bold text-slate-200">Ce vrei să produci?</h3>
                  <span className="text-red-400 text-[11px]">*</span>
                  <InfoHint label="Despre tip lucrare">
                    Alege tipul de lucrare. Poți începe cu o cerere generică dacă nu ești sigur — detaliile se
                    completează în workspace-ul cererii.
                  </InfoHint>
                </div>
                <IntakeWorkTypePicker
                  selectedWorkTypeId={selectedWorkTypeId}
                  onSelect={setSelectedWorkTypeId}
                  registry={productFamilies}
                  loading={loadingFamilies}
                />
              </section>

              <section className="space-y-3">
                <h3 className="text-[12px] font-bold text-slate-200">Date cerere</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label
                      className="text-[10px] text-slate-500 uppercase tracking-wide block mb-1"
                      htmlFor="new-intake-channel"
                    >
                      Canal <span className="text-red-400">*</span>
                    </label>
                    <select
                      id="new-intake-channel"
                      name="new-intake-channel"
                      aria-label="Canal"
                      value={intake.channel}
                      onChange={(e) => setIntake({ ...intake, channel: e.target.value })}
                      className="w-full bg-[#1A2236] border border-[#2A3548] rounded-lg px-3 py-2 text-[12px] text-slate-200 outline-none focus:border-blue-500/50"
                    >
                      {CHANNELS.map((c) => (
                        <option key={c.value} value={c.value}>
                          {c.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label
                      className="text-[10px] text-slate-500 uppercase tracking-wide block mb-1"
                      htmlFor="new-intake-priority"
                    >
                      Prioritate
                    </label>
                    <select
                      id="new-intake-priority"
                      name="new-intake-priority"
                      aria-label="Prioritate"
                      value={intake.priority}
                      onChange={(e) =>
                        setIntake({ ...intake, priority: e.target.value as IntakeRequestEntity["priority"] })
                      }
                      className="w-full bg-[#1A2236] border border-[#2A3548] rounded-lg px-3 py-2 text-[12px] text-slate-200 outline-none focus:border-blue-500/50"
                    >
                      {PRIORITIES.map((p) => (
                        <option key={p.value} value={p.value}>
                          {p.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label
                      className="text-[10px] text-slate-500 uppercase tracking-wide block mb-1"
                      htmlFor="new-intake-delivery-type"
                    >
                      Tip livrare
                    </label>
                    <select
                      id="new-intake-delivery-type"
                      name="new-intake-delivery-type"
                      aria-label="Tip livrare"
                      value={intake.delivery_type}
                      onChange={(e) => setIntake({ ...intake, delivery_type: e.target.value })}
                      className="w-full bg-[#1A2236] border border-[#2A3548] rounded-lg px-3 py-2 text-[12px] text-slate-200 outline-none focus:border-blue-500/50"
                    >
                      {INTAKE_DELIVERY_OPTIONS.map((d) => (
                        <option key={d.value} value={d.value}>
                          {d.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="md:col-span-2">
                    <label
                      className="text-[10px] text-slate-500 uppercase tracking-wide block mb-1"
                      htmlFor="new-intake-description"
                    >
                      Descriere scurtă <span className="text-red-400">*</span>
                    </label>
                    <textarea
                      id="new-intake-description"
                      name="new-intake-description"
                      value={intake.description}
                      onChange={(e) => setIntake({ ...intake, description: e.target.value })}
                      placeholder="Ex: Litere volumetrice pentru fațadă, 12 caractere, montaj inclus..."
                      rows={3}
                      className="w-full bg-[#1A2236] border border-[#2A3548] rounded-lg px-3 py-2 text-[12px] text-slate-200 placeholder:text-slate-600 outline-none focus:border-blue-500/50 resize-none"
                    />
                  </div>
                </div>
              </section>
            </div>
          )}

          {(familyLoadError || error) && (
            <div className="mt-3 flex items-start gap-2 px-3 py-2 bg-red-900/20 border border-red-800/40 rounded-lg">
              <AlertTriangle className="w-3.5 h-3.5 text-red-400 mt-0.5 shrink-0" />
              <p className="text-[11px] text-red-300">{error ?? familyLoadError}</p>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between px-5 py-3 border-t border-[#2A3548] bg-[#0A0F1C]">
          <button
            onClick={step === "details" ? () => setStep("client") : onClose}
            className="text-[12px] font-semibold text-slate-400 hover:text-slate-200 transition-colors"
            disabled={submitting}
          >
            {step === "details" ? "← Înapoi" : "Anulează"}
          </button>
          <div className="flex flex-col items-end gap-1">
            {step === "details" && missingRequirementsMessage && !submitting && (
              <p
                className="text-[10px] text-amber-400/90"
                data-testid="create-intake-missing-requirements"
              >
                {missingRequirementsMessage}
              </p>
            )}
            <div className="flex items-center gap-2">
              {step === "client" ? (
                <button
                  onClick={() => setStep("details")}
                  disabled={!canProceedFromClient()}
                  className={`px-4 py-2 text-[12px] font-bold rounded-lg transition-colors ${
                    canProceedFromClient()
                      ? "bg-blue-600 hover:bg-blue-500 text-white"
                      : "bg-slate-700/60 text-slate-500 cursor-not-allowed"
                  }`}
                >
                  Continuă →
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={!canSubmit() || submitting}
                  className={`px-4 py-2 text-[12px] font-bold rounded-lg transition-colors flex items-center gap-2 ${
                    canSubmit() && !submitting
                      ? "bg-emerald-600 hover:bg-emerald-500 text-white"
                      : "bg-slate-700/60 text-slate-500 cursor-not-allowed"
                  }`}
                >
                  {submitting ? (
                    <>
                      <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                      Se creează...
                    </>
                  ) : (
                    <>
                      <Plus className="w-3.5 h-3.5" />
                      Creează Cerere
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
