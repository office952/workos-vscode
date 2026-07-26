import { Zap, LogIn, Shield, Database, Factory } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export default function LoginGate() {
  const { login } = useAuth();

  return (
    <div className="min-h-screen flex items-center justify-center bg-wo-surface-app p-4">
      <div className="w-full max-w-md bg-wo-surface-raised border border-wo-border-subtle rounded-2xl p-8 shadow-2xl">
        {/* Logo */}
        <div className="flex items-center justify-center gap-2 mb-6">
          <div className="w-12 h-12 rounded-xl bg-primary/20 border border-primary/40 flex items-center justify-center">
            <Zap className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h1 className="text-[22px] font-bold tracking-tight text-wo-text-primary">
              ERP WorkOS
            </h1>
            <p className="text-[11px] text-wo-text-dim uppercase tracking-wider">
              Production Intelligence
            </p>
          </div>
        </div>

        {/* Tagline */}
        <p className="text-center text-[13px] text-wo-text-muted mb-6 leading-relaxed">
          Sistem de management integrat pentru producție, intake, ofertare și comenzi.
        </p>

        {/* Feature grid */}
        <div className="grid grid-cols-3 gap-2 mb-6">
          <div className="bg-wo-surface-shell border border-wo-border-subtle rounded-lg p-2.5 text-center">
            <Factory className="w-4 h-4 text-primary mx-auto mb-1" />
            <p className="text-[10px] text-wo-text-muted">Producție</p>
          </div>
          <div className="bg-wo-surface-shell border border-wo-border-subtle rounded-lg p-2.5 text-center">
            <Database className="w-4 h-4 text-wo-success mx-auto mb-1" />
            <p className="text-[10px] text-wo-text-muted">Inventar OC</p>
          </div>
          <div className="bg-wo-surface-shell border border-wo-border-subtle rounded-lg p-2.5 text-center">
            <Shield className="w-4 h-4 text-wo-warning mx-auto mb-1" />
            <p className="text-[10px] text-wo-text-muted">Governance</p>
          </div>
        </div>

        {/* Login button */}
        <button
          onClick={login}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary hover:opacity-90 text-primary-foreground rounded-lg text-[13px] font-bold transition-colors"
        >
          <LogIn className="w-4 h-4" />
          Autentificare
        </button>

        <p className="text-center text-[10px] text-wo-text-dim mt-4">
          Accesul este restricționat la utilizatori autorizați.
        </p>
      </div>
    </div>
  );
}