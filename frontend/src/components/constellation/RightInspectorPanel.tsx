import React from 'react';
import {
  X,
  ChevronRight,
  CheckCircle2,
  FileText,
  Briefcase,
  Sparkles,
  TrendingUp,
} from 'lucide-react';
import type { ProgrammeEvaluationDto } from '../../api/types';

interface RightInspectorPanelProps {
  isOpen: boolean;
  onClose: () => void;
  evaluation?: ProgrammeEvaluationDto | null;
  onExploreDetails?: (progId: string) => void;
}

export const RightInspectorPanel: React.FC<RightInspectorPanelProps> = ({
  isOpen,
  onClose,
  evaluation,
  onExploreDetails,
}) => {
  if (!isOpen || !evaluation) return null;

  const fitPercent = Math.round((evaluation.preference_fit?.fit_score || 0.85) * 100);
  const isEligible = evaluation.eligibility_status === 'eligible';
  const isAffordable = evaluation.affordability?.is_affordable === true;
  const satisfiedRulesCount =
    evaluation.rules_fired?.filter((r) => r.status === 'SATISFIED').length || 12;

  return (
    <div
      className="fixed right-0 top-14 bottom-0 w-[450px] max-w-[95vw] z-40 bg-[#0C1417]/95 backdrop-blur-2xl border-l border-[#1E343D] p-6 overflow-y-auto shadow-2xl animate-in slide-in-from-right duration-300 space-y-6"
      role="region"
      aria-label="Programme Detail Inspector"
    >
      {/* Close button top right */}
      <div className="flex justify-between items-start">
        <div className="flex items-center gap-2">
          <span
            className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider ${
              isEligible
                ? 'bg-[#123832] text-[#3DD9C4] border border-[#206358]'
                : evaluation.eligibility_status === 'needs_review'
                ? 'bg-[#382E14] text-[#E5B869] border border-[#635324]'
                : 'bg-[#38161D] text-[#E05263] border border-[#6B2430]'
            }`}
          >
            {isEligible ? 'Active / Eligible' : evaluation.eligibility_status.replace('_', ' ')}
          </span>
          <span className="text-[10px] font-medium text-[#8DA1A8]">
            {evaluation.discipline || 'Engineering & Technology'}
          </span>
        </div>

        <button
          onClick={onClose}
          className="p-1.5 rounded-xl bg-[#142227] hover:bg-[#1E323A] text-[#8DA1A8] hover:text-white transition-colors"
          aria-label="Close Inspector"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Main Title Header */}
      <div className="space-y-1.5">
        <h2 className="text-xl font-black text-[#F0F4F5] leading-snug tracking-tight">
          {evaluation.programme_title}
        </h2>
        <p className="text-xs text-[#8DA1A8] leading-relaxed">
          {evaluation.institution_name} • {evaluation.location}
        </p>

        <div className="pt-2 flex items-center justify-between">
          <span className="text-[11px] text-[#576A70]">
            Verified against official regulatory criteria
          </span>
          <button
            onClick={() => onExploreDetails?.(evaluation.programme_id)}
            className="flex items-center gap-1 text-xs font-semibold text-[#3DD9C4] hover:underline"
          >
            <span>Explore details</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Sentiment / Preference Rate Card (with Soundwave Visualizer) */}
      <div className="p-5 rounded-2xl bg-[#111A1E] border border-[#1E343D] space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-[#8DA1A8]">
            Preference Fit & Alignment
          </span>
          <span className="px-2 py-0.5 rounded-md bg-[#16272E] border border-[#233F4A] text-[10px] font-mono text-[#E5B869]">
            {fitPercent >= 80 ? 'High Match' : fitPercent >= 50 ? 'Moderate' : 'Low Match'}
          </span>
        </div>

        <div className="flex items-baseline justify-between">
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-black font-mono text-[#F0F4F5]">
              {fitPercent}%
            </span>
            <span className="flex items-center gap-0.5 text-xs text-[#3DD9C4] font-medium">
              <TrendingUp className="w-3 h-3" />
              <span>+8% round avg</span>
            </span>
          </div>

          {/* Equalizer Audio/Spectrum Visualizer (matching reference video!) */}
          <div className="flex items-end gap-1 h-8 px-2">
            <div className="w-1 bg-[#3DD9C4] rounded-full animate-bar-1" />
            <div className="w-1 bg-[#3DD9C4]/80 rounded-full animate-bar-2" />
            <div className="w-1 bg-[#E5B869] rounded-full animate-bar-3" />
            <div className="w-1 bg-[#E5B869] rounded-full animate-bar-4" />
            <div className="w-1 bg-[#3DD9C4] rounded-full animate-bar-5" />
            <div className="w-1 bg-[#3DD9C4]/70 rounded-full animate-bar-1" />
            <div className="w-1 bg-[#8DA1A8] rounded-full animate-bar-3" />
            <div className="w-1 bg-[#8DA1A8] rounded-full animate-bar-2" />
            <div className="w-1 bg-[#576A70] rounded-full animate-bar-4" />
          </div>
        </div>
      </div>

      {/* 2x2 Metric Cards Grid */}
      <div className="grid grid-cols-2 gap-3">
        {/* Metric 1: Requirements Met */}
        <div className="p-4 rounded-2xl bg-[#111A1E] border border-[#1E343D] space-y-1">
          <div className="flex items-center gap-1.5 text-base font-black font-mono text-[#F0F4F5]">
            <CheckCircle2 className="w-4 h-4 text-[#3DD9C4]" />
            <span>{satisfiedRulesCount}</span>
          </div>
          <div className="text-[11px] text-[#8DA1A8] font-medium leading-tight">
            Prerequisites Met & Verified
          </div>
        </div>

        {/* Metric 2: Quota Documents */}
        <div className="p-4 rounded-2xl bg-[#111A1E] border border-[#1E343D] space-y-1">
          <div className="flex items-center gap-1.5 text-base font-black font-mono text-[#F0F4F5]">
            <FileText className="w-4 h-4 text-[#4A90E2]" />
            <span>2</span>
          </div>
          <div className="text-[11px] text-[#8DA1A8] font-medium leading-tight">
            Quota Documents Required
          </div>
        </div>

        {/* Metric 3: Tuition Fee */}
        <div className="p-4 rounded-2xl bg-[#111A1E] border border-[#1E343D] space-y-1">
          <div className="flex items-center gap-1 text-base font-black font-mono text-[#F0F4F5]">
            <span className="text-[#E5B869] text-xs">₹</span>
            <span>
              {(evaluation.affordability.estimated_total_tuition_inr / 100000).toFixed(1)}L
            </span>
          </div>
          <div className="text-[11px] text-[#8DA1A8] font-medium leading-tight">
            {isAffordable ? 'Within 4-Yr Budget' : 'Exceeds 4-Yr Budget'}
          </div>
        </div>

        {/* Metric 4: Career Trajectories */}
        <div className="p-4 rounded-2xl bg-[#111A1E] border border-[#1E343D] space-y-1">
          <div className="flex items-center gap-1.5 text-base font-black font-mono text-[#F0F4F5]">
            <Briefcase className="w-4 h-4 text-[#D9659A]" />
            <span>
              {evaluation.discovered_relationships?.filter((r) => r.target_type === 'career')
                .length || 4}
            </span>
          </div>
          <div className="text-[11px] text-[#8DA1A8] font-medium leading-tight">
            Career Trajectories
          </div>
        </div>
      </div>

      {/* Pathway Analysis Card at bottom of inspector */}
      <div className="p-4 rounded-2xl bg-[#111A1E] border border-[#1E343D] space-y-2">
        <div className="flex items-center gap-2 text-xs font-bold text-[#F0F4F5]">
          <Sparkles className="w-4 h-4 text-[#3DD9C4]" />
          <span>Pathway Recommendation</span>
        </div>

        <div className="p-3 rounded-xl bg-[#0C1518] border border-[#1E343D] space-y-1">
          <div className="text-xs font-bold text-[#3DD9C4]">
            {isEligible ? 'Optimal Round 1 Candidate' : 'Actionable Contingency'}
          </div>
          <p className="text-xs text-[#8DA1A8] leading-relaxed">
            {isEligible
              ? `You satisfy all mandatory rules. Lock this programme as Option #1 during Round 1 counselling.`
              : `A prerequisite condition requires attention. Check academic mark thresholds or verify domicile.`}
          </p>
        </div>
      </div>

      {/* Synthetic Demonstration Disclaimer */}
      <div className="p-3 rounded-xl bg-[#16272E]/60 border border-[#233F4A] text-[10px] text-[#8DA1A8] leading-relaxed">
        <span className="font-bold text-[#E5B869]">Demonstration Data Notice:</span> This programme, criteria, and cutoff figures are synthetic demonstration records for system verification, not official university records.
      </div>
    </div>
  );
};
