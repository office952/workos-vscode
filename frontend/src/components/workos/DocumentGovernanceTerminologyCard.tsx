interface DocumentGovernanceTerminologyCardProps {
  className?: string;
}

export default function DocumentGovernanceTerminologyCard({ className = "" }: DocumentGovernanceTerminologyCardProps) {
  return (
    <div className={`mt-3 rounded-lg border border-slate-700/40 bg-wo-surface-inset p-3 ${className}`.trim()}>
      <p className="text-[10px] uppercase tracking-wide text-slate-500">Terminologie governance</p>
      <div className="mt-2 space-y-1 text-[11px] text-slate-300">
        <p>
          <span className="font-semibold text-slate-200">Order snapshot</span>: instantaneu comercial blocat la acceptare (config, preț, termene).
        </p>
        <p>
          <span className="font-semibold text-slate-200">Output snapshot</span>: instantaneu al compoziției de output aprobat în Quotes.
        </p>
        <p>
          <span className="font-semibold text-slate-200">Document snapshot reference</span>: legătura din Order către output snapshot-ul aprobat.
        </p>
        <p>
          <span className="font-semibold text-slate-200">Commercial document export</span>: randare read-only pentru ofertă, fără mutație de status.
        </p>
      </div>
    </div>
  );
}