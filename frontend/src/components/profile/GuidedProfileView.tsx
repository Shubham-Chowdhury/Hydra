import React, { useState } from 'react';
import {
  GraduationCap,
  Award,
  Wallet,
  MapPin,
  Sparkles,
  ChevronRight,
  ChevronLeft,
  Plus,
  Trash2,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  UserCheck,
} from 'lucide-react';
import type { StudentProfileRequest, SubjectScoreDto } from '../../api/types';
import { PageHeader } from '../common/PageHeader';
import { ProvenanceIndicator } from '../common/ProvenanceIndicator';

interface GuidedProfileViewProps {
  currentProfile?: StudentProfileRequest;
  onSubmit: (profile: StudentProfileRequest) => void;
  isLoading: boolean;
  onNavigateToExplore?: () => void;
}

const DEFAULT_SUBJECTS: SubjectScoreDto[] = [
  { subject_code: 'MATH', subject_name: 'Mathematics', score: 88, max_score: 100, grading_scale: 'percentage' },
  { subject_code: 'ENG', subject_name: 'English', score: 78, max_score: 100, grading_scale: 'percentage' },
  { subject_code: 'PHYS', subject_name: 'Physics', score: 82, max_score: 100, grading_scale: 'percentage' },
];

export const GuidedProfileView: React.FC<GuidedProfileViewProps> = ({
  currentProfile,
  onSubmit,
  isLoading,
}) => {
  const [currentStep, setCurrentStep] = useState<number>(1);
  const totalSteps = 6;

  // Form states initialized from currentProfile if present
  const [studentId] = useState<string>(
    currentProfile?.student_id || 'STU_MASTER_REF'
  );
  const [board, setBoard] = useState<string>(
    currentProfile?.subject_scores?.[0]?.board || 'CBSE (All India)'
  );
  const [subjects, setSubjects] = useState<SubjectScoreDto[]>(
    currentProfile?.subject_scores && currentProfile.subject_scores.length > 0
      ? currentProfile.subject_scores
      : DEFAULT_SUBJECTS
  );

  const [entranceExam, setEntranceExam] = useState<string>(
    currentProfile?.entrance_exam_name || 'JEE Main'
  );
  const [entranceRank, setEntranceRank] = useState<string>(
    currentProfile?.entrance_rank ? String(currentProfile.entrance_rank) : '18500'
  );

  const [totalBudgetInr, setTotalBudgetInr] = useState<number>(
    currentProfile?.total_budget_inr || 800000
  );

  const [preferredLocations, setPreferredLocations] = useState<string>(
    currentProfile?.preferred_locations ? currentProfile.preferred_locations.join(', ') : 'Karnataka, Maharashtra'
  );

  const [preferredDisciplines, setPreferredDisciplines] = useState<string>(
    currentProfile?.preferred_disciplines ? currentProfile.preferred_disciplines.join(', ') : 'Computer Science, Data Science'
  );

  const [careerGoals, setCareerGoals] = useState<string>(
    currentProfile?.career_goals ? currentProfile.career_goals.join(', ') : 'Software Engineer, Systems Architect'
  );

  const [formError, setFormError] = useState<string | null>(null);

  // Quick Preset Handlers (Demonstration / Testing Scenarios)
  const applyPreset = (preset: 'eligible' | 'ineligible' | 'needs_review' | 'unaffordable') => {
    if (typeof window !== 'undefined' && !window.confirm('Load demonstration testing scenario? This will replace your current profile inputs with synthetic demonstration test data.')) {
      return;
    }
    setFormError(null);
    if (preset === 'eligible') {
      setSubjects([
        { subject_code: 'MATH', subject_name: 'Mathematics', score: 88, max_score: 100, grading_scale: 'percentage' },
        { subject_code: 'ENG', subject_name: 'English', score: 78, max_score: 100, grading_scale: 'percentage' },
        { subject_code: 'PHYS', subject_name: 'Physics', score: 82, max_score: 100, grading_scale: 'percentage' },
      ]);
      setEntranceExam('JEE Main');
      setEntranceRank('18500');
      setTotalBudgetInr(800000);
      setPreferredLocations('Karnataka, Maharashtra');
      setPreferredDisciplines('Computer Science, Data Science');
      setCareerGoals('Software Engineer');
    } else if (preset === 'ineligible') {
      setSubjects([
        { subject_code: 'MATH', subject_name: 'Mathematics', score: 65, max_score: 100, grading_scale: 'percentage' },
        { subject_code: 'ENG', subject_name: 'English', score: 75, max_score: 100, grading_scale: 'percentage' },
        { subject_code: 'PHYS', subject_name: 'Physics', score: 70, max_score: 100, grading_scale: 'percentage' },
      ]);
      setEntranceExam('JEE Main');
      setEntranceRank('38000');
      setTotalBudgetInr(800000);
      setPreferredLocations('Karnataka');
      setPreferredDisciplines('Computer Science');
      setCareerGoals('Software Engineer');
    } else if (preset === 'needs_review') {
      setSubjects([
        { subject_code: 'BIO', subject_name: 'Biology', score: 84, max_score: 100, grading_scale: 'percentage' },
      ]);
      setEntranceExam('');
      setEntranceRank('');
      setTotalBudgetInr(600000);
      setPreferredLocations('Telangana');
      setPreferredDisciplines('Biotechnology');
      setCareerGoals('Biomedical Researcher');
    } else if (preset === 'unaffordable') {
      setSubjects([
        { subject_code: 'MATH', subject_name: 'Mathematics', score: 88, max_score: 100, grading_scale: 'percentage' },
        { subject_code: 'PHYS', subject_name: 'Physics', score: 85, max_score: 100, grading_scale: 'percentage' },
      ]);
      setEntranceExam('JEE Main');
      setEntranceRank('15000');
      setTotalBudgetInr(450000);
      setPreferredLocations('Delhi NCR, Bengaluru');
      setPreferredDisciplines('Robotics');
      setCareerGoals('Robotics Engineer');
    }
  };

  const handleAddSubject = () => {
    setSubjects([
      ...subjects,
      { subject_code: 'SUBJ', subject_name: '', score: 75, max_score: 100, grading_scale: 'percentage' },
    ]);
  };

  const handleRemoveSubject = (idx: number) => {
    setSubjects(subjects.filter((_, i) => i !== idx));
  };

  const handleSubjectChange = (idx: number, field: keyof SubjectScoreDto, val: unknown) => {
    const next = [...subjects];
    next[idx] = { ...next[idx], [field]: val };
    setSubjects(next);
  };

  const buildProfileRequest = (): StudentProfileRequest => {
    const rankNum = parseInt(entranceRank, 10);
    const hasExam = entranceExam.trim() && !isNaN(rankNum) && rankNum > 0;

    return {
      student_id: studentId || 'STU_MASTER_REF',
      subject_scores: subjects.map((s) => ({
        ...s,
        board: board.trim() || 'CBSE',
      })),
      entrance_exam_name: hasExam ? entranceExam.trim() : undefined,
      entrance_rank: hasExam ? rankNum : undefined,
      total_budget_inr: Number(totalBudgetInr),
      preferred_locations: preferredLocations
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
      preferred_disciplines: preferredDisciplines
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
      career_goals: careerGoals
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
    };
  };

  const handleFinalSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setFormError(null);

    if (subjects.length === 0) {
      setFormError('Please add at least one subject score.');
      return;
    }

    const profile = buildProfileRequest();
    onSubmit(profile);
  };

  const stepLabels = [
    'Academic Record',
    'Entrance Exams',
    'Financial Budget',
    'Locations & Disciplines',
    'Career Goals',
    'Review & Evaluate',
  ];

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <PageHeader
        title="Student Profile & Digital Twin"
        description="Provide your verified academic, financial, and geographical facts. Hydra evaluates your criteria with deterministic rules and zero probabilistic speculation."
        badge={
          <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-[#E1EEE8] text-[#176B63] border border-[#A3D1C0]">
            Verified Input Layer
          </span>
        }
      />

      {/* Demonstration / Testing Presets Banner */}
      <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-4 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-[#176B63]" />
            <div>
              <span className="text-xs font-bold text-[#1C2B2A]">
                Demonstration & Testing Scenarios (Synthetic Data):
              </span>
              <p className="text-[11px] text-[#64736F]">
                Load pre-configured test scenarios to verify deterministic rules. Never silently overwrites your saved facts.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-1.5">
            <button
              type="button"
              onClick={() => applyPreset('eligible')}
              className="px-2.5 py-1 text-xs rounded-lg bg-[#E6F4ED] text-[#2D6A4F] hover:bg-[#D4EFE0] font-medium border border-[#2D6A4F]/20 transition-colors"
              title="Loads synthetic test profile matching all prerequisites"
            >
              Demo: Full Match (88% Math, JEE 18.5k)
            </button>
            <button
              type="button"
              onClick={() => applyPreset('ineligible')}
              className="px-2.5 py-1 text-xs rounded-lg bg-[#FDE8E8] text-[#A33434] hover:bg-[#FCD8D8] font-medium border border-[#A33434]/20 transition-colors"
              title="Loads synthetic test profile with prerequisite deficit"
            >
              Demo: Prerequisite Deficit (65% Math)
            </button>
            <button
              type="button"
              onClick={() => applyPreset('needs_review')}
              className="px-2.5 py-1 text-xs rounded-lg bg-[#FEF7EC] text-[#8A5B16] hover:bg-[#FDEED3] font-medium border border-[#8A5B16]/20 transition-colors"
              title="Loads synthetic test profile with missing facts"
            >
              Demo: Missing Fact (Omit Subject)
            </button>
            <button
              type="button"
              onClick={() => applyPreset('unaffordable')}
              className="px-2.5 py-1 text-xs rounded-lg bg-[#EDF4F1] text-[#52615E] hover:bg-[#DCE5DF] font-medium border border-[#DCE5DF] transition-colors"
              title="Loads synthetic test profile with budget limit"
            >
              Demo: Budget Limit (₹4.5L Total)
            </button>
          </div>
        </div>
      </div>

      {/* Step Progress Stepper */}
      <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-4 shadow-xs">
        <div className="flex items-center justify-between overflow-x-auto scrollbar-none gap-2 py-1">
          {stepLabels.map((label, index) => {
            const stepNum = index + 1;
            const isCompleted = stepNum < currentStep;
            const isCurrent = stepNum === currentStep;
            return (
              <button
                key={label}
                type="button"
                onClick={() => setCurrentStep(stepNum)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                  isCurrent
                    ? 'bg-[#176B63] text-white shadow-xs'
                    : isCompleted
                    ? 'bg-[#E1EEE8] text-[#176B63]'
                    : 'text-[#64736F] hover:bg-[#EDF4F1]'
                }`}
              >
                <span
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-bold ${
                    isCurrent
                      ? 'bg-white text-[#176B63]'
                      : isCompleted
                      ? 'bg-[#176B63] text-white'
                      : 'bg-[#DCE5DF] text-[#64736F]'
                  }`}
                >
                  {isCompleted ? '✓' : stepNum}
                </span>
                <span>{label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Step Form Body */}
      <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-6 shadow-xs space-y-6">
        {formError && (
          <div className="p-3.5 rounded-xl bg-[#FDE8E8] border border-[#A33434]/30 text-[#A33434] text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{formError}</span>
          </div>
        )}

        {/* STEP 1: Academic Record */}
        {currentStep === 1 && (
          <div className="space-y-4">
            <div className="border-b border-[#DCE5DF] pb-3">
              <h3 className="text-base font-bold text-[#1C2B2A] flex items-center gap-2">
                <GraduationCap className="w-4 h-4 text-[#176B63]" />
                <span>Step 1: Academic Record & 10+2 Scores</span>
              </h3>
              <p className="text-xs text-[#52615E] mt-0.5">
                Evaluated deterministically against programme subject prerequisites (e.g. Mathematics ≥ 80%).
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-[#1C2B2A] mb-1">
                  Examination Board / Authority
                </label>
                <input
                  type="text"
                  value={board}
                  onChange={(e) => setBoard(e.target.value)}
                  placeholder="e.g. CBSE, Karnataka State Board, ICSE"
                  className="w-full px-3 py-2 rounded-xl border border-[#DCE5DF] bg-[#F6F8F6] text-xs focus:bg-white focus:outline-none focus:border-[#176B63]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#1C2B2A] mb-1">
                  Grading Scale
                </label>
                <input
                  type="text"
                  value="Percentage (0 - 100%)"
                  disabled
                  className="w-full px-3 py-2 rounded-xl border border-[#DCE5DF] bg-[#EDF4F1] text-xs text-[#52615E] cursor-not-allowed"
                />
                <span className="text-[11px] text-[#64736F] mt-0.5 block">
                  Deterministic rules compare on 100-point percentage basis.
                </span>
              </div>
            </div>

            <div className="pt-2">
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-bold text-[#1C2B2A]">
                  Subject Marks & Prerequisites
                </label>
                <button
                  type="button"
                  onClick={handleAddSubject}
                  className="px-2.5 py-1 text-xs rounded-lg bg-[#E1EEE8] text-[#176B63] hover:bg-[#D0E5DC] font-semibold flex items-center gap-1"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Subject</span>
                </button>
              </div>

              <div className="space-y-2">
                {subjects.map((subj, index) => (
                  <div
                    key={index}
                    className="p-3 rounded-xl border border-[#DCE5DF] bg-[#F6F8F6] flex flex-col sm:flex-row items-center gap-3"
                  >
                    <div className="w-full sm:w-1/3">
                      <input
                        type="text"
                        value={subj.subject_name}
                        onChange={(e) => handleSubjectChange(index, 'subject_name', e.target.value)}
                        placeholder="Subject (e.g. Mathematics)"
                        className="w-full px-2.5 py-1.5 rounded-lg border border-[#DCE5DF] bg-white text-xs focus:outline-none focus:border-[#176B63]"
                      />
                    </div>
                    <div className="w-full sm:w-1/4">
                      <input
                        type="text"
                        value={subj.subject_code}
                        onChange={(e) => handleSubjectChange(index, 'subject_code', e.target.value.toUpperCase())}
                        placeholder="Code (e.g. MATH)"
                        className="w-full px-2.5 py-1.5 rounded-lg border border-[#DCE5DF] bg-white text-xs uppercase focus:outline-none focus:border-[#176B63]"
                      />
                    </div>
                    <div className="w-full sm:w-1/4 flex items-center gap-2">
                      <input
                        type="number"
                        min="0"
                        max="100"
                        value={subj.score}
                        onChange={(e) => handleSubjectChange(index, 'score', parseFloat(e.target.value) || 0)}
                        placeholder="Score (%)"
                        className="w-full px-2.5 py-1.5 rounded-lg border border-[#DCE5DF] bg-white text-xs focus:outline-none focus:border-[#176B63]"
                      />
                      <span className="text-xs text-[#52615E] font-medium">%</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleRemoveSubject(index)}
                      className="p-1.5 text-[#A33434] hover:bg-[#FDE8E8] rounded-lg transition-colors self-end sm:self-center"
                      title="Remove subject"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* STEP 2: Entrance Exams */}
        {currentStep === 2 && (
          <div className="space-y-4">
            <div className="border-b border-[#DCE5DF] pb-3">
              <h3 className="text-base font-bold text-[#1C2B2A] flex items-center gap-2">
                <Award className="w-4 h-4 text-[#176B63]" />
                <span>Step 2: Competitive Entrance Examination</span>
              </h3>
              <p className="text-xs text-[#52615E] mt-0.5">
                Compared against opening and closing ranks reported in university cutoffs.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-[#1C2B2A] mb-1">
                  Examination Name
                </label>
                <input
                  type="text"
                  value={entranceExam}
                  onChange={(e) => setEntranceExam(e.target.value)}
                  placeholder="e.g. JEE Main, MHT-CET, NEET"
                  className="w-full px-3 py-2 rounded-xl border border-[#DCE5DF] bg-[#F6F8F6] text-xs focus:bg-white focus:outline-none focus:border-[#176B63]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#1C2B2A] mb-1">
                  All-India / State Rank
                </label>
                <input
                  type="number"
                  min="1"
                  value={entranceRank}
                  onChange={(e) => setEntranceRank(e.target.value)}
                  placeholder="e.g. 18500"
                  className="w-full px-3 py-2 rounded-xl border border-[#DCE5DF] bg-[#F6F8F6] text-xs focus:bg-white focus:outline-none focus:border-[#176B63]"
                />
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#EDF4F1] border border-[#DCE5DF] text-xs text-[#52615E] flex items-start gap-2.5">
              <HelpCircle className="w-4 h-4 text-[#176B63] shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-[#1C2B2A]">Rank Evaluation Standard:</span>{' '}
                Our rule engine compares your verified entrance rank against official programme cutoffs. If your rank is lower (better) than the cutoff rank, you satisfy the rank requirement.
              </div>
            </div>
          </div>
        )}

        {/* STEP 3: Financial Budget */}
        {currentStep === 3 && (
          <div className="space-y-4">
            <div className="border-b border-[#DCE5DF] pb-3">
              <h3 className="text-base font-bold text-[#1C2B2A] flex items-center gap-2">
                <Wallet className="w-4 h-4 text-[#176B63]" />
                <span>Step 3: Tuition Budget Constraints</span>
              </h3>
              <p className="text-xs text-[#52615E] mt-0.5">
                Directly compared in INR against programme tuition. Affordability is evaluated separately from academic eligibility.
              </p>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-[#1C2B2A]">
                  Total 4-Year Tuition Budget (INR):
                </label>
                <span className="text-base font-extrabold text-[#176B63]">
                  ₹{(totalBudgetInr / 100000).toFixed(2)} Lakhs (₹{totalBudgetInr.toLocaleString()})
                </span>
              </div>

              <input
                type="range"
                min="200000"
                max="3000000"
                step="50000"
                value={totalBudgetInr}
                onChange={(e) => setTotalBudgetInr(parseInt(e.target.value, 10))}
                className="w-full accent-[#176B63] cursor-pointer"
              />

              <div className="flex justify-between text-[11px] text-[#64736F]">
                <span>₹2.0 Lakh (Subsidized)</span>
                <span>₹10.0 Lakh</span>
                <span>₹20.0 Lakh</span>
                <span>₹30.0 Lakh (Self-financed)</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                <div className="p-3 rounded-xl bg-[#F6F8F6] border border-[#DCE5DF]">
                  <span className="text-[11px] text-[#64736F] block">Equivalent Annual Cap:</span>
                  <span className="text-sm font-bold text-[#1C2B2A]">
                    ₹{(totalBudgetInr / 4 / 100000).toFixed(2)} Lakh / year
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-[#F6F8F6] border border-[#DCE5DF]">
                  <span className="text-[11px] text-[#64736F] block">Cost Basis:</span>
                  <span className="text-sm font-bold text-[#1C2B2A]">
                    Tuition Fees Only (Hostel/Living Excluded)
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* STEP 4: Locations & Disciplines */}
        {currentStep === 4 && (
          <div className="space-y-4">
            <div className="border-b border-[#DCE5DF] pb-3">
              <h3 className="text-base font-bold text-[#1C2B2A] flex items-center gap-2">
                <MapPin className="w-4 h-4 text-[#176B63]" />
                <span>Step 4: Location & Discipline Preferences</span>
              </h3>
              <p className="text-xs text-[#52615E] mt-0.5">
                Used to compute preference fit scores without overriding deterministic eligibility rules.
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-[#1C2B2A] mb-1">
                  Preferred States / Cities (Comma separated)
                </label>
                <input
                  type="text"
                  value={preferredLocations}
                  onChange={(e) => setPreferredLocations(e.target.value)}
                  placeholder="e.g. Karnataka, Maharashtra, Telangana, Delhi NCR"
                  className="w-full px-3 py-2 rounded-xl border border-[#DCE5DF] bg-[#F6F8F6] text-xs focus:bg-white focus:outline-none focus:border-[#176B63]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#1C2B2A] mb-1">
                  Target Academic Disciplines (Comma separated)
                </label>
                <input
                  type="text"
                  value={preferredDisciplines}
                  onChange={(e) => setPreferredDisciplines(e.target.value)}
                  placeholder="e.g. Computer Science, Artificial Intelligence, Electronics"
                  className="w-full px-3 py-2 rounded-xl border border-[#DCE5DF] bg-[#F6F8F6] text-xs focus:bg-white focus:outline-none focus:border-[#176B63]"
                />
              </div>
            </div>
          </div>
        )}

        {/* STEP 5: Career Goals */}
        {currentStep === 5 && (
          <div className="space-y-4">
            <div className="border-b border-[#DCE5DF] pb-3">
              <h3 className="text-base font-bold text-[#1C2B2A] flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-[#176B63]" />
                <span>Step 5: Career Goals & Natural Language Interests</span>
              </h3>
              <p className="text-xs text-[#52615E] mt-0.5">
                Traversed via NetworkX semantic graph and FastEmbed embeddings for career trajectories.
              </p>
            </div>

            <div>
              <label className="block text-xs font-bold text-[#1C2B2A] mb-1">
                Target Roles & Aspirations (Comma separated)
              </label>
              <textarea
                rows={3}
                value={careerGoals}
                onChange={(e) => setCareerGoals(e.target.value)}
                placeholder="e.g. Machine Learning Engineer, Embedded Systems Architect, Quantitative Analyst"
                className="w-full px-3 py-2 rounded-xl border border-[#DCE5DF] bg-[#F6F8F6] text-xs focus:bg-white focus:outline-none focus:border-[#176B63]"
              />
            </div>

            <div className="p-4 rounded-xl bg-[#EDF4F1] border border-[#DCE5DF] text-xs text-[#52615E]">
              <span className="font-semibold text-[#1C2B2A]">Deterministic Traversal:</span>{' '}
              Hydra maps your stated goals to academic curricula through structured knowledge graph edges, ensuring every suggested skill has an accredited curriculum source.
            </div>
          </div>
        )}

        {/* STEP 6: Review & Evaluate */}
        {currentStep === 6 && (
          <div className="space-y-4">
            <div className="border-b border-[#DCE5DF] pb-3">
              <h3 className="text-base font-bold text-[#1C2B2A] flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#2D6A4F]" />
                <span>Step 6: Review Profile Facts & Evaluate</span>
              </h3>
              <p className="text-xs text-[#52615E] mt-0.5">
                Inspect your profile facts prior to evaluation. All inputs are marked as user-provided evidence.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-[#F6F8F6] border border-[#DCE5DF] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#1C2B2A]">Academic Scores:</span>
                  <ProvenanceIndicator category="user_provided" />
                </div>
                <div className="space-y-1 text-xs text-[#52615E]">
                  {subjects.map((s, idx) => (
                    <div key={idx} className="flex justify-between">
                      <span>{s.subject_name || s.subject_code}:</span>
                      <span className="font-semibold text-[#1C2B2A]">{s.score}%</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#F6F8F6] border border-[#DCE5DF] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#1C2B2A]">Entrance Exam & Budget:</span>
                  <ProvenanceIndicator category="user_provided" />
                </div>
                <div className="space-y-1 text-xs text-[#52615E]">
                  <div className="flex justify-between">
                    <span>Exam:</span>
                    <span className="font-semibold text-[#1C2B2A]">{entranceExam || 'None'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Rank:</span>
                    <span className="font-semibold text-[#1C2B2A]">
                      {entranceRank ? `#${entranceRank}` : 'None'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Total 4-Yr Budget:</span>
                    <span className="font-semibold text-[#1C2B2A]">₹{(totalBudgetInr / 100000).toFixed(1)} Lakh</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-[#E6F4ED] border border-[#2D6A4F]/20 text-xs text-[#2D6A4F] flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>
                Ready to evaluate. The backend will execute deterministic rule trees and compute INR affordability.
              </span>
            </div>
          </div>
        )}

        {/* Stepper Navigation Footer */}
        <div className="flex items-center justify-between pt-4 border-t border-[#DCE5DF]">
          {currentStep > 1 ? (
            <button
              type="button"
              onClick={() => setCurrentStep(currentStep - 1)}
              className="px-4 py-2 rounded-xl border border-[#DCE5DF] text-xs font-semibold text-[#52615E] hover:bg-[#EDF4F1] flex items-center gap-1.5 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              <span>Back</span>
            </button>
          ) : (
            <div />
          )}

          {currentStep < totalSteps ? (
            <button
              type="button"
              onClick={() => setCurrentStep(currentStep + 1)}
              className="px-5 py-2.5 rounded-xl bg-[#176B63] hover:bg-[#155E57] text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-xs"
            >
              <span>Next: {stepLabels[currentStep]}</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              type="button"
              onClick={() => handleFinalSubmit()}
              disabled={isLoading}
              className="px-6 py-2.5 rounded-xl bg-[#176B63] hover:bg-[#155E57] text-white text-xs font-bold flex items-center gap-2 transition-all shadow-xs disabled:opacity-50"
            >
              <UserCheck className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              <span>{isLoading ? 'Evaluating Facts...' : 'Save Profile & Run Evaluation'}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
