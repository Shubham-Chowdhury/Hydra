import React, { useState, useEffect } from 'react';
import type {
  BossFightReportDto,
  ProgrammeResponse,
  SimulationResultDto,
  StudentProfileRequest,
  TwinSnapshotDto,
} from '../../api/types';
import { hydraApi, ApiError } from '../../api/client';

interface SimulatorBossFightViewProps {
  currentSnapshot?: TwinSnapshotDto | null;
  profile?: StudentProfileRequest;
}

export const SimulatorBossFightView: React.FC<SimulatorBossFightViewProps> = ({
  currentSnapshot,
  profile,
}) => {
  const [programmes, setProgrammes] = useState<ProgrammeResponse[]>([]);
  const [selectedProgrammeId, setSelectedProgrammeId] = useState<string>('SYNTH_IN_CS_01');
  const [activeMode, setActiveMode] = useState<'deterministic' | 'monte_carlo' | 'boss_fight'>('deterministic');

  // Deterministic controls
  const [scenarioType, setScenarioType] = useState<string>('tuition_increase');
  const [tuitionHikePct, setTuitionHikePct] = useState<number>(25);
  const [budgetCotPct, setBudgetCotPct] = useState<number>(30);
  const [rankSlip, setRankSlip] = useState<number>(15000);

  // Monte Carlo controls
  const [mcIterations, setMcIterations] = useState<number>(100);
  const [mcSeed, setMcSeed] = useState<number>(42);

  // Results
  const [simResult, setSimResult] = useState<SimulationResultDto | null>(null);
  const [bossReport, setBossReport] = useState<BossFightReportDto | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadCatalog = async () => {
      try {
        const progs = await hydraApi.getProgrammes();
        setProgrammes(progs);
      } catch {
        setSelectedProgrammeId('SYNTH_IN_CS_01');
      }
    };
    loadCatalog();
  }, []);

  const runDeterministic = async () => {
    setLoading(true);
    setError(null);
    setSimResult(null);

    const params: Record<string, any> = {};
    if (scenarioType === 'tuition_increase') params.tuition_increase_pct = tuitionHikePct / 100;
    if (scenarioType === 'budget_decrease') params.budget_decrease_pct = budgetCotPct / 100;
    if (scenarioType === 'entrance_rank_deterioration') params.rank_slip_positions = rankSlip;

    try {
      const payload = {
        target_programme_id: selectedProgrammeId,
        scenario_type: scenarioType,
        parameters: params,
        ...(currentSnapshot?.snapshot_id
          ? { snapshot_id: currentSnapshot.snapshot_id }
          : profile
          ? { profile }
          : {}),
      };
      const res = await hydraApi.runSimulation(payload);
      setSimResult(res);
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else setError('Failed to run deterministic simulation.');
    } finally {
      setLoading(false);
    }
  };

  const runMonteCarlo = async () => {
    setLoading(true);
    setError(null);
    setSimResult(null);

    try {
      const payload = {
        target_programme_id: selectedProgrammeId,
        scenario_type: 'monte_carlo_multivariate',
        monte_carlo_config: {
          iterations: mcIterations,
          seed: mcSeed,
        },
        ...(currentSnapshot?.snapshot_id
          ? { snapshot_id: currentSnapshot.snapshot_id }
          : profile
          ? { profile }
          : {}),
      };
      const res = await hydraApi.runSimulation(payload);
      setSimResult(res);
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else setError('Failed to run Monte Carlo simulation.');
    } finally {
      setLoading(false);
    }
  };

  const runBossFight = async () => {
    setLoading(true);
    setError(null);
    setBossReport(null);

    try {
      const payload = {
        target_programme_id: selectedProgrammeId,
        ...(currentSnapshot?.snapshot_id
          ? { snapshot_id: currentSnapshot.snapshot_id }
          : profile
          ? { profile }
          : {}),
      };
      const res = await hydraApi.runBossFight(payload);
      setBossReport(res);
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else setError('Failed to execute Boss-Fight stress test.');
    } finally {
      setLoading(false);
    }
  };

  const getRobustnessBadge = (classification: string) => {
    switch (classification) {
      case 'robust_under_tested_scenarios':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-300">
            Robust Under Tested Scenarios
          </span>
        );
      case 'fragile':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-300">
            Fragile (High Sensitivity)
          </span>
        );
      case 'fails_under_tested_scenarios':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-800 border border-rose-300">
            Fails Under Adverse Scenarios
          </span>
        );
      default:
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-gray-100 text-gray-700">
            Insufficient Evidence
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 text-[#111215]">
      {/* Top Banner */}
      <div className="bg-white rounded-3xl border border-gray-200/80 p-6 shadow-xs">
        <div className="flex items-start gap-3">
          <span className="text-2xl">⚔️</span>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold tracking-tight text-[#111215]">Simulation & Boss-Fight Stress Testing</h2>
              <span className="text-xs font-semibold px-3 py-0.5 rounded-full bg-rose-50 text-rose-800 border border-rose-200">
                Adversarial Perturbation
              </span>
            </div>
            <p className="text-xs text-gray-500 max-w-2xl leading-relaxed">
              Perturbs admissions parameters in an isolated sandbox state to evaluate fragility and identify
              surviving fallback pathways. Simulated outcome frequencies reflect empirical modeling assumptions.
            </p>
          </div>
        </div>
      </div>

      {/* Mode Selection Tabs & Target Programme */}
      <div className="bg-white rounded-3xl border border-gray-200/80 p-6 shadow-xs space-y-4">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div className="flex-1 space-y-2">
            <label className="text-xs font-bold text-gray-700 uppercase tracking-wider">
              Target Academic Programme
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

          {/* Mode Switcher */}
          <div className="flex bg-gray-100 p-1.5 rounded-full border border-gray-200 text-xs self-start md:self-auto">
            <button
              onClick={() => setActiveMode('deterministic')}
              className={`px-3.5 py-1.5 rounded-full font-bold transition-all cursor-pointer ${
                activeMode === 'deterministic'
                  ? 'bg-white text-[#111215] shadow-xs'
                  : 'text-gray-500 hover:text-gray-900'
              }`}
            >
              Deterministic
            </button>
            <button
              onClick={() => setActiveMode('monte_carlo')}
              className={`px-3.5 py-1.5 rounded-full font-bold transition-all cursor-pointer ${
                activeMode === 'monte_carlo'
                  ? 'bg-white text-[#111215] shadow-xs'
                  : 'text-gray-500 hover:text-gray-900'
              }`}
            >
              Monte Carlo
            </button>
            <button
              onClick={() => setActiveMode('boss_fight')}
              className={`px-3.5 py-1.5 rounded-full font-bold transition-all cursor-pointer ${
                activeMode === 'boss_fight'
                  ? 'bg-rose-600 text-white shadow-xs'
                  : 'text-gray-500 hover:text-rose-700'
              }`}
            >
              ⚔️ Boss-Fight
            </button>
          </div>
        </div>

        {/* Mode Specific Controls */}
        {activeMode === 'deterministic' && (
          <div className="pt-4 border-t border-gray-100 flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-700 font-semibold">Scenario Perturbation</label>
                <select
                  value={scenarioType}
                  onChange={(e) => setScenarioType(e.target.value)}
                  className="w-full mt-1 px-3 py-2 rounded-xl bg-gray-50/80 border border-gray-200 text-xs text-gray-900 focus:outline-none"
                >
                  <option value="tuition_increase">Tuition Increase (+%)</option>
                  <option value="budget_decrease">Student Budget Decrease (-%)</option>
                  <option value="entrance_rank_deterioration">Entrance Rank Deterioration (+Positions)</option>
                  <option value="cutoff_movement">Closing Cutoff Movement (-% Stricter)</option>
                  <option value="missing_mandatory_evidence">Missing Mathematics Marksheet</option>
                </select>
              </div>

              {scenarioType === 'tuition_increase' && (
                <div>
                  <label className="text-xs text-gray-700 font-medium">
                    Tuition Inflation: +{tuitionHikePct}%
                  </label>
                  <input
                    type="range"
                    min="5"
                    max="100"
                    step="5"
                    value={tuitionHikePct}
                    onChange={(e) => setTuitionHikePct(Number(e.target.value))}
                    className="w-full mt-2 accent-rose-600"
                  />
                </div>
              )}

              {scenarioType === 'budget_decrease' && (
                <div>
                  <label className="text-xs text-gray-700 font-medium">
                    Budget Reduction: -{budgetCotPct}%
                  </label>
                  <input
                    type="range"
                    min="5"
                    max="75"
                    step="5"
                    value={budgetCotPct}
                    onChange={(e) => setBudgetCotPct(Number(e.target.value))}
                    className="w-full mt-2 accent-rose-600"
                  />
                </div>
              )}

              {scenarioType === 'entrance_rank_deterioration' && (
                <div>
                  <label className="text-xs text-gray-700 font-medium">
                    Rank Slip: +{rankSlip.toLocaleString()} positions
                  </label>
                  <input
                    type="range"
                    min="1000"
                    max="50000"
                    step="1000"
                    value={rankSlip}
                    onChange={(e) => setRankSlip(Number(e.target.value))}
                    className="w-full mt-2 accent-rose-600"
                  />
                </div>
              )}
            </div>

            <button
              onClick={runDeterministic}
              disabled={loading}
              className="px-5 py-2.5 rounded-full font-bold text-xs bg-[#111215] text-[#E8F84A] hover:bg-black disabled:opacity-50 transition-all shrink-0 cursor-pointer shadow-xs"
            >
              {loading ? 'Simulating...' : 'Apply Scenario'}
            </button>
          </div>
        )}

        {activeMode === 'monte_carlo' && (
          <div className="pt-4 border-t border-gray-100 flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div className="flex gap-4">
              <div>
                <label className="text-xs text-gray-700 font-medium">Iterations</label>
                <input
                  type="number"
                  min="10"
                  max="500"
                  value={mcIterations}
                  onChange={(e) => setMcIterations(Number(e.target.value))}
                  className="w-24 mt-1 px-3 py-1.5 rounded-xl bg-gray-50 border border-gray-200 text-xs text-gray-900"
                />
              </div>
              <div>
                <label className="text-xs text-gray-700 font-medium">Random Seed</label>
                <input
                  type="number"
                  value={mcSeed}
                  onChange={(e) => setMcSeed(Number(e.target.value))}
                  className="w-24 mt-1 px-3 py-1.5 rounded-xl bg-gray-50 border border-gray-200 text-xs text-gray-900"
                />
              </div>
            </div>

            <button
              onClick={runMonteCarlo}
              disabled={loading}
              className="px-5 py-2.5 rounded-full font-bold text-xs bg-[#111215] text-[#E8F84A] hover:bg-black disabled:opacity-50 transition-all shrink-0 cursor-pointer shadow-xs"
            >
              {loading ? 'Sampling...' : 'Run Monte Carlo'}
            </button>
          </div>
        )}

        {activeMode === 'boss_fight' && (
          <div className="pt-4 border-t border-gray-100 flex items-center justify-between gap-4 flex-wrap">
            <p className="text-xs text-gray-600 max-w-lg">
              Unleash 6 simultaneous hostile perturbations (rank slip, tuition hike, budget drop, cutoff tightening, missing transcripts).
            </p>
            <button
              onClick={runBossFight}
              disabled={loading}
              className="px-6 py-2.5 rounded-full font-bold text-xs bg-rose-600 hover:bg-rose-700 text-white shadow-xs disabled:opacity-50 transition-all cursor-pointer"
            >
              {loading ? 'Attacking Plan...' : '⚔️ Engage Boss-Fight'}
            </button>
          </div>
        )}

        {error && (
          <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium">
            {error}
          </div>
        )}
      </div>

      {/* Deterministic Simulation Result */}
      {simResult && !simResult.monte_carlo_metrics && (
        <div className="p-6 rounded-3xl border border-gray-200/80 bg-white shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-[#111215] text-sm">Counterfactual Result: {simResult.scenario.scenario_type}</h3>
            <span className="text-xs font-mono text-gray-500">{simResult.simulation_id}</span>
          </div>

          <div className="p-4 rounded-2xl border border-gray-200 bg-gray-50/80 text-xs text-gray-700 space-y-1">
            <div className="font-bold text-[#111215]">{simResult.delta_summary}</div>
            <div className="text-gray-500">Assumptions: {simResult.scenario.assumptions.join(' ')}</div>
          </div>

          <div className="grid grid-cols-2 gap-4 text-xs">
            <div className="p-3.5 rounded-2xl border border-gray-200 bg-white space-y-1.5 shadow-2xs">
              <div className="text-gray-500 font-bold uppercase tracking-wider text-[11px]">Baseline Reality</div>
              <div>Eligibility: <span className={simResult.baseline_eligible ? 'text-emerald-700 font-bold' : 'text-rose-700 font-bold'}>{simResult.baseline_eligible ? 'Eligible' : 'Ineligible'}</span></div>
              <div>Affordability: <span className={simResult.baseline_affordable ? 'text-emerald-700 font-bold' : 'text-rose-700 font-bold'}>{simResult.baseline_affordable ? 'Affordable' : 'Exceeds Budget'}</span></div>
            </div>
            <div className="p-3.5 rounded-2xl border border-gray-200 bg-white space-y-1.5 shadow-2xs">
              <div className="text-gray-500 font-bold uppercase tracking-wider text-[11px]">Hypothetical Scenario</div>
              <div>Eligibility: <span className={simResult.scenario_eligible ? 'text-emerald-700 font-bold' : 'text-rose-700 font-bold'}>{simResult.scenario_eligible ? 'Eligible' : 'Ineligible'}</span></div>
              <div>Affordability: <span className={simResult.scenario_affordable ? 'text-emerald-700 font-bold' : 'text-rose-700 font-bold'}>{simResult.scenario_affordable ? 'Affordable' : 'Exceeds Budget'}</span></div>
            </div>
          </div>
        </div>
      )}

      {/* Monte Carlo Results */}
      {simResult && simResult.monte_carlo_metrics && (
        <div className="p-6 rounded-3xl border border-gray-200/80 bg-white shadow-xs space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-[#111215] text-sm">Monte Carlo Statistical Simulation</h3>
            <span className="text-xs font-mono text-gray-500">{simResult.simulation_id}</span>
          </div>

          {/* Outcome Frequencies */}
          {simResult.monte_carlo_outcome_frequencies && (
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                Simulated Outcome Frequencies
              </h4>
              <div className="space-y-2">
                <div>
                  <div className="flex justify-between text-xs text-emerald-800 font-semibold">
                    <span>Eligible & Affordable</span>
                    <span>{(simResult.monte_carlo_outcome_frequencies.eligible_and_affordable * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2.5 mt-1">
                    <div
                      className="bg-emerald-500 h-2.5 rounded-full"
                      style={{ width: `${simResult.monte_carlo_outcome_frequencies.eligible_and_affordable * 100}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs text-amber-800 font-semibold">
                    <span>Eligible but Tuition Exceeds Budget</span>
                    <span>{(simResult.monte_carlo_outcome_frequencies.eligible_unaffordable * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2.5 mt-1">
                    <div
                      className="bg-amber-500 h-2.5 rounded-full"
                      style={{ width: `${simResult.monte_carlo_outcome_frequencies.eligible_unaffordable * 100}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-xs text-rose-800 font-semibold">
                    <span>Ineligible (Prerequisite Violated)</span>
                    <span>{(simResult.monte_carlo_outcome_frequencies.ineligible * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2.5 mt-1">
                    <div
                      className="bg-rose-500 h-2.5 rounded-full"
                      style={{ width: `${simResult.monte_carlo_outcome_frequencies.ineligible * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Distribution Quantile Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(simResult.monte_carlo_metrics).map(([key, metric]) => (
              <div key={key} className="p-4 rounded-2xl border border-gray-200 bg-gray-50/80 space-y-2 text-xs">
                <div className="font-bold text-[#111215]">{metric.variable_name}</div>
                <div className="grid grid-cols-2 gap-1 text-[11px] text-gray-600">
                  <div>Mean: <span className="text-[#111215] font-mono font-semibold">{metric.mean.toLocaleString()}</span></div>
                  <div>Median: <span className="text-[#111215] font-mono font-semibold">{metric.median.toLocaleString()}</span></div>
                  <div>P10: <span className="text-[#111215] font-mono font-semibold">{metric.p10.toLocaleString()}</span></div>
                  <div>P90: <span className="text-[#111215] font-mono font-semibold">{metric.p90.toLocaleString()}</span></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Boss-Fight Adversarial Report */}
      {bossReport && (
        <div className="p-6 rounded-3xl border border-rose-200 bg-white shadow-xs space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-100 pb-4">
            <div>
              <div className="text-xs text-gray-500 font-bold uppercase tracking-wider">Boss-Fight Stress Test Outcome</div>
              <h3 className="text-lg font-bold text-[#111215] mt-1">{bossReport.target_programme_title}</h3>
            </div>
            <div>
              {getRobustnessBadge(bossReport.overall_robustness)}
            </div>
          </div>

          {/* Attack Battery Matrix */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wider">
              Adversarial Attacks Battery ({bossReport.attacks_survived}/{bossReport.total_attacks_tested} Survived)
            </h4>

            <div className="space-y-2">
              {bossReport.attack_outcomes.map((att, i) => (
                <div
                  key={i}
                  className={`p-3.5 rounded-2xl border text-xs flex flex-col md:flex-row md:items-center justify-between gap-2 ${
                    att.survived
                      ? 'border-emerald-200 bg-emerald-50/50'
                      : 'border-rose-200 bg-rose-50/50'
                  }`}
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-[#111215]">{att.attack_type.replace('_', ' ').toUpperCase()}</span>
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                          att.survived ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                        }`}
                      >
                        {att.survived ? '✓ Survived' : '✕ Failed'}
                      </span>
                    </div>
                    <p className="text-gray-500 text-[11px]">{att.perturbation_description}</p>
                    <p className="text-gray-700 text-[11px]">{att.explanation}</p>
                  </div>

                  {att.failed_constraint && (
                    <span className="px-2.5 py-1 rounded-full bg-rose-100 text-rose-800 border border-rose-300 text-[10px] font-mono shrink-0">
                      {att.failed_constraint}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Fallback Recommendation */}
          <div className="p-4 rounded-2xl border border-gray-200 bg-gray-50/80 space-y-2 text-xs">
            <div className="font-bold text-[#111215]">Fallback Resilience Recommendation:</div>
            <p className="text-gray-700 leading-relaxed">{bossReport.fallback_recommendation}</p>
            {bossReport.surviving_alternative_programmes.length > 0 && (
              <div className="pt-2 text-indigo-700 text-[11px] font-semibold">
                Surviving Programmes in Catalogue: {bossReport.surviving_alternative_programmes.join(', ')}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

