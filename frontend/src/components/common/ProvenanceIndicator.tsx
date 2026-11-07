import React from 'react';
import { ShieldCheck, User, LineChart, HelpCircle, FileText } from 'lucide-react';

export type SourceCategory =
  | 'verified'
  | 'user_provided'
  | 'estimated'
  | 'unavailable'
  | 'synthetic_demo'
  | string;

interface ProvenanceIndicatorProps {
  category: SourceCategory;
  sourceLabel?: string;
  isSynthetic?: boolean;
  className?: string;
}

export const ProvenanceIndicator: React.FC<ProvenanceIndicatorProps> = ({
  category,
  sourceLabel,
  isSynthetic = false,
  className = '',
}) => {
  const normalized = (category || '').toLowerCase().trim();

  let label = sourceLabel || 'Information Source';
  let badgeColor = 'bg-[#EDF4F1] text-[#52615E] border-[#DCE5DF]';
  let Icon = FileText;

  if (isSynthetic || normalized.includes('synthetic')) {
    label = sourceLabel || 'Demonstration Record';
    badgeColor = 'bg-[#FEF7EC] text-[#8A5B16] border-[#F6DCAD]';
    Icon = HelpCircle;
  } else if (normalized.includes('verified') || normalized.includes('official')) {
    label = sourceLabel || 'Officially Verified Source';
    badgeColor = 'bg-[#E6F4ED] text-[#2D6A4F] border-[#A8D5BC]';
    Icon = ShieldCheck;
  } else if (normalized.includes('user') || normalized.includes('student')) {
    label = sourceLabel || 'Student Provided Fact';
    badgeColor = 'bg-[#E9F1F7] text-[#315C86] border-[#BDD6EA]';
    Icon = User;
  } else if (normalized.includes('estimate') || normalized.includes('forecast') || normalized.includes('simulation')) {
    label = sourceLabel || 'Estimated / Hypothetical Model';
    badgeColor = 'bg-[#FEF7EC] text-[#8A5B16] border-[#F6DCAD]';
    Icon = LineChart;
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium border ${badgeColor} ${className}`}
      title={`Data Origin: ${label}`}
    >
      <Icon className="w-3 h-3 shrink-0" aria-hidden="true" />
      <span>{label}</span>
    </span>
  );
};

