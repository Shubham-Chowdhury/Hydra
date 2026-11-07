/**
 * Central Referee Multi-Agent Orchestration View for Hydra.
 *
 * Coordinates and displays synthesized recommendations across all 6 intelligent
 * agents (Twin, Franchise, Rule Engine, Heist Planner, Simulator, Oracle,
 * Interest Decoder) with a highly visual, modern neo-dashboard aesthetic.
 */

import React, { useState } from 'react';
import { hydraApi } from '../../api/client';
import type {
  AgentResponseEnvelopeDto,
  ConflictRecordDto,
  RefereeEvaluationResponseDto,
  RefereeProgrammeDecisionDto,
  StudentProfileRequest,
} from '../../api/types';
import {
  ShieldCheck,
  CheckCircle2,
  Play,
  RotateCw,
  Award,
  Users,
  Compass,
  LineChart,
  Swords,
  Brain,
  MapPin,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

interface CentralRefereeViewProps {
  profile?: StudentProfileRequest;
}

export const CentralRefereeView: React.FC<CentralRefereeViewProps> = ({ profile }) => {
  const [includeAuction, setIncludeAuction] = useState<boolean>(true);
  const [includePlanning, setIncludePlanning] = useState<boolean>(true);
  const [includeStressTest, setIncludeStressTest] = useState<boolean>(true);
  const [includeOracle, setIncludeOracle] = useState<boolean>(true);
  const [interestNarrative, setInterestNarrative] = useState<string>(
    'I love building autonomous robotic systems, machine learning models, and scalable software algorithms.'
  );

  const [loading, setLoading] = useState<boolean>(false);
  const [refereeResult, setRefereeResult] = useState<RefereeEvaluationResponseDto | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [expandedProgrammeId, setExpandedProgrammeId] = useState<string | null>(null);

  const defaultProfile: StudentProfileRequest = {
    student_id: 'STU_MASTER_REF',
    subject_scores: [
      { subject_code: 'MATH', subject_name: 'Mathematics', score: 92.0, grading_scale: 'percentage' },
      { subject_code: 'PHYS', subject_name: 'Physics', score: 88.0, grading_scale: 'percentage' },
      { subject_code: 'CHEM', subject_name: 'Chemistry', score: 85.0, grading_scale: 'percentage' },
      { subject_code: 'ENG', subject_name: 'English', score: 80.0, grading_scale: 'percentage' },
    ],
    entrance_exam_name: 'JEE Main',
    entrance_rank: 12000,
    total_budget_inr: 2000000.0,
    preferred_disciplines: ['Computer Science', 'Robotics'],
    career_goals: ['Machine Learning Engineer', 'Software Systems Engineer'],
  };

  const activeProfile = profile || defaultProfile;

  const handleRunEvaluation = async () => {
    setLoading(true);
    setErrorMessage(null);
    setRefereeResult(null);

    try {
      const res = await hydraApi.evaluateWithReferee({
        profile: activeProfile,
        include_auction: includeAuction,
        include_planning: includePlanning,
        include_stress_test: includeStressTest,
        include_oracle: includeOracle,
        interest_narrative: interestNarrative,
      });
      setRefereeResult(res);
    } catch (err: any) {
      setErrorMessage(err.message || 'Referee multi-agent orchestration failed.');
    } finally {
      setLoading(false);
    }
  };

  const getAgentVisual = (agentName: string) => {
    const a = agentName.toLowerCase();
    if (a.includes('twin')) return { icon: Users, color: 'text-blue-600 bg-blue-50 border-blue-200', title: 'Student Digital Twin' };
    if (a.includes('rule') || a.includes('engine')) return { icon: ShieldCheck, color: 'text-emerald-600 bg-emerald-50 border-emerald-200', title: 'Symbolic Rule Core' };
    if (a.includes('franchise') || a.includes('auction')) return { icon: Award, color: 'text-amber-600 bg-amber-50 border-amber-200', title: 'Franchise Auction' };
    if (a.includes('oracle')) return { icon: LineChart, color: 'text-purple-600 bg-purple-50 border-purple-200', title: 'Oracle Predictor' };
    if (a.includes('planner') || a.includes('heist')) return { icon: Compass, color: 'text-cyan-600 bg-cyan-50 border-cyan-200', title: 'A* Heist Planner' };
    if (a.includes('simulator') || a.includes('boss')) return { icon: Swords, color: 'text-rose-600 bg-rose-50 border-rose-200', title: 'Boss-Fight Simulator' };
    return { icon: Brain, color: 'text-indigo-600 bg-indigo-50 border-indigo-200', title: 'Interest Decoder' };
  };

  return (
    <div className="space-y-6 text-[#111215]">
      {/* Control Cockpit Card */}
      <div className="bg-white rounded-3xl p-6 border border-gray-200/70 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl">⚖️</span>
              <h2 className="text-2xl font-bold tracking-tight text-[#111215]">
                Central Referee Multi-Agent Orchestration
              </h2>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Synthesizes independent evaluations across all 6 specialized agents and enforces deterministic rule precedence.
            </p>
          </div>

          <button
            onClick={handleRunEvaluation}
            disabled={loading}
            className="px-6 py-3 rounded-full bg-[#111215] hover:bg-black text-white font-bold text-xs shadow-md transition-all hover:scale-105 active:scale-95 disabled:opacity-50 flex items-center gap-2 shrink-0 cursor-pointer"
          >
            {loading ? (
              <>
                <RotateCw className="w-4 h-4 animate-spin text-[#E8F84A]" />
                <span>Synthesizing All Agents...</span>
              </>
            ) : (
              <>
                <span>Execute Multi-Agent Pipeline</span>
                <Play className="w-3.5 h-3.5 fill-[#E8F84A] text-[#E8F84A]" />
              </>
            )}
          </button>
        </div>

        {/* Pipeline Toggle Pills */}
        <div className="mt-5 pt-4 border-t border-gray-100 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <label className="flex items-center gap-2 p-2.5 rounded-2xl bg-gray-50/80 border border-gray-200/60 cursor-pointer hover:bg-gray-100 transition-colors">
            <input
              type="checkbox"
              checked={includeAuction}
              onChange={(e) => setIncludeAuction(e.target.checked)}
              className="rounded text-[#111215] focus:ring-[#111215] cursor-pointer"
            />
            <span className="font-semibold text-gray-800">Franchise Auction</span>
          </label>
          <label className="flex items-center gap-2 p-2.5 rounded-2xl bg-gray-50/80 border border-gray-200/60 cursor-pointer hover:bg-gray-100 transition-colors">
            <input
              type="checkbox"
              checked={includePlanning}
              onChange={(e) => setIncludePlanning(e.target.checked)}
              className="rounded text-[#111215] focus:ring-[#111215] cursor-pointer"
            />
            <span className="font-semibold text-gray-800">A* Heist Planner</span>
          </label>
          <label className="flex items-center gap-2 p-2.5 rounded-2xl bg-gray-50/80 border border-gray-200/60 cursor-pointer hover:bg-gray-100 transition-colors">
            <input
              type="checkbox"
              checked={includeStressTest}
              onChange={(e) => setIncludeStressTest(e.target.checked)}
              className="rounded text-[#111215] focus:ring-[#111215] cursor-pointer"
            />
            <span className="font-semibold text-gray-800">Boss-Fight Stress Test</span>
          </label>
          <label className="flex items-center gap-2 p-2.5 rounded-2xl bg-gray-50/80 border border-gray-200/60 cursor-pointer hover:bg-gray-100 transition-colors">
            <input
              type="checkbox"
              checked={includeOracle}
              onChange={(e) => setIncludeOracle(e.target.checked)}
              className="rounded text-[#111215] focus:ring-[#111215] cursor-pointer"
            />
            <span className="font-semibold text-gray-800">Oracle Cutoff Gating</span>
          </label>
        </div>

        {/* Narrative Input Field */}
        <div className="mt-4">
          <label className="block text-[11px] font-bold text-gray-500 mb-1.5 uppercase tracking-wider">
            Natural-Language Student Interest Input (Decoded by Interest Decoder)
          </label>
          <input
            type="text"
            value={interestNarrative}
            onChange={(e) => setInterestNarrative(e.target.value)}
            placeholder="Describe your passions, technical curiosities, or preferred industries..."
            className="w-full bg-gray-50/70 border border-gray-200/80 rounded-2xl p-3 text-xs text-[#111215] focus:bg-white focus:outline-none focus:border-[#111215] transition-all shadow-2xs"
          />
        </div>
      </div>

      {errorMessage && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-2xl text-xs font-medium">
          {errorMessage}
        </div>
      )}

      {/* Main Multi-Agent Results Canvas */}
      {refereeResult && (
        <div className="space-y-6 animate-in fade-in duration-300">
          {/* Participating Agents Visual Grid */}
          <div className="bg-white rounded-3xl p-6 border border-gray-200/70 shadow-xs">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                <h3 className="text-sm font-bold text-[#111215] uppercase tracking-wider">
                  Participating Agent Envelopes ({refereeResult.agent_envelopes.length})
                </h3>
              </div>
              <span className="text-xs font-mono px-3 py-1 rounded-full bg-gray-100 text-gray-600 font-semibold">
                Consensus Snapshot: {refereeResult.snapshot_id?.slice(0, 12)}...
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
              {refereeResult.agent_envelopes.map((env: AgentResponseEnvelopeDto, i: number) => {
                const visual = getAgentVisual(env.agent_name);
                const Icon = visual.icon;
                return (
                  <div
                    key={i}
                    className="p-4 bg-gray-50/70 rounded-2xl border border-gray-200/70 flex flex-col justify-between hover:bg-white hover:shadow-2xs transition-all space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className={`w-7 h-7 rounded-xl flex items-center justify-center border shadow-2xs ${visual.color}`}>
                          <Icon className="w-3.5 h-3.5" />
                        </div>
                        <span className="font-bold text-xs text-[#111215]">{visual.title}</span>
                      </div>
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                        {env.execution_status}
                      </span>
                    </div>

                    <p className="text-[11px] text-gray-600 leading-relaxed">
                      {env.explanation}
                    </p>

                    <div className="pt-2 border-t border-gray-200/50 flex justify-between text-[10px] text-gray-400 font-mono">
                      <span>{env.agent_name}</span>
                      <span className="text-emerald-700 font-semibold">Verified</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Visual Conflict Detection Ledger */}
          <div className="bg-white rounded-3xl p-6 border border-gray-200/70 shadow-xs">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-[#111215] uppercase tracking-wider">
                Multi-Agent Conflict Arbitration
              </h3>
              <span className="text-xs px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 font-bold border border-emerald-200">
                {refereeResult.conflicts_detected.length} Discrepancies
              </span>
            </div>

            {refereeResult.conflicts_detected.length === 0 ? (
              <div className="p-4 bg-emerald-50/70 border border-emerald-200 rounded-2xl flex items-center gap-2.5 text-xs text-emerald-900 font-medium">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>
                  <strong>Perfect Multi-Agent Consensus:</strong> All agent evaluations operated in complete harmony with the 9-tier decision hierarchy.
                </span>
              </div>
            ) : (
              <div className="space-y-3">
                {refereeResult.conflicts_detected.map((conf: ConflictRecordDto) => (
                  <div
                    key={conf.conflict_id}
                    className="p-4 bg-amber-50 border border-amber-200 rounded-2xl text-xs space-y-1 text-amber-950"
                  >
                    <div className="flex justify-between items-center font-bold">
                      <span>Conflict: {conf.field_or_claim}</span>
                      <span className="font-mono px-2 py-0.5 rounded-full bg-amber-200 text-amber-900 text-[10px]">
                        Arbitrated: {conf.resolved_value}
                      </span>
                    </div>
                    <p className="text-gray-700 text-[11px]">{conf.explanation}</p>
                    <div className="text-[11px] font-semibold text-amber-700">
                      Strategy: {conf.resolution_strategy}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Master Recommendation Decisions - Podium Cards */}
          <div className="bg-white rounded-3xl p-6 border border-gray-200/70 shadow-xs space-y-5">
            <div className="flex items-center justify-between border-b border-gray-100 pb-4">
              <div>
                <h3 className="text-lg font-bold text-[#111215]">
                  Synthesized Pathway Recommendations
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  Ordered by 3-State Eligibility, INR Affordability, and Franchise Preference Auction Rank.
                </p>
              </div>
              <span className="text-xs px-3.5 py-1.5 rounded-full bg-[#E8F84A] text-[#111215] font-bold shadow-2xs">
                Top Picks: {refereeResult.top_recommended_programmes.length}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {refereeResult.programme_decisions.map((dec: RefereeProgrammeDecisionDto, idx: number) => {
                const isExpanded = expandedProgrammeId === dec.programme_id;
                const isTopPick = refereeResult.top_recommended_programmes.includes(dec.programme_id);
                const tuitionLakh = (dec.tuition_inr / 100000).toFixed(2);
                const fitScore = dec.preference_fit !== null ? Math.round(dec.preference_fit * 100) : null;

                return (
                  <div
                    key={dec.programme_id}
                    className={`rounded-3xl border p-5 transition-all flex flex-col justify-between ${
                      isTopPick
                        ? 'border-[#111215] bg-gradient-to-br from-yellow-500/5 via-white to-emerald-500/5 ring-1 ring-[#111215] shadow-sm'
                        : 'border-gray-200/70 bg-white hover:border-gray-300 shadow-xs'
                    }`}
                  >
                    <div className="space-y-3">
                      {/* Top Rank Badge */}
                      <div className="flex items-center justify-between">
                        <span
                          className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs ${
                            idx === 0
                              ? 'bg-amber-400 text-black shadow-xs'
                              : idx === 1
                              ? 'bg-gray-300 text-black shadow-xs'
                              : idx === 2
                              ? 'bg-amber-700 text-white shadow-xs'
                              : 'bg-gray-100 text-gray-700'
                          }`}
                        >
                          #{idx + 1}
                        </span>

                        <div className="flex items-center gap-1.5">
                          {dec.eligibility_status === 'eligible' ? (
                            <span className="px-2.5 py-0.5 rounded-full bg-emerald-500 text-white text-[11px] font-bold">
                              Eligible
                            </span>
                          ) : (
                            <span className="px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300 text-[11px] font-bold">
                              {dec.eligibility_status}
                            </span>
                          )}

                          <span
                            className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${
                              dec.is_affordable
                                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                                : 'bg-rose-50 text-rose-800 border-rose-200'
                            }`}
                          >
                            ₹{tuitionLakh}L
                          </span>
                        </div>
                      </div>

                      {/* Title & Institution */}
                      <div>
                        <h4 className="text-sm font-bold text-[#111215] leading-snug line-clamp-2">
                          {dec.programme_title}
                        </h4>
                        <div className="text-[11px] text-gray-500 flex items-center gap-1 mt-1">
                          <MapPin className="w-3 h-3 text-gray-400" />
                          <span>{dec.institution_name}</span>
                        </div>
                      </div>

                      {/* Visual Fit Meter */}
                      {fitScore !== null && (
                        <div className="bg-gray-50 p-2.5 rounded-2xl border border-gray-200/60">
                          <div className="flex justify-between text-[11px] mb-1 font-semibold">
                            <span className="text-gray-500">Multi-Agent Fit:</span>
                            <span className="text-[#111215] font-bold">{fitScore}%</span>
                          </div>
                          <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-emerald-500 rounded-full"
                              style={{ width: `${fitScore}%` }}
                            />
                          </div>
                        </div>
                      )}

                      {/* Consensus Summary Note */}
                      <p className="text-[11px] text-gray-600 line-clamp-2 leading-relaxed">
                        {dec.decision_summary}
                      </p>
                    </div>

                    {/* Expand Details Trigger */}
                    <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between text-xs">
                      <button
                        onClick={() => setExpandedProgrammeId(isExpanded ? null : dec.programme_id)}
                        className="text-gray-700 hover:text-black font-semibold flex items-center gap-1 cursor-pointer"
                      >
                        <span>{isExpanded ? 'Hide Trace' : 'View Agent Traces'}</span>
                        {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                      </button>

                      {isTopPick && (
                        <span className="text-[11px] font-bold text-amber-600 flex items-center gap-1">
                          <Award className="w-3.5 h-3.5" />
                          <span>Top Pick</span>
                        </span>
                      )}
                    </div>

                    {/* Expanded Trace Drawer */}
                    {isExpanded && (
                      <div className="mt-3 p-3 bg-gray-50 rounded-2xl border border-gray-200/70 text-[11px] space-y-2">
                        <div className="font-bold text-gray-800">Arbitration Breakdown:</div>
                        <div className="space-y-1 text-gray-600">
                          <div><strong>Precedence:</strong> {dec.franchise_proposal_status || 'Deterministic Priority'}</div>
                          <div><strong>Rule Verified:</strong> {dec.rule_traces?.length || 0} Criteria Evaluated</div>
                          <div><strong>Franchise Rank:</strong> #{dec.auction_rank || 'N/A'}</div>
                          <div><strong>Oracle Status:</strong> {dec.oracle_status}</div>
                          {dec.boss_fight_robustness && (
                            <div><strong>Stress Test:</strong> Survived {dec.boss_fight_survived}/{dec.boss_fight_total} ({dec.boss_fight_robustness})</div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
