import React from 'react';
import {
  Compass,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Sparkles,
  Scale,
  Orbit,
  BookOpen,
  Route,
  Brain,
  UserCheck,
  ShieldCheck,
  HelpCircle,
} from 'lucide-react';
import type { NavigationDestination } from './StudentSidebar';

interface AppHeaderProps {
  isBackendHealthy: boolean | null;
  onRetryHealth: () => void;
  onToggleTechnicalDrawer: () => void;
  isTechnicalDrawerOpen: boolean;
  comparedProgrammesCount: number;
  currentDestination: NavigationDestination;
  onNavigate: (dest: NavigationDestination) => void;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  isBackendHealthy,
  onRetryHealth,
  onToggleTechnicalDrawer,
  isTechnicalDrawerOpen,
  comparedProgrammesCount,
  currentDestination,
  onNavigate,
}) => {
  return (
    <header className="sticky top-0 z-50 bg-[#070B0E]/95 backdrop-blur-xl border-b border-[#1A2930]">
      {/* Demonstration Banner */}
      <div className="bg-[#101C21] border-b border-[#1E343D] px-4 py-1 text-center text-[11px] font-mono text-[#E5B869] flex items-center justify-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-[#E5B869] animate-pulse" />
        <span>SYNTHETIC DEMONSTRATION KNOWLEDGE UNIVERSE • VERIFIED DETERMINISTIC INFERENCE</span>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
        {/* Brand identity */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#E5B869] to-[#D49F43] text-[#070B0E] flex items-center justify-center shadow-lg glow-gold">
            <Compass className="w-5 h-5" aria-hidden="true" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-black text-[#F0F4F5] tracking-tight">
                HYDRA
              </span>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-[#142227] text-[#3DD9C4] border border-[#233F4A]">
                Constellation v2.0
              </span>
            </div>
          </div>
        </div>

        {/* View Mode Navigation Switcher */}
        <div className="hidden md:flex items-center gap-1 p-1 rounded-2xl bg-[#0C1518] border border-[#1E343D]">
          <button
            onClick={() => onNavigate('overview')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
              currentDestination === 'overview'
                ? 'bg-[#3DD9C4] text-[#070B0E] glow-cyan shadow-sm'
                : 'text-[#8DA1A8] hover:text-[#F0F4F5] hover:bg-[#142227]'
            }`}
          >
            <Orbit className="w-3.5 h-3.5" />
            <span>Constellation</span>
          </button>

          <button
            onClick={() => onNavigate('programmes')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
              currentDestination === 'programmes'
                ? 'bg-[#3DD9C4] text-[#070B0E] glow-cyan shadow-sm'
                : 'text-[#8DA1A8] hover:text-[#F0F4F5] hover:bg-[#142227]'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Catalog</span>
          </button>

          <button
            onClick={() => onNavigate('compare')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
              currentDestination === 'compare'
                ? 'bg-[#3DD9C4] text-[#070B0E] glow-cyan shadow-sm'
                : 'text-[#8DA1A8] hover:text-[#F0F4F5] hover:bg-[#142227]'
            }`}
          >
            <Scale className="w-3.5 h-3.5" />
            <span>Compare</span>
            {comparedProgrammesCount > 0 && (
              <span className="ml-0.5 px-1.5 py-0.2 rounded-full text-[10px] bg-[#E5B869] text-[#070B0E] font-black">
                {comparedProgrammesCount}
              </span>
            )}
          </button>

          <button
            onClick={() => onNavigate('plan')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
              currentDestination === 'plan'
                ? 'bg-[#3DD9C4] text-[#070B0E] glow-cyan shadow-sm'
                : 'text-[#8DA1A8] hover:text-[#F0F4F5] hover:bg-[#142227]'
            }`}
          >
            <Route className="w-3.5 h-3.5" />
            <span>Action Plan</span>
          </button>

          <button
            onClick={() => onNavigate('careers')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
              currentDestination === 'careers'
                ? 'bg-[#3DD9C4] text-[#070B0E] glow-cyan shadow-sm'
                : 'text-[#8DA1A8] hover:text-[#F0F4F5] hover:bg-[#142227]'
            }`}
          >
            <Brain className="w-3.5 h-3.5" />
            <span>Interests</span>
          </button>

          <button
            onClick={() => onNavigate('profile')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
              currentDestination === 'profile'
                ? 'bg-[#3DD9C4] text-[#070B0E] glow-cyan shadow-sm'
                : 'text-[#8DA1A8] hover:text-[#F0F4F5] hover:bg-[#142227]'
            }`}
          >
            <UserCheck className="w-3.5 h-3.5" />
            <span>Profile</span>
          </button>

          <button
            onClick={() => onNavigate('sources')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
              currentDestination === 'sources'
                ? 'bg-[#3DD9C4] text-[#070B0E] glow-cyan shadow-sm'
                : 'text-[#8DA1A8] hover:text-[#F0F4F5] hover:bg-[#142227]'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Evidence</span>
          </button>

          <button
            onClick={() => onNavigate('help')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
              currentDestination === 'help'
                ? 'bg-[#3DD9C4] text-[#070B0E] glow-cyan shadow-sm'
                : 'text-[#8DA1A8] hover:text-[#F0F4F5] hover:bg-[#142227]'
            }`}
          >
            <HelpCircle className="w-3.5 h-3.5" />
            <span>Help</span>
          </button>
        </div>

        {/* Right utility actions */}
        <div className="flex items-center gap-2.5">
          {/* Backend Health Badge */}
          <div
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs border border-[#1E343D] bg-[#0C1518]"
            aria-label="Backend API Service Status"
            title={
              isBackendHealthy
                ? 'API Connected: Backend HTTP service is online. (Indicates API server liveness only; does not imply Oracle or external agent data are validated).'
                : isBackendHealthy === false
                ? 'API Offline: Unable to reach backend server at http://127.0.0.1:8000.'
                : 'Checking backend API connectivity...'
            }
          >
            {isBackendHealthy === null ? (
              <>
                <Sparkles className="w-3 h-3 text-[#8DA1A8] animate-pulse" />
                <span className="text-[#8DA1A8] text-[11px]">Connecting...</span>
              </>
            ) : isBackendHealthy ? (
              <>
                <CheckCircle2 className="w-3 h-3 text-[#3DD9C4]" />
                <span className="text-[#3DD9C4] font-mono text-[11px]">API Connected</span>
              </>
            ) : (
              <>
                <XCircle className="w-3 h-3 text-[#E05263]" />
                <span className="text-[#E05263] font-mono text-[11px]">API Offline</span>
                <button
                  onClick={onRetryHealth}
                  className="ml-1 text-[#E05263] hover:underline inline-flex items-center"
                  title="Retry connecting to API"
                >
                  <RefreshCw className="w-2.5 h-2.5" />
                </button>
              </>
            )}
          </div>

          {/* Technical Inspector Toggle for Counselors / Engineers */}
          <button
            onClick={onToggleTechnicalDrawer}
            className={`text-xs font-bold px-3 py-1.5 rounded-xl border flex items-center gap-1.5 transition-all shadow-sm ${
              isTechnicalDrawerOpen
                ? 'bg-[#3DD9C4] text-[#070B0E] border-[#3DD9C4] glow-cyan'
                : 'bg-[#142227] text-[#8DA1A8] border-[#233F4A] hover:bg-[#1C2F36] hover:text-[#F0F4F5]'
            }`}
            title="Inspect Multi-Agent Technical Audit & System Diagnostics (Advanced)"
            aria-expanded={isTechnicalDrawerOpen}
          >
            <Scale className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Advanced Audit</span>
          </button>
        </div>
      </div>
    </header>
  );
};
