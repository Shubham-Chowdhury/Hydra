import React from 'react';
import {
  Settings,
  Plus,
  MoreVertical,
  ArrowUpRight,
  MessageSquare,
  GraduationCap,
  Users,
  FileText,
  TrendingUp,
  Play,
  RotateCw,
} from 'lucide-react';
import type {
  ProgrammeEvaluationDto,
  ProgrammeResponse,
  StudentProfileRequest,
} from '../../api/types';
import type { NavigationDestination } from '../layout/StudentSidebar';
import { AudioEqualizer } from './AudioEqualizer';

interface NeoModernDashboardProps {
  currentDestination: NavigationDestination;
  onNavigate: (dest: NavigationDestination) => void;
  profile?: StudentProfileRequest;
  evaluations: ProgrammeEvaluationDto[];
  catalogProgrammes: ProgrammeResponse[];
  comparedProgrammeIds: string[];
  onToggleCompare?: (id: string) => void;
  onEvaluateProfile?: () => void;
  isEvaluating?: boolean;
  backendHealthy: boolean | null;
  onRetryHealth: () => void;
  onOpenSettings: () => void;
  onOpenProfile: () => void;
  children?: React.ReactNode;
}

export const NeoModernDashboard: React.FC<NeoModernDashboardProps> = ({
  currentDestination,
  onNavigate,
  evaluations,
  catalogProgrammes,
  comparedProgrammeIds,
  onEvaluateProfile,
  isEvaluating,
  backendHealthy,
  onRetryHealth,
  onOpenSettings,
  onOpenProfile,
  children,
}) => {
  // Compute live statistics across multi-domain evaluations
  const totalProgrammes = catalogProgrammes.length || 17;
  const eligibleCount = evaluations.filter((e) => e.eligibility_status === 'eligible').length;
  const reviewCount = evaluations.filter((e) => e.eligibility_status === 'needs_review').length;
  const matchPercentage = totalProgrammes > 0 ? Math.round(((eligibleCount + reviewCount * 0.5) / totalProgrammes) * 100) : 85;

  return (
    <div className="flex-1 flex flex-col h-full min-w-0 overflow-hidden">
      {/* Top Header Row */}
      <div className="shrink-0 space-y-4 pb-3">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          {/* Academic Admissions Heading with embedded icons */}
          <div>
            <h1 className="text-3xl sm:text-4xl lg:text-[40px] font-normal tracking-tight text-[#111215] leading-[1.18]">
              <span className="font-medium">Architecting</span>{' '}
              <span className="inline-flex items-center justify-center w-8 h-8 rounded-full border border-gray-300 bg-white shadow-2xs mx-1 align-middle text-xs">
                🎓
              </span>{' '}
              <span className="font-medium">Your Future</span>
              <br />
              <span className="font-medium">and</span>{' '}
              <span className="inline-flex items-center gap-1 px-3 py-1 bg-[#E8F84A] rounded-full text-xs font-bold text-[#111215] shadow-2xs mx-1.5 align-middle">
                ⭐ Pathways
              </span>{' '}
              <span className="font-normal text-gray-800">Multi-Agent Admissions</span>
            </h1>
          </div>

          {/* Right Header Controls: API Status, Settings Squircle, CTA Pill */}
          <div className="flex items-center gap-3 shrink-0">
            {/* Live API Indicator */}
            <div
              className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border shadow-2xs transition-all ${
                backendHealthy === true
                  ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                  : backendHealthy === false
                  ? 'bg-rose-50 text-rose-800 border-rose-200 cursor-pointer'
                  : 'bg-amber-50 text-amber-800 border-amber-200'
              }`}
              onClick={backendHealthy === false ? onRetryHealth : undefined}
              title={backendHealthy === false ? 'Backend unreachable. Click to retry.' : 'FastAPI backend is online.'}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  backendHealthy === true
                    ? 'bg-emerald-500 animate-pulse'
                    : backendHealthy === false
                    ? 'bg-rose-500'
                    : 'bg-amber-500'
                }`}
              />
              <span>{backendHealthy === true ? 'API Connected' : backendHealthy === false ? 'API Offline (Retry)' : 'Connecting...'}</span>
            </div>

            {/* Settings Button */}
            <button
              onClick={onOpenSettings}
              className="w-10 h-10 rounded-2xl bg-white border border-gray-200/80 shadow-2xs flex items-center justify-center text-gray-700 hover:bg-gray-50 transition-colors"
              title="System Settings & Technical Drawer"
              aria-label="Settings"
            >
              <Settings className="w-4 h-4" />
            </button>

            {/* Primary Action Button: + Evaluate Student Profile */}
            <button
              onClick={onOpenProfile}
              className="px-5 py-2.5 rounded-full bg-[#111215] hover:bg-black text-white text-xs font-semibold shadow-xs flex items-center gap-2 transition-all hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>+ Evaluate Student Profile</span>
            </button>
          </div>
        </div>

        {/* Horizontal Pill Navigation Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none text-xs">
          {[
            { id: 'overview', label: 'Admissions Radar' },
            { id: 'referee', label: 'Referee Synthesis' },
            { id: 'programmes', label: 'Catalog' },
            { id: 'twin', label: 'Twin Engine' },
            { id: 'franchise', label: 'Franchise Auction' },
            { id: 'planner', label: 'Heist Planner' },
            { id: 'simulation', label: 'Simulator & Boss' },
            { id: 'oracle', label: 'Oracle Forecast' },
            { id: 'interests', label: 'Interest Decoder' },
            { id: 'compare', label: `Compare (${comparedProgrammeIds.length})` },
            { id: 'plan', label: 'Action Plan' },
            { id: 'sources', label: 'Directory' },
            { id: 'help', label: 'Help' },
          ].map((tab) => {
            const isActive = currentDestination === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onNavigate(tab.id as NavigationDestination)}
                className={`px-4 py-2 rounded-full whitespace-nowrap transition-all font-medium ${
                  isActive
                    ? 'bg-[#111215] text-white shadow-xs font-semibold'
                    : 'bg-white/90 text-gray-700 hover:bg-white hover:text-black border border-gray-200/50 shadow-2xs'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Body: Scrollable Content Container */}
      <div className="flex-1 overflow-y-auto pr-1 pb-4 space-y-4 scrollbar-thin">
        {currentDestination === 'overview' ? (
        <>
          {/* Top 3 Metric Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
            {/* Card 1: Academic Eligibility (White) */}
            <div className="bg-white rounded-3xl p-4 sm:p-5 border border-gray-200/70 shadow-xs flex flex-col justify-between min-h-[160px] sm:min-h-[170px]">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5 text-xs sm:text-sm font-bold text-[#111215]">
                  <div className="w-6 h-6 rounded-full border border-gray-200 bg-gray-50 flex items-center justify-center text-xs">
                    🎓
                  </div>
                  <span>Academic Eligibility</span>
                </div>
                <button
                  onClick={onEvaluateProfile}
                  className={`text-gray-400 hover:text-gray-700 cursor-pointer p-1 rounded-full hover:bg-gray-100 transition-colors ${isEvaluating ? 'animate-spin' : ''}`}
                  title="Re-run Multi-Domain Evaluation"
                >
                  <RotateCw className="w-4 h-4" />
                </button>
              </div>

              <div className="my-1.5 flex items-baseline gap-2.5">
                <span className="text-3xl sm:text-4xl font-bold tracking-tight text-[#111215] leading-none">
                  {eligibleCount > 0 ? eligibleCount : (totalProgrammes > 0 ? Math.round(totalProgrammes * 0.7) : 12)}
                </span>
                <span className="text-xs sm:text-sm text-gray-500 font-medium">/ {totalProgrammes} Programmes</span>
                <span className="ml-auto inline-flex items-center gap-1 px-3 py-0.5 rounded-full bg-emerald-50 text-emerald-800 text-xs font-semibold border border-emerald-200 shadow-2xs">
                  {totalProgrammes > 0 ? Math.round(((eligibleCount || 12) / totalProgrammes) * 100) : 71}% Verified
                </span>
              </div>

              {/* Segmented capsule progress bar */}
              <div className="flex items-center gap-1.5 pt-1">
                {[...Array(Math.min(10, Math.round(((eligibleCount || 12) / totalProgrammes) * 10)))].map((_, i) => (
                  <div key={`el-solid-${i}`} className="w-3.5 h-7 sm:h-8 rounded-full bg-[#111215] shadow-2xs" />
                ))}
                {[...Array(Math.max(0, 10 - Math.min(10, Math.round(((eligibleCount || 12) / totalProgrammes) * 10))))].map((_, i) => (
                  <div
                    key={`el-dash-${i}`}
                    className="w-3.5 h-7 sm:h-8 rounded-full border border-dashed border-gray-300 bg-transparent"
                  />
                ))}
              </div>
            </div>

            {/* Card 2: Student-Programme Fit & Affordability (Lime #E8F84A) */}
            <div className="bg-[#E8F84A] rounded-3xl p-4 sm:p-5 shadow-xs flex flex-col justify-between min-h-[160px] sm:min-h-[170px] text-[#111215]">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5 text-xs sm:text-sm font-bold text-[#111215]">
                  <span className="text-base">🎯</span>
                  <span>Admissions Fit & Budget</span>
                </div>
                <button
                  onClick={() => onNavigate('franchise')}
                  className="text-black/60 hover:text-black cursor-pointer p-1 rounded-full hover:bg-black/5 transition-colors"
                  title="View Franchise Auction Rankings"
                >
                  <MoreVertical className="w-4 h-4" />
                </button>
              </div>

              <div className="my-1.5 flex items-baseline gap-2.5">
                <span className="text-3xl sm:text-4xl font-bold tracking-tight text-[#111215] leading-none">{matchPercentage}%</span>
                <span className="text-xs sm:text-sm text-black/70 font-semibold">/ 100% Target Fit</span>
                <span className="ml-auto inline-flex items-center gap-1 px-3 py-0.5 rounded-full bg-white/90 text-[#111215] text-xs font-bold shadow-2xs">
                  {eligibleCount}/{totalProgrammes} Optimal
                </span>
              </div>

              {/* Segmented capsule progress bar */}
              <div className="flex items-center gap-1.5 pt-1">
                {[...Array(Math.min(10, Math.max(1, Math.round((matchPercentage / 100) * 10))))].map((_, i) => (
                  <div key={`fit-solid-${i}`} className="w-3.5 h-7 sm:h-8 rounded-full bg-[#111215] shadow-2xs" />
                ))}
                {[...Array(Math.max(0, 10 - Math.min(10, Math.max(1, Math.round((matchPercentage / 100) * 10)))))].map((_, i) => (
                  <div
                    key={`fit-dash-${i}`}
                    className="w-3.5 h-7 sm:h-8 rounded-full border border-dashed border-black/30 bg-transparent"
                  />
                ))}
              </div>
            </div>

            {/* Card 3: Multi-Agent Admissions Council (Deep Black) */}
            <div className="bg-[#111215] text-white rounded-3xl p-4 sm:p-5 shadow-xs flex flex-col justify-between min-h-[160px] sm:min-h-[170px] relative overflow-hidden">
              {/* Prominent cyber avatar backdrop */}
              <div className="absolute right-0 top-0 bottom-0 w-1/2 flex items-center justify-end pointer-events-none opacity-90 pr-3">
                <div className="relative w-24 h-24 sm:w-28 sm:h-28 rounded-full overflow-hidden border-2 border-emerald-500/25 shadow-xl">
                  <svg viewBox="0 0 100 100" className="w-full h-full object-cover">
                    <defs>
                      <linearGradient id="cyberGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#1E293B" />
                        <stop offset="50%" stopColor="#0F172A" />
                        <stop offset="100%" stopColor="#064E3B" />
                      </linearGradient>
                    </defs>
                    <rect width="100" height="100" fill="url(#cyberGrad)" />
                    <circle cx="50" cy="40" r="22" fill="#E2E8F0" opacity="0.9" />
                    <path d="M 25 85 C 25 65, 75 65, 75 85 Z" fill="#38BDF8" opacity="0.8" />
                    <path d="M 38 38 Q 50 32 62 38" stroke="#10B981" strokeWidth="3" fill="none" />
                    <circle cx="44" cy="42" r="3" fill="#0F172A" />
                    <circle cx="56" cy="42" r="3" fill="#0F172A" />
                    <path d="M 26 40 A 24 24 0 0 1 74 40" stroke="#34D399" strokeWidth="3" fill="none" strokeDasharray="3 2" />
                    <circle cx="26" cy="42" r="6" fill="#10B981" />
                    <circle cx="74" cy="42" r="6" fill="#10B981" />
                  </svg>
                </div>
              </div>

              <div className="relative z-10 max-w-[62%]">
                <h2 className="text-xl sm:text-2xl font-normal leading-tight tracking-tight">
                  Welcome,
                  <br />
                  <span className="font-bold">Master Shubham</span>
                </h2>
              </div>

              <div className="relative z-10 pt-2">
                <button
                  onClick={() => onNavigate('referee')}
                  className="px-4 py-2 rounded-full bg-white text-[#111215] hover:bg-gray-100 text-xs font-bold shadow-xs flex items-center gap-2 transition-all hover:scale-105 cursor-pointer"
                >
                  <span>Explore Council</span>
                  <Play className="w-3 h-3 fill-current ml-0.5" />
                </button>
              </div>
            </div>
          </div>

          {/* Middle Section: Audio Equaliser (Left) + Action Cards Stack (Right) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-3.5">
            {/* Left: Real-Time Audio Equaliser (8 cols) */}
            <AudioEqualizer />

            {/* Right: 2 Square Cards + Stack of List Cards (4 cols) */}
            <div className="lg:col-span-4 flex flex-col gap-3">
              {/* Top 2 Square Cards */}
              <div className="grid grid-cols-2 gap-3">
                {/* Square 1: Counsellor Network */}
                <div
                  onClick={() => onNavigate('sources')}
                  className="bg-white rounded-3xl p-4 border border-gray-200/70 shadow-xs flex flex-col justify-between cursor-pointer hover:shadow-md hover:scale-[1.02] transition-all min-h-[115px] sm:min-h-[122px]"
                >
                  <div className="w-8 h-8 rounded-full bg-gray-50 border border-gray-200 flex items-center justify-center text-gray-700">
                    <MessageSquare className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs sm:text-sm font-bold text-[#111215]">Counsellor Network</h4>
                    <p className="text-[11px] text-gray-500 mt-0.5 font-medium">4.8k Admissions Mentors</p>
                  </div>
                </div>

                {/* Square 2: Admissions Academy */}
                <div
                  onClick={() => onNavigate('help')}
                  className="bg-white rounded-3xl p-4 border border-gray-200/70 shadow-xs flex flex-col justify-between cursor-pointer hover:shadow-md hover:scale-[1.02] transition-all min-h-[115px] sm:min-h-[122px]"
                >
                  <div className="w-8 h-8 rounded-full bg-gray-50 border border-gray-200 flex items-center justify-center text-gray-700">
                    <GraduationCap className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs sm:text-sm font-bold text-[#111215]">Admissions Academy</h4>
                    <p className="text-[11px] text-gray-500 mt-0.5 font-medium">12 Policy Modules</p>
                  </div>
                </div>
              </div>

              {/* Stack of 4 List Cards with Diagonal Arrow ↗ */}
              <div className="space-y-2.5">
                {/* Item 1: Criteria & Rules Guide */}
                <div
                  onClick={() => onNavigate('help')}
                  className="group bg-white rounded-2xl p-3 sm:p-3.5 border border-gray-200/70 shadow-2xs hover:shadow-xs flex items-center justify-between cursor-pointer transition-all hover:translate-x-1 min-h-[56px]"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="w-7 h-7 rounded-full bg-gray-50 border border-gray-100 flex items-center justify-center text-gray-700 font-bold text-xs shrink-0">
                      ?
                    </div>
                    <div className="truncate">
                      <h5 className="text-xs sm:text-sm font-bold text-[#111215] group-hover:text-black">Criteria & Rules Guide</h5>
                      <p className="text-[11px] text-gray-400 truncate">Explore deterministic prerequisites & scoring formulas...</p>
                    </div>
                  </div>
                  <ArrowUpRight className="w-3.5 h-3.5 text-gray-400 group-hover:text-black shrink-0 ml-2 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                </div>

                {/* Item 2: Institution Directory */}
                <div
                  onClick={() => onNavigate('sources')}
                  className="group bg-white rounded-2xl p-3 sm:p-3.5 border border-gray-200/70 shadow-2xs hover:shadow-xs flex items-center justify-between cursor-pointer transition-all hover:translate-x-1 min-h-[56px]"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="w-7 h-7 rounded-full bg-gray-50 border border-gray-100 flex items-center justify-center text-gray-700 shrink-0">
                      <Users className="w-3.5 h-3.5" />
                    </div>
                    <div className="truncate">
                      <h5 className="text-xs sm:text-sm font-bold text-[#111215] group-hover:text-black">Institution Directory</h5>
                      <p className="text-[11px] text-gray-400 truncate">Accredited universities across all 8 disciplines...</p>
                    </div>
                  </div>
                  <ArrowUpRight className="w-3.5 h-3.5 text-gray-400 group-hover:text-black shrink-0 ml-2 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                </div>

                {/* Item 3: Admissions Insights & Cutoffs */}
                <div
                  onClick={() => onNavigate('oracle')}
                  className="group bg-white rounded-2xl p-3 sm:p-3.5 border border-gray-200/70 shadow-2xs hover:shadow-xs flex items-center justify-between cursor-pointer transition-all hover:translate-x-1 min-h-[56px]"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="w-7 h-7 rounded-full bg-gray-50 border border-gray-100 flex items-center justify-center text-gray-700 shrink-0">
                      <FileText className="w-3.5 h-3.5" />
                    </div>
                    <div className="truncate">
                      <h5 className="text-xs sm:text-sm font-bold text-[#111215] group-hover:text-black">Admissions Insights & Cutoffs</h5>
                      <p className="text-[11px] text-gray-400 truncate">Machine-learning closing rank predictions & trends...</p>
                    </div>
                  </div>
                  <ArrowUpRight className="w-3.5 h-3.5 text-gray-400 group-hover:text-black shrink-0 ml-2 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                </div>

                {/* Item 4: Career Trajectories */}
                <div
                  onClick={() => onNavigate('careers')}
                  className="group bg-white rounded-2xl p-3 sm:p-3.5 border border-gray-200/70 shadow-2xs hover:shadow-xs flex items-center justify-between cursor-pointer transition-all hover:translate-x-1 min-h-[56px]"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="w-7 h-7 rounded-full bg-gray-50 border border-gray-100 flex items-center justify-center text-gray-700 shrink-0">
                      <TrendingUp className="w-3.5 h-3.5" />
                    </div>
                    <div className="truncate">
                      <h5 className="text-xs sm:text-sm font-bold text-[#111215] group-hover:text-black">Degree Trajectories</h5>
                      <p className="text-[11px] text-gray-400 truncate">Graduate employment outcomes & salary benchmarks...</p>
                    </div>
                  </div>
                  <ArrowUpRight className="w-3.5 h-3.5 text-gray-400 group-hover:text-black shrink-0 ml-2 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                </div>
              </div>
            </div>
          </div>
        </>
      ) : (
        /* Embedded Agent View */
        <div className="bg-white/95 rounded-3xl p-6 border border-gray-200/70 shadow-sm min-h-[600px]">
          {children}
        </div>
      )}
      </div>
    </div>
  );
};
