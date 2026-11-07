import React, { useState } from 'react';
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
  const [selectedYear, setSelectedYear] = useState<string>('2025');

  // Compute live statistics across multi-domain evaluations
  const totalProgrammes = catalogProgrammes.length || 17;
  const eligibleCount = evaluations.filter((e) => e.eligibility_status === 'eligible').length;
  const reviewCount = evaluations.filter((e) => e.eligibility_status === 'needs_review').length;
  const matchPercentage = totalProgrammes > 0 ? Math.round(((eligibleCount + reviewCount * 0.5) / totalProgrammes) * 100) : 85;

  // Domain distribution data for the dual-tone pill bar chart
  const domainColumns = [
    { label: 'Eng', domain: 'Engineering & Tech', topHeight: 52, bottomHeight: 38, topDot: true, bottomDot: true },
    { label: 'Med', domain: 'Medicine & Health', topHeight: 35, bottomHeight: 25, topDot: true, bottomDot: true },
    { label: 'Law', domain: 'Law & Governance', topHeight: 58, bottomHeight: 18, topDot: true, bottomDot: true },
    { label: 'Mgmt', domain: 'Business & Mgmt', topHeight: 0, bottomHeight: 0, badge: '32%', badgeType: 'lime', topDot: false, bottomDot: false, hasDashedLine: true },
    { label: 'Design', domain: 'Design & Media', topHeight: 48, bottomHeight: 42, badge: '87%', badgeType: 'black', topDot: true, bottomDot: true },
    { label: 'Sci', domain: 'Natural Sciences', topHeight: 0, bottomHeight: 0, topDot: false, bottomDot: false, hasDashedLine: true },
    { label: 'Arts', domain: 'Humanities & Arts', topHeight: 38, bottomHeight: 34, topDot: true, bottomDot: true },
    { label: 'Arch', domain: 'Architecture & Built Env', topHeight: 32, bottomHeight: 28, topDot: true, bottomDot: true },
  ];

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
      <div className="flex-1 overflow-y-auto pr-1 pb-6 space-y-6 scrollbar-thin">
        {currentDestination === 'overview' ? (
        <>
          {/* Top 3 Metric Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* Card 1: Academic Eligibility (White) */}
            <div className="bg-white rounded-3xl p-6 border border-gray-200/60 shadow-xs flex flex-col justify-between min-h-[190px]">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-semibold text-[#111215]">
                  <div className="w-5 h-5 rounded-full border border-gray-200 flex items-center justify-center text-[10px]">
                    🎓
                  </div>
                  <span>Academic Eligibility</span>
                </div>
                <button
                  onClick={onEvaluateProfile}
                  className={`text-gray-400 hover:text-gray-600 cursor-pointer ${isEvaluating ? 'animate-spin' : ''}`}
                  title="Re-run Multi-Domain Evaluation"
                >
                  <RotateCw className="w-4 h-4" />
                </button>
              </div>

              <div className="my-4 flex items-baseline gap-2">
                <span className="text-4xl font-bold tracking-tight text-[#111215]">
                  {eligibleCount > 0 ? eligibleCount : (totalProgrammes > 0 ? Math.round(totalProgrammes * 0.7) : 12)}
                </span>
                <span className="text-xs text-gray-500 font-medium">/ {totalProgrammes} Programmes</span>
                <span className="ml-auto inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 text-[11px] font-semibold border border-emerald-200">
                  {totalProgrammes > 0 ? Math.round(((eligibleCount || 12) / totalProgrammes) * 100) : 71}% Verified
                </span>
              </div>

              {/* Segmented capsule progress bar */}
              <div className="flex items-center gap-1.5 pt-2">
                {[...Array(Math.min(10, Math.round(((eligibleCount || 12) / totalProgrammes) * 10)))].map((_, i) => (
                  <div key={`el-solid-${i}`} className="w-4 h-9 rounded-full bg-[#111215]" />
                ))}
                {[...Array(Math.max(0, 10 - Math.min(10, Math.round(((eligibleCount || 12) / totalProgrammes) * 10))))].map((_, i) => (
                  <div
                    key={`el-dash-${i}`}
                    className="w-4 h-9 rounded-full border border-dashed border-gray-300 bg-transparent"
                  />
                ))}
              </div>
            </div>

            {/* Card 2: Student-Programme Fit & Affordability (Lime #E8F84A) */}
            <div className="bg-[#E8F84A] rounded-3xl p-6 shadow-xs flex flex-col justify-between min-h-[190px] text-[#111215]">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-bold text-[#111215]">
                  <span className="text-sm">🎯</span>
                  <span>Admissions Fit & Budget</span>
                </div>
                <button
                  onClick={() => onNavigate('franchise')}
                  className="text-black/60 hover:text-black cursor-pointer"
                  title="View Franchise Auction Rankings"
                >
                  <MoreVertical className="w-4 h-4" />
                </button>
              </div>

              <div className="my-4 flex items-baseline gap-2">
                <span className="text-4xl font-bold tracking-tight text-[#111215]">{matchPercentage}%</span>
                <span className="text-xs text-black/60 font-semibold">/ 100% Target Fit</span>
                <span className="ml-auto inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-white/80 text-[#111215] text-[11px] font-bold shadow-2xs">
                  {eligibleCount}/{totalProgrammes} Optimal
                </span>
              </div>

              {/* Segmented capsule progress bar */}
              <div className="flex items-center gap-1.5 pt-2">
                {[...Array(Math.min(10, Math.max(1, Math.round((matchPercentage / 100) * 10))))].map((_, i) => (
                  <div key={`fit-solid-${i}`} className="w-4 h-9 rounded-full bg-[#111215]" />
                ))}
                {[...Array(Math.max(0, 10 - Math.min(10, Math.max(1, Math.round((matchPercentage / 100) * 10)))))].map((_, i) => (
                  <div
                    key={`fit-dash-${i}`}
                    className="w-4 h-9 rounded-full border border-dashed border-black/30 bg-transparent"
                  />
                ))}
              </div>
            </div>

            {/* Card 3: Multi-Agent Admissions Council (Deep Black) */}
            <div className="bg-[#111215] text-white rounded-3xl p-6 shadow-xs flex flex-col justify-between min-h-[190px] relative overflow-hidden">
              {/* Subtle avatar backdrop */}
              <div className="absolute right-0 top-0 bottom-0 w-1/2 flex items-center justify-end pointer-events-none opacity-90 pr-2">
                <div className="relative w-28 h-28 sm:w-32 sm:h-32 rounded-full overflow-hidden border-2 border-emerald-500/20 shadow-lg">
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

              <div className="relative z-10 max-w-[65%]">
                <h2 className="text-xl sm:text-2xl font-normal leading-snug tracking-tight">
                  Synthesize <span className="inline-block text-xs align-super">↗</span>
                  <br />
                  <span className="font-semibold">Council Consensus</span>
                  <br />
                  Across 6 Agents
                </h2>
              </div>

              <div className="relative z-10 pt-4">
                <button
                  onClick={() => onNavigate('referee')}
                  className="px-5 py-2.5 rounded-full bg-white text-[#111215] hover:bg-gray-100 text-xs font-bold shadow-xs flex items-center gap-1.5 transition-all hover:scale-105 cursor-pointer"
                >
                  <span>Explore Council</span>
                  <Play className="w-3 h-3 fill-current ml-0.5" />
                </button>
              </div>
            </div>
          </div>

          {/* Middle Section: Statistics Pill Bar Chart (Left) + Action Cards Stack (Right) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
            {/* Left: Discipline Fit Matrix Capsule Bar Chart (8 cols) */}
            <div className="lg:col-span-8 bg-white rounded-3xl p-6 border border-gray-200/60 shadow-xs flex flex-col justify-between">
              {/* Chart Header */}
              <div className="flex flex-wrap items-center justify-between gap-4 pb-6">
                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-2">
                    <div className="w-5 h-5 rounded-lg bg-gray-100 flex items-center justify-center text-xs text-gray-700">
                      📊
                    </div>
                    <h3 className="text-base font-bold text-[#111215]">Discipline Fit Matrix</h3>
                  </div>

                  {/* Legend */}
                  <div className="flex items-center gap-4 text-xs">
                    <div className="flex items-center gap-1.5 font-medium text-gray-700">
                      <span className="w-2.5 h-2.5 rounded-full bg-[#111215]" />
                      <span>Eligibility Benchmark</span>
                    </div>
                    <div className="flex items-center gap-1.5 font-medium text-gray-700">
                      <span className="w-2.5 h-2.5 rounded-full bg-[#E8F84A]" />
                      <span>Budget & Preference Fit</span>
                    </div>
                  </div>
                </div>

                {/* Filter Dropdown */}
                <div>
                  <select
                    value={selectedYear}
                    onChange={(e) => setSelectedYear(e.target.value)}
                    className="bg-white border border-gray-200 text-xs font-semibold text-gray-800 rounded-xl px-3 py-1.5 focus:outline-none cursor-pointer shadow-2xs"
                  >
                    <option value="2025">All Disciplines ⌄</option>
                    <option value="STEM">STEM Programmes ⌄</option>
                    <option value="LiberalArts">Liberal Arts & Law ⌄</option>
                  </select>
                </div>
              </div>

              {/* Dual-Tone Capsule Bar Chart Area */}
              <div className="relative pt-6 pb-2">
                {/* Horizontal Grid lines (1.0 to 0.1) */}
                <div className="absolute inset-0 flex flex-col justify-between pointer-events-none text-[10px] text-gray-300 font-mono">
                  {[1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1].map((val) => (
                    <div key={val} className="w-full border-b border-gray-100/80 flex items-center">
                      <span className="w-6 text-right pr-2 text-gray-400 select-none">{val.toFixed(1)}</span>
                    </div>
                  ))}
                </div>

                {/* Capsule Bars Container */}
                <div className="relative pl-8 pr-4 h-[260px] flex items-end justify-between gap-2 sm:gap-4 z-10">
                  {domainColumns.map((col) => {
                    const totalH = col.topHeight + col.bottomHeight;
                    return (
                      <div key={col.label} className="flex-1 flex flex-col items-center justify-end h-full group">
                        {/* Floating Badges */}
                        {col.badge && (
                          <div className="mb-2 flex flex-col items-center">
                            <span
                              className={`px-2 py-0.5 rounded-full text-[11px] font-bold shadow-2xs ${
                                col.badgeType === 'black'
                                  ? 'bg-[#111215] text-white'
                                  : 'bg-[#E8F84A] text-[#111215]'
                              }`}
                            >
                              {col.badge}
                            </span>
                          </div>
                        )}

                        {/* Capsule Column */}
                        {totalH > 0 ? (
                          <div
                            className="w-8 sm:w-10 rounded-full flex flex-col overflow-hidden shadow-2xs transition-transform group-hover:scale-[1.03]"
                            style={{ height: `${totalH * 2.2}px` }}
                          >
                            {/* Top Black Section */}
                            <div
                              className="bg-[#111215] flex items-center justify-center relative"
                              style={{ height: `${col.topHeight * 2.2}px` }}
                            >
                              {col.topDot && (
                                <span className="w-2.5 h-2.5 rounded-full bg-white absolute top-2" />
                              )}
                            </div>

                            {/* Bottom Lime Section */}
                            <div
                              className="bg-[#E8F84A] flex items-center justify-center relative"
                              style={{ height: `${col.bottomHeight * 2.2}px` }}
                            >
                              {col.bottomDot && (
                                <span className="w-2.5 h-2.5 rounded-full bg-[#111215] absolute bottom-2" />
                              )}
                            </div>
                          </div>
                        ) : (
                          /* Dashed line placeholder with dot */
                          <div className="w-8 sm:w-10 flex flex-col items-center justify-end h-36">
                            <span className="w-3 h-3 rounded-full bg-gray-400/80 mb-1" />
                            <div className="w-px h-28 border-r border-dashed border-gray-300" />
                          </div>
                        )}

                        {/* Bottom Label (Discipline Domain) */}
                        <span
                          className="mt-3 text-[11px] font-bold text-gray-700 whitespace-nowrap cursor-default hover:text-black transition-colors"
                          title={col.domain}
                        >
                          {col.label}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Quick Domain Metrics Banner underneath chart */}
              <div className="mt-4 pt-4 border-t border-gray-100 flex flex-wrap items-center justify-between text-xs text-gray-500">
                <div className="flex items-center gap-4">
                  <span><strong>17</strong> Multi-Domain Programmes</span>
                  <span>•</span>
                  <span><strong>8</strong> Broad Disciplines</span>
                  <span>•</span>
                  <span><strong>6</strong> Autonomous Agents</span>
                </div>
                <button
                  onClick={() => onNavigate('programmes')}
                  className="font-semibold text-[#111215] hover:underline flex items-center gap-1 cursor-pointer"
                >
                  <span>Explore Multi-Domain Catalogue</span>
                  <ArrowUpRight className="w-3 h-3" />
                </button>
              </div>
            </div>

            {/* Right: 2 Square Cards + Stack of List Cards (4 cols) */}
            <div className="lg:col-span-4 flex flex-col gap-4">
              {/* Top 2 Square Cards */}
              <div className="grid grid-cols-2 gap-4">
                {/* Square 1: Counsellor Network */}
                <div
                  onClick={() => onNavigate('sources')}
                  className="bg-white rounded-3xl p-5 border border-gray-200/60 shadow-xs flex flex-col justify-between cursor-pointer hover:shadow-sm hover:scale-[1.02] transition-all min-h-[120px]"
                >
                  <div className="w-8 h-8 rounded-full border border-gray-200 flex items-center justify-center text-gray-700">
                    <MessageSquare className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-[#111215]">Counsellor Network</h4>
                    <p className="text-[11px] text-gray-500 mt-0.5">4.8k Admissions Mentors</p>
                  </div>
                </div>

                {/* Square 2: Admissions Academy */}
                <div
                  onClick={() => onNavigate('help')}
                  className="bg-white rounded-3xl p-5 border border-gray-200/60 shadow-xs flex flex-col justify-between cursor-pointer hover:shadow-sm hover:scale-[1.02] transition-all min-h-[120px]"
                >
                  <div className="w-8 h-8 rounded-full border border-gray-200 flex items-center justify-center text-gray-700">
                    <GraduationCap className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-[#111215]">Admissions Academy</h4>
                    <p className="text-[11px] text-gray-500 mt-0.5">12 Policy Modules</p>
                  </div>
                </div>
              </div>

              {/* Stack of 4 List Cards with Diagonal Arrow ↗ */}
              <div className="space-y-3">
                {/* Item 1: Criteria & Rules Guide */}
                <div
                  onClick={() => onNavigate('help')}
                  className="bg-white rounded-2xl p-4 border border-gray-200/60 shadow-2xs hover:shadow-xs flex items-center justify-between cursor-pointer transition-all hover:translate-x-1"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-700 font-bold text-xs shrink-0">
                      ?
                    </div>
                    <div className="truncate">
                      <h5 className="text-xs font-bold text-[#111215]">Criteria & Rules Guide</h5>
                      <p className="text-[11px] text-gray-400 truncate">Explore deterministic prerequisites & scoring formulas...</p>
                    </div>
                  </div>
                  <ArrowUpRight className="w-4 h-4 text-gray-400 shrink-0 ml-2" />
                </div>

                {/* Item 2: Institution Directory */}
                <div
                  onClick={() => onNavigate('sources')}
                  className="bg-white rounded-2xl p-4 border border-gray-200/60 shadow-2xs hover:shadow-xs flex items-center justify-between cursor-pointer transition-all hover:translate-x-1"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-700 shrink-0">
                      <Users className="w-4 h-4" />
                    </div>
                    <div className="truncate">
                      <h5 className="text-xs font-bold text-[#111215]">Institution Directory</h5>
                      <p className="text-[11px] text-gray-400 truncate">Accredited universities across all 8 disciplines...</p>
                    </div>
                  </div>
                  <ArrowUpRight className="w-4 h-4 text-gray-400 shrink-0 ml-2" />
                </div>

                {/* Item 3: Admissions Insights & Cutoffs */}
                <div
                  onClick={() => onNavigate('oracle')}
                  className="bg-white rounded-2xl p-4 border border-gray-200/60 shadow-2xs hover:shadow-xs flex items-center justify-between cursor-pointer transition-all hover:translate-x-1"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-700 shrink-0">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div className="truncate">
                      <h5 className="text-xs font-bold text-[#111215]">Admissions Insights & Cutoffs</h5>
                      <p className="text-[11px] text-gray-400 truncate">Machine-learning closing rank predictions & trends...</p>
                    </div>
                  </div>
                  <ArrowUpRight className="w-4 h-4 text-gray-400 shrink-0 ml-2" />
                </div>

                {/* Item 4: Career Trajectories */}
                <div
                  onClick={() => onNavigate('careers')}
                  className="bg-white rounded-2xl p-4 border border-gray-200/60 shadow-2xs hover:shadow-xs flex items-center justify-between cursor-pointer transition-all hover:translate-x-1"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-700 shrink-0">
                      <TrendingUp className="w-4 h-4" />
                    </div>
                    <div className="truncate">
                      <h5 className="text-xs font-bold text-[#111215]">Degree Trajectories</h5>
                      <p className="text-[11px] text-gray-400 truncate">Graduate employment outcomes & salary benchmarks...</p>
                    </div>
                  </div>
                  <ArrowUpRight className="w-4 h-4 text-gray-400 shrink-0 ml-2" />
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
