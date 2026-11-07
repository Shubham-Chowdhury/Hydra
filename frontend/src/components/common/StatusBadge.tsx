import React from 'react';
import { CheckCircle2, HelpCircle, XCircle, Info } from 'lucide-react';

export type AcademicStatus =
  | 'eligible'
  | 'ineligible'
  | 'needs_review'
  | 'unconditional_candidate'
  | 'conditional_candidate'
  | 'no_bid'
  | string;

interface StatusBadgeProps {
  status: AcademicStatus;
  size?: 'sm' | 'md';
  customLabel?: string;
  showIcon?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'md',
  customLabel,
  showIcon = true,
}) => {
  const normalized = (status || '').toLowerCase().trim();

  let text = customLabel || status;
  let bgClass = 'bg-[#EDF4F1] text-[#52615E] border-[#DCE5DF]';
  let IconComponent = Info;

  if (normalized === 'eligible' || normalized === 'unconditional_candidate') {
    text = customLabel || (normalized === 'eligible' ? 'Meets Requirements' : 'Unconditional Candidate');
    bgClass = 'bg-[#E6F4ED] text-[#2D6A4F] border-[#A8D5BC]';
    IconComponent = CheckCircle2;
  } else if (normalized === 'needs_review' || normalized === 'conditional_candidate') {
    text = customLabel || (normalized === 'needs_review' ? 'Needs More Information' : 'Conditional (Pending Review)');
    bgClass = 'bg-[#FEF7EC] text-[#8A5B16] border-[#F6DCAD]';
    IconComponent = HelpCircle;
  } else if (normalized === 'ineligible' || normalized === 'no_bid') {
    text = customLabel || (normalized === 'ineligible' ? 'Requirement Not Met' : 'Ineligible (No Bid)');
    bgClass = 'bg-[#FDE8E8] text-[#A33434] border-[#F8B4B4]';
    IconComponent = XCircle;
  }

  const sizeClasses =
    size === 'sm'
      ? 'text-xs px-2.5 py-0.5 gap-1.5 font-medium'
      : 'text-xs px-3 py-1 gap-2 font-semibold';

  return (
    <span
      className={`inline-flex items-center rounded-full border ${bgClass} ${sizeClasses} transition-colors`}
      role="status"
    >
      {showIcon && <IconComponent className={size === 'sm' ? 'w-3.5 h-3.5 shrink-0' : 'w-4 h-4 shrink-0'} aria-hidden="true" />}
      <span>{text}</span>
    </span>
  );
};

