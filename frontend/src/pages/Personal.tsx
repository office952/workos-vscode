import { useState } from "react";
import { usePersonalData } from "@/hooks/usePersonalData";
import {
  type PersonalRole,
  type PersonalStatus,
  type PersonalMember,
} from "@/lib/mockData";
import {
  Users,
  Search,
  User,
  Shield,
  Wrench,
  Crown,
  GraduationCap,
  CheckCircle2,
  Clock,
  AlertTriangle,
  BookOpen,
  Phone,
  ChevronRight,
  Activity,
  Star,
  Calendar,
  Database,
  Loader2,
} from "lucide-react";

const roleConfig: Record<PersonalRole, { label: string; cls: string; icon: React.ReactNode }> = {
  operator: { label: "Operator", cls: "bg-blue-900/40 text-blue-300 border-blue-700", icon: <User className="w-3 h-3" /> },
  team_lead: { label: "Team Lead", cls: "bg-purple-900/40 text-purple-300 border-purple-700", icon: <Shield className="w-3 h-3" /> },
  technician: { label: "Tehnician", cls: "bg-cyan-900/40 text-cyan-300 border-cyan-700", icon: <Wrench className="w-3 h-3" /> },
  manager: { label: "Manager", cls: "bg-amber-900/40 text-amber-300 border-amber-700", icon: <Crown className="w-3 h-3" /> },
  apprentice: { label: "Ucenic", cls: "bg-slate-700/60 text-slate-300 border-slate-600", icon: <GraduationCap className="w-3 h-3" /> },
};

const statusConfig: Record<PersonalStatus, { label: string; cls: string; icon: React.ReactNode }> = {
  active: { label: "Activ", cls: "text-emerald-400", icon: <CheckCircle2 className="w-3 h-3" /> },
  on_leave: { label: "Concediu", cls: "text-amber-400", icon: <Clock className="w-3 h-3" /> },
  sick: { label: "Medical", cls: "text-red-400", icon: <AlertTriangle className="w-3 h-3" /> },
  training: { label: "Training", cls: "text-blue-400", icon: <BookOpen className="w-3 h-3" /> },
};

function RoleBadge({ role }: { role: PersonalRole }) {
  const cfg = roleConfig[role];
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-semibold rounded border ${cfg.cls}`}>
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

function StatusDot({ status }: { status: PersonalStatus }) {
  const cfg = statusConfig[status];
  return (
    <span className={`inline-flex items-center gap-1 text-[11px] font-medium ${cfg.cls}`}>
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

function QualityBar({ score }: { score: number }) {
  const color = score >= 90 ? "bg-emerald-500" : score >= 80 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${score}%` }} />
      </div>
      <span className="text-[11px] text-slate-400 font-mono w-8 text-right">{score}%</span>
    </div>
  );
}

function DataSourceBadge({ source }: { source: "db" | "mock" | "empty" | "error" | "loading" }) {
  if (source === "loading") return null;
  const isLive = source === "db";
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-semibold rounded-full border ${
        isLive
          ? "bg-emerald-900/40 text-emerald-300 border-emerald-700"
          : "bg-amber-900/40 text-amber-300 border-amber-700"
      }`}
    >
      <Database className="w-3 h-3" />
      {isLive ? "Live DB" : source === "mock" ? "Mock Data" : "No Data"}
    </span>
  );
}

export default function Personal() {
  const { members, loading, source } = usePersonalData();
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState<PersonalStatus | "all">("all");
  const [selected, setSelected] = useState<PersonalMember | null>(null);

  const statusCounts = {
    active: members.filter((c) => c.status === "active").length,
    on_leave: members.filter((c) => c.status === "on_leave").length,
    sick: members.filter((c) => c.status === "sick").length,
    training: members.filter((c) => c.status === "training").length,
  };

  const filtered = members.filter((c) => {
    if (filterStatus !== "all" && c.status !== filterStatus) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return c.name.toLowerCase().includes(q) || c.workcenterName.toLowerCase().includes(q) || c.skills.some((s) => s.toLowerCase().includes(q));
    }
    return true;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
        <span className="ml-2 text-slate-400 text-sm">Se încarcă personalul...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Users className="w-5 h-5 text-purple-400" />
          <h1 className="text-[18px] font-bold text-slate-100">Personal / Angajați</h1>
          <span className="text-[10px] text-slate-500 bg-slate-800 px-2 py-0.5 rounded-full ml-1">
            {members.length} persoane
          </span>
          <DataSourceBadge source={source} />
        </div>
      </div>

      {/* Status Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {(Object.entries(statusCounts) as [PersonalStatus, number][]).map(([status, count]) => {
          const cfg = statusConfig[status];
          const isActive = filterStatus === status;
          return (
            <div
              key={status}
              onClick={() => setFilterStatus(filterStatus === status ? "all" : status)}
              className={`bg-[#1A2236] border rounded-lg p-3 cursor-pointer transition-all ${
                isActive ? "border-blue-500/50 ring-1 ring-blue-500/30" : "border-[#2A3548] hover:border-slate-500"
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className={cfg.cls}>{cfg.icon}</span>
                <span className="text-[12px] font-semibold text-slate-200">{cfg.label}</span>
              </div>
              <p className="text-[24px] font-bold text-slate-100">{count}</p>
            </div>
          );
        })}
      </div>

      {/* Search */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 bg-[#111827] border border-[#1E293B] rounded-lg px-3 py-2 flex-1 max-w-md focus-within:border-blue-500/50">
          <Search className="w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Caută nume, workcenter, skill..."
            className="bg-transparent text-[13px] text-slate-200 placeholder:text-slate-600 outline-none w-full"
          />
        </div>
        {filterStatus !== "all" && (
          <button onClick={() => setFilterStatus("all")} className="text-[11px] text-slate-400 hover:text-slate-200 transition-colors">
            Resetează filtru
          </button>
        )}
        <span className="text-[11px] text-slate-500 ml-auto">{filtered.length} rezultate</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* List */}
        <div className="lg:col-span-2 space-y-2">
          {filtered.map((col) => (
            <div
              key={col.id}
              onClick={() => setSelected(col)}
              className={`bg-[#111827] border rounded-lg p-3 cursor-pointer transition-all ${
                selected?.id === col.id ? "border-blue-500/50 ring-1 ring-blue-500/30" : "border-[#1E293B] hover:border-slate-500"
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-slate-700 flex items-center justify-center text-[13px] font-bold text-slate-300 shrink-0">
                  {col.name.split(" ").map((n) => n[0]).join("")}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-[13px] font-semibold text-slate-200">{col.name}</span>
                    <RoleBadge role={col.role} />
                    <StatusDot status={col.status} />
                  </div>
                  <div className="flex items-center gap-3 text-[10px] text-slate-500">
                    <span>{col.workcenterName}</span>
                    <span>•</span>
                    <span>{col.currentJobId || "—"}</span>
                    <span>•</span>
                    <span>Azi: {col.tasksCompletedToday} task-uri</span>
                    <span>•</span>
                    <span>Q: {col.qualityScore}%</span>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-600 shrink-0" />
              </div>
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-8 text-center text-slate-500 text-[13px]">
              Niciun angajat găsit.
            </div>
          )}
        </div>

        {/* Detail Panel */}
        <div className="space-y-4">
          {selected ? (
            <>
              <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 rounded-full bg-slate-700 flex items-center justify-center text-[16px] font-bold text-slate-300">
                    {selected.name.split(" ").map((n) => n[0]).join("")}
                  </div>
                  <div>
                    <h3 className="text-[16px] font-bold text-slate-100">{selected.name}</h3>
                    <div className="flex items-center gap-2 mt-0.5">
                      <RoleBadge role={selected.role} />
                      <StatusDot status={selected.status} />
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Workcenter</p>
                      <p className="text-[12px] text-slate-300">{selected.workcenterName}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Schimb</p>
                      <p className="text-[12px] text-slate-300 font-mono">{selected.shiftStart} — {selected.shiftEnd}</p>
                    </div>
                  </div>

                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Skills</p>
                    <div className="flex flex-wrap gap-1">
                      {selected.skills.map((s) => (
                        <span key={s} className="px-2 py-0.5 text-[10px] bg-slate-800 text-slate-300 rounded border border-slate-700">
                          {s}
                        </span>
                      ))}
                      {selected.skills.length === 0 && (
                        <span className="text-[10px] text-slate-600">Niciun skill definit</span>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Task Curent</p>
                      <p className="text-[12px] text-slate-300 font-mono">{selected.currentTaskId || "—"}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Job Curent</p>
                      <p className="text-[12px] text-slate-300 font-mono">{selected.currentJobId || "—"}</p>
                    </div>
                  </div>

                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1 flex items-center gap-1">
                      <Phone className="w-3 h-3" /> Contact
                    </p>
                    <p className="text-[12px] text-slate-300">{selected.phone}</p>
                  </div>

                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1 flex items-center gap-1">
                      <Calendar className="w-3 h-3" /> Data angajării
                    </p>
                    <p className="text-[12px] text-slate-300">{new Date(selected.hireDate).toLocaleDateString("ro-RO")}</p>
                  </div>
                </div>
              </div>

              {/* Performance */}
              <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Activity className="w-4 h-4 text-blue-400" />
                  <span className="text-[13px] font-bold text-slate-200">Performanță</span>
                </div>
                <div className="space-y-3">
                  <div className="grid grid-cols-3 gap-3">
                    <div className="bg-[#1A2236] rounded-lg p-2 text-center">
                      <p className="text-[18px] font-bold text-slate-100">{selected.tasksCompletedToday}</p>
                      <p className="text-[9px] text-slate-500 uppercase">Azi</p>
                    </div>
                    <div className="bg-[#1A2236] rounded-lg p-2 text-center">
                      <p className="text-[18px] font-bold text-slate-100">{selected.tasksCompletedWeek}</p>
                      <p className="text-[9px] text-slate-500 uppercase">Săptămâna</p>
                    </div>
                    <div className="bg-[#1A2236] rounded-lg p-2 text-center">
                      <p className="text-[18px] font-bold text-slate-100">{selected.avgTaskDurationMin}m</p>
                      <p className="text-[9px] text-slate-500 uppercase">Avg/Task</p>
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center gap-1 mb-1">
                      <Star className="w-3 h-3 text-amber-400" />
                      <p className="text-[10px] text-slate-500 uppercase tracking-wide">Scor Calitate</p>
                    </div>
                    <QualityBar score={selected.qualityScore} />
                  </div>
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Ore lucrate azi</p>
                    <p className="text-[14px] font-bold text-slate-200">{selected.hoursToday}h</p>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-8 text-center">
              <Users className="w-8 h-8 text-slate-600 mx-auto mb-2" />
              <p className="text-[13px] text-slate-500">Selectează un angajat pentru detalii</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}