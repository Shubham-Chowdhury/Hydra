import React, { useState, useEffect } from 'react';
import {
  UserCheck,
  ShieldCheck,
  Award,
  AlertTriangle,
  HelpCircle,
  CheckCircle2,
  Network,
  Layers,
  Database,
  ArrowRight,
  Banknote,
  BookOpen,
  Compass,
  Copy,
  Check,
  RefreshCw,
  MapPin,
} from 'lucide-react';
import type { StudentProfileRequest, TwinSnapshotDto, StudentTwinResponse } from '../../api/types';
import { hydraApi, ApiError } from '../../api/client';

const PRESET_PROFILES: { label: string; description: string; data: StudentProfileRequest }[] = [
  {
    label: 'Complete STEM Candidate',
    description: 'All 5 dimensions complete with JEE rank & full budget',
    data: {
      student_id: 'STU_IND_2026_01',
      subject_scores: [
        { subject_code: 'MATH', subject_name: 'Mathematics', score: 92, max_score: 100, grading_scale: 'percentage' },
        { subject_code: 'PHYS', subject_name: 'Physics', score: 88, max_score: 100, grading_scale: 'percentage' },
        { subject_code: 'CHEM', subject_name: 'Chemistry', score: 84, max_score: 100, grading_scale: 'percentage' },
        { subject_code: 'ENG', subject_name: 'English', score: 80, max_score: 100, grading_scale: 'percentage' },
      ],
      entrance_exam_name: 'JEE Main',
      entrance_rank: 4200,
      total_budget_inr: 800000,
      preferred_locations: ['Karnataka', 'Maharashtra'],
      preferred_disciplines: ['Computer Science'],
      career_goals: ['Software Engineer', 'Systems Architect'],
      certifications: ['Python Programming Basics'],
    },
  },
  {
    label: 'CBSE CGPA (Historical CCE 2016)',
    description: 'Historical Class X CCE (2009-2017) converted via authorized CBSE indicative 9.5 rule',
    data: {
      student_id: 'STU_CBSE_HIST_02',
      subject_scores: [
        {
          subject_code: 'MATH',
          subject_name: 'Mathematics',
          score: 9.2,
          max_score: 10.0,
          grading_scale: 'cbse_10_point',
          board: 'CBSE',
          conversion_policy_id: 'CBSE_HISTORICAL_CCE_INDICATIVE',
          examination_year: 2016,
        },
        {
          subject_code: 'PHYS',
          subject_name: 'Physics',
          score: 8.8,
          max_score: 10.0,
          grading_scale: 'cbse_10_point',
          board: 'CBSE',
          conversion_policy_id: 'CBSE_HISTORICAL_CCE_INDICATIVE',
          examination_year: 2016,
        },
        {
          subject_code: 'CHEM',
          subject_name: 'Chemistry',
          score: 9.0,
          max_score: 10.0,
          grading_scale: 'cbse_10_point',
          board: 'CBSE',
          conversion_policy_id: 'CBSE_HISTORICAL_CCE_INDICATIVE',
          examination_year: 2016,
        },
      ],
      entrance_exam_name: 'JEE Main',
      entrance_rank: 6100,
      total_budget_inr: 750000,
      preferred_locations: ['Telangana'],
      preferred_disciplines: ['Data Science'],
      career_goals: ['Data Scientist'],
      certifications: [],
    },
  },
  {
    label: 'Biotechnology (No Entrance Exam)',
    description: 'High biology marks, no entrance exam (optional for biotech)',
    data: {
      student_id: 'STU_BIO_2026_03',
      subject_scores: [
        { subject_code: 'BIO', subject_name: 'Biology', score: 86, max_score: 100, grading_scale: 'percentage' },
        { subject_code: 'CHEM', subject_name: 'Chemistry', score: 82, max_score: 100, grading_scale: 'percentage' },
        { subject_code: 'ENG', subject_name: 'English', score: 78, max_score: 100, grading_scale: 'percentage' },
      ],
      entrance_exam_name: undefined,
      entrance_rank: undefined,
      total_budget_inr: 650000,
      preferred_locations: ['Telangana'],
      preferred_disciplines: ['Biotechnology'],
      career_goals: ['Biomedical Researcher'],
      certifications: ['Molecular Biology Summer Lab'],
    },
  },
  {
    label: 'Pan-India Candidate (Anywhere in India)',
    description: 'Explicit anywhere-in-India geographic scope without location constraints',
    data: {
      student_id: 'STU_PAN_INDIA_06',
      subject_scores: [
        { subject_code: 'MATH', subject_name: 'Mathematics', score: 91, max_score: 100, grading_scale: 'percentage' },
        { subject_code: 'PHYS', subject_name: 'Physics', score: 87, max_score: 100, grading_scale: 'percentage' },
        { subject_code: 'CHEM', subject_name: 'Chemistry', score: 83, max_score: 100, grading_scale: 'percentage' },
      ],
      entrance_exam_name: 'JEE Main',
      entrance_rank: 5100,
      total_budget_inr: 850000,
      preferred_locations: ['anywhere in india'],
      preferred_disciplines: ['Computer Science'],
      career_goals: ['Software Engineer'],
      certifications: [],
    },
  },
  {
    label: 'Partial (Missing Budget & Exam)',
    description: 'Partially specified profile demonstrating unstated facts',
    data: {
      student_id: 'STU_PARTIAL_2026_04',
      subject_scores: [
        { subject_code: 'MATH', subject_name: 'Mathematics', score: 78, max_score: 100, grading_scale: 'percentage' },
        { subject_code: 'PHYS', subject_name: 'Physics', score: 72, max_score: 100, grading_scale: 'percentage' },
      ],
      entrance_exam_name: 'JEE Main',
      entrance_rank: undefined,
      total_budget_inr: 0,
      preferred_locations: [],
      preferred_disciplines: ['Engineering'],
      career_goals: [],
      certifications: [],
    },
  },
  {
    label: 'Needs Review (Unsupported US GPA)',
    description: 'Unsupported 4-point GPA flagged safely for manual audit',
    data: {
      student_id: 'STU_INTL_2026_05',
      subject_scores: [
        { subject_code: 'MATH', subject_name: 'Mathematics', score: 3.8, max_score: 4.0, grading_scale: 'us_4_point_gpa' },
        { subject_code: 'PHYS', subject_name: 'Physics', score: 3.6, max_score: 4.0, grading_scale: 'us_4_point_gpa' },
        { subject_code: 'ENG', subject_name: 'English', score: 3.9, max_score: 4.0, grading_scale: 'us_4_point_gpa' },
      ],
      entrance_exam_name: 'SAT',
      entrance_rank: 1450,
      total_budget_inr: 1200000,
      preferred_locations: ['Karnataka'],
      preferred_disciplines: ['Computer Science'],
      career_goals: ['Software Engineer'],
      certifications: [],
    },
  },
];

export const StudentDigitalTwinView: React.FC = () => {
  const [activePresetIndex, setActivePresetIndex] = useState<number>(0);
  const [twinSnapshot, setTwinSnapshot] = useState<TwinSnapshotDto | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedFingerprint, setCopiedFingerprint] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'academics' | 'pathways' | 'frame' | 'provenance'>('overview');

  const constructTwin = async (profileData: StudentProfileRequest) => {
    setIsLoading(true);
    setError(null);
    try {
      const res: StudentTwinResponse = await hydraApi.constructTwin(profileData);
      setTwinSnapshot(res.snapshot);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`Failed to construct twin (${err.status}): ${err.message}`);
      } else if (err instanceof Error) {
        setError(`Connection failed: ${err.message}`);
      } else {
        setError('Unexpected error constructing digital twin.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    constructTwin(PRESET_PROFILES[0].data);
  }, []);

  const handleSelectPreset = (idx: number) => {
    setActivePresetIndex(idx);
    constructTwin(PRESET_PROFILES[idx].data);
  };

  const handleCopyFingerprint = (fp: string) => {
    navigator.clipboard.writeText(fp);
    setCopiedFingerprint(true);
    setTimeout(() => setCopiedFingerprint(false), 2000);
  };

  const getCompletenessBadge = (state: string) => {
    switch (state.toLowerCase()) {
      case 'complete':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-700/60">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            Complete
          </span>
        );
      case 'partial':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-950/80 text-amber-300 border border-amber-700/60">
            <HelpCircle className="w-3.5 h-3.5 text-amber-400" />
            Partial
          </span>
        );
      case 'needs_review':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-950/80 text-rose-300 border border-rose-700/60">
            <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
            Needs Review
          </span>
        );
    }
  };

  const getOriginBadge = (category: string) => {
    switch (category) {
      case 'user_provided':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-blue-950/80 text-blue-300 border border-blue-800">
            USER_PROVIDED
          </span>
        );
      case 'deterministically_derived':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-purple-950/80 text-purple-300 border border-purple-800">
            DETERMINISTICALLY_DERIVED
          </span>
        );
      case 'external_verified':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-emerald-950/80 text-emerald-300 border border-emerald-800">
            EXTERNAL_VERIFIED
          </span>
        );
      case 'unknown':
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-slate-800 text-slate-400 border border-slate-700">
            UNKNOWN
          </span>
        );
    }
  };

  const getGeographicBadge = (prefType?: string) => {
    switch (prefType) {
      case 'preferred_locations':
        return (
          <span className="px-2.5 py-0.5 rounded text-[11px] font-mono font-semibold bg-cyan-950/80 text-cyan-300 border border-cyan-800">
            PREFERRED_LOCATIONS
          </span>
        );
      case 'anywhere_in_india':
        return (
          <span className="px-2.5 py-0.5 rounded text-[11px] font-mono font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-800">
            ANYWHERE_IN_INDIA
          </span>
        );
      case 'not_provided':
      default:
        return (
          <span className="px-2.5 py-0.5 rounded text-[11px] font-mono font-semibold bg-slate-800 text-slate-400 border border-slate-700">
            NOT_PROVIDED (NEUTRAL)
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Mission Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900/90 to-cyan-950/40 border border-cyan-800/40 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-950 border border-cyan-800 text-cyan-300 text-xs font-mono mb-2">
              <UserCheck className="w-3.5 h-3.5 text-cyan-400" />
              Phase 4: Student Digital Twin Agent
            </div>
            <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              Student Digital Twin Representation
            </h2>
            <p className="mt-1 text-slate-300 text-sm max-w-2xl leading-relaxed">
              Symbolic representation distinguishing user-supplied facts, deterministic mathematical
              normalizations, and unstated fields with zero speculative hallucination.
            </p>
          </div>

          {twinSnapshot && (
            <div className="flex flex-col items-start md:items-end gap-1.5 p-3 rounded-xl bg-slate-950/60 border border-slate-800">
              <div className="text-xs text-slate-400">Twin Identifier & Fingerprint</div>
              <div className="flex items-center gap-2 font-mono text-xs text-cyan-300">
                <span className="font-semibold">{twinSnapshot.twin_id}</span>
                <button
                  type="button"
                  onClick={() => handleCopyFingerprint(twinSnapshot.profile_fingerprint)}
                  className="p-1 hover:bg-slate-800 rounded transition text-slate-400 hover:text-slate-200"
                  title="Copy SHA-256 fingerprint"
                >
                  {copiedFingerprint ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
              {twinSnapshot.snapshot_id && (
                <div className="text-[10px] text-cyan-400/80 font-mono">
                  Snap: {twinSnapshot.snapshot_id}
                </div>
              )}
              <div className="text-[10px] text-slate-500 font-mono truncate max-w-[200px]" title={twinSnapshot.profile_fingerprint}>
                SHA-256: {twinSnapshot.profile_fingerprint.slice(0, 16)}…
              </div>
            </div>
          )}
        </div>

        {/* Preset Selector */}
        <div className="mt-6 pt-5 border-t border-slate-800">
          <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
            Load Candidate Profile Fixtures:
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2.5">
            {PRESET_PROFILES.map((preset, idx) => (
              <button
                key={preset.label}
                type="button"
                onClick={() => handleSelectPreset(idx)}
                className={`p-3 rounded-xl text-left border transition-all ${
                  activePresetIndex === idx
                    ? 'bg-cyan-950/90 border-cyan-500 text-cyan-200 shadow-md ring-1 ring-cyan-500/30'
                    : 'bg-slate-950/40 border-slate-800/80 text-slate-400 hover:bg-slate-900 hover:text-slate-200'
                }`}
              >
                <div className="font-semibold text-xs text-white">{preset.label}</div>
                <div className="text-[11px] text-slate-400 mt-1 line-clamp-2 leading-snug">
                  {preset.description}
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error Notice */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/70 border border-rose-800 text-rose-200 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800">
          <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin mx-auto mb-3" />
          <p className="text-slate-300 text-sm">Constructing Student Digital Twin snapshot...</p>
        </div>
      )}

      {twinSnapshot && !isLoading && (
        <div className="space-y-6">
          {/* Sub-tab Navigation */}
          <div className="flex border-b border-slate-800 gap-1 overflow-x-auto pb-1 text-xs font-medium">
            <button
              type="button"
              onClick={() => setActiveTab('overview')}
              className={`px-4 py-2 rounded-t-lg transition flex items-center gap-2 ${
                activeTab === 'overview'
                  ? 'bg-slate-850 text-cyan-300 border-b-2 border-cyan-400 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <UserCheck className="w-4 h-4" />
              Completeness Overview
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('academics')}
              className={`px-4 py-2 rounded-t-lg transition flex items-center gap-2 ${
                activeTab === 'academics'
                  ? 'bg-slate-850 text-cyan-300 border-b-2 border-cyan-400 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <BookOpen className="w-4 h-4" />
              Academic Identity & Normalization
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('pathways')}
              className={`px-4 py-2 rounded-t-lg transition flex items-center gap-2 ${
                activeTab === 'pathways'
                  ? 'bg-slate-850 text-cyan-300 border-b-2 border-cyan-400 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Network className="w-4 h-4" />
              Semantic Pathways ({twinSnapshot.semantic_network_pathways.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('frame')}
              className={`px-4 py-2 rounded-t-lg transition flex items-center gap-2 ${
                activeTab === 'frame'
                  ? 'bg-slate-850 text-cyan-300 border-b-2 border-cyan-400 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="w-4 h-4" />
              Symbolic Frame Representation
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('provenance')}
              className={`px-4 py-2 rounded-t-lg transition flex items-center gap-2 ${
                activeTab === 'provenance'
                  ? 'bg-slate-850 text-cyan-300 border-b-2 border-cyan-400 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Database className="w-4 h-4" />
              Fact Provenance Table ({Object.keys(twinSnapshot.facts).length})
            </button>
          </div>

          {/* TAB 1: OVERVIEW */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Overall Completeness Banner */}
              <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="text-xs uppercase font-mono tracking-wider text-slate-400">
                    Overall Profile Completeness Status
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xl font-bold text-white capitalize">
                      {twinSnapshot.overall_completeness.replace('_', ' ')}
                    </span>
                    {getCompletenessBadge(twinSnapshot.overall_completeness)}
                  </div>
                  <p className="text-xs text-slate-400">
                    Calculated independently across 5 dimensions. Profile completeness does NOT dictate programme eligibility.
                  </p>
                </div>
                <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                  <span>Student ID:</span>
                  <span className="text-white font-semibold">{twinSnapshot.student_id || 'Anonymous'}</span>
                </div>
              </div>

              {/* 5 Dimensional Completeness Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(twinSnapshot.completeness_dimensions).map(([dimName, dim]) => (
                  <div key={dimName} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <span className="text-xs uppercase font-mono font-bold text-slate-300">
                          {dimName.replace(/_/g, ' ')}
                        </span>
                        {getCompletenessBadge(dim.state)}
                      </div>
                      <p className="text-xs text-slate-400 leading-relaxed mb-3">
                        {dim.explanation}
                      </p>
                    </div>

                    <div className="text-[11px] space-y-1 pt-2 border-t border-slate-800/80">
                      {dim.available_facts.length > 0 && (
                        <div className="text-slate-400">
                          <span className="text-emerald-400 font-semibold">Available:</span> {dim.available_facts.join(', ')}
                        </div>
                      )}
                      {dim.missing_facts.length > 0 && (
                        <div className="text-slate-400">
                          <span className="text-amber-400 font-semibold">Missing:</span> {dim.missing_facts.join(', ')}
                        </div>
                      )}
                      {dim.review_facts.length > 0 && (
                        <div className="text-slate-400">
                          <span className="text-rose-400 font-semibold">Under Review:</span> {dim.review_facts.join(', ')}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Missing Information & Validation Findings */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-3">
                    <HelpCircle className="w-4 h-4 text-amber-400" />
                    Missing Profile Information
                  </h3>
                  {twinSnapshot.missing_information.length > 0 ? (
                    <ul className="space-y-2 text-xs text-slate-300">
                      {twinSnapshot.missing_information.map((item, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-amber-400 font-mono">•</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <div className="text-xs text-emerald-400 flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4" />
                      No critical missing information detected.
                    </div>
                  )}
                </div>

                <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-3">
                    <ShieldCheck className="w-4 h-4 text-cyan-400" />
                    Validation & Derivation Audit Findings
                  </h3>
                  {twinSnapshot.validation_findings.length > 0 ? (
                    <ul className="space-y-2 text-xs text-slate-300">
                      {twinSnapshot.validation_findings.map((item, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-cyan-400 font-mono">•</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <div className="text-xs text-slate-400">
                      All reported facts satisfy structural schema criteria.
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: ACADEMIC IDENTITY */}
          {activeTab === 'academics' && (
            <div className="space-y-6">
              {/* Score-Based Academic Highlights */}
              {(twinSnapshot.academic_identity.score_based_academic_highlights || twinSnapshot.academic_identity.academic_strengths || []).length > 0 && (
                <div className="p-4 rounded-xl bg-cyan-950/40 border border-cyan-800/60 space-y-2">
                  <div className="text-xs uppercase font-mono tracking-wider text-cyan-300 flex items-center gap-1.5">
                    <Award className="w-4 h-4 text-cyan-400" />
                    Score-Based Academic Highlights (Threshold ≥ {twinSnapshot.academic_identity.highlight_threshold || 75.0}%, Heuristic v{twinSnapshot.academic_identity.highlight_heuristic_version || '1.0'})
                  </div>
                  <p className="text-[11px] text-slate-400 italic">
                    Disclaimer: Indicates high relative performance on reported subject scores exceeding Hydra's heuristic threshold (≥ 75.0%). This reflects recorded grades, NOT general cognitive aptitude or intelligence.
                  </p>
                  <div className="flex flex-wrap gap-2 pt-1">
                    {(twinSnapshot.academic_identity.score_based_academic_highlights || twinSnapshot.academic_identity.academic_strengths).map((str, idx) => (
                      <span key={idx} className="px-3 py-1 rounded-full text-xs font-semibold bg-cyan-900/60 text-cyan-200 border border-cyan-700">
                        {str}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Subject Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {twinSnapshot.academic_identity.subject_scores.map((subj) => (
                  <div key={subj.subject_code} className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="font-bold text-sm text-white">{subj.subject_name}</div>
                        <div className="text-xs font-mono text-cyan-400">{subj.subject_code}</div>
                      </div>
                      {getCompletenessBadge(subj.conversion_status)}
                    </div>

                    <div className="space-y-1.5 text-xs">
                      <div className="flex justify-between text-slate-400">
                        <span>Reported Score:</span>
                        <span className="text-white font-mono">{subj.original_score} / {subj.max_score}</span>
                      </div>
                      <div className="flex justify-between text-slate-400">
                        <span>Grading Scale:</span>
                        <span className="font-mono text-slate-300">{subj.grading_scale}</span>
                      </div>
                      {subj.board && (
                        <div className="flex justify-between text-slate-400">
                          <span>Board:</span>
                          <span className="font-mono text-slate-300">{subj.board}</span>
                        </div>
                      )}
                      {subj.conversion_policy_id && (
                        <div className="flex justify-between text-slate-400">
                          <span>Conversion Policy:</span>
                          <span className="font-mono text-cyan-300 text-[10px]">{subj.conversion_policy_id}</span>
                        </div>
                      )}
                      <div className="flex justify-between text-slate-400 pt-1 border-t border-slate-800">
                        <span>Normalized Pct:</span>
                        <span className="font-mono font-bold text-cyan-300">
                          {subj.normalized_percentage !== null && subj.normalized_percentage !== undefined
                            ? `${subj.normalized_percentage.toFixed(2)}%`
                            : 'N/A (Review Required)'}
                        </span>
                      </div>
                      {subj.is_indicative && (
                        <div className="mt-1.5 flex items-center justify-between text-[10px] px-2 py-1 rounded bg-amber-950/80 border border-amber-800/90 text-amber-300 font-mono">
                          <span>Indicative (Explanatory Display Only)</span>
                          <span className="text-[9px] text-amber-400/80">Non-Institutional</span>
                        </div>
                      )}
                    </div>

                    <div className="text-[11px] text-slate-400 bg-slate-950 p-2 rounded border border-slate-800/80">
                      {subj.conversion_explanation}
                    </div>
                  </div>
                ))}
              </div>

              {/* Entrance Exam, Financial Constraints, & Geographic Scope */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4 border-t border-slate-800">
                <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Compass className="w-4 h-4 text-cyan-400" />
                    Entrance Examination Profile
                  </h3>
                  <div className="space-y-2 text-xs text-slate-300">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Examination Name:</span>
                      <span className="font-semibold text-white">
                        {twinSnapshot.entrance_exam_profile.exam_name || 'None Reported'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Entrance Rank:</span>
                      <span className="font-mono font-semibold text-cyan-300">
                        {twinSnapshot.entrance_exam_profile.rank ? `#${twinSnapshot.entrance_exam_profile.rank}` : 'None'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Rank Basis:</span>
                      <span className="font-mono text-slate-300">
                        {twinSnapshot.entrance_exam_profile.rank_basis || 'N/A'}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 pt-2 border-t border-slate-800 leading-relaxed">
                      {twinSnapshot.entrance_exam_profile.interpretation_notes}
                    </div>
                  </div>
                </div>

                <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Banknote className="w-4 h-4 text-emerald-400" />
                    Financial & Budget Constraints
                  </h3>
                  <div className="space-y-2 text-xs text-slate-300">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Total Education Budget:</span>
                      <span className="font-mono font-bold text-emerald-300">
                        INR {twinSnapshot.financial_constraints.total_budget_inr.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Cost Basis:</span>
                      <span className="font-mono text-slate-300">{twinSnapshot.financial_constraints.cost_basis}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Affordability Readiness:</span>
                      <span className="font-semibold text-white">
                        {twinSnapshot.financial_constraints.affordability_readiness ? 'Ready' : 'Unbudgeted'}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 pt-2 border-t border-slate-800 leading-relaxed">
                      {twinSnapshot.financial_constraints.notes}
                    </div>
                  </div>
                </div>

                <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-purple-400" />
                      Geographic Scope & Preferences
                    </h3>
                  </div>
                  <div className="space-y-2 text-xs text-slate-300">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Preference Type:</span>
                      {getGeographicBadge(twinSnapshot.geographic_preferences.preference_type)}
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Target Locations:</span>
                      <span className="font-medium text-white">
                        {twinSnapshot.geographic_preferences.preferred_locations && twinSnapshot.geographic_preferences.preferred_locations.length > 0
                          ? twinSnapshot.geographic_preferences.preferred_locations.join(', ')
                          : 'None (Unfiltered)'}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 pt-2 border-t border-slate-800 leading-relaxed">
                      {twinSnapshot.geographic_preferences.notes}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: SEMANTIC PATHWAYS */}
          {activeTab === 'pathways' && (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 text-xs text-slate-300">
                Discovered semantic connections across NetworkX graph between student career goals,
                disciplines, and academic programmes.
              </div>

              {twinSnapshot.semantic_network_pathways.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {twinSnapshot.semantic_network_pathways.map((pathway, idx) => (
                    <div key={idx} className="p-3.5 rounded-xl bg-slate-900/50 border border-slate-800 flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-white">{pathway.source}</span>
                        <ArrowRight className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                        <span className="text-cyan-300 font-medium">{pathway.target}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-950 text-cyan-300 border border-cyan-800">
                          {pathway.relationship}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-8 text-center rounded-xl bg-slate-900/30 border border-slate-800 text-slate-400 text-sm">
                  No semantic pathways discovered for the reported preferences.
                </div>
              )}
            </div>
          )}

          {/* TAB 4: SYMBOLIC FRAME */}
          {activeTab === 'frame' && (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 text-xs text-slate-300">
                Resolved frame hierarchy using Hydra's Frame-Based Knowledge Representation System.
                Shows explicit student slots merged with inherited defaults from <code className="text-cyan-300">FRAME_STUDENT_BASE</code>.
              </div>

              <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
                <div className="flex items-center justify-between text-xs font-mono pb-3 border-b border-slate-800">
                  <div className="text-white">
                    Frame ID: <span className="text-cyan-300 font-bold">{String((twinSnapshot.frame_representation as Record<string, unknown>).frame_id || '')}</span>
                  </div>
                  <div className="text-slate-400">
                    Parent: <span className="text-purple-300">{String((twinSnapshot.frame_representation as Record<string, unknown>).parent_frame_id || '')}</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  {Object.entries((twinSnapshot.frame_representation as { slots?: Record<string, { value: unknown; source_type: string; inheritance_path: string[] }> }).slots || {}).map(([slotKey, slotData]) => (
                    <div key={slotKey} className="p-3 rounded-lg bg-slate-950 border border-slate-850 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-cyan-400 font-semibold">{slotKey}</span>
                        <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                          slotData.source_type === 'inherited_default'
                            ? 'bg-purple-950 text-purple-300 border border-purple-800'
                            : 'bg-blue-950 text-blue-300 border border-blue-800'
                        }`}>
                          {slotData.source_type}
                        </span>
                      </div>
                      <div className="font-mono text-white text-xs truncate">
                        {typeof slotData.value === 'object' ? JSON.stringify(slotData.value) : String(slotData.value)}
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono">
                        Path: {slotData.inheritance_path.join(' → ')}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: FACT PROVENANCE */}
          {activeTab === 'provenance' && (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 text-xs text-slate-300">
                Auditable atomic fact records. Every attribute explicitly identifies its origin category,
                validation lifecycle status, derivation rule, and human-readable explanation.
              </div>

              <div className="overflow-x-auto rounded-xl border border-slate-800">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-900 border-b border-slate-800 text-slate-400 font-mono uppercase text-[11px]">
                      <th className="p-3">Fact Identifier</th>
                      <th className="p-3">Field Name</th>
                      <th className="p-3">Origin Category</th>
                      <th className="p-3">Status</th>
                      <th className="p-3">Derivation Rule</th>
                      <th className="p-3">Explanation</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-850">
                    {Object.values(twinSnapshot.facts).map((fact) => (
                      <tr key={fact.fact_id} className="hover:bg-slate-900/40">
                        <td className="p-3 font-mono text-cyan-300 font-medium">{fact.fact_id}</td>
                        <td className="p-3 font-mono text-slate-300">{fact.field_name}</td>
                        <td className="p-3">{getOriginBadge(fact.origin_category)}</td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                            fact.validation_status === 'valid'
                              ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                              : fact.validation_status === 'needs_review'
                              ? 'bg-amber-950 text-amber-300 border border-amber-800'
                              : 'bg-rose-950 text-rose-300 border border-rose-800'
                          }`}>
                            {fact.validation_status}
                          </span>
                        </td>
                        <td className="p-3 font-mono text-purple-300">{fact.derivation_rule || '—'}</td>
                        <td className="p-3 text-slate-300 max-w-xs">{fact.explanation}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
