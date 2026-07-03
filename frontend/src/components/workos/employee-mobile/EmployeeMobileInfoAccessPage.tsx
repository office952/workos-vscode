import EmployeeMobileAccountPanel from "@/components/workos/employee-mobile/EmployeeMobileAccountPanel";

export default function EmployeeMobileInfoAccessPage() {
  return (
    <div className="space-y-3" data-testid="employee-mobile-info-access">
      <div className="px-0.5">
        <h2 className="text-[15px] font-semibold text-slate-100">Info &amp; acces</h2>
        <p className="text-[11px] text-slate-500 mt-0.5">Cont, profil legat și instalare aplicație</p>
      </div>
      <EmployeeMobileAccountPanel />
    </div>
  );
}
