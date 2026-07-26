/**
 * Angajati — Evidenta interna (lista principala)
 * Afiseaza angajatii cu alerte, documente, status.
 * Link spre profil individual.
 *
 * EVIDENTA INTERNA — NU este document fiscal/contabil.
 */
import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  Users,
  Search,
  ChevronRight,
  AlertTriangle,
  CheckCircle2,
  Bell,
  FileText,
  Heart,
  Calendar,
  Phone,
  Info,
  Loader2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { usePersonalDemoModule } from "@/hooks/usePersonalDemoModule";
import { DOCUMENT_STATUS_CONFIG } from "@/lib/employeeRecordsData";

export default function EmployeesRecords() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const { employeeRecords, documents, alerts, loading, error } = usePersonalDemoModule();

  const employeesWithAlerts = useMemo(() => {
    return employeeRecords.map((emp) => {
      const empAlerts = alerts.filter((a) => a.employeeId === emp.id);
      const empDocs = documents.filter((d) => d.employeeId === emp.id);
      const medicinaDoc = empDocs.find((d) => d.tip === "medicina_muncii");
      const hasExpiredDoc = empDocs.some((d) => d.status === "expirat" || d.status === "expira_curand");
      const hasMissingDoc = empDocs.some((d) => d.status === "lipsa");
      return { ...emp, alerts: empAlerts, medicinaStatus: medicinaDoc?.status || "lipsa", hasExpiredDoc, hasMissingDoc };
    });
  }, [employeeRecords, alerts, documents]);

  const filtered = useMemo(() => {
    return employeesWithAlerts.filter((emp) => {
      if (statusFilter !== "all" && emp.status !== statusFilter) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return emp.name.toLowerCase().includes(q) || emp.functie.toLowerCase().includes(q) || emp.departament.toLowerCase().includes(q);
      }
      return true;
    });
  }, [employeesWithAlerts, statusFilter, searchQuery]);

  const totalActivi = employeeRecords.filter((e) => e.status === "activ").length;
  const totalAlerts = alerts.filter((a) => a.employeeId !== "").length;
  const medicinaProblems = documents.filter((d) => d.tip === "medicina_muncii" && (d.status === "expirat" || d.status === "expira_curand")).length;
  const docsLipsa = documents.filter((d) => d.status === "lipsa").length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 gap-2 text-slate-400 text-sm">
        <Loader2 className="w-5 h-5 animate-spin" />
        Se încarcă angajații din registry operațional...
      </div>
    );
  }

  if (error) {
    return (
      <Alert className="bg-red-900/20 border-red-700/50 text-red-100">
        <AlertTriangle className="h-4 w-4 text-red-400" />
        <AlertDescription className="text-[12px]">{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2 flex-wrap">
            <Users className="w-5 h-5 text-purple-400" />
            <h1 className="text-[18px] font-bold text-slate-100">Evidență internă HR</h1>
            <Badge
              className="text-[10px] uppercase tracking-wide bg-amber-900/50 text-amber-300 border-amber-600/60 hover:bg-amber-900/50"
            >
              DEMO
            </Badge>
            <Badge
              className="text-[10px] uppercase tracking-wide bg-purple-900/40 text-purple-300 border-purple-700/60 hover:bg-purple-900/40"
            >
              HR INTERN
            </Badge>
          </div>
          <p className="text-[13px] text-slate-300 pl-7">
            Fișe interne angajați, statusuri și date administrative. Nu este payroll fiscal — date demo locale.
          </p>
        </div>
      </div>

      <Alert className="bg-amber-900/20 border-amber-700/50 text-amber-100">
        <Info className="h-4 w-4 text-amber-400" />
        <AlertDescription className="text-[12px] text-amber-100/90">
          Datele modulului sunt demonstrative, dar lista de angajați vine din registry-ul operațional live. Nu
          calculează payroll fiscal.
        </AlertDescription>
      </Alert>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <Users className="w-4 h-4 text-blue-400" />
            <span className="text-[10px] text-slate-500 uppercase">Angajati activi</span>
          </div>
          <p className="text-[22px] font-bold text-slate-100">{totalActivi}</p>
        </div>
        <div className={`bg-wo-surface-raised border rounded-lg p-3 ${totalAlerts > 0 ? "border-amber-800/40" : "border-wo-border-strong"}`}>
          <div className="flex items-center gap-2 mb-1">
            <Bell className="w-4 h-4 text-amber-400" />
            <span className="text-[10px] text-slate-500 uppercase">Alerte active</span>
          </div>
          <p className={`text-[22px] font-bold ${totalAlerts > 0 ? "text-amber-400" : "text-slate-500"}`}>{totalAlerts}</p>
        </div>
        <div className={`bg-wo-surface-raised border rounded-lg p-3 ${medicinaProblems > 0 ? "border-red-800/40" : "border-wo-border-strong"}`}>
          <div className="flex items-center gap-2 mb-1">
            <Heart className="w-4 h-4 text-pink-400" />
            <span className="text-[10px] text-slate-500 uppercase">Medicina muncii</span>
          </div>
          <p className={`text-[22px] font-bold ${medicinaProblems > 0 ? "text-red-400" : "text-emerald-400"}`}>
            {medicinaProblems > 0 ? `${medicinaProblems} probleme` : "OK"}
          </p>
        </div>
        <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <FileText className="w-4 h-4 text-slate-400" />
            <span className="text-[10px] text-slate-500 uppercase">Documente lipsa</span>
          </div>
          <p className={`text-[22px] font-bold ${docsLipsa > 0 ? "text-amber-400" : "text-slate-500"}`}>{docsLipsa}</p>
        </div>
      </div>

      {/* Global Alerts */}
      {alerts.filter((a) => a.severity === "error").length > 0 && (
        <div className="bg-red-900/10 border border-red-800/30 rounded-lg px-4 py-3 space-y-1">
          {alerts.filter((a) => a.severity === "error").map((alert) => (
            <div key={alert.id} className="flex items-center gap-2">
              <AlertTriangle className="w-3.5 h-3.5 text-red-400 shrink-0" />
              <p className="text-[11px] text-red-300">
                <strong>{alert.employeeName}:</strong> {alert.message}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2 bg-wo-surface-raised border border-wo-border-subtle rounded-lg px-3 py-2 flex-1 max-w-md focus-within:border-blue-500/50">
          <Search className="w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Cauta nume, functie, departament..."
            className="bg-transparent text-[13px] text-slate-200 placeholder:text-slate-600 outline-none w-full"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-wo-surface-raised border border-wo-border-subtle rounded-md px-2 py-2 text-[12px] text-slate-200"
        >
          <option value="all">Toate statusurile</option>
          <option value="activ">Activ</option>
          <option value="inactiv">Inactiv</option>
          <option value="plecat">Plecat</option>
        </select>
        <span className="text-[11px] text-slate-500 ml-auto">{filtered.length} angajati</span>
      </div>

      {/* Employee List */}
      <div className="space-y-2">
        {filtered.map((emp) => (
          <button
            key={emp.id}
            onClick={() => navigate(`/employees-records/${emp.id}`)}
            className="w-full bg-wo-surface-raised border border-wo-border-subtle rounded-lg px-4 py-3 text-left transition-all hover:border-slate-500 hover:scale-[1.005]"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-slate-700 flex items-center justify-center text-[13px] font-bold text-slate-300 shrink-0">
                {emp.name.split(" ").map((n) => n[0]).slice(0, 2).join("")}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                  <span className="text-[13px] font-semibold text-slate-200">{emp.name}</span>
                  <span className={`px-2 py-0.5 text-[10px] font-semibold rounded border ${
                    emp.status === "activ"
                      ? "bg-emerald-900/40 text-emerald-300 border-emerald-700"
                      : emp.status === "inactiv"
                        ? "bg-amber-900/40 text-amber-300 border-amber-700"
                        : "bg-red-900/40 text-red-300 border-red-700"
                  }`}>
                    {emp.status === "activ" ? "Activ" : emp.status === "inactiv" ? "Inactiv" : "Plecat"}
                  </span>
                  {emp.alerts.length > 0 && (
                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[9px] font-bold rounded-full bg-amber-900/40 text-amber-300 border border-amber-700">
                      <Bell className="w-2.5 h-2.5" /> {emp.alerts.length}
                    </span>
                  )}
                  {emp.hasExpiredDoc && (
                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[9px] font-bold rounded-full bg-red-900/40 text-red-300 border border-red-700">
                      <AlertTriangle className="w-2.5 h-2.5" /> Doc expirat
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3 text-[10px] text-slate-500">
                  <span>{emp.functie}</span>
                  <span className="text-slate-700">|</span>
                  <span>{emp.statiePrincipala}</span>
                  <span className="text-slate-700">|</span>
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {new Date(emp.dataAngajarii).toLocaleDateString("ro-RO")}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {/* Medicina muncii status dot */}
                <div className="text-center">
                  <Heart className={`w-4 h-4 ${
                    emp.medicinaStatus === "valid" ? "text-emerald-400" :
                    emp.medicinaStatus === "expira_curand" ? "text-amber-400" :
                    emp.medicinaStatus === "expirat" ? "text-red-400" : "text-slate-600"
                  }`} />
                  <p className="text-[8px] text-slate-600 mt-0.5">Med.</p>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-600" />
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}