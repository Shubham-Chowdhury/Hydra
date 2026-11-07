import React from 'react';
import {
  LayoutDashboard,
  UserCheck,
  GraduationCap,
  Scale,
  Route,
  Briefcase,
  ShieldCheck,
  HelpCircle,
  ChevronRight,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import type { StudentProfileRequest } from '../../api/types';

export type NavigationDestination =
  | 'overview'
  | 'referee'
  | 'twin'
  | 'franchise'
  | 'planner'
  | 'simulation'
  | 'oracle'
  | 'interests'
  | 'profile'
  | 'programmes'
  | 'compare'
  | 'plan'
  | 'careers'
  | 'sources'
  | 'help';

interface StudentSidebarProps {
  currentDestination: NavigationDestination;
  onNavigate: (destination: NavigationDestination) => void;
  profile?: StudentProfileRequest;
  comparedCount: number;
  evaluationsCount: number;
}

export const StudentSidebar: React.FC<StudentSidebarProps> = ({
  currentDestination,
  onNavigate,
  profile,
  comparedCount,
  evaluationsCount,
}) => {
  // Compute profile completeness score (0 to 100%)
  const computeCompleteness = (): { percent: number; missing: string[] } => {
    if (!profile) return { percent: 0, missing: ['Academic marks', 'Entrance exam', 'Financial budget', 'Location preference'] };

    const missing: string[] = [];
    let score = 0;

    // Academic scores (30%)
    if (profile.subject_scores && profile.subject_scores.length >= 3) {
      score += 30;
    } else {
      missing.push('Academic subject marks');
    }

    // Entrance exam (25%)
    if (profile.entrance_rank && profile.entrance_rank > 0) {
      score += 25;
    } else {
      missing.push('Entrance exam & rank');
    }

    // Financial budget (20%)
    if (profile.total_budget_inr && profile.total_budget_inr > 0) {
      score += 20;
    } else {
      missing.push('Annual or total budget');
    }

    // Location preferences (15%)
    if (profile.preferred_locations && profile.preferred_locations.length > 0) {
      score += 15;
    } else {
      missing.push('Preferred cities/states');
    }

    // Interests / goals (10%)
    if ((profile.career_goals && profile.career_goals.length > 0) || (profile.preferred_disciplines && profile.preferred_disciplines.length > 0)) {
      score += 10;
    } else {
      missing.push('Interests & career goals');
    }

    return { percent: score, missing };
  };

  const { percent: completenessPercent, missing: missingItems } = computeCompleteness();

  const navItems: Array<{
    id: NavigationDestination;
    label: string;
    description: string;
    icon: React.ComponentType<{ className?: string }>;
    badge?: string | number;
  }> = [
    {
      id: 'overview',
      label: 'Overview',
      description: 'Counselling hub & next steps',
      icon: LayoutDashboard,
    },
    {
      id: 'profile',
      label: 'My Profile',
      description: 'Academic & financial facts',
      icon: UserCheck,
      badge: profile ? `${completenessPercent}%` : 'Setup',
    },
    {
      id: 'programmes',
      label: 'Explore Programmes',
      description: 'Eligibility & preferences',
      icon: GraduationCap,
      badge: evaluationsCount > 0 ? evaluationsCount : undefined,
    },
    {
      id: 'compare',
      label: 'Compare Options',
      description: 'Side-by-side differences',
      icon: Scale,
      badge: comparedCount > 0 ? comparedCount : undefined,
    },
    {
      id: 'plan',
      label: 'My Action Plan',
      description: 'Milestones & scenario check',
      icon: Route,
    },
    {
      id: 'careers',
      label: 'Career Exploration',
      description: 'Interest decoder & skills',
      icon: Briefcase,
    },
    {
      id: 'sources',
      label: 'Sources & Evidence',
      description: 'Admissions knowledge base',
      icon: ShieldCheck,
    },
    {
      id: 'help',
      label: 'Help & Glossary',
      description: 'Admissions terminology & FAQs',
      icon: HelpCircle,
    },
  ];

  return (
    <aside className="w-64 bg-[#FFFFFF] border-r border-[#DCE5DF] flex flex-col justify-between shrink-0 min-h-[calc(100vh-4rem)]">
      {/* Navigation Links */}
      <div className="py-4 px-3 space-y-1">
        <div className="px-3 pb-2 text-[11px] font-bold uppercase tracking-wider text-[#64736F]">
          Guidance Navigation
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentDestination === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full text-left px-3 py-2.5 rounded-xl flex items-center justify-between text-sm transition-colors ${
                isActive
                  ? 'bg-[#E1EEE8] text-[#176B63] font-semibold border-l-4 border-[#176B63]'
                  : 'text-[#52615E] hover:bg-[#EDF4F1] hover:text-[#1C2B2A]'
              }`}
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <Icon
                  className={`w-4 h-4 shrink-0 ${
                    isActive ? 'text-[#176B63]' : 'text-[#64736F]'
                  }`}
                />
                <div className="min-w-0">
                  <div className="truncate leading-tight text-xs sm:text-sm">{item.label}</div>
                  <div className="text-[11px] text-[#64736F] truncate hidden lg:block">
                    {item.description}
                  </div>
                </div>
              </div>

              {item.badge !== undefined && (
                <span
                  className={`text-[11px] font-medium px-1.5 py-0.5 rounded-full shrink-0 ml-1 ${
                    isActive
                      ? 'bg-[#176B63] text-white'
                      : 'bg-[#EDF4F1] text-[#52615E] border border-[#DCE5DF]'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Profile Completeness Card at bottom of sidebar */}
      <div className="p-4 m-3 rounded-xl bg-[#F6F8F6] border border-[#DCE5DF]">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs font-semibold text-[#1C2B2A]">Profile Completeness</span>
          <span
            className={`text-xs font-bold ${
              completenessPercent === 100
                ? 'text-[#2D6A4F]'
                : completenessPercent >= 60
                ? 'text-[#176B63]'
                : 'text-[#8A5B16]'
            }`}
          >
            {completenessPercent}%
          </span>
        </div>
        <p className="text-[10px] text-[#64736F] leading-tight mb-2">
          Measures information provided. Does not imply admission readiness or eligibility.
        </p>

        {/* Progress Bar */}
        <div className="w-full h-2 rounded-full bg-[#DCE5DF] overflow-hidden mb-2">
          <div
            className={`h-full transition-all duration-500 rounded-full ${
              completenessPercent === 100
                ? 'bg-[#2D6A4F]'
                : completenessPercent >= 60
                ? 'bg-[#176B63]'
                : 'bg-[#8A5B16]'
            }`}
            style={{ width: `${completenessPercent}%` }}
          />
        </div>

        {completenessPercent === 100 ? (
          <div className="flex items-center gap-1.5 text-[11px] text-[#2D6A4F]">
            <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
            <span>Profile details complete for evaluation (not an admission guarantee)</span>
          </div>
        ) : (
          <div>
            <div className="flex items-center gap-1.5 text-[11px] text-[#8A5B16] mb-1">
              <AlertCircle className="w-3.5 h-3.5 shrink-0" />
              <span>{missingItems.length} optional detail{missingItems.length > 1 ? 's' : ''} unprovided (not failed requirements)</span>
            </div>
            <button
              onClick={() => onNavigate('profile')}
              className="text-[11px] text-[#176B63] hover:underline font-semibold flex items-center gap-1 mt-1"
            >
              <span>Add optional facts</span>
              <ChevronRight className="w-3 h-3" />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
};
