import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';

interface EligibilityBadgeProps {
  status: 'eligible' | 'ineligible' | 'needs_review' | string;
}

export const EligibilityBadge: React.FC<EligibilityBadgeProps> = ({ status }) => {
  switch (status) {
    case 'eligible':
      return (
        <span
          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-300 border border-emerald-800 shadow-sm shadow-emerald-900/30"
          aria-label="Eligibility Status: Eligible"
        >
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" aria-hidden="true" />
          Eligible
        </span>
      );
    case 'ineligible':
      return (
        <span
          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-950 text-rose-300 border border-rose-800 shadow-sm shadow-rose-900/30"
          aria-label="Eligibility Status: Ineligible"
        >
          <XCircle className="w-3.5 h-3.5 text-rose-400" aria-hidden="true" />
          Ineligible
        </span>
      );
    case 'needs_review':
    default:
      return (
        <span
          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-950 text-amber-300 border border-amber-800 shadow-sm shadow-amber-900/30"
          aria-label="Eligibility Status: Needs Review"
        >
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" aria-hidden="true" />
          Needs Review
        </span>
      );
  }
};

