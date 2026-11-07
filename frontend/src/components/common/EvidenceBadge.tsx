import React from 'react';
import { Layers, Sparkles, Compass, AlertCircle } from 'lucide-react';

interface EvidenceBadgeProps {
  evidenceTier?: 'comprehensive' | 'partial' | 'exploratory' | 'unscored' | string;
  coverageRatio?: number;
  activeDimensionsCount?: number;
  isUnscored?: boolean;
}

export const EvidenceBadge: React.FC<EvidenceBadgeProps> = ({
  evidenceTier,
  coverageRatio,
  activeDimensionsCount = 0,
  isUnscored = false,
}) => {
  const tier = (evidenceTier || '').toLowerCase();

  if (isUnscored || tier === 'unscored' || activeDimensionsCount === 0) {
    return (
      <span
        className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-[#EDF4F1] text-[#52615E] border border-[#DCE5DF]"
        title="Zero active preference dimensions provided. This recommendation is unscored and provided for exploratory browsing only."
      >
        <AlertCircle className="w-3.5 h-3.5 text-[#52615E]" aria-hidden="true" />
        <span>Unscored (0/4 Dimensions)</span>
      </span>
    );
  }

  if (tier === 'exploratory' || activeDimensionsCount === 1) {
    return (
      <span
        className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-[#FEF7EC] text-[#8A5B16] border border-[#F6DCAD]"
        title="Sparse evidence: Only 1 preference dimension available. Treated as an exploratory signal, not a definitive match."
      >
        <Compass className="w-3.5 h-3.5 text-[#8A5B16]" aria-hidden="true" />
        <span>Exploratory Signal (1/4 Dimensions)</span>
      </span>
    );
  }

  if (tier === 'partial' || (activeDimensionsCount >= 2 && activeDimensionsCount < 4)) {
    const pct = coverageRatio ? Math.round(coverageRatio * 100) : activeDimensionsCount * 25;
    return (
      <span
        className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-[#E9F1F7] text-[#315C86] border border-[#BDD6EA]"
        title={`Partial evidence: ${activeDimensionsCount} of 4 preference dimensions provided (${pct}% coverage).`}
      >
        <Layers className="w-3.5 h-3.5 text-[#315C86]" aria-hidden="true" />
        <span>Partial Evidence ({activeDimensionsCount}/4 Dimensions)</span>
      </span>
    );
  }

  return (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-[#E1EEE8] text-[#176B63] border border-[#A3D1C0]"
      title="All 4 preference dimensions (Academic, Discipline, Career, Geographic) are actively provided."
    >
      <Sparkles className="w-3.5 h-3.5 text-[#176B63]" aria-hidden="true" />
      <span>Comprehensive Evidence (4/4 Dimensions)</span>
    </span>
  );
};

