import React from 'react';
import {
  Compass,
  CheckCircle2,
  HelpCircle,
  XCircle,
  ArrowRight,
  GraduationCap,
  Scale,
  Route,
  Briefcase,
  ShieldCheck,
  UserCheck,
  Sparkles,
} from 'lucide-react';
import type {
  ProgrammeEvaluationDto,
  StudentProfileRequest,
} from '../../api/types';
import type { NavigationDestination } from '../layout/StudentSidebar';
import { PageHeader } from '../common/PageHeader';
import { StatusBadge } from '../common/StatusBadge';
import { EvidenceBadge } from '../common/EvidenceBadge';

interface OverviewDashboardViewProps {
  profile?: StudentProfileRequest;
  evaluations: ProgrammeEvaluationDto[];
  onNavigate: (destination: NavigationDestination) => void;
  onEvaluate: () => void;
  isEvaluating: boolean;
}

export const OverviewDashboardView: React.FC<OverviewDashboardViewProps> = ({
  profile,
  evaluations,
  onNavigate,
  onEvaluate,
  isEvaluating,
}) => {
  const eligibleCount = evaluations.filter((e) => e.eligibility_status === 'eligible').length;
  const needsReviewCount = evaluations.filter((e) => e.eligibility_status === 'needs_review').length;
  const ineligibleCount = evaluations.filter((e) => e.eligibility_status === 'ineligible').length;

  const hasEvaluated = evaluations.length > 0;
  const hasProfile = !!profile;

  // Derive next action
  const getNextStep = () => {
    if (!hasProfile) {
      return {
        title: 'Complete Your Academic Profile',
        description:
          'Provide your 10+2 subject marks, entrance exam details, and annual tuition budget so Hydra can evaluate deterministic admission rules.',
        actionLabel: 'Complete Profile Now',
        destination: 'profile' as NavigationDestination,
      };
    }
    if (!hasEvaluated) {
      return {
        title: 'Evaluate Programme Eligibility',
        description:
          'Your profile facts are ready. Run our deterministic rule engine to verify mandatory criteria and budget fit with zero hallucinations.',
        actionLabel: 'Evaluate Programmes',
        isTrigger: true,
      };
    }
    if (eligibleCount > 0) {
      return {
        title: 'Explore Eligible Programmes & Build Action Plan',
        description: `You satisfy all mandatory criteria for ${eligibleCount} programme${
          eligibleCount > 1 ? 's' : ''
        }. Review your match details and examine next milestones.`,
        actionLabel: 'View Eligible Programmes',
        destination: 'programmes' as NavigationDestination,
      };
    }
    return {
      title: 'Review Missing Prerequisites & What-If Scenarios',
      description:
        'Some programmes require additional facts or higher scores. Explore our planning simulator to see what score adjustments unlock admission.',
      actionLabel: 'Open Action Planner',
      destination: 'plan' as NavigationDestination,
    };
  };

  const nextStep = getNextStep();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Student Admissions Hub"
        description="A calm, evidence-first platform for evaluating university prerequisites, tuition affordability, and career paths."
        badge={
          <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-[#E1EEE8] text-[#176B63] border border-[#A3D1C0]">
            Deterministic Decision Support
          </span>
        }
      />

      {/* Hero Welcome & Next Step Card */}
      <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-6 shadow-xs relative overflow-hidden">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#E1EEE8] text-[#176B63] text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5 text-[#176B63]" />
              <span>Next Recommended Action</span>
            </div>
            <h2 className="text-xl font-bold text-[#1C2B2A]">{nextStep.title}</h2>
            <p className="text-sm text-[#52615E] leading-relaxed">
              {nextStep.description}
            </p>
          </div>

          <div className="shrink-0 w-full md:w-auto">
            {'isTrigger' in nextStep ? (
              <button
                onClick={onEvaluate}
                disabled={isEvaluating}
                className="w-full md:w-auto px-5 py-3 rounded-xl bg-[#176B63] hover:bg-[#155E57] text-white font-semibold text-sm shadow-xs flex items-center justify-center gap-2 transition-all disabled:opacity-50"
              >
                <Compass className={`w-4 h-4 ${isEvaluating ? 'animate-spin' : ''}`} />
                <span>{isEvaluating ? 'Evaluating Rules...' : nextStep.actionLabel}</span>
              </button>
            ) : (
              <button
                onClick={() => onNavigate(nextStep.destination)}
                className="w-full md:w-auto px-5 py-3 rounded-xl bg-[#176B63] hover:bg-[#155E57] text-white font-semibold text-sm shadow-xs flex items-center justify-center gap-2 transition-all"
              >
                <span>{nextStep.actionLabel}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Facts Snapshot Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Profile Card */}
        <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-xl p-4">
          <div className="flex items-center justify-between text-[#64736F] text-xs font-medium mb-1">
            <span>Student Profile</span>
            <UserCheck className="w-4 h-4 text-[#176B63]" />
          </div>
          <div className="text-base font-bold text-[#1C2B2A] truncate">
            {profile?.student_id || 'STU_MASTER_REF'}
          </div>
          <p className="text-xs text-[#52615E] mt-1">
            {profile?.subject_scores?.[0]?.board || 'CBSE (All India)'}
          </p>
        </div>

        {/* Exam Score Card */}
        <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-xl p-4">
          <div className="flex items-center justify-between text-[#64736F] text-xs font-medium mb-1">
            <span>Entrance Exam</span>
            <GraduationCap className="w-4 h-4 text-[#176B63]" />
          </div>
          <div className="text-base font-bold text-[#1C2B2A]">
            {profile?.entrance_rank ? (
              <span>Rank #{profile.entrance_rank.toLocaleString()}</span>
            ) : (
              <span className="text-[#64736F] font-normal">Not provided</span>
            )}
          </div>
          <p className="text-xs text-[#52615E] mt-1">
            {profile?.entrance_exam_name || 'JEE Main 2025'}
          </p>
        </div>

        {/* Budget Card */}
        <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-xl p-4">
          <div className="flex items-center justify-between text-[#64736F] text-xs font-medium mb-1">
            <span>Tuition Budget (4-Yr)</span>
            <ShieldCheck className="w-4 h-4 text-[#176B63]" />
          </div>
          <div className="text-base font-bold text-[#1C2B2A]">
            {profile?.total_budget_inr ? (
              `₹${(profile.total_budget_inr / 100000).toFixed(1)} Lakh`
            ) : (
              '₹12.0 Lakh'
            )}
          </div>
          <p className="text-xs text-[#52615E] mt-1">Tuition only basis (INR)</p>
        </div>

        {/* Target Discipline */}
        <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-xl p-4">
          <div className="flex items-center justify-between text-[#64736F] text-xs font-medium mb-1">
            <span>Preferred Fields</span>
            <Briefcase className="w-4 h-4 text-[#176B63]" />
          </div>
          <div className="text-base font-bold text-[#1C2B2A] truncate">
            {profile?.preferred_disciplines?.[0] || 'Computer Science'}
          </div>
          <p className="text-xs text-[#52615E] mt-1">
            {profile?.preferred_locations?.join(', ') || 'Bengaluru, Hyderabad'}
          </p>
        </div>
      </div>

      {/* Evaluation Outcomes Summary */}
      {hasEvaluated ? (
        <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-6 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#DCE5DF]">
            <div>
              <h3 className="text-base font-bold text-[#1C2B2A]">Evaluation Results</h3>
              <p className="text-xs text-[#52615E]">
                Evaluated across {evaluations.length} programmes using deterministic rules and INR tuition comparison.
              </p>
            </div>
            <button
              onClick={() => onNavigate('programmes')}
              className="text-xs font-semibold text-[#176B63] hover:underline flex items-center gap-1 self-start sm:self-auto"
            >
              <span>View all {evaluations.length} programmes</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="p-4 rounded-xl bg-[#E6F4ED] border border-[#2D6A4F]/20 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#2D6A4F] text-white flex items-center justify-center shrink-0">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xl font-extrabold text-[#2D6A4F]">{eligibleCount}</div>
                <div className="text-xs font-medium text-[#1C2B2A]">Fully Eligible</div>
                <div className="text-[11px] text-[#52615E]">All prerequisites satisfied</div>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#FEF7EC] border border-[#8A5B16]/20 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#8A5B16] text-white flex items-center justify-center shrink-0">
                <HelpCircle className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xl font-extrabold text-[#8A5B16]">{needsReviewCount}</div>
                <div className="text-xs font-medium text-[#1C2B2A]">Needs Verification</div>
                <div className="text-[11px] text-[#52615E]">Missing facts or documents</div>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#FDE8E8] border border-[#A33434]/20 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#A33434] text-white flex items-center justify-center shrink-0">
                <XCircle className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xl font-extrabold text-[#A33434]">{ineligibleCount}</div>
                <div className="text-xs font-medium text-[#1C2B2A]">Ineligible</div>
                <div className="text-[11px] text-[#52615E]">Prerequisite not met</div>
              </div>
            </div>
          </div>

          {/* Top Recommendations Preview */}
          <div className="mt-4 pt-4 border-t border-[#DCE5DF]">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#64736F] mb-3">
              Top Matched Programmes
            </h4>
            <div className="space-y-2.5">
              {evaluations.slice(0, 3).map((evaluation) => (
                <div
                  key={evaluation.programme_id}
                  className="p-3.5 rounded-xl border border-[#DCE5DF] bg-[#F6F8F6] hover:bg-[#FFFFFF] transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-[#1C2B2A]">
                        {evaluation.programme_title}
                      </span>
                      <StatusBadge status={evaluation.eligibility_status} />
                    </div>
                    <div className="flex items-center gap-3 text-xs text-[#52615E]">
                      <span>{evaluation.institution_name}</span>
                      <span>•</span>
                      <span>
                        Total Tuition: ₹
                        {(evaluation.affordability.estimated_total_tuition_inr / 100000).toFixed(1)} Lakh
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <EvidenceBadge
                      activeDimensionsCount={evaluation.evidence ? evaluation.evidence.length : 4}
                    />
                    <button
                      onClick={() => onNavigate('programmes')}
                      className="px-3 py-1.5 rounded-lg bg-[#FFFFFF] border border-[#DCE5DF] hover:bg-[#E1EEE8] hover:text-[#176B63] text-xs font-semibold text-[#52615E] transition-colors"
                    >
                      Inspect
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        /* Empty Evaluation Prompt */
        <div className="bg-[#FFFFFF] border border-dashed border-[#DCE5DF] rounded-2xl p-8 text-center space-y-4">
          <div className="w-12 h-12 rounded-xl bg-[#EDF4F1] text-[#176B63] mx-auto flex items-center justify-center">
            <Compass className="w-6 h-6" />
          </div>
          <div className="max-w-md mx-auto space-y-1">
            <h3 className="text-base font-bold text-[#1C2B2A]">No Evaluations Performed Yet</h3>
            <p className="text-xs text-[#52615E]">
              Hydra evaluates your profile against demonstration programmes with deterministic rules,
              explicit INR tuition verification, and traceable reasoning.
            </p>
          </div>
          <button
            onClick={onEvaluate}
            disabled={isEvaluating}
            className="px-4 py-2 rounded-xl bg-[#176B63] text-white text-xs font-semibold hover:bg-[#155E57] shadow-xs inline-flex items-center gap-1.5"
          >
            <Compass className={`w-3.5 h-3.5 ${isEvaluating ? 'animate-spin' : ''}`} />
            <span>{isEvaluating ? 'Evaluating...' : 'Run Quick Evaluation'}</span>
          </button>
        </div>
      )}

      {/* 4 Feature Exploration Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <button
          onClick={() => onNavigate('programmes')}
          className="text-left p-5 rounded-2xl bg-[#FFFFFF] border border-[#DCE5DF] hover:border-[#176B63] hover:shadow-xs transition-all group"
        >
          <div className="w-10 h-10 rounded-xl bg-[#E1EEE8] text-[#176B63] flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
            <GraduationCap className="w-5 h-5" />
          </div>
          <h4 className="text-sm font-bold text-[#1C2B2A] group-hover:text-[#176B63]">
            Explore Catalog
          </h4>
          <p className="text-xs text-[#52615E] mt-1">
            Filter synthetic university programmes by eligibility, discipline, location, and fees.
          </p>
        </button>

        <button
          onClick={() => onNavigate('compare')}
          className="text-left p-5 rounded-2xl bg-[#FFFFFF] border border-[#DCE5DF] hover:border-[#176B63] hover:shadow-xs transition-all group"
        >
          <div className="w-10 h-10 rounded-xl bg-[#E1EEE8] text-[#176B63] flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
            <Scale className="w-5 h-5" />
          </div>
          <h4 className="text-sm font-bold text-[#1C2B2A] group-hover:text-[#176B63]">
            Compare Programmes
          </h4>
          <p className="text-xs text-[#52615E] mt-1">
            Compare 2 to 4 options side-by-side: prerequisites, tuition gaps, and preference match.
          </p>
        </button>

        <button
          onClick={() => onNavigate('plan')}
          className="text-left p-5 rounded-2xl bg-[#FFFFFF] border border-[#DCE5DF] hover:border-[#176B63] hover:shadow-xs transition-all group"
        >
          <div className="w-10 h-10 rounded-xl bg-[#E1EEE8] text-[#176B63] flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
            <Route className="w-5 h-5" />
          </div>
          <h4 className="text-sm font-bold text-[#1C2B2A] group-hover:text-[#176B63]">
            Action Plan & Simulator
          </h4>
          <p className="text-xs text-[#52615E] mt-1">
            View milestone checklists, simulate what-if grade variations, and check plan resilience.
          </p>
        </button>

        <button
          onClick={() => onNavigate('careers')}
          className="text-left p-5 rounded-2xl bg-[#FFFFFF] border border-[#DCE5DF] hover:border-[#176B63] hover:shadow-xs transition-all group"
        >
          <div className="w-10 h-10 rounded-xl bg-[#E1EEE8] text-[#176B63] flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
            <Briefcase className="w-5 h-5" />
          </div>
          <h4 className="text-sm font-bold text-[#1C2B2A] group-hover:text-[#176B63]">
            Career Pathways
          </h4>
          <p className="text-xs text-[#52615E] mt-1">
            Decode natural language interests into validated academic concepts and career tracks.
          </p>
        </button>
      </div>
    </div>
  );
};
