import React, { useState } from 'react';
import {
  Search,
  SlidersHorizontal,
  LayoutGrid,
  List,
  CheckCircle2,
  AlertCircle,
  XCircle,
  Scale,
} from 'lucide-react';
import type {
  ProgrammeEvaluationDto,
  ProgrammeResponse,
} from '../../api/types';
import { VisualProgrammeCard } from './VisualProgrammeCard';

interface ProgrammeDiscoveryViewProps {
  evaluations: ProgrammeEvaluationDto[];
  catalogProgrammes: ProgrammeResponse[];
  comparedProgrammeIds: string[];
  onToggleCompare: (programmeId: string) => void;
  onNavigateToCompare: () => void;
  onEvaluate?: () => void;
  isEvaluating?: boolean;
}

export const ProgrammeDiscoveryView: React.FC<ProgrammeDiscoveryViewProps> = ({
  evaluations,
  comparedProgrammeIds,
  onToggleCompare,
  onNavigateToCompare,
}) => {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'eligible' | 'needs_review' | 'ineligible'>('all');
  const [affordabilityFilter, setAffordabilityFilter] = useState<'all' | 'affordable' | 'unaffordable'>('all');
  const [selectedDomain, setSelectedDomain] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  const domainPills = [
    { id: 'all', label: 'All Disciplines', icon: '🌐' },
    { id: 'Engineering', label: 'Engineering & Tech', icon: '⚡' },
    { id: 'Medicine', label: 'Medicine & Health', icon: '🩺' },
    { id: 'Law', label: 'Law & Governance', icon: '⚖️' },
    { id: 'Business', label: 'Business & FinTech', icon: '💼' },
    { id: 'Design', label: 'Design & Architecture', icon: '🎨' },
    { id: 'Sciences', label: 'Mathematics & Science', icon: '🔬' },
    { id: 'Humanities', label: 'Humanities & Psychology', icon: '📚' },
  ];

  // Filter evaluations
  const filteredEvaluations = evaluations.filter((ev) => {
    // Search filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchName = ev.programme_title.toLowerCase().includes(q);
      const matchInst = ev.institution_name.toLowerCase().includes(q);
      const matchDisc = ev.discipline.toLowerCase().includes(q);
      const matchLoc = ev.location.toLowerCase().includes(q);
      if (!matchName && !matchInst && !matchDisc && !matchLoc) return false;
    }

    // Status filter
    if (statusFilter !== 'all' && ev.eligibility_status !== statusFilter) {
      return false;
    }

    // Affordability filter
    if (affordabilityFilter !== 'all') {
      const isAffordable = ev.affordability?.is_affordable === true;
      if (affordabilityFilter === 'affordable' && !isAffordable) return false;
      if (affordabilityFilter === 'unaffordable' && isAffordable) return false;
    }

    // Domain filter
    if (selectedDomain !== 'all') {
      const d = ev.discipline.toLowerCase();
      if (selectedDomain === 'Engineering' && !d.includes('computer') && !d.includes('data') && !d.includes('robotics') && !d.includes('engineering') && !d.includes('electronics')) return false;
      if (selectedDomain === 'Medicine' && !d.includes('medicine') && !d.includes('pharmacy') && !d.includes('bio')) return false;
      if (selectedDomain === 'Law' && !d.includes('law')) return false;
      if (selectedDomain === 'Business' && !d.includes('business') && !d.includes('finance') && !d.includes('commerce') && !d.includes('management')) return false;
      if (selectedDomain === 'Design' && !d.includes('design') && !d.includes('architecture')) return false;
      if (selectedDomain === 'Sciences' && !d.includes('math') && !d.includes('science') && !d.includes('economics')) return false;
      if (selectedDomain === 'Humanities' && !d.includes('humanities') && !d.includes('psychology')) return false;
    }

    return true;
  });

  const eligibleCount = evaluations.filter((e) => e.eligibility_status === 'eligible').length;
  const reviewCount = evaluations.filter((e) => e.eligibility_status === 'needs_review').length;
  const ineligibleCount = evaluations.filter((e) => e.eligibility_status === 'ineligible').length;
  const affordableCount = evaluations.filter((e) => e.affordability?.is_affordable === true).length;

  return (
    <div className="space-y-6">
      {/* Top Header & Visual Statistics Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold text-[#111215] tracking-tight">
              Academic Discovery & Pathway Recommendations
            </h2>
            <span className="px-2.5 py-0.5 rounded-full bg-[#E8F84A] text-[#111215] font-bold text-xs shadow-2xs">
              {evaluations.length} Active Programmes
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Visual multi-domain catalogue evaluated deterministically across verified facts, eligibility rules, and budget limits.
          </p>
        </div>

        {/* View Mode Toggle (Grid / Stream) */}
        <div className="flex items-center gap-2 bg-gray-100 p-1 rounded-2xl border border-gray-200/80 shrink-0">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-2 rounded-xl transition-all cursor-pointer ${
              viewMode === 'grid'
                ? 'bg-white text-[#111215] shadow-2xs font-semibold'
                : 'text-gray-500 hover:text-black'
            }`}
            title="Visual Grid View"
          >
            <LayoutGrid className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-2 rounded-xl transition-all cursor-pointer ${
              viewMode === 'list'
                ? 'bg-white text-[#111215] shadow-2xs font-semibold'
                : 'text-gray-500 hover:text-black'
            }`}
            title="Visual List View"
          >
            <List className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Filter and Visual Search Controls Card */}
      <div className="bg-white rounded-3xl p-5 border border-gray-200/70 shadow-xs space-y-4">
        {/* Search Row */}
        <div className="relative">
          <Search className="w-4 h-4 text-gray-400 absolute left-4 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by programme name, university, discipline, or campus city..."
            className="w-full pl-11 pr-4 py-3 rounded-2xl border border-gray-200 bg-gray-50/60 text-xs text-[#111215] focus:bg-white focus:outline-none focus:border-[#111215] transition-all shadow-2xs"
          />
        </div>

        {/* Domain Filter Pills Row */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none text-xs">
          {domainPills.map((d) => (
            <button
              key={d.id}
              onClick={() => setSelectedDomain(d.id)}
              className={`px-3.5 py-1.5 rounded-full whitespace-nowrap transition-all font-semibold flex items-center gap-1.5 cursor-pointer ${
                selectedDomain === d.id
                  ? 'bg-[#111215] text-white shadow-xs'
                  : 'bg-gray-100/80 hover:bg-gray-200/70 text-gray-700'
              }`}
            >
              <span>{d.icon}</span>
              <span>{d.label}</span>
            </button>
          ))}
        </div>

        {/* Quick Toggles: Status & Budget */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-gray-100 text-xs">
          {/* Eligibility Filter Pills */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="font-bold text-gray-500 mr-1 flex items-center gap-1">
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <span>Status:</span>
            </span>
            <button
              onClick={() => setStatusFilter('all')}
              className={`px-3 py-1 rounded-full font-semibold transition-all cursor-pointer ${
                statusFilter === 'all'
                  ? 'bg-[#111215] text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              All ({evaluations.length})
            </button>
            <button
              onClick={() => setStatusFilter('eligible')}
              className={`px-3 py-1 rounded-full font-semibold transition-all flex items-center gap-1 cursor-pointer ${
                statusFilter === 'eligible'
                  ? 'bg-emerald-600 text-white'
                  : 'bg-emerald-50 text-emerald-800 hover:bg-emerald-100'
              }`}
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Eligible ({eligibleCount})</span>
            </button>
            <button
              onClick={() => setStatusFilter('needs_review')}
              className={`px-3 py-1 rounded-full font-semibold transition-all flex items-center gap-1 cursor-pointer ${
                statusFilter === 'needs_review'
                  ? 'bg-amber-600 text-white'
                  : 'bg-amber-50 text-amber-800 hover:bg-amber-100'
              }`}
            >
              <AlertCircle className="w-3.5 h-3.5" />
              <span>Review ({reviewCount})</span>
            </button>
            <button
              onClick={() => setStatusFilter('ineligible')}
              className={`px-3 py-1 rounded-full font-semibold transition-all flex items-center gap-1 cursor-pointer ${
                statusFilter === 'ineligible'
                  ? 'bg-rose-600 text-white'
                  : 'bg-rose-50 text-rose-800 hover:bg-rose-100'
              }`}
            >
              <XCircle className="w-3.5 h-3.5" />
              <span>Ineligible ({ineligibleCount})</span>
            </button>
          </div>

          {/* Budget Filter */}
          <div className="flex items-center gap-1.5">
            <span className="font-bold text-gray-500 mr-1">Budget:</span>
            <button
              onClick={() => setAffordabilityFilter('all')}
              className={`px-2.5 py-1 rounded-full font-semibold cursor-pointer ${
                affordabilityFilter === 'all'
                  ? 'bg-[#111215] text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setAffordabilityFilter('affordable')}
              className={`px-2.5 py-1 rounded-full font-semibold cursor-pointer ${
                affordabilityFilter === 'affordable'
                  ? 'bg-emerald-600 text-white'
                  : 'bg-emerald-50 text-emerald-800 hover:bg-emerald-100'
              }`}
            >
              Within Budget ({affordableCount})
            </button>
            <button
              onClick={() => setAffordabilityFilter('unaffordable')}
              className={`px-2.5 py-1 rounded-full font-semibold cursor-pointer ${
                affordabilityFilter === 'unaffordable'
                  ? 'bg-rose-600 text-white'
                  : 'bg-rose-50 text-rose-800 hover:bg-rose-100'
              }`}
            >
              Exceeds Budget ({evaluations.length - affordableCount})
            </button>
          </div>
        </div>
      </div>

      {/* Floating Comparison Action Bar if 2+ selected */}
      {comparedProgrammeIds.length > 0 && (
        <div className="p-4 bg-[#111215] text-white rounded-3xl flex items-center justify-between shadow-lg text-xs animate-in fade-in duration-200">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center">
              <Scale className="w-4 h-4 text-[#E8F84A]" />
            </div>
            <div>
              <span className="font-bold block">
                {comparedProgrammeIds.length} Programme{comparedProgrammeIds.length > 1 ? 's' : ''} Selected
              </span>
              <span className="text-[11px] text-gray-300">
                Ready for side-by-side multi-dimensional comparison.
              </span>
            </div>
          </div>
          <button
            onClick={onNavigateToCompare}
            className="px-5 py-2.5 rounded-full bg-[#E8F84A] hover:bg-[#d8e838] text-[#111215] font-bold text-xs shadow-sm transition-all hover:scale-105 cursor-pointer"
          >
            Open Comparison Matrix ▷
          </button>
        </div>
      )}

      {/* Visual Programme Results Container */}
      {filteredEvaluations.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 text-center space-y-3 border border-gray-200/60 shadow-xs">
          <div className="w-12 h-12 rounded-full bg-gray-100 mx-auto flex items-center justify-center text-xl">
            🔍
          </div>
          <h4 className="text-base font-bold text-gray-900">
            No programmes match your current filter selections.
          </h4>
          <p className="text-xs text-gray-500 max-w-sm mx-auto">
            Try resetting your search query, or selecting 'All' in status or discipline filters.
          </p>
          <button
            onClick={() => {
              setSearchQuery('');
              setStatusFilter('all');
              setAffordabilityFilter('all');
              setSelectedDomain('all');
            }}
            className="mt-2 px-4 py-2 rounded-full bg-[#111215] text-white text-xs font-semibold hover:bg-black cursor-pointer"
          >
            Reset All Filters
          </button>
        </div>
      ) : (
        <div
          className={
            viewMode === 'grid'
              ? 'grid grid-cols-1 xl:grid-cols-2 gap-5'
              : 'space-y-4'
          }
        >
          {filteredEvaluations.map((ev) => (
            <VisualProgrammeCard
              key={ev.programme_id}
              evaluation={ev}
              isCompared={comparedProgrammeIds.includes(ev.programme_id)}
              onToggleCompare={onToggleCompare}
              layout={viewMode}
            />
          ))}
        </div>
      )}
    </div>
  );
};
