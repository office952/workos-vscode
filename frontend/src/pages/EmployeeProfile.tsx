/**
 * Employee Profile — Internal Records
 * Tabs: Profil | Documente | Medicina muncii | Alerte
 *
 * EVIDENȚĂ INTERNĂ — NU este document fiscal/contabil.
 */
import { useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  User,
  FileText,
  Heart,
  Bell,
  Phone,
  Mail,
  Calendar,
  MapPin,
  Shield,
  AlertTriangle,
  CheckCircle2,
  Clock,
  XCircle,
  Info,
  Lock,
} from "lucide-react";
import { Loader2 } from "lucide-react";
import { usePersonalDemoModule } from "@/hooks/usePersonalDemoModule";
import {
  DOCUMENT_STATUS_CONFIG,
  getEmployeeById,
  getDocumentsForEmployee,
  getAlertsForEmployee,
  getAdvancesForEmployee,
  type EmployeeDocument,
  type EmployeeRecord,
  type InternalAlert,
  type Advance,
} from "@/lib/employeeRecordsData";

type TabId = "profil" | "documente" | "medicina" | "alerte";

const TABS: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: "profil", label: "Profil", icon: <User className="w-4 h-4" /> },
  { id: "documente", label: "Documente", icon: <FileText className="w-4 h-4" /> },
  { id: "medicina", label: "Medicina muncii", icon: <Heart className="w-4 h-4" /> },
  { id: "alerte", label: "Alerte", icon: <Bell className="w-4 h-4" /> },
];

export default function EmployeeProfile() {
  const { employeeId } = useParams<{ employeeId: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<TabId>("profil");

  const { employeeRecords, documents: allDocuments, alerts: allAlerts, advances: allAdvances, loading, error } =
    usePersonalDemoModule();

  const employee = useMemo(
    () => getEmployeeById(employeeId || "", employeeRecords),
    [employeeId, employeeRecords]
  );
  const documents = useMemo(
    () => getDocumentsForEmployee(employeeId || "", allDocuments),
    [employeeId, allDocuments]
  );
  const alerts = useMemo(
    () => getAlertsForEmployee(employeeId || "", allAlerts),
    [employeeId, allAlerts]
  );
  const advances = useMemo(
    () => getAdvancesForEmployee(employeeId || "", allAdvances),
    [employeeId, allAdvances]
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 gap-2 text-slate-400 text-sm">
        <Loader2 className="w-5 h-5 animate-spin" />
        Se încarcă profilul din registry operațional...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 text-red-300 text-sm">{error}</div>
    );
  }

  if (!employee) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-slate-400">Angajat negăsit.</p>
      </div>
    );
  }

  const medicinaDocs = documents.filter((d) => d.tip === "medicina_muncii");
  const alertCount = alerts.length;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate("/employees-records")}
          className="p-2 rounded-lg bg-wo-surface-raised border border-wo-border-strong hover:border-slate-500 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 text-slate-300" />
        </button>
        <div className="flex items-center gap-3 flex-1">
          <div className="w-11 h-11 rounded-full bg-slate-700 flex items-center justify-center text-[14px] font-bold text-slate-300">
            {employee.name.split(" ").map((n) => n[0]).slice(0, 2).join("")}
          </div>
          <div>
            <h1 className="text-[18px] font-bold text-slate-100">{employee.name}</h1>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-[12px] text-slate-400">{employee.functie}</span>
              <span className="text-[10px] text-slate-600">•</span>
              <span className="text-[12px] text-slate-400">{employee.departament}</span>
              <span className={`px-2 py-0.5 text-[10px] font-semibold rounded border ${
                employee.status === "activ"
                  ? "bg-emerald-900/40 text-emerald-300 border-emerald-700"
                  : employee.status === "inactiv"
                    ? "bg-amber-900/40 text-amber-300 border-amber-700"
                    : "bg-red-900/40 text-red-300 border-red-700"
              }`}>
                {employee.status === "activ" ? "Activ" : employee.status === "inactiv" ? "Inactiv" : "Plecat"}
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-semibold rounded bg-slate-800 text-slate-400 border border-slate-700">
            <Lock className="w-3 h-3" /> Confidențial
          </span>
          <span className="px-3 py-1 text-[10px] font-semibold rounded-full bg-amber-900/30 text-amber-300 border border-amber-700/50">
            DEMO
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-[12px] font-semibold transition-colors ${
              activeTab === tab.id
                ? "bg-wo-surface-raised text-slate-100 border border-wo-border-strong"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            {tab.icon}
            {tab.label}
            {tab.id === "alerte" && alertCount > 0 && (
              <span className="px-1.5 py-0.5 text-[9px] font-bold rounded-full bg-red-900/50 text-red-300 border border-red-700">
                {alertCount}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === "profil" && <ProfileTab employee={employee} advances={advances} />}
      {activeTab === "documente" && <DocumentsTab documents={documents} />}
      {activeTab === "medicina" && <MedicinaTab documents={medicinaDocs} employeeName={employee.name} />}
      {activeTab === "alerte" && <AlertsTab alerts={alerts} />}
    </div>
  );
}

// ============================================================
// PROFILE TAB
// ============================================================
function ProfileTab({ employee, advances }: { employee: EmployeeRecord; advances: Advance[] }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Info */}
      <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-5 space-y-4">
        <h3 className="text-[14px] font-semibold text-slate-200">Informații generale</h3>
        <div className="grid grid-cols-2 gap-4">
          <InfoField icon={<User className="w-3.5 h-3.5 text-slate-500" />} label="Funcție" value={employee.functie} />
          <InfoField icon={<MapPin className="w-3.5 h-3.5 text-slate-500" />} label="Departament" value={employee.departament} />
          <InfoField icon={<MapPin className="w-3.5 h-3.5 text-slate-500" />} label="Stație principală" value={employee.statiePrincipala} />
          <InfoField icon={<Calendar className="w-3.5 h-3.5 text-slate-500" />} label="Data angajării" value={new Date(employee.dataAngajarii).toLocaleDateString("ro-RO")} />
          <InfoField icon={<Phone className="w-3.5 h-3.5 text-slate-500" />} label="Telefon" value={employee.telefon} />
          <InfoField icon={<Mail className="w-3.5 h-3.5 text-slate-500" />} label="Email" value={employee.email} />
        </div>
        {employee.observatii && (
          <div className="bg-wo-surface-raised rounded-lg p-3">
            <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Observații interne</p>
            <p className="text-[12px] text-slate-300">{employee.observatii}</p>
          </div>
        )}
      </div>

      {/* Program & Skills */}
      <div className="space-y-4">
        <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-5 space-y-3">
          <h3 className="text-[14px] font-semibold text-slate-200">Program de lucru</h3>
          <div className="grid grid-cols-2 gap-3">
            <InfoField icon={<Clock className="w-3.5 h-3.5 text-slate-500" />} label="Program" value="Luni – Vineri" />
            <InfoField icon={<Clock className="w-3.5 h-3.5 text-slate-500" />} label="Ore/zi" value="8h (+ 30 min pauză masă)" />
          </div>
          <p className="text-[10px] text-slate-600 italic">Program standard intern. Configurabil dacă există orar special.</p>
        </div>

        <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-5 space-y-3">
          <h3 className="text-[14px] font-semibold text-slate-200">Skill-uri / Stații</h3>
          <div className="flex flex-wrap gap-2">
            {employee.skills.map((skill) => (
              <span key={skill} className="px-3 py-1 text-[11px] font-medium bg-blue-900/30 text-blue-300 border border-blue-700/50 rounded-lg">
                {skill}
              </span>
            ))}
          </div>
        </div>

        {/* Active debts summary */}
        {advances.length > 0 && (
          <div className="bg-wo-surface-raised border border-amber-800/30 rounded-lg p-5 space-y-3">
            <h3 className="text-[14px] font-semibold text-amber-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" /> Datorii active
            </h3>
            <div className="space-y-2">
              {advances.filter((a) => a.status === "activ").map((adv) => (
                <div key={adv.id} className="flex items-center justify-between px-3 py-2 bg-wo-surface-raised rounded-lg">
                  <div>
                    <p className="text-[12px] text-slate-200 font-medium">
                      {adv.tip === "avans" ? "Avans" : adv.tip === "imprumut" ? "Împrumut" : "Reținere"}
                    </p>
                    <p className="text-[10px] text-slate-500">{adv.observatii}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-[14px] font-bold text-amber-300">{adv.tip === "imprumut" ? adv.soldRamas : adv.suma} lei</p>
                    {adv.tip === "imprumut" && (
                      <p className="text-[10px] text-slate-500">rată {adv.rataLunara} lei/lună</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function InfoField({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-start gap-2">
      <div className="mt-0.5">{icon}</div>
      <div>
        <p className="text-[10px] text-slate-500 uppercase tracking-wide">{label}</p>
        <p className="text-[12px] text-slate-200 font-medium mt-0.5">{value}</p>
      </div>
    </div>
  );
}

// ============================================================
// DOCUMENTS TAB
// ============================================================
function DocumentsTab({ documents }: { documents: EmployeeDocument[] }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-[14px] font-semibold text-slate-200">Documente angajat</h3>
        <button
          disabled
          title="Coming soon — necesită sistem de fișiere backend"
          className="px-3 py-1.5 text-[11px] font-semibold text-slate-500 bg-wo-surface-raised border border-wo-border-strong rounded-md cursor-not-allowed"
        >
          + Adaugă document — coming soon
        </button>
      </div>

      {documents.length === 0 ? (
        <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-8 text-center">
          <FileText className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-[13px] text-slate-500">Nu există documente înregistrate.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {documents.map((doc) => {
            const statusCfg = DOCUMENT_STATUS_CONFIG[doc.status];
            return (
              <div key={doc.id} className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg px-4 py-3 flex items-center gap-4">
                <FileText className="w-5 h-5 text-slate-500 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] font-semibold text-slate-200">{doc.tipLabel}</p>
                  <div className="flex items-center gap-3 mt-0.5 text-[10px] text-slate-500">
                    <span>Emis: {new Date(doc.dataEmitere).toLocaleDateString("ro-RO")}</span>
                    {doc.dataExpirare && (
                      <span>Expiră: {new Date(doc.dataExpirare).toLocaleDateString("ro-RO")}</span>
                    )}
                    {doc.observatii && <span className="text-slate-400">{doc.observatii}</span>}
                  </div>
                </div>
                <span className={`px-2.5 py-0.5 text-[10px] font-semibold rounded border ${statusCfg.cls}`}>
                  {statusCfg.label}
                </span>
                <button
                  disabled
                  title="Coming soon — necesită sistem de fișiere"
                  className="px-2 py-1 text-[10px] text-slate-600 bg-slate-800 rounded cursor-not-allowed"
                >
                  Vezi fișier
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ============================================================
// MEDICINA MUNCII TAB
// ============================================================
function MedicinaTab({ documents, employeeName }: { documents: EmployeeDocument[]; employeeName: string }) {
  const latest = documents.length > 0 ? documents[documents.length - 1] : null;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Heart className="w-5 h-5 text-pink-400" />
        <h3 className="text-[14px] font-semibold text-slate-200">Medicina muncii — {employeeName}</h3>
      </div>

      <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-5">
        <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-3">Status curent</p>
        {latest ? (
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              {latest.status === "valid" && <CheckCircle2 className="w-6 h-6 text-emerald-400" />}
              {latest.status === "expira_curand" && <Clock className="w-6 h-6 text-amber-400" />}
              {latest.status === "expirat" && <XCircle className="w-6 h-6 text-red-400" />}
              <div>
                <p className="text-[16px] font-bold text-slate-100">
                  {latest.status === "valid" ? "Valid" : latest.status === "expira_curand" ? "Expiră curând" : "EXPIRAT"}
                </p>
                <p className="text-[12px] text-slate-400">
                  Emis: {new Date(latest.dataEmitere).toLocaleDateString("ro-RO")}
                  {latest.dataExpirare && ` · Expiră: ${new Date(latest.dataExpirare).toLocaleDateString("ro-RO")}`}
                </p>
              </div>
            </div>

            {latest.status === "expirat" && (
              <div className="bg-red-900/20 border border-red-800/40 rounded-lg px-4 py-3">
                <p className="text-[12px] text-red-300 font-semibold flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" /> Atenție: Fișa medicală este expirată!
                </p>
                <p className="text-[11px] text-red-200/70 mt-1">Programează reînnoire urgentă. Angajatul nu poate lucra legal fără fișă medicală validă.</p>
              </div>
            )}

            {latest.status === "expira_curand" && (
              <div className="bg-amber-900/20 border border-amber-800/40 rounded-lg px-4 py-3">
                <p className="text-[12px] text-amber-300 font-semibold flex items-center gap-2">
                  <Clock className="w-4 h-4" /> Fișa medicală expiră curând
                </p>
                <p className="text-[11px] text-amber-200/70 mt-1">Programează reînnoire înainte de data expirării.</p>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-slate-800/50 rounded-lg px-4 py-3">
            <p className="text-[12px] text-slate-400">Nu există înregistrare medicina muncii.</p>
          </div>
        )}
      </div>

      <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-5">
        <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-3">Istoric</p>
        {documents.length === 0 ? (
          <p className="text-[12px] text-slate-500">Niciun document medicina muncii.</p>
        ) : (
          <div className="space-y-2">
            {documents.map((doc) => {
              const statusCfg = DOCUMENT_STATUS_CONFIG[doc.status];
              return (
                <div key={doc.id} className="flex items-center gap-3 px-3 py-2 bg-wo-surface-raised rounded-lg">
                  <Heart className="w-4 h-4 text-pink-400 shrink-0" />
                  <div className="flex-1">
                    <p className="text-[12px] text-slate-200">
                      Emis: {new Date(doc.dataEmitere).toLocaleDateString("ro-RO")}
                      {doc.dataExpirare && ` → Expiră: ${new Date(doc.dataExpirare).toLocaleDateString("ro-RO")}`}
                    </p>
                  </div>
                  <span className={`px-2 py-0.5 text-[10px] font-semibold rounded border ${statusCfg.cls}`}>
                    {statusCfg.label}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="bg-wo-surface-inset border border-wo-border-subtle rounded-lg px-4 py-3">
        <p className="text-[10px] text-slate-600 flex items-center gap-2">
          <Shield className="w-3 h-3" />
          Nu se afișează date medicale sensibile. Doar status document (valid/expirat).
        </p>
      </div>
    </div>
  );
}

// ============================================================
// ALERTS TAB
// ============================================================
function AlertsTab({ alerts }: { alerts: InternalAlert[] }) {
  const severityIcon = {
    error: <XCircle className="w-4 h-4 text-red-400" />,
    warning: <AlertTriangle className="w-4 h-4 text-amber-400" />,
    info: <Info className="w-4 h-4 text-blue-400" />,
  };
  const severityCls = {
    error: "border-red-800/40 bg-red-900/10",
    warning: "border-amber-800/40 bg-amber-900/10",
    info: "border-blue-800/40 bg-blue-900/10",
  };

  return (
    <div className="space-y-4">
      <h3 className="text-[14px] font-semibold text-slate-200 flex items-center gap-2">
        <Bell className="w-4 h-4 text-amber-400" /> Alerte interne
      </h3>

      {alerts.length === 0 ? (
        <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-8 text-center">
          <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
          <p className="text-[13px] text-slate-400">Nicio alertă activă. Totul este în ordine.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {alerts.map((alert) => (
            <div key={alert.id} className={`border rounded-lg px-4 py-3 ${severityCls[alert.severity]}`}>
              <div className="flex items-start gap-3">
                <div className="mt-0.5">{severityIcon[alert.severity]}</div>
                <div className="flex-1">
                  <p className="text-[12px] font-semibold text-slate-200">{alert.message}</p>
                  <p className="text-[10px] text-slate-500 mt-1">
                    {new Date(alert.date).toLocaleDateString("ro-RO")}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}