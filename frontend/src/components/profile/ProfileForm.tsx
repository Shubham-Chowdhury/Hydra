import React, { useState } from 'react';
import { Plus, Trash2, Sparkles, Send, BookOpen, MapPin, Award } from 'lucide-react';
import type { StudentProfileRequest, SubjectScoreDto } from '../../api/types';

interface ProfileFormProps {
  onSubmit: (profile: StudentProfileRequest) => void;
  isLoading: boolean;
}

const DEFAULT_SUBJECTS: SubjectScoreDto[] = [
  { subject_code: 'MATH', subject_name: 'Mathematics', score: 85, max_score: 100, grading_scale: 'percentage' },
  { subject_code: 'ENG', subject_name: 'English', score: 75, max_score: 100, grading_scale: 'percentage' },
  { subject_code: 'PHYS', subject_name: 'Physics', score: 80, max_score: 100, grading_scale: 'percentage' },
];

export const ProfileForm: React.FC<ProfileFormProps> = ({ onSubmit, isLoading }) => {
  const [subjects, setSubjects] = useState<SubjectScoreDto[]>(DEFAULT_SUBJECTS);
  const [entranceExam, setEntranceExam] = useState<string>('JEE Main');
  const [entranceRank, setEntranceRank] = useState<string>('18500');
  const [locations, setLocations] = useState<string>('Karnataka, Maharashtra');
  const [budgetInr, setBudgetInr] = useState<number>(800000);
  const [disciplines, setDisciplines] = useState<string>('Computer Science, Data Science');
  const [careerGoals, setCareerGoals] = useState<string>('Software Engineer, Data Scientist');
  const [certifications, setCertifications] = useState<string>('');
  const [formError, setFormError] = useState<string | null>(null);

  // Quick preset loader
  const loadPreset = (presetType: 'eligible' | 'ineligible' | 'needs_review' | 'unaffordable') => {
    setFormError(null);
    if (presetType === 'eligible') {
      setSubjects([
        { subject_code: 'MATH', subject_name: 'Mathematics', score: 88, max_score: 100, grading_scale: 'percentage' },
        { subject_code: 'ENG', subject_name: 'English', score: 78, max_score: 100, grading_scale: 'percentage' },
        { subject_code: 'PHYS', subject_name: 'Physics', score: 82, max_score: 100, grading_scale: 'percentage' },
      ]);
      setEntranceExam('JEE Main');
      setEntranceRank('18500');
      setLocations('Karnataka, Maharashtra');
      setBudgetInr(800000);
      setDisciplines('Computer Science, Data Science');
      setCareerGoals('Software Engineer');
      setCertifications('');
    } else if (presetType === 'ineligible') {
      setSubjects([
        { subject_code: 'MATH', subject_name: 'Mathematics', score: 65, max_score: 100, grading_scale: 'percentage' }, // Fails 80%
        { subject_code: 'ENG', subject_name: 'English', score: 75, max_score: 100, grading_scale: 'percentage' },
        { subject_code: 'PHYS', subject_name: 'Physics', score: 70, max_score: 100, grading_scale: 'percentage' },
      ]);
      setEntranceExam('JEE Main');
      setEntranceRank('38000'); // Beyond 35000 cutoff
      setLocations('Karnataka');
      setBudgetInr(800000);
      setDisciplines('Computer Science');
      setCareerGoals('Software Engineer');
      setCertifications('');
    } else if (presetType === 'needs_review') {
      setSubjects([
        { subject_code: 'BIO', subject_name: 'Biology', score: 82, max_score: 100, grading_scale: 'percentage' },
        // Missing Chemistry: mandatory subject fact omitted, producing legitimate needs_review
      ]);
      setEntranceExam('');
      setEntranceRank('');
      setLocations('Telangana');
      setBudgetInr(600000);
      setDisciplines('Biotechnology');
      setCareerGoals('Biomedical Researcher');
      setCertifications('');
    } else if (presetType === 'unaffordable') {
      setSubjects([
        { subject_code: 'MATH', subject_name: 'Mathematics', score: 85, max_score: 100, grading_scale: 'percentage' },
        { subject_code: 'PHYS', subject_name: 'Physics', score: 80, max_score: 100, grading_scale: 'percentage' },
      ]);
      setEntranceExam('');
      setEntranceRank('');
      setLocations('Delhi NCR');
      setBudgetInr(500000); // 5L is less than Robotics 16L
      setDisciplines('Robotics');
      setCareerGoals('Robotics Engineer');
      setCertifications('');
    }
  };

  const handleAddSubject = () => {
    setSubjects([
      ...subjects,
      { subject_code: '', subject_name: '', score: 0, max_score: 100, grading_scale: 'percentage' },
    ]);
  };

  const handleRemoveSubject = (index: number) => {
    setSubjects(subjects.filter((_, i) => i !== index));
  };

  const handleSubjectChange = (index: number, field: keyof SubjectScoreDto, value: unknown) => {
    const updated = [...subjects];
    updated[index] = { ...updated[index], [field]: value };
    setSubjects(updated);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    // Basic Validation
    if (subjects.length === 0) {
      setFormError('Please provide at least one subject score.');
      return;
    }

    for (const sub of subjects) {
      if (!sub.subject_code.trim()) {
        setFormError('All subjects must have a valid subject code.');
        return;
      }
      if (sub.score < 0 || sub.max_score! <= 0) {
        setFormError('Subject scores must be non-negative and max score must be positive.');
        return;
      }
    }

    if (budgetInr < 0) {
      setFormError('Total education budget cannot be negative.');
      return;
    }

    const rankNum = entranceRank.trim() ? parseInt(entranceRank, 10) : undefined;
    if (rankNum !== undefined && (isNaN(rankNum) || rankNum < 1)) {
      setFormError('Entrance rank must be a positive integer.');
      return;
    }

    const payload: StudentProfileRequest = {
      subject_scores: subjects,
      entrance_exam_name: entranceExam.trim() || undefined,
      entrance_rank: rankNum,
      preferred_locations: locations
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
      total_budget_inr: budgetInr,
      preferred_disciplines: disciplines
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
      career_goals: careerGoals
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
      certifications: certifications
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
    };

    onSubmit(payload);
  };

  const formattedBudget = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(budgetInr || 0);

  return (
    <form onSubmit={handleSubmit} className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
      {/* Header and Preset Buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-cyan-400" aria-hidden="true" />
            Student Academic Profile Input
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Input verified grades, entrance exams, and constraints for deterministic evaluation.
          </p>
        </div>

        {/* Demo Presets */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          <span className="text-slate-400 mr-1 flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" aria-hidden="true" /> Demo Presets:
          </span>
          <button
            type="button"
            onClick={() => loadPreset('eligible')}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-emerald-300 border border-emerald-900/60 transition-colors"
          >
            Eligible
          </button>
          <button
            type="button"
            onClick={() => loadPreset('ineligible')}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-rose-300 border border-rose-900/60 transition-colors"
          >
            Ineligible
          </button>
          <button
            type="button"
            onClick={() => loadPreset('needs_review')}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-amber-300 border border-amber-900/60 transition-colors"
          >
            Needs Review
          </button>
          <button
            type="button"
            onClick={() => loadPreset('unaffordable')}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-cyan-900/60 transition-colors"
          >
            Unaffordable
          </button>
        </div>
      </div>

      {formError && (
        <div className="mt-4 p-3 rounded bg-rose-950/60 border border-rose-800 text-rose-200 text-xs" role="alert">
          {formError}
        </div>
      )}

      {/* Subject Scores Section */}
      <div className="mt-5">
        <div className="flex items-center justify-between mb-2">
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Academic Subject Scores (Class 12 / Higher Secondary)
          </label>
          <button
            type="button"
            onClick={handleAddSubject}
            className="inline-flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300 font-medium"
          >
            <Plus className="w-3.5 h-3.5" aria-hidden="true" /> Add Subject
          </button>
        </div>

        <div className="space-y-2">
          {subjects.map((sub, idx) => (
            <div key={idx} className="grid grid-cols-12 gap-2 items-center bg-slate-950 p-2.5 rounded-lg border border-slate-800/80">
              <div className="col-span-3 sm:col-span-2">
                <input
                  type="text"
                  placeholder="Code (e.g. MATH)"
                  value={sub.subject_code}
                  onChange={(e) => handleSubjectChange(idx, 'subject_code', e.target.value.toUpperCase())}
                  className="w-full text-xs font-mono bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-white focus:outline-none focus:ring-1 focus:ring-cyan-500 uppercase"
                  required
                />
              </div>

              <div className="col-span-4 sm:col-span-4">
                <input
                  type="text"
                  placeholder="Subject Name"
                  value={sub.subject_name}
                  onChange={(e) => handleSubjectChange(idx, 'subject_name', e.target.value)}
                  className="w-full text-xs bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-white focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  required
                />
              </div>

              <div className="col-span-2 sm:col-span-2">
                <input
                  type="number"
                  placeholder="Score"
                  step="0.1"
                  value={sub.score}
                  onChange={(e) => handleSubjectChange(idx, 'score', parseFloat(e.target.value) || 0)}
                  className="w-full text-xs font-mono bg-slate-900 border border-slate-700 rounded px-2 py-1.5 text-white focus:outline-none focus:ring-1 focus:ring-cyan-500 text-right"
                  required
                />
              </div>

              <div className="col-span-2 sm:col-span-3">
                <select
                  value={sub.grading_scale}
                  onChange={(e) => handleSubjectChange(idx, 'grading_scale', e.target.value)}
                  className="w-full text-xs bg-slate-900 border border-slate-700 rounded px-2 py-1.5 text-white focus:outline-none focus:ring-1 focus:ring-cyan-500"
                >
                  <option value="percentage">Percentage (%)</option>
                  <option value="cbse_10_point">CBSE 10-Point (CGPA)</option>
                  <option value="unrecognized">Other / Unverified</option>
                </select>
              </div>

              <div className="col-span-1 text-center">
                <button
                  type="button"
                  onClick={() => handleRemoveSubject(idx)}
                  className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                  title="Remove subject"
                  disabled={subjects.length <= 1}
                >
                  <Trash2 className="w-3.5 h-3.5" aria-hidden="true" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Entrance Exam & Rank */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-5">
        <div>
          <label htmlFor="entranceExam" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
            Entrance Examination (Optional)
          </label>
          <input
            id="entranceExam"
            type="text"
            placeholder="e.g. JEE Main, MHT-CET, KCET"
            value={entranceExam}
            onChange={(e) => setEntranceExam(e.target.value)}
            className="w-full text-xs bg-slate-950 border border-slate-800 rounded px-3 py-2 text-white focus:outline-none focus:ring-1 focus:ring-cyan-500"
          />
        </div>

        <div>
          <label htmlFor="entranceRank" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
            Entrance Exam Rank (When applicable)
          </label>
          <input
            id="entranceRank"
            type="number"
            placeholder="e.g. 18500"
            value={entranceRank}
            onChange={(e) => setEntranceRank(e.target.value)}
            className="w-full text-xs font-mono bg-slate-950 border border-slate-800 rounded px-3 py-2 text-white focus:outline-none focus:ring-1 focus:ring-cyan-500"
          />
        </div>
      </div>

      {/* Budget & Locations */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
        <div>
          <label htmlFor="budgetInr" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5 flex items-center justify-between">
            <span>Total Education Budget (INR)</span>
            <span className="text-cyan-400 font-mono font-bold">₹{formattedBudget}</span>
          </label>
          <div className="relative">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              ₹
            </span>
            <input
              id="budgetInr"
              type="number"
              step="10000"
              value={budgetInr}
              onChange={(e) => setBudgetInr(parseFloat(e.target.value) || 0)}
              className="w-full text-xs font-mono pl-7 bg-slate-950 border border-slate-800 rounded px-3 py-2 text-white focus:outline-none focus:ring-1 focus:ring-cyan-500"
              required
            />
          </div>
          <span className="text-[10px] text-slate-500 mt-1 block">
            Covers total duration tuition comparison (cost basis: tuition_only_total).
          </span>
        </div>

        <div>
          <label htmlFor="locations" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5 flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
            Preferred States / Locations
          </label>
          <input
            id="locations"
            type="text"
            placeholder="e.g. Karnataka, Maharashtra, Delhi NCR"
            value={locations}
            onChange={(e) => setLocations(e.target.value)}
            className="w-full text-xs bg-slate-950 border border-slate-800 rounded px-3 py-2 text-white focus:outline-none focus:ring-1 focus:ring-cyan-500"
          />
        </div>
      </div>

      {/* Disciplines, Career Goals & Certifications */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">
        <div>
          <label htmlFor="disciplines" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
            Preferred Disciplines
          </label>
          <input
            id="disciplines"
            type="text"
            placeholder="e.g. Computer Science, Robotics"
            value={disciplines}
            onChange={(e) => setDisciplines(e.target.value)}
            className="w-full text-xs bg-slate-950 border border-slate-800 rounded px-3 py-2 text-white focus:outline-none focus:ring-1 focus:ring-cyan-500"
          />
        </div>

        <div>
          <label htmlFor="careerGoals" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
            Target Career Goals
          </label>
          <input
            id="careerGoals"
            type="text"
            placeholder="e.g. Software Engineer, Data Scientist"
            value={careerGoals}
            onChange={(e) => setCareerGoals(e.target.value)}
            className="w-full text-xs bg-slate-950 border border-slate-800 rounded px-3 py-2 text-white focus:outline-none focus:ring-1 focus:ring-cyan-500"
          />
        </div>

        <div>
          <label htmlFor="certifications" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5 flex items-center gap-1">
            <Award className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
            Certifications (If any)
          </label>
          <input
            id="certifications"
            type="text"
            placeholder="e.g. Laboratory Safety Training Certification"
            value={certifications}
            onChange={(e) => setCertifications(e.target.value)}
            className="w-full text-xs bg-slate-950 border border-slate-800 rounded px-3 py-2 text-white focus:outline-none focus:ring-1 focus:ring-cyan-500"
          />
        </div>
      </div>

      {/* Submit Button */}
      <div className="mt-6 pt-4 border-t border-slate-800 flex items-center justify-end">
        <button
          type="submit"
          disabled={isLoading}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-gradient-to-r from-cyan-500 to-violet-600 hover:from-cyan-400 hover:to-violet-500 text-white font-medium text-xs shadow-lg shadow-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all focus:outline-none focus:ring-2 focus:ring-cyan-400"
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Evaluating Rules & Graph...</span>
            </>
          ) : (
            <>
              <Send className="w-3.5 h-3.5" aria-hidden="true" />
              <span>Run Deterministic Evaluation</span>
            </>
          )}
        </button>
      </div>
    </form>
  );
};
