import {
  Mail,
  Shield,
  Smartphone,
  User,
  UserCheck,
  UserX,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useEmployeeMobileSelfLink } from "@/hooks/useEmployeeMobileSelfLink";
import {
  employeeMobileAuthRoleLabel,
  getEmployeeMobileAccessSummary,
  shouldProbeEmployeeMobileSelfLink,
} from "@/lib/employeeMobileAccess";
import { cn } from "@/lib/utils";
import { EmployeeMobileInstallCard } from "@/components/workos/employee-mobile/EmployeeMobileShell";
import {
  EmployeeMobileLoadingState,
  EmployeeMobileStatusBadge,
} from "@/components/workos/employee-mobile/EmployeeMobileStates";

function selfLinkMessage(state: ReturnType<typeof useEmployeeMobileSelfLink>["state"]): string | null {
  if (state === "loading") return null;
  if (state === "linked") return "Profil angajat legat — identitate confirmată de server.";
  if (state === "missing") {
    return "Contul nu este legat de un profil de angajat activ. Contactează administratorul.";
  }
  if (state === "inactive") return "Profilul de angajat nu este activ pentru Employee Mobile.";
  if (state === "unavailable") return "Nu am putut confirma legătura profilului angajat.";
  return null;
}

export default function EmployeeMobileAccountPanel() {
  const { user } = useAuth();
  const access = getEmployeeMobileAccessSummary(user?.role);
  const probeSelfLink = shouldProbeEmployeeMobileSelfLink(user?.role);
  const { state: linkState, employeeName } = useEmployeeMobileSelfLink(probeSelfLink);
  const linkMessage = probeSelfLink ? selfLinkMessage(linkState) : null;

  const displayName = user?.name ?? user?.email ?? "Utilizator autentificat";
  const roleLabel = employeeMobileAuthRoleLabel(user?.role);

  return (
    <section
      className="rounded-2xl border border-[#1E293B] bg-[#111827] p-4 space-y-4"
      data-testid="employee-mobile-account-panel"
    >
      <div className="flex items-start gap-3">
        <div
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-500/10 text-slate-400 ring-1 ring-slate-500/15"
          aria-hidden
        >
          <User className="w-5 h-5" />
        </div>
        <div className="min-w-0 flex-1">
          <h2 className="text-[14px] font-semibold text-slate-100">Cont și profil</h2>
          <p className="text-[11px] text-slate-400 leading-relaxed mt-0.5">
            Același cont WorkOS ca pe desktop — contextul afișat depinde de rol.
          </p>
        </div>
      </div>

      <div
        className="rounded-xl border border-[#243044] bg-[#0A1020]/60 p-3 space-y-2.5"
        data-testid="employee-mobile-account-auth"
      >
        <div className="flex items-start justify-between gap-2 flex-wrap">
          <p className="text-[13px] font-semibold text-slate-100 truncate">{displayName}</p>
          <EmployeeMobileStatusBadge
            label={roleLabel}
            variant={access.variant === "manager" ? "review" : "live"}
            testId="employee-mobile-account-role-badge"
          />
        </div>
        {user?.email && (
          <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <Mail className="w-3.5 h-3.5 shrink-0" aria-hidden />
            <span className="truncate">{user.email}</span>
          </div>
        )}
        {employeeName && (
          <div className="flex items-center gap-1.5 text-[11px] text-slate-300">
            <UserCheck className="w-3.5 h-3.5 shrink-0 text-emerald-400" aria-hidden />
            <span>
              Angajat operațional: <span className="font-medium text-slate-200">{employeeName}</span>
            </span>
          </div>
        )}
      </div>

      <div
        className={cn(
          "rounded-xl border px-3 py-2.5 space-y-1",
          access.variant === "manager"
            ? "border-violet-800/40 bg-violet-950/20"
            : "border-emerald-800/35 bg-emerald-950/15",
        )}
        data-testid="employee-mobile-account-access-summary"
      >
        <div className="flex items-center gap-1.5">
          <Shield className="w-3.5 h-3.5 shrink-0 text-slate-400" aria-hidden />
          <p className="text-[11px] font-semibold text-slate-200">{access.title}</p>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed pl-5">{access.description}</p>
      </div>

      {probeSelfLink && linkState === "loading" && (
        <EmployeeMobileLoadingState
          message="Se verifică profilul angajat…"
          testId="employee-mobile-account-link-loading"
        />
      )}

      {probeSelfLink && linkMessage && linkState !== "loading" && (
        <div
          className={cn(
            "rounded-lg border px-3 py-2 text-[11px] leading-relaxed flex items-start gap-2",
            linkState === "linked"
              ? "border-emerald-800/40 bg-emerald-950/20 text-emerald-200"
              : "border-amber-800/40 bg-amber-950/20 text-amber-200",
          )}
          data-testid="employee-mobile-account-self-link"
        >
          {linkState === "linked" ? (
            <UserCheck className="w-3.5 h-3.5 shrink-0 mt-0.5" aria-hidden />
          ) : (
            <UserX className="w-3.5 h-3.5 shrink-0 mt-0.5" aria-hidden />
          )}
          <span>{linkMessage}</span>
        </div>
      )}

      {!probeSelfLink && user?.role === "admin" && (
        <p
          className="text-[11px] text-slate-500 leading-relaxed"
          data-testid="employee-mobile-account-admin-note"
        >
          Cont administrator — gestionezi angajații centralizat din zona desktop Angajați operaționali.
        </p>
      )}

      <div className="flex items-center gap-2 text-[10px] text-slate-500">
        <Smartphone className="w-3.5 h-3.5 shrink-0" aria-hidden />
        <span>Employee Mobile — fără cont separat față de WorkOS.</span>
      </div>

      <EmployeeMobileInstallCard compact />
    </section>
  );
}
