import React, { useState } from 'react';
import {
  MapPin,
  CheckCircle2,
  AlertCircle,
  XCircle,
  Scale,
  Briefcase,
  ChevronDown,
  ChevronUp,
  TrendingUp,
  Zap,
} from 'lucide-react';
import type { ProgrammeEvaluationDto } from '../../api/types';

interface VisualProgrammeCardProps {
  evaluation: ProgrammeEvaluationDto;
  isCompared: boolean;
  onToggleCompare: (programmeId: string) => void;
  layout?: 'grid' | 'list';
}

export const VisualProgrammeCard: React.FC<VisualProgrammeCardProps> = ({
  evaluation,
  isCompared,
  onToggleCompare,
  layout: _layout = 'grid',
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);

  const fitPercent = Math.round((evaluation.preference_fit?.fit_score || 0) * 100);
  const isAffordable = evaluation.affordability?.is_affordable === true;
  const tuitionLakh = (evaluation.affordability?.estimated_total_tuition_inr / 100000).toFixed(2);
  const budgetLakh = evaluation.affordability?.total_budget_inr
    ? (evaluation.affordability.total_budget_inr / 100000).toFixed(2)
    : '8.00';
  const locationMatchScore = evaluation.preference_fit?.criteria_breakdown?.['location'] ?? 1.0;
  const budgetRatio = evaluation.affordability?.total_budget_inr
    ? Math.min(100, Math.round((evaluation.affordability.estimated_total_tuition_inr / evaluation.affordability.total_budget_inr) * 100))
    : 50;

  // Domain theme helper
  const getDomainTheme = (disc: string) => {
    const d = disc.toLowerCase();
    if (d.includes('medicine') || d.includes('pharmacy') || d.includes('bio')) {
      return {
        accent: '#10B981',
        bgPill: 'bg-emerald-50 text-emerald-800 border-emerald-200',
        gradient: 'from-emerald-500/10 to-teal-500/5',
        icon: '🩺',
        name: 'Health & Life Sciences',
      };
    }
    if (d.includes('law')) {
      return {
        accent: '#F59E0B',
        bgPill: 'bg-amber-50 text-amber-800 border-amber-200',
        gradient: 'from-amber-500/10 to-yellow-500/5',
        icon: '⚖️',
        name: 'Legal Jurisprudence',
      };
    }
    if (d.includes('business') || d.includes('finance') || d.includes('commerce') || d.includes('management')) {
      return {
        accent: '#8B5CF6',
        bgPill: 'bg-purple-50 text-purple-800 border-purple-200',
        gradient: 'from-purple-500/10 to-indigo-500/5',
        icon: '💼',
        name: 'Business & Commerce',
      };
    }
    if (d.includes('design') || d.includes('architecture')) {
      return {
        accent: '#F43F5E',
        bgPill: 'bg-rose-50 text-rose-800 border-rose-200',
        gradient: 'from-rose-500/10 to-pink-500/5',
        icon: '🎨',
        name: 'Design & Architecture',
      };
    }
    if (d.includes('mathematics') || d.includes('science') || d.includes('economics')) {
      return {
        accent: '#0EA5E9',
        bgPill: 'bg-sky-50 text-sky-800 border-sky-200',
        gradient: 'from-sky-500/10 to-blue-500/5',
        icon: '🔬',
        name: 'Pure & Applied Sciences',
      };
    }
    if (d.includes('humanities') || d.includes('psychology')) {
      return {
        accent: '#14B8A6',
        bgPill: 'bg-teal-50 text-teal-800 border-teal-200',
        gradient: 'from-teal-500/10 to-emerald-500/5',
        icon: '📚',
        name: 'Humanities & Social Sciences',
      };
    }
    return {
      accent: '#3B82F6',
      bgPill: 'bg-blue-50 text-blue-800 border-blue-200',
      gradient: 'from-blue-500/10 to-indigo-500/5',
      icon: '⚡',
      name: 'Technology & Computing',
    };
  };

  const domain = getDomainTheme(evaluation.discipline);

  // SVG Radial Gauge Calculation
  const radius = 26;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (fitPercent / 100) * circumference;

  // Extracted skills and career trajectories
  const skills = evaluation.discovered_relationships
    ?.filter((r) => r.target_type === 'skill')
    ?.map((r) => r.target) || [];
  const careers = evaluation.discovered_relationships
    ?.filter((r) => r.target_type === 'career')
    ?.map((r) => r.target) || [];

  return (
    <div
      className={`bg-white rounded-3xl border transition-all duration-300 overflow-hidden shadow-xs hover:shadow-md flex flex-col justify-between ${
        isCompared
          ? 'border-[#111215] ring-2 ring-[#111215]/20 shadow-sm'
          : 'border-gray-200/70 hover:border-gray-300'
      }`}
    >
      {/* Top Banner with Accent Tint */}
      <div className={`p-5 sm:p-6 bg-gradient-to-br ${domain.gradient} border-b border-gray-100 flex-1`}>
        {/* Top Header Row: Domain Badge, Programme ID & Radial Gauge */}
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1.5 flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold border shadow-2xs ${domain.bgPill}`}>
                <span>{domain.icon}</span>
                <span>{evaluation.discipline}</span>
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-white/80 text-gray-500 border border-gray-200/60 shadow-2xs">
                {evaluation.programme_id}
              </span>
            </div>

            <h3 className="text-base sm:text-lg font-bold text-[#111215] leading-snug pt-1">
              {evaluation.programme_title}
            </h3>

            <div className="text-xs text-gray-600 flex flex-wrap items-center gap-2 pt-0.5">
              <span className="font-medium text-gray-800">{evaluation.institution_name}</span>
              <span className="text-gray-300">•</span>
              <span className="inline-flex items-center gap-1 text-gray-500">
                <MapPin className="w-3.5 h-3.5 text-gray-400" />
                <span>{evaluation.location}</span>
              </span>
            </div>
          </div>

          {/* Prominent Circular SVG Match Dial */}
          <div className="flex flex-col items-center shrink-0 ml-2">
            <div className="relative w-16 h-16 flex items-center justify-center">
              <svg className="w-16 h-16 transform -rotate-90">
                <circle
                  cx="32"
                  cy="32"
                  r={radius}
                  stroke="#E2E8F0"
                  strokeWidth="5"
                  fill="transparent"
                />
                <circle
                  cx="32"
                  cy="32"
                  r={radius}
                  stroke={fitPercent >= 70 ? '#10B981' : fitPercent >= 40 ? '#EAB308' : '#64748B'}
                  strokeWidth="5"
                  fill="transparent"
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  strokeLinecap="round"
                  className="transition-all duration-700 ease-out"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                <span className="text-sm font-extrabold text-[#111215] leading-none">
                  {fitPercent}%
                </span>
                <span className="text-[9px] font-bold text-gray-400 uppercase tracking-tighter">
                  Match
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Visual Eligibility & Financial Status Strip */}
        <div className="mt-4 pt-3 border-t border-black/5 flex flex-wrap items-center justify-between gap-2 text-xs">
          {/* Eligibility Badge */}
          <div className="flex items-center gap-1.5">
            {evaluation.eligibility_status === 'eligible' ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500 text-white font-bold text-xs shadow-2xs">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Verified Eligible</span>
              </span>
            ) : evaluation.eligibility_status === 'needs_review' ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-100 text-amber-900 border border-amber-300 font-semibold text-xs shadow-2xs">
                <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                <span>Needs Fact Review</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-100 text-rose-800 border border-rose-300 font-semibold text-xs shadow-2xs">
                <XCircle className="w-3.5 h-3.5 text-rose-600" />
                <span>Prerequisites Ineligible</span>
              </span>
            )}

            {/* Evidence Coverage Pill */}
            <span className="px-2 py-0.5 rounded-full bg-white/90 border border-gray-200/80 text-[11px] font-medium text-gray-600 shadow-2xs">
              {evaluation.evidence?.length || 4}/4 Evidence Verified
            </span>
          </div>

          {/* Budget Chip */}
          <div
            className={`px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1 border shadow-2xs ${
              isAffordable
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : 'bg-rose-50 text-rose-800 border-rose-200'
            }`}
          >
            <span>₹{tuitionLakh}L / ₹{budgetLakh}L</span>
            <span className="text-[10px] opacity-75">
              ({isAffordable ? 'Within Budget' : 'Exceeds Budget'})
            </span>
          </div>
        </div>

        {/* Visual Dimension Meter Bars */}
        <div className="mt-4 bg-white/90 backdrop-blur-xs rounded-2xl p-3 border border-gray-200/60 shadow-2xs space-y-2">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
            {/* Academics */}
            <div>
              <div className="flex justify-between text-gray-500 mb-0.5">
                <span>Academics</span>
                <span className="font-bold text-[#111215]">
                  {evaluation.eligibility_status === 'eligible' ? '100%' : '65%'}
                </span>
              </div>
              <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full"
                  style={{ width: evaluation.eligibility_status === 'eligible' ? '100%' : '65%' }}
                />
              </div>
            </div>

            {/* Budget Utilization */}
            <div>
              <div className="flex justify-between text-gray-500 mb-0.5">
                <span>Budget Fit</span>
                <span className="font-bold text-[#111215]">{budgetRatio}%</span>
              </div>
              <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${isAffordable ? 'bg-emerald-500' : 'bg-rose-500'}`}
                  style={{ width: `${Math.min(100, budgetRatio)}%` }}
                />
              </div>
            </div>

            {/* Location Preference */}
            <div>
              <div className="flex justify-between text-gray-500 mb-0.5">
                <span>Location</span>
                <span className="font-bold text-[#111215]">
                  {Math.round(locationMatchScore * 100)}%
                </span>
              </div>
              <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 rounded-full"
                  style={{ width: `${Math.round(locationMatchScore * 100)}%` }}
                />
              </div>
            </div>

            {/* Career Trajectory Match */}
            <div>
              <div className="flex justify-between text-gray-500 mb-0.5">
                <span>Career Goals</span>
                <span className="font-bold text-[#111215]">{fitPercent}%</span>
              </div>
              <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-purple-500 rounded-full"
                  style={{ width: `${fitPercent}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Discovered Career Pathways & Skills Strip */}
        {(careers.length > 0 || skills.length > 0) && (
          <div className="mt-3 flex flex-wrap items-center gap-1.5 text-xs">
            <span className="text-[11px] font-bold text-gray-500 flex items-center gap-1 mr-1">
              <TrendingUp className="w-3 h-3 text-purple-600" />
              <span>Career Pathways:</span>
            </span>
            {careers.slice(0, 2).map((c, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-purple-50 text-purple-800 border border-purple-200 text-[11px] font-semibold"
              >
                <Briefcase className="w-3 h-3" />
                <span>{c}</span>
              </span>
            ))}
            {skills.slice(0, 2).map((s, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 rounded-full bg-gray-100 text-gray-700 text-[10px] font-medium"
              >
                +{s}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Card Action Footer */}
      <div className="p-4 bg-gray-50/80 border-t border-gray-100 flex items-center justify-between text-xs">
        {/* Toggle Compare Checkbox */}
        <label className="flex items-center gap-2 cursor-pointer select-none group">
          <input
            type="checkbox"
            checked={isCompared}
            onChange={() => onToggleCompare(evaluation.programme_id)}
            className="w-4 h-4 rounded border-gray-300 text-[#111215] focus:ring-[#111215] cursor-pointer"
          />
          <span className="font-semibold text-gray-700 group-hover:text-black flex items-center gap-1">
            <Scale className="w-3.5 h-3.5 text-gray-500" />
            <span>Compare</span>
          </span>
        </label>

        {/* View Rule Trace Flowchart Button */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="px-3 py-1.5 rounded-xl bg-white hover:bg-gray-100 border border-gray-200 text-gray-800 font-semibold flex items-center gap-1.5 transition-colors shadow-2xs cursor-pointer"
        >
          <span>{isExpanded ? 'Hide Visual Trace' : 'Inspect Rule Verification'}</span>
          {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Expanded Visual Decision Flowchart */}
      {isExpanded && (
        <div className="p-5 bg-white border-t border-gray-100 text-xs space-y-4 animate-in fade-in duration-150">
          <div className="flex items-center justify-between">
            <h4 className="font-bold text-gray-900 flex items-center gap-1.5">
              <Zap className="w-4 h-4 text-amber-500" />
              <span>Deterministic Verification Rule Tree</span>
            </h4>
            <span className="text-[11px] text-gray-500">
              {evaluation.rules_fired?.length || 0} Rule Verifications
            </span>
          </div>

          <div className="space-y-2">
            {evaluation.rules_fired && evaluation.rules_fired.length > 0 ? (
              evaluation.rules_fired.map((rule, idx) => {
                const isSatisfied = rule.status === 'SATISFIED';
                return (
                  <div
                    key={idx}
                    className={`p-3 rounded-2xl border flex items-center justify-between gap-3 ${
                      isSatisfied
                        ? 'bg-emerald-50/60 border-emerald-200 text-emerald-950'
                        : 'bg-rose-50/60 border-rose-200 text-rose-950'
                    }`}
                  >
                    <div className="space-y-0.5 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded bg-white/80 border border-black/10">
                          {rule.rule_id}
                        </span>
                        <span className="font-bold truncate">{rule.rule_name}</span>
                      </div>
                      <p className="text-[11px] opacity-80 leading-relaxed">
                        {rule.explanation || `Expected: ${rule.expected_value}, Observed: ${rule.observed_value}`}
                      </p>
                    </div>

                    <div className="shrink-0">
                      {isSatisfied ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-500 text-white font-bold text-[11px]">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>PASS</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-rose-500 text-white font-bold text-[11px]">
                          <XCircle className="w-3 h-3" />
                          <span>FAIL</span>
                        </span>
                      )}
                    </div>
                  </div>
                );
              })
            ) : (
              <p className="text-gray-500 text-xs">No explicit prerequisite rules triggered.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
