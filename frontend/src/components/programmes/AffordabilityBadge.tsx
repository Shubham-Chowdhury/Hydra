import React from 'react';
import { AlertCircle, Check } from 'lucide-react';
import type { AffordabilityDto } from '../../api/types';

interface AffordabilityBadgeProps {
  affordability: AffordabilityDto;
}

export const AffordabilityBadge: React.FC<AffordabilityBadgeProps> = ({ affordability }) => {
  const formattedTuition = new Intl.NumberFormat('en-IN', {
    maximumFractionDigits: 0,
  }).format(affordability.estimated_total_tuition_inr);

  if (affordability.is_affordable) {
    return (
      <span
        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-cyan-950 text-cyan-300 border border-cyan-800"
        title={`Total Tuition: ₹${formattedTuition} (Tuition-only total)`}
        aria-label="Affordable within budget"
      >
        <Check className="w-3.5 h-3.5 text-cyan-400" aria-hidden="true" />
        <span>Affordable (₹{formattedTuition})</span>
      </span>
    );
  }

  return (
    <span
      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-orange-950/80 text-orange-300 border border-orange-800/80"
      title={`Total Tuition: ₹${formattedTuition} (Exceeds stated budget)`}
      aria-label="Unaffordable within budget"
    >
      <AlertCircle className="w-3.5 h-3.5 text-orange-400" aria-hidden="true" />
      <span>Budget Exceeded (₹{formattedTuition})</span>
    </span>
  );
};
