import { Zap, LogIn, Shield, Database, Factory } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export default function LoginGate() {
  const { login } = useAuth();

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0A0F1C] p-4">
      <div className="w-full max-w-md bg-[#111827] border border-[#1E293B] rounded-2xl p-8 shadow-2xl">
        {/* Logo */}
        <div className="flex items-center justify-center gap-2 mb-6">
          <div className="w-12 h-12 rounded-xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center">
            <Zap className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <h1 className="text-[22px] font-bold tracking-tight text-slate-100">
              ERP WorkOS
            </h1>
            <p className="text-[11px] text-slate-500 uppercase tracking-wider">
              Production Intelligence
            </p>
          </div>
        </div>

        {/* Tagline */}
        <p className="text-center text-[13px] text-slate-400 mb-6 leading-relaxed">
          Sistem de management integrat pentru producție, intake, ofertare și comenzi.
        </p>

        {/* Feature grid */}
        <div className="grid grid-cols-3 gap-2 mb-6">
          <div className="bg-[#0D1321] border border-[#1E293B] rounded-lg p-2.5 text-center">
            <Factory className="w-4 h-4 text-blue-400 mx-auto mb-1" />
            <p className="text-[10px] text-slate-400">Producție</p>
          </div>
          <div className="bg-[#0D1321] border border-[#1E293B] rounded-lg p-2.5 text-center">
            <Database className="w-4 h-4 text-emerald-400 mx-auto mb-1" />
            <p className="text-[10px] text-slate-400">Inventar OC</p>
          </div>
          <div className="bg-[#0D1321] border border-[#1E293B] rounded-lg p-2.5 text-center">
            <Shield className="w-4 h-4 text-amber-400 mx-auto mb-1" />
            <p className="text-[10px] text-slate-400">Governance</p>
          </div>
        </div>

        {/* Login button */}
        <button
          onClick={login}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-[13px] font-bold transition-colors"
        >
          <LogIn className="w-4 h-4" />
          Autentificare
        </button>

        <p className="text-center text-[10px] text-slate-600 mt-4">
          Accesul este restricționat la utilizatori autorizați.
        </p>
      </div>
    </div>
  );
}