import React from 'react';
import {
  X,
  ExternalLink,
  ChevronUp,
} from 'lucide-react';

interface FloatingAnalysisCardProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectProgramme?: (progId: string) => void;
}

export const FloatingAnalysisCard: React.FC<FloatingAnalysisCardProps> = ({
  isOpen,
  onClose,
  onSelectProgramme,
}) => {
  if (!isOpen) return null;

  return (
    <div
      className="absolute bottom-36 left-1/2 -translate-x-1/2 w-[720px] max-w-[95vw] z-50 animate-in fade-in slide-in-from-bottom-4 duration-300"
      role="dialog"
      aria-labelledby="pathway-analysis-title"
    >
      <div className="bg-[#0C1417]/95 backdrop-blur-2xl border border-[#1E343D] rounded-3xl p-5 shadow-2xl space-y-3.5">
        {/* Header */}
        <div className="flex items-center justify-between pb-1">
          <div className="flex items-center gap-2">
            <span
              id="pathway-analysis-title"
              className="text-xs font-black tracking-widest text-[#F0F4F5] uppercase"
            >
              PATHWAY ANALYSIS
            </span>
            <span className="px-2 py-0.5 rounded-full bg-[#1A2616] text-[#E5B869] text-[10px] font-mono border border-[#E5B869]/30">
              SYNTHETIC DEMO
            </span>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-[#16272E] border border-[#233F4A] text-[11px] font-mono text-[#8DA1A8]">
              <ChevronUp className="w-3 h-3 text-[#3DD9C4]" />
              <span>+3 Alerts</span>
            </div>
            <button
              onClick={onClose}
              className="w-6 h-6 rounded-full bg-[#16272E] hover:bg-[#203640] text-[#8DA1A8] hover:text-white flex items-center justify-center transition-colors"
              aria-label="Close Analysis"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Card 1: Critical Concerns / Prerequisites (Red / Crimson glow) */}
        <div
          onClick={() => onSelectProgramme?.('PROG_001')}
          className="group relative p-4 rounded-2xl bg-[#111A1E]/80 hover:bg-[#152329] border border-[#23353D] hover:border-[#E05263]/50 transition-all cursor-pointer overflow-hidden"
        >
          {/* Subtle top crimson glow bar */}
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-[#E05263]/60 to-transparent" />

          <div className="flex items-start justify-between gap-4 mb-1.5">
            <div className="flex items-center gap-2">
              <span className="text-[#E05263] font-bold text-sm">[</span>
              <span className="text-xs font-bold text-[#F0F4F5] group-hover:text-[#E05263] transition-colors">
                Critical Prerequisite Constraint
              </span>
              <span className="text-[#E05263] font-bold text-sm">]</span>
            </div>

            <div className="flex items-center gap-1 text-[11px] font-mono text-[#8DA1A8] group-hover:text-[#F0F4F5]">
              <span>JEE Main Cutoff Rank ≤ 35,000</span>
              <ExternalLink className="w-3 h-3 text-[#8DA1A8] group-hover:text-[#3DD9C4]" />
            </div>
          </div>

          <p className="text-xs text-[#8DA1A8] leading-relaxed pl-3">
            Applicants with competitive ranks above 35,000 face immediate exclusion during round 1 seat allocation. Verified 10+2 Mathematics mark of 80% is mandatory.
          </p>
        </div>

        {/* Card 2: Propose De-regulation / Optimal Pathway (Cyan glow) */}
        <div
          onClick={() => onSelectProgramme?.('PROG_001')}
          className="group relative p-4 rounded-2xl bg-[#111A1E]/80 hover:bg-[#152329] border border-[#23353D] hover:border-[#3DD9C4]/50 transition-all cursor-pointer overflow-hidden"
        >
          {/* Subtle top cyan glow bar */}
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-[#3DD9C4]/60 to-transparent" />

          <div className="flex items-start justify-between gap-4 mb-1.5">
            <div className="flex items-center gap-2">
              <span className="text-[#3DD9C4] font-bold text-sm">[</span>
              <span className="text-xs font-bold text-[#F0F4F5] group-hover:text-[#3DD9C4] transition-colors">
                Recommended Verified Pathway
              </span>
              <span className="text-[#3DD9C4] font-bold text-sm">]</span>
            </div>

            <div className="flex items-center gap-1 text-[11px] font-mono text-[#8DA1A8] group-hover:text-[#F0F4F5]">
              <span>B.Tech in Computer Science & AI</span>
              <ExternalLink className="w-3 h-3 text-[#8DA1A8] group-hover:text-[#3DD9C4]" />
            </div>
          </div>

          <p className="text-xs text-[#8DA1A8] leading-relaxed pl-3">
            All 4 evidence dimensions are satisfied: Academic Eligibility, Entrance Rank Cutoff (#18,500), Tuition Affordability (₹7.2L), and Preference Alignment (85%).
          </p>
        </div>
      </div>
    </div>
  );
};
