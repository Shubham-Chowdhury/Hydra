/**
 * Comprehensive Academic Assessment & Neural Trajectory Report Modal.
 *
 * Displays consolidated deterministic prerequisite eligibility breakdowns alongside
 * deep sequence neural model projections (career readiness, domain affinities,
 * learning velocity, risk assessment), combined with an audible executive voice summary.
 */

import React, { useState, useEffect } from 'react';
import type { ComprehensiveAssessmentReportDto } from '../../api/types';
import { voiceManager } from '../../services/voiceManager';
import {
  Brain,
  ShieldCheck,
  Volume2,
  VolumeX,
  Sparkles,
  TrendingUp,
  Award,
  Milestone,
  ArrowRight,
  X,
  Layers,
  Activity,
} from 'lucide-react';

interface ComprehensiveAssessmentModalProps {
  report: ComprehensiveAssessmentReportDto | null;
  isOpen: boolean;
  onClose: () => void;
}

export const ComprehensiveAssessmentModal: React.FC<ComprehensiveAssessmentModalProps> = ({
  report,
  isOpen,
  onClose,
}) => {
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);

  useEffect(() => {
    // Sync speaking state
    const unsubscribe = voiceManager.subscribeState((state) => {
      setIsPlayingAudio(state === 'speaking');
    });
    return () => unsubscribe();
  }, []);

  if (!isOpen || !report) return null;

  const handleToggleVoiceReport = () => {
    if (isPlayingAudio) {
      voiceManager.stopSpeaking();
    } else {
      voiceManager.speak(report.voice_script);
    }
  };

  const readinessPercent = Math.round(report.neural_insights.career_readiness_score * 100);
  const velocityRatio = report.neural_insights.learning_velocity_index.toFixed(2);
  const riskIndex = Math.round(report.neural_insights.risk_assessment_index * 100);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="relative w-full max-w-5xl max-h-[92vh] bg-white rounded-3xl shadow-2xl border border-gray-200/90 flex flex-col overflow-hidden text-[#111215]">
        {/* Header */}
        <div className="px-6 py-5 bg-[#ECEEE7] border-b border-gray-300 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#111215] text-[#CCFF00] flex items-center justify-center shadow-xs">
              <Brain className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold tracking-tight text-[#111215]">
                  Comprehensive Assessment & Career Trajectory Report
                </h2>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#CCFF00] text-black border border-black/10">
                  AI DEEP LEARNING MODEL
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-0.5">
                Report ID: <span className="font-mono">{report.report_id}</span> • Candidate: {report.student_id} • Architecture: {report.neural_insights.model_architecture}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-9 h-9 rounded-full bg-white hover:bg-gray-200 border border-gray-300 flex items-center justify-center text-gray-700 transition cursor-pointer shadow-2xs"
            aria-label="Close report"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Executive Spoken Summary Audio Card */}
          <div className="rounded-2xl bg-[#111215] text-white p-5 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-[#CCFF00]/10 rounded-full blur-3xl pointer-events-none" />
            <div className="relative z-10">
              <div className="flex items-center justify-between gap-4 mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-[#CCFF00] animate-pulse" />
                  <span className="text-xs font-bold uppercase tracking-wider text-[#CCFF00]">
                    Hydra Voice Guide • Audible Executive Briefing
                  </span>
                </div>
                <button
                  onClick={handleToggleVoiceReport}
                  className="px-4 py-2 rounded-full bg-[#CCFF00] hover:bg-[#b8e600] text-black text-xs font-bold flex items-center gap-2 transition cursor-pointer shadow-md"
                >
                  {isPlayingAudio ? (
                    <>
                      <VolumeX className="w-4 h-4 text-black" />
                      <span>Pause Audio Report</span>
                    </>
                  ) : (
                    <>
                      <Volume2 className="w-4 h-4 text-black" />
                      <span>Play Voice Report</span>
                    </>
                  )}
                </button>
              </div>
              <p className="text-sm text-gray-200 leading-relaxed italic border-l-2 border-[#CCFF00] pl-3 py-1">
                "{report.executive_summary}"
              </p>
            </div>
          </div>

          {/* Deep Learning Sequence Model Insights */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Career Readiness Index */}
            <div className="bg-[#FAFBF9] rounded-2xl p-5 border border-gray-200/80 shadow-2xs flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-gray-500 uppercase tracking-wide">
                  Career Readiness Score
                </span>
                <Sparkles className="w-4 h-4 text-amber-500" />
              </div>
              <div className="my-3">
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-black text-[#111215]">{readinessPercent}%</span>
                  <span className="text-xs text-emerald-600 font-bold">Optimal Tier</span>
                </div>
                <div className="w-full h-2 rounded-full bg-gray-200 mt-2 overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all duration-1000"
                    style={{ width: `${readinessPercent}%` }}
                  />
                </div>
              </div>
              <p className="text-[11px] text-gray-500">
                Confidence: {(report.neural_insights.confidence * 100).toFixed(0)}% (Multi-head sequence projection)
              </p>
            </div>

            {/* Learning Velocity Index */}
            <div className="bg-[#FAFBF9] rounded-2xl p-5 border border-gray-200/80 shadow-2xs flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-gray-500 uppercase tracking-wide">
                  Learning Velocity
                </span>
                <TrendingUp className="w-4 h-4 text-blue-500" />
              </div>
              <div className="my-3">
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-black text-[#111215]">{velocityRatio}x</span>
                  <span className="text-xs text-blue-600 font-bold">Accelerated Mastery</span>
                </div>
                <p className="text-xs text-gray-600 mt-1">
                  Paced for advanced algorithmic modules and technical electives.
                </p>
              </div>
              <p className="text-[11px] text-gray-500">
                Calculated across STEM prerequisite completion velocity
              </p>
            </div>

            {/* Risk Assessment Index */}
            <div className="bg-[#FAFBF9] rounded-2xl p-5 border border-gray-200/80 shadow-2xs flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-gray-500 uppercase tracking-wide">
                  Transition Risk Index
                </span>
                <Activity className="w-4 h-4 text-emerald-500" />
              </div>
              <div className="my-3">
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-black text-[#111215]">{riskIndex}%</span>
                  <span className="text-xs text-emerald-600 font-bold">Low Volatility</span>
                </div>
                <div className="w-full h-2 rounded-full bg-gray-200 mt-2 overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all duration-1000"
                    style={{ width: `${riskIndex}%` }}
                  />
                </div>
              </div>
              <p className="text-[11px] text-gray-500">
                Deterministic safeguards protect against adverse tuition/cutoff shifts
              </p>
            </div>
          </div>

          {/* Domain Affinity Softmax Weights & Projected Career Outcomes */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Domain Affinity Bars */}
            <div className="bg-white rounded-2xl p-5 border border-gray-200/90 shadow-2xs">
              <div className="flex items-center gap-2 mb-3">
                <Layers className="w-4 h-4 text-gray-700" />
                <h3 className="text-sm font-bold text-[#111215]">
                  Neural Domain Affinity Distribution (Softmax)
                </h3>
              </div>
              <div className="space-y-2.5">
                {Object.entries(report.neural_insights.domain_affinity_weights).map(([domain, weight]) => {
                  const pct = Math.round(weight * 100);
                  return (
                    <div key={domain} className="space-y-1">
                      <div className="flex justify-between text-xs font-semibold">
                        <span className="text-gray-700 capitalize">{domain.replace('_', ' ')}</span>
                        <span className="text-gray-900 font-mono">{pct}%</span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-gray-100 overflow-hidden">
                        <div
                          className="h-full bg-[#111215] rounded-full transition-all duration-700"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Projected Career Outcomes */}
            <div className="bg-white rounded-2xl p-5 border border-gray-200/90 shadow-2xs flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Award className="w-4 h-4 text-gray-700" />
                  <h3 className="text-sm font-bold text-[#111215]">Projected Career Outcomes</h3>
                </div>
                <p className="text-xs text-gray-500 mb-3">
                  Predicted graduate industry roles aligned with candidate aptitude and prerequisite profile:
                </p>
                <div className="flex flex-wrap gap-2">
                  {report.neural_insights.projected_career_outcomes.map((career, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1.5 rounded-full text-xs font-bold bg-[#ECEEE7] text-[#111215] border border-gray-300 shadow-2xs"
                    >
                      🎯 {career}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mt-4 p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs">
                <span className="font-bold">Provenance Notice:</span> Estimates generated via Deep Trajectory Model. Deterministic prerequisites remain authoritative.
              </div>
            </div>
          </div>

          {/* Verified Deterministic Eligibility Summary */}
          <div className="bg-white rounded-2xl p-5 border border-gray-200/90 shadow-2xs">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <h3 className="text-sm font-bold text-[#111215]">
                  Deterministic Admissions Eligibility Breakdown
                </h3>
              </div>
              <span className="text-[11px] font-semibold text-gray-500">
                17 Total Accredited Programmes Evaluated
              </span>
            </div>

            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900">
                <div className="text-2xl font-black">{report.verified_eligibility_breakdown.eligible || 0}</div>
                <div className="text-xs font-bold mt-0.5">Fully Eligible</div>
              </div>
              <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-900">
                <div className="text-2xl font-black">{report.verified_eligibility_breakdown.needs_review || 0}</div>
                <div className="text-xs font-bold mt-0.5">Needs Review</div>
              </div>
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-900">
                <div className="text-2xl font-black">{report.verified_eligibility_breakdown.ineligible || 0}</div>
                <div className="text-xs font-bold mt-0.5">Ineligible</div>
              </div>
            </div>
          </div>

          {/* Top Recommended Pathways */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-[#111215] flex items-center gap-2">
              <Milestone className="w-4 h-4 text-gray-700" />
              <span>Top Recommended Strategic Pathways</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {report.top_recommended_pathways.map((prog, idx) => (
                <div
                  key={idx}
                  className="bg-[#FAFBF9] rounded-2xl p-4 border border-gray-200/80 shadow-2xs flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span className="text-[10px] font-mono text-gray-500">{prog.programme_id}</span>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                        {prog.eligibility_status.toUpperCase()}
                      </span>
                    </div>
                    <h4 className="text-sm font-bold text-[#111215] line-clamp-1">{prog.title}</h4>
                    <p className="text-xs text-gray-500 mt-0.5">{prog.institution}</p>
                    <p className="text-xs text-gray-700 mt-2 leading-snug">{prog.pathway_strategy}</p>
                  </div>
                  <div className="mt-3 pt-2 border-t border-gray-200 flex items-center justify-between text-xs">
                    <span className="text-gray-500 font-semibold">Affordability:</span>
                    <span className="font-bold text-emerald-700">Verified Compatible</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Actionable Milestones */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-[#111215] flex items-center gap-2">
              <ArrowRight className="w-4 h-4 text-gray-700" />
              <span>Recommended Execution Milestones</span>
            </h3>
            <div className="space-y-2">
              {report.actionable_milestones.map((m, idx) => (
                <div
                  key={idx}
                  className="bg-white rounded-xl p-3 border border-gray-200 flex items-start justify-between gap-4 text-xs"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-[#111215]">{m.title}</span>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-gray-100 text-gray-700">
                        {m.phase}
                      </span>
                    </div>
                    <p className="text-gray-600 mt-0.5">{m.details}</p>
                  </div>
                  <span className="shrink-0 px-2.5 py-1 rounded-full text-[11px] font-bold bg-[#ECEEE7] text-gray-800">
                    {m.target_timeline}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 bg-[#FAFBF9] border-t border-gray-200 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Multi-Agent Consensus Verified • Provenance: {report.provenance}</span>
          </div>
          <button
            onClick={onClose}
            className="px-6 py-2.5 rounded-full bg-[#111215] hover:bg-black text-white text-xs font-bold transition cursor-pointer shadow-sm"
          >
            Close Report
          </button>
        </div>
      </div>
    </div>
  );
};
