import React, { useState } from 'react';
import {
  Route,
  CheckCircle2,
  AlertCircle,
  Sliders,
  ShieldAlert,
  ShieldCheck,
  FileText,
  Calendar,
  Sparkles,
} from 'lucide-react';
import type {
  ProgrammeEvaluationDto,
  StudentProfileRequest,
} from '../../api/types';
import { PageHeader } from '../common/PageHeader';
import { StatusBadge } from '../common/StatusBadge';
import { DemoNoticeBanner } from '../common/DemoNoticeBanner';

interface StudentActionPlanViewProps {
  profile?: StudentProfileRequest;
  evaluations: ProgrammeEvaluationDto[];
  onNavigateToProfile: () => void;
}

export const StudentActionPlanView: React.FC<StudentActionPlanViewProps> = ({
  profile,
  evaluations,
}) => {
  const [activeTab, setActiveTab] = useState<'roadmap' | 'simulator' | 'robustness'>('roadmap');

  // Selected target programme for action planning
  const [selectedProgrammeId, setSelectedProgrammeId] = useState<string>(
    evaluations[0]?.programme_id || 'PROG_001'
  );

  // Scenario Simulator sliders
  const currentMath =
    profile?.subject_scores?.find(
      (s) => s.subject_code === 'MATH' || s.subject_name.toLowerCase().includes('math')
    )?.score || 85;
  const currentRank = profile?.entrance_rank || 18500;
  const currentBudget = profile?.total_budget_inr || 800000;

  const [simulatedMath, setSimulatedMath] = useState<number>(currentMath);
  const [simulatedRank, setSimulatedRank] = useState<number>(currentRank);
  const [simulatedBudget, setSimulatedBudget] = useState<number>(currentBudget);

  const targetEvaluation =
    evaluations.find((e) => e.programme_id === selectedProgrammeId) || evaluations[0];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Admissions Action Plan & Simulator"
        description="Structured milestones for university admission, counterfactual scenario testing ('What-if?'), and contingency robustness planning."
        badge={
          <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-[#E1EEE8] text-[#176B63] border border-[#A3D1C0]">
            Decision & Action Hub
          </span>
        }
      />

      <DemoNoticeBanner />

      {/* Mode Tabs */}
      <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-2 shadow-xs flex flex-wrap gap-1">
        <button
          onClick={() => setActiveTab('roadmap')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'roadmap'
              ? 'bg-[#176B63] text-white shadow-xs'
              : 'text-[#52615E] hover:bg-[#EDF4F1] hover:text-[#1C2B2A]'
          }`}
        >
          <Route className="w-4 h-4" />
          <span>1. Admissions Milestone Roadmap</span>
        </button>

        <button
          onClick={() => setActiveTab('simulator')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'simulator'
              ? 'bg-[#176B63] text-white shadow-xs'
              : 'text-[#52615E] hover:bg-[#EDF4F1] hover:text-[#1C2B2A]'
          }`}
        >
          <Sliders className="w-4 h-4" />
          <span>2. "What-If?" Scenario Simulator</span>
        </button>

        <button
          onClick={() => setActiveTab('robustness')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'robustness'
              ? 'bg-[#176B63] text-white shadow-xs'
              : 'text-[#52615E] hover:bg-[#EDF4F1] hover:text-[#1C2B2A]'
          }`}
        >
          <ShieldAlert className="w-4 h-4" />
          <span>3. Plan Robustness & Contingency</span>
        </button>
      </div>

      {/* TAB 1: Admissions Milestone Roadmap */}
      {activeTab === 'roadmap' && (
        <div className="space-y-6">
          {/* Target Programme Picker */}
          {evaluations.length > 0 && (
            <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-4 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-[#1C2B2A]">Target Programme:</span>
                <select
                  value={selectedProgrammeId}
                  onChange={(e) => setSelectedProgrammeId(e.target.value)}
                  className="px-3 py-1.5 rounded-xl border border-[#DCE5DF] bg-[#F6F8F6] text-xs font-semibold text-[#176B63] focus:bg-white focus:outline-none focus:border-[#176B63]"
                >
                  {evaluations.map((ev) => (
                    <option key={ev.programme_id} value={ev.programme_id}>
                      {ev.programme_title} ({ev.institution_name})
                    </option>
                  ))}
                </select>
              </div>

              {targetEvaluation && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-[#52615E]">Current Evaluation:</span>
                  <StatusBadge status={targetEvaluation.eligibility_status} />
                </div>
              )}
            </div>
          )}

          {/* Sequential Milestones */}
          <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-6 shadow-xs space-y-6">
            <div>
              <h3 className="text-base font-bold text-[#1C2B2A]">
                Structured Pathway to Admission
              </h3>
              <p className="text-xs text-[#52615E] mt-0.5">
                Deterministic checklist generated from official university prerequisites and counselling authority rules.
              </p>
            </div>

            <div className="relative pl-6 space-y-6 before:content-[''] before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-[#DCE5DF]">
              {/* Milestone 1 */}
              <div className="relative">
                <div className="absolute -left-6 top-1 w-5 h-5 rounded-full bg-[#2D6A4F] text-white flex items-center justify-center text-[10px] font-bold">
                  ✓
                </div>
                <div className="bg-[#F6F8F6] border border-[#DCE5DF] rounded-xl p-4 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[#1C2B2A]">
                      Milestone 1: 10+2 Subject Qualification & Board Verification
                    </span>
                    <span className="text-[11px] font-semibold text-[#2D6A4F] bg-[#E6F4ED] px-2 py-0.5 rounded-full">
                      Verified
                    </span>
                  </div>
                  <p className="text-xs text-[#52615E]">
                    Mathematics (88%), Physics (82%), and English (78%) meet the mandatory 80% STEM requirement.
                  </p>
                  <div className="text-[11px] text-[#64736F] flex items-center gap-1.5 pt-1">
                    <FileText className="w-3.5 h-3.5" />
                    <span>Evidence: CBSE 10+2 Marksheet certified</span>
                  </div>
                </div>
              </div>

              {/* Milestone 2 */}
              <div className="relative">
                <div className="absolute -left-6 top-1 w-5 h-5 rounded-full bg-[#176B63] text-white flex items-center justify-center text-[10px] font-bold">
                  2
                </div>
                <div className="bg-[#F6F8F6] border border-[#DCE5DF] rounded-xl p-4 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[#1C2B2A]">
                      Milestone 2: Entrance Examination Score Submission
                    </span>
                    <span className="text-[11px] font-semibold text-[#176B63] bg-[#E1EEE8] px-2 py-0.5 rounded-full">
                      Ready to Submit
                    </span>
                  </div>
                  <p className="text-xs text-[#52615E]">
                    JEE Main 2025 Rank #{currentRank.toLocaleString()} satisfies the general cutoff rank threshold of 35,000.
                  </p>
                  <div className="text-[11px] text-[#64736F] flex items-center gap-1.5 pt-1">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>Portal window opens: May 15, 2025</span>
                  </div>
                </div>
              </div>

              {/* Milestone 3 */}
              <div className="relative">
                <div className="absolute -left-6 top-1 w-5 h-5 rounded-full bg-[#8A5B16] text-white flex items-center justify-center text-[10px] font-bold">
                  3
                </div>
                <div className="bg-[#F6F8F6] border border-[#DCE5DF] rounded-xl p-4 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[#1C2B2A]">
                      Milestone 3: Domicile & Category Quota Documentation
                    </span>
                    <span className="text-[11px] font-semibold text-[#8A5B16] bg-[#FEF7EC] px-2 py-0.5 rounded-full">
                      Action Required
                    </span>
                  </div>
                  <p className="text-xs text-[#52615E]">
                    If applying under Home State quota in Karnataka, ensure valid domicile certificate issued by the tahsildar.
                  </p>
                  <div className="text-[11px] text-[#8A5B16] font-medium flex items-center gap-1.5 pt-1">
                    <AlertCircle className="w-3.5 h-3.5" />
                    <span>Upload required before Round 1 seat allocation</span>
                  </div>
                </div>
              </div>

              {/* Milestone 4 */}
              <div className="relative">
                <div className="absolute -left-6 top-1 w-5 h-5 rounded-full bg-[#64736F] text-white flex items-center justify-center text-[10px] font-bold">
                  4
                </div>
                <div className="bg-[#F6F8F6] border border-[#DCE5DF] rounded-xl p-4 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[#1C2B2A]">
                      Milestone 4: Centralized Choice Locking & Seat Allocation
                    </span>
                    <span className="text-[11px] font-semibold text-[#64736F] bg-[#EDF4F1] px-2 py-0.5 rounded-full">
                      Upcoming
                    </span>
                  </div>
                  <p className="text-xs text-[#52615E]">
                    Lock your preferred branches in descending preference order. Maintain 2 safety options with cutoff rank &gt; 30,000.
                  </p>
                </div>
              </div>

              {/* Milestone 5 */}
              <div className="relative">
                <div className="absolute -left-6 top-1 w-5 h-5 rounded-full bg-[#64736F] text-white flex items-center justify-center text-[10px] font-bold">
                  5
                </div>
                <div className="bg-[#F6F8F6] border border-[#DCE5DF] rounded-xl p-4 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[#1C2B2A]">
                      Milestone 5: Seat Acceptance Fee & Physical Reporting
                    </span>
                    <span className="text-[11px] font-semibold text-[#64736F] bg-[#EDF4F1] px-2 py-0.5 rounded-full">
                      Upcoming
                    </span>
                  </div>
                  <p className="text-xs text-[#52615E]">
                    Remit provisional seat fee (adjusted against 1st year tuition) and submit original certificates for campus verification.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: "What-If?" Scenario Simulator */}
      {activeTab === 'simulator' && (
        <div className="space-y-6">
          <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-6 shadow-xs space-y-6">
            <div>
              <h3 className="text-base font-bold text-[#1C2B2A]">
                Explore Counterfactual Scenarios
              </h3>
              <p className="text-xs text-[#52615E] mt-0.5">
                Simulate changes to your marks, competitive rank, or financial budget to observe deterministic rule outcomes.
              </p>
            </div>

            {/* Simulator Controls */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 p-4 rounded-xl bg-[#F6F8F6] border border-[#DCE5DF]">
              {/* Mathematics Score Slider */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="font-bold text-[#1C2B2A]">Mathematics Score:</span>
                  <span className="font-bold text-[#176B63]">{simulatedMath}%</span>
                </div>
                <input
                  type="range"
                  min="50"
                  max="100"
                  value={simulatedMath}
                  onChange={(e) => setSimulatedMath(parseInt(e.target.value, 10))}
                  className="w-full accent-[#176B63] cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-[#64736F]">
                  <span>50%</span>
                  <span>Cutoff: 80%</span>
                  <span>100%</span>
                </div>
              </div>

              {/* Entrance Rank Slider */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="font-bold text-[#1C2B2A]">Entrance Rank:</span>
                  <span className="font-bold text-[#176B63]">#{simulatedRank.toLocaleString()}</span>
                </div>
                <input
                  type="range"
                  min="2000"
                  max="60000"
                  step="500"
                  value={simulatedRank}
                  onChange={(e) => setSimulatedRank(parseInt(e.target.value, 10))}
                  className="w-full accent-[#176B63] cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-[#64736F]">
                  <span>#2,000 (Top)</span>
                  <span>#35,000 (Cutoff)</span>
                  <span>#60,000</span>
                </div>
              </div>

              {/* 4-Yr Budget Slider */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="font-bold text-[#1C2B2A]">Total Budget:</span>
                  <span className="font-bold text-[#176B63]">
                    ₹{(simulatedBudget / 100000).toFixed(1)} Lakh
                  </span>
                </div>
                <input
                  type="range"
                  min="300000"
                  max="2500000"
                  step="50000"
                  value={simulatedBudget}
                  onChange={(e) => setSimulatedBudget(parseInt(e.target.value, 10))}
                  className="w-full accent-[#176B63] cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-[#64736F]">
                  <span>₹3.0 Lakh</span>
                  <span>₹12.0 Lakh</span>
                  <span>₹25.0 Lakh</span>
                </div>
              </div>
            </div>

            {/* Real-time Scenario Evaluation Outcome */}
            <div className="p-4 rounded-xl border border-[#DCE5DF] bg-white space-y-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-[#176B63]" />
                <span className="text-xs font-bold text-[#1C2B2A]">
                  Simulated Outcome for {targetEvaluation?.programme_title || 'Target Programme'}:
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3 rounded-lg bg-[#F6F8F6] border border-[#DCE5DF]">
                  <span className="text-[11px] text-[#64736F] block">Math Prerequisite (≥80%):</span>
                  {simulatedMath >= 80 ? (
                    <span className="text-xs font-bold text-[#2D6A4F] flex items-center gap-1 mt-0.5">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Satisfied ({simulatedMath}%)
                    </span>
                  ) : (
                    <span className="text-xs font-bold text-[#A33434] flex items-center gap-1 mt-0.5">
                      <AlertCircle className="w-3.5 h-3.5" /> Deficit ({simulatedMath}% &lt; 80%)
                    </span>
                  )}
                </div>

                <div className="p-3 rounded-lg bg-[#F6F8F6] border border-[#DCE5DF]">
                  <span className="text-[11px] text-[#64736F] block">Rank Cutoff (≤35,000):</span>
                  {simulatedRank <= 35000 ? (
                    <span className="text-xs font-bold text-[#2D6A4F] flex items-center gap-1 mt-0.5">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Within Cutoff (#{simulatedRank})
                    </span>
                  ) : (
                    <span className="text-xs font-bold text-[#A33434] flex items-center gap-1 mt-0.5">
                      <AlertCircle className="w-3.5 h-3.5" /> Outside Cutoff (#{simulatedRank})
                    </span>
                  )}
                </div>

                <div className="p-3 rounded-lg bg-[#F6F8F6] border border-[#DCE5DF]">
                  <span className="text-[11px] text-[#64736F] block">Tuition Affordability (₹7.2L):</span>
                  {simulatedBudget >= 720000 ? (
                    <span className="text-xs font-bold text-[#2D6A4F] flex items-center gap-1 mt-0.5">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Within Budget
                    </span>
                  ) : (
                    <span className="text-xs font-bold text-[#A33434] flex items-center gap-1 mt-0.5">
                      <AlertCircle className="w-3.5 h-3.5" /> Shortfall of ₹{((720000 - simulatedBudget) / 100000).toFixed(1)}L
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: Plan Robustness & Contingency */}
      {activeTab === 'robustness' && (
        <div className="space-y-6">
          <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-6 shadow-xs space-y-6">
            <div>
              <h3 className="text-base font-bold text-[#1C2B2A]">
                Plan Robustness & Adversity Analysis
              </h3>
              <p className="text-xs text-[#52615E] mt-0.5">
                Stress-test your admission strategy against real-world uncertainties without panic.
              </p>
            </div>

            <div className="space-y-4">
              {/* Challenge 1 */}
              <div className="p-4 rounded-xl border border-[#DCE5DF] bg-[#F6F8F6] space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-md bg-[#FEF7EC] text-[#8A5B16] flex items-center justify-center font-bold text-xs">
                      1
                    </div>
                    <span className="text-xs font-bold text-[#1C2B2A]">
                      Potential Challenge: Cutoff Rank Inflation
                    </span>
                  </div>
                  <span className="text-[11px] font-semibold text-[#8A5B16] bg-[#FEF7EC] px-2 py-0.5 rounded-full">
                    Medium Likelihood
                  </span>
                </div>
                <p className="text-xs text-[#52615E]">
                  If applicant volume surges for Computer Science, the closing rank could tighten by 5–8% (e.g. from 35,000 to 32,500).
                </p>
                <div className="p-3 rounded-lg bg-white border border-[#DCE5DF] text-xs space-y-1">
                  <span className="font-semibold text-[#2D6A4F] flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5" /> Recommended Mitigation:
                  </span>
                  <p className="text-[#52615E]">
                    Your current rank #{currentRank.toLocaleString()} provides a comfortable margin of 16,500 ranks. Keep 1 backup programme in Information Technology as a safety hedge.
                  </p>
                </div>
              </div>

              {/* Challenge 2 */}
              <div className="p-4 rounded-xl border border-[#DCE5DF] bg-[#F6F8F6] space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-md bg-[#FEF7EC] text-[#8A5B16] flex items-center justify-center font-bold text-xs">
                      2
                    </div>
                    <span className="text-xs font-bold text-[#1C2B2A]">
                      Potential Challenge: Ancillary Living & Hostel Expenses
                    </span>
                  </div>
                  <span className="text-[11px] font-semibold text-[#315C86] bg-[#E9F1F7] px-2 py-0.5 rounded-full">
                    Financial Notice
                  </span>
                </div>
                <p className="text-xs text-[#52615E]">
                  Hydra calculates tuition-only fees (₹7.2 Lakh). Living and hostel costs in metropolitan campuses typically require ₹80,000–₹1,20,000 per year.
                </p>
                <div className="p-3 rounded-lg bg-white border border-[#DCE5DF] text-xs space-y-1">
                  <span className="font-semibold text-[#2D6A4F] flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5" /> Recommended Mitigation:
                  </span>
                  <p className="text-[#52615E]">
                    Budget an additional ₹3.5–4.0 Lakh for living expenses across 4 years or consider local day-scholar accommodation if available.
                  </p>
                </div>
              </div>

              {/* Challenge 3 */}
              <div className="p-4 rounded-xl border border-[#DCE5DF] bg-[#F6F8F6] space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-md bg-[#E6F4ED] text-[#2D6A4F] flex items-center justify-center font-bold text-xs">
                      3
                    </div>
                    <span className="text-xs font-bold text-[#1C2B2A]">
                      Potential Challenge: Certificate Verification Deadlines
                    </span>
                  </div>
                  <span className="text-[11px] font-semibold text-[#2D6A4F] bg-[#E6F4ED] px-2 py-0.5 rounded-full">
                    Low Risk / Operational
                  </span>
                </div>
                <p className="text-xs text-[#52615E]">
                  Government quota seats require tahsildar-issued domicile certificates dated within 6 months of counselling.
                </p>
                <div className="p-3 rounded-lg bg-white border border-[#DCE5DF] text-xs space-y-1">
                  <span className="font-semibold text-[#2D6A4F] flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5" /> Recommended Mitigation:
                  </span>
                  <p className="text-[#52615E]">
                    Apply for updated domicile certificates at your local revenue office 30 days prior to choice registration.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
