import React from 'react';
import { Compass, ShieldAlert, Sparkles, CheckCircle2, XCircle } from 'lucide-react';

interface NavbarProps {
  isBackendHealthy: boolean | null;
}

export const Navbar: React.FC<NavbarProps> = ({ isBackendHealthy }) => {
  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-50">
      {/* Synthetic Demonstration Warning Banner */}
      <div className="bg-amber-950/40 border-b border-amber-800/40 px-4 py-1.5 text-xs text-amber-300 flex items-center justify-center gap-2">
        <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" aria-hidden="true" />
        <span>
          <strong>DEMONSTRATION CATALOGUE:</strong> All programmes, cutoffs, and institutions shown are synthetic demonstration models, not official admissions criteria.
        </span>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 ring-1 ring-white/20">
            <Compass className="w-6 h-6 text-white" aria-hidden="true" />
          </div>
          <div>
            <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
              Hydra
            </span>
            <span className="ml-2 text-xs font-mono uppercase px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
              Phase 1
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs">
            {isBackendHealthy === null ? (
              <>
                <Sparkles className="w-3.5 h-3.5 text-slate-400 animate-pulse" />
                <span className="text-slate-400 font-mono">Checking API...</span>
              </>
            ) : isBackendHealthy ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400 font-mono">API Online</span>
              </>
            ) : (
              <>
                <XCircle className="w-3.5 h-3.5 text-rose-400" />
                <span className="text-rose-400 font-mono">API Offline</span>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

