import React, { useState, useEffect } from 'react';
import type { PlanningResultDto, ProgrammeResponse, StudentProfileRequest, TwinSnapshotDto } from '../../api/types';
import { hydraApi, ApiError } from '../../api/client';

interface HeistPlannerViewProps {
  currentSnapshot?: TwinSnapshotDto | null;
  profile?: StudentProfileRequest;
}

export const HeistPlannerView: React.FC<HeistPlannerViewProps> = ({
  currentSnapshot,
  profile,
}) => {
  const [programmes, setProgrammes] = useState<ProgrammeResponse[]>([]);
  const [selectedProgrammeId, setSelectedProgrammeId] = useState<string>('SYNTH_IN_CS_01');
  const [useHeuristic, setUseHeuristic] = useState<boolean>(true);
  const [planningResult, setPlanningResult] = useState<PlanningResultDto | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadCatalog = async () => {
      try {
        const progs = await hydraApi.getProgrammes();
        setProgrammes(progs);
        if (progs.length > 0 && !selectedProgrammeId) {
          setSelectedProgrammeId(progs[0].programme_id);
        }
      } catch {
        // Fallback to canonical IDs if fetch fails
        setSelectedProgrammeId('SYNTH_IN_CS_01');
      }
    };
    loadCatalog();
  }, []);

  useEffect(() => {
    const handleVoicePlannerRun = () => {
      runPlanner();
    };
    window.addEventListener('hydra:run_planner', handleVoicePlannerRun);
    return () => window.removeEventListener('hydra:run_planner', handleVoicePlannerRun);
  }, [selectedProgrammeId, useHeuristic, currentSnapshot, profile]);

  const runPlanner = async () => {
    if (!selectedProgrammeId) return;
    setLoading(true);
    setError(null);

    try {
      const payload = {
        target_programme_id: selectedProgrammeId,
        use_heuristic: useHeuristic,
        ...(currentSnapshot?.snapshot_id
          ? { snapshot_id: currentSnapshot.snapshot_id }
          : profile
          ? { profile }
          : {}),
      };

      const result = await hydraApi.planPathway(payload);
      setPlanningResult(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`Planning failed: ${err.message}`);
      } else {
        setError('Failed to execute A* pathway planner.');
      }
    } finally {
      setLoading(false);
    }
  };

  const getCategoryBadge = (category: string) => {
    switch (category) {
      case 'information_gathering':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            Information Gathering
          </span>
        );
      case 'documentation':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            Documentation
          </span>
        );
      case 'preparation':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            Preparation
          </span>
        );
      case 'eligibility_pathway':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-purple-50 text-purple-700 border border-purple-200">
            Alternative Pathway (OR)
          </span>
        );
      case 'preference_change':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-cyan-50 text-cyan-700 border border-cyan-200">
            Preference Adjustment
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            Non-Actionable (Immutable)
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 text-[#111215]">
      {/* Banner */}
      <div className="bg-white rounded-3xl border border-gray-200/80 p-6 shadow-xs">
        <div className="flex items-start gap-3">
          <span className="text-2xl">🗺️</span>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold tracking-tight text-[#111215]">Heist Planner</h2>
              <span className="text-xs font-semibold px-3 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
                A* State-Space Search
              </span>
            </div>
            <p className="text-xs text-gray-500 max-w-2xl leading-relaxed">
              Discovers mathematically cost-optimal action pathways transitioning the student from their
              current state toward target programme prerequisites. Distinguishes actionable future tasks
              from immutable historical records.
            </p>
          </div>
        </div>
      </div>

      {/* Target Programme & Search Controls */}
      <div className="bg-white rounded-3xl border border-gray-200/80 p-6 shadow-xs space-y-4">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div className="flex-1 space-y-2">
            <label className="text-xs font-bold text-gray-700 uppercase tracking-wider">
              Select Target Programme
            </label>
            <select
              value={selectedProgrammeId}
              onChange={(e) => setSelectedProgrammeId(e.target.value)}
              className="w-full max-w-xl px-3.5 py-2.5 rounded-2xl bg-gray-50/80 border border-gray-200 text-xs text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#111215]/20 focus:border-[#111215]"
            >
              {programmes.length > 0 ? (
                programmes.map((p) => (
                  <option key={p.programme_id} value={p.programme_id}>
                    {p.title} ({p.institution_name})
                  </option>
                ))
              ) : (
                <>
                  <option value="SYNTH_IN_CS_01">B.Tech. in Computer Science (Demo Tech)</option>
                  <option value="SYNTH_IN_DS_02">B.Tech. in Data Science (National Demo Univ)</option>
                  <option value="SYNTH_IN_EC_03">B.Tech. in Electronics & Communication</option>
                  <option value="SYNTH_IN_BT_04">B.Tech. in Biotechnology (Metropolitan)</option>
                </>
              )}
            </select>
          </div>

          {/* Heuristic Toggle */}
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 cursor-pointer text-xs text-gray-700 font-medium">
              <input
                type="checkbox"
                checked={useHeuristic}
                onChange={(e) => setUseHeuristic(e.target.checked)}
                className="rounded bg-gray-100 border-gray-300 text-[#111215] focus:ring-0"
              />
              <span>Use Admissible Heuristic h(n)</span>
            </label>

            <button
              onClick={runPlanner}
              disabled={loading || (!currentSnapshot && !profile)}
              className="px-5 py-2.5 rounded-full font-bold text-xs transition-all flex items-center justify-center gap-2 bg-[#111215] text-[#E8F84A] hover:bg-black disabled:opacity-50 disabled:cursor-not-allowed shadow-xs cursor-pointer"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Searching Pathways...</span>
                </>
              ) : (
                <>
                  <span>🧭</span>
                  <span>Search Feasible Pathway</span>
                </>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium">
            {error}
          </div>
        )}
      </div>

      {/* Planning Results */}
      {planningResult && (
        <div className="space-y-6">
          {/* Status Metrics Bar */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-3xl border border-gray-200/80 p-4 shadow-xs">
              <div className="text-xs text-gray-500 font-medium">Planning Outcome</div>
              <div className="text-base font-bold mt-1">
                {planningResult.goal_reached ? (
                  <span className="text-emerald-700">✓ Pathway Found</span>
                ) : (
                  <span className="text-rose-700">✕ No Feasible Path</span>
                )}
              </div>
              <div className="text-[11px] text-gray-500 mt-0.5">
                Initial: {planningResult.initial_status}
              </div>
            </div>

            <div className="bg-white rounded-3xl border border-gray-200/80 p-4 shadow-xs">
              <div className="text-xs text-gray-500 font-medium">Total Action Cost</div>
              <div className="text-2xl font-bold text-[#111215] mt-1 font-mono">
                {planningResult.total_cost.toFixed(1)}{' '}
                <span className="text-xs font-normal text-gray-500">pts</span>
              </div>
              <div className="text-[11px] text-gray-500 mt-0.5">Effort Accumulation</div>
            </div>

            <div className="bg-white rounded-3xl border border-gray-200/80 p-4 shadow-xs">
              <div className="text-xs text-gray-500 font-medium">Estimated Duration</div>
              <div className="text-2xl font-bold text-[#111215] mt-1 font-mono">
                ~{planningResult.total_duration_days}{' '}
                <span className="text-xs font-normal text-gray-500">days</span>
              </div>
              <div className="text-[11px] text-gray-500 mt-0.5">Sequential Timeline</div>
            </div>

            <div className="bg-white rounded-3xl border border-gray-200/80 p-4 shadow-xs">
              <div className="text-xs text-gray-500 font-medium">Nodes Expanded</div>
              <div className="text-2xl font-bold text-[#111215] mt-1 font-mono">
                {planningResult.nodes_expanded}
              </div>
              <div className="text-[11px] text-gray-500 mt-0.5 truncate">
                {planningResult.heuristic_used}
              </div>
            </div>
          </div>

          {/* Explanation Banner */}
          <div className="p-4 rounded-2xl border border-gray-200/80 bg-white shadow-xs text-xs text-gray-700">
            <span className="font-bold text-[#111215]">Plan Summary: </span>
            {planningResult.explanation}
          </div>

          {/* Action Sequence Pathway */}
          {planningResult.actions.length > 0 ? (
            <div className="space-y-3">
              <h3 className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                Step-by-Step Action Pathway ({planningResult.actions.length} Steps)
              </h3>

              <div className="space-y-3">
                {planningResult.actions.map((act, idx) => (
                  <div
                    key={act.action_id}
                    className="p-4 rounded-2xl border border-gray-200/80 bg-white shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4"
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-full bg-[#111215] text-[#E8F84A] font-bold text-xs flex items-center justify-center shrink-0">
                        {idx + 1}
                      </div>
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <h4 className="font-bold text-[#111215] text-sm">{act.title}</h4>
                          {getCategoryBadge(act.category)}
                          <span className="text-[10px] font-mono text-gray-500">{act.action_id}</span>
                        </div>
                        <p className="text-xs text-gray-600 mt-1">{act.description}</p>
                        {act.evidence_requirement && (
                          <div className="text-[11px] text-amber-700 mt-1 font-medium">
                            📄 Required Evidence: {act.evidence_requirement}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-4 self-end md:self-auto shrink-0 text-right">
                      <div>
                        <div className="text-[10px] text-gray-500">Effort</div>
                        <div className="text-xs font-bold text-gray-900 font-mono">
                          {act.cost} {act.cost_unit}
                        </div>
                      </div>
                      <div>
                        <div className="text-[10px] text-gray-500">Duration</div>
                        <div className="text-xs font-bold text-gray-900 font-mono">
                          {act.duration_days > 0 ? `~${act.duration_days} days` : 'Immediate'}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : planningResult.goal_reached ? (
            <div className="p-8 rounded-3xl border border-emerald-200 bg-emerald-50/60 text-center shadow-xs">
              <span className="text-3xl">🎉</span>
              <h4 className="font-bold text-emerald-900 mt-2 text-sm">Zero Actions Required</h4>
              <p className="text-xs text-emerald-700 mt-1">
                Student already meets all mandatory eligibility prerequisites for this programme.
              </p>
            </div>
          ) : (
            <div className="p-8 rounded-3xl border border-rose-200 bg-rose-50/60 text-center shadow-xs">
              <span className="text-3xl">🛑</span>
              <h4 className="font-bold text-rose-900 mt-2 text-sm">No Feasible Pathway Found</h4>
              <p className="text-xs text-rose-700 mt-1 max-w-lg mx-auto">
                The candidate has demonstrably failed mandatory prerequisites (e.g. past Class XII academic benchmarks)
                that cannot be altered by valid prospective actions.
              </p>
            </div>
          )}

          {/* Alternative OR Branches */}
          {planningResult.alternative_routes.length > 0 && (
            <div className="p-5 rounded-3xl border border-gray-200/80 bg-white shadow-xs space-y-3">
              <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                Alternative Qualification Tracks (Nested OR Semantics)
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {planningResult.alternative_routes.map((route, i) => (
                  <div key={i} className="p-3.5 rounded-2xl border border-gray-200 bg-gray-50/80 space-y-2">
                    <div className="flex items-center justify-between text-xs font-bold text-[#111215]">
                      <span>{route.pathway_name}</span>
                      <span className="text-indigo-700 font-mono">
                        {(route.readiness_ratio * 100).toFixed(0)}% Ready
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-indigo-600 h-full rounded-full transition-all"
                        style={{ width: `${route.readiness_ratio * 100}%` }}
                      />
                    </div>
                    <div className="text-[11px] text-gray-500">
                      Required conditions: {route.required_conditions.join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

