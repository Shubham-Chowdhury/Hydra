/**
 * Oracle Admissions Cutoff Forecasting View for Hydra (M005).
 *
 * Provides a provenance-honest UI displaying data readiness diagnostics,
 * forecasting model catalog, query target specification, and advisory
 * cutoff forecasts with uncertainty intervals.
 */

import React, { useEffect, useState } from 'react';
import { apiClient } from '../../api/client';
import type {
  CutoffForecastDto,
  ForecastTargetDto,
  OracleStatusResponseDto,
  ProgrammeResponse,
} from '../../api/types';

interface OracleForecastViewProps {
  programmes: ProgrammeResponse[];
}

export const OracleForecastView: React.FC<OracleForecastViewProps> = ({ programmes }) => {
  const [oracleStatus, setOracleStatus] = useState<OracleStatusResponseDto | null>(null);
  const [loadingStatus, setLoadingStatus] = useState<boolean>(true);
  const [querying, setQuerying] = useState<boolean>(false);
  const [forecast, setForecast] = useState<CutoffForecastDto | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Forecast query form state
  const [selectedProgrammeId, setSelectedProgrammeId] = useState<string>(
    programmes.length > 0 ? programmes[0].programme_id : ''
  );
  const [futureYear, setFutureYear] = useState<number>(2027);
  const [counsellingRound, setCounsellingRound] = useState<number>(1);
  const [examName, setExamName] = useState<string>('JEE Advanced');
  const [seatType, setSeatType] = useState<string>('OPEN');
  const [quota, setQuota] = useState<string>('AI');
  const [genderPool, setGenderPool] = useState<string>('Gender-Neutral');
  const [rankBasis, setRankBasis] = useState<string>('CRL');

  useEffect(() => {
    fetchStatus();
  }, []);

  useEffect(() => {
    if (!selectedProgrammeId && programmes.length > 0) {
      setSelectedProgrammeId(programmes[0].programme_id);
    }
  }, [programmes, selectedProgrammeId]);

  const fetchStatus = async () => {
    setLoadingStatus(true);
    setErrorMessage(null);
    try {
      const res = await apiClient.getOracleStatus();
      setOracleStatus(res);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to retrieve Oracle status');
    } finally {
      setLoadingStatus(false);
    }
  };

  const executeForecastQuery = async () => {
    if (!selectedProgrammeId) return;

    setQuerying(true);
    setErrorMessage(null);
    setForecast(null);

    const target: ForecastTargetDto = {
      institution_id: programmes.find((p) => p.programme_id === selectedProgrammeId)?.institution_name || 'INST_DEMO',
      programme_id: selectedProgrammeId,
      future_academic_year: futureYear,
      counselling_round: counsellingRound,
      exam_name: examName,
      seat_type: seatType,
      quota,
      gender_pool: genderPool,
      rank_basis: rankBasis,
      target_type: 'closing_rank',
    };

    try {
      const res = await apiClient.generateCutoffForecast(target);
      setForecast(res);
    } catch (err: any) {
      setErrorMessage(err.message || 'Error generating cutoff forecast');
    } finally {
      setQuerying(false);
    }
  };

  useEffect(() => {
    const handleVoiceForecast = () => {
      executeForecastQuery();
    };
    window.addEventListener('hydra:run_forecast', handleVoiceForecast);
    return () => window.removeEventListener('hydra:run_forecast', handleVoiceForecast);
  }, [selectedProgrammeId, futureYear, counsellingRound, examName, seatType, quota, genderPool, rankBasis, programmes]);

  const handleForecastSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    executeForecastQuery();
  };

  return (
    <div className="space-y-6">
      {/* Header & Data Readiness Gate */}
      <div className="bg-white rounded-3xl border border-gray-200/80 p-6 shadow-xs text-[#111215]">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-2xl">🔮</span>
              <h2 className="text-xl font-bold tracking-tight text-[#111215]">Oracle Cutoff Forecaster</h2>
              <span className="text-xs font-semibold px-3 py-1 rounded-full bg-amber-50 text-amber-900 border border-amber-200">
                Probabilistic Trend Estimation
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1 max-w-2xl leading-relaxed">
              ML trend forecasting with strict empirical data-readiness gating. Evaluates closing rank trajectories with calibrated confidence intervals.
            </p>
          </div>
          <button
            onClick={fetchStatus}
            disabled={loadingStatus}
            className="text-xs font-semibold px-4 py-2 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-800 border border-gray-200 transition-all shadow-2xs self-start md:self-auto"
          >
            {loadingStatus ? 'Checking Readiness...' : '🔄 Refresh Data Audit'}
          </button>
        </div>

        {/* Data Readiness Diagnostic Box */}
        {oracleStatus && (
          <div className="mt-5 border-t border-gray-100 pt-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs uppercase tracking-wider text-gray-500 font-bold">
                Admissions Data Readiness Gate
              </span>
              <span
                className={`text-xs px-3 py-1 rounded-full font-mono font-bold ${
                  oracleStatus.status === 'READY'
                    ? 'bg-emerald-50 text-emerald-800 border border-emerald-300'
                    : 'bg-amber-50 text-amber-800 border border-amber-300'
                }`}
              >
                ● {oracleStatus.status}
              </span>
            </div>

            <p className="text-xs text-gray-700 bg-gray-50/80 p-3 rounded-2xl border border-gray-200/70">
              {oracleStatus.readiness_report.message}
            </p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 text-xs">
              <div className="bg-gray-50/80 p-3.5 rounded-2xl border border-gray-200/70">
                <span className="text-gray-500 text-[11px] block">Inspected Records</span>
                <span className="text-gray-900 font-mono font-bold text-lg">
                  {oracleStatus.readiness_report.total_records_inspected}
                </span>
              </div>
              <div className="bg-emerald-50/60 p-3.5 rounded-2xl border border-emerald-200/70">
                <span className="text-emerald-700 text-[11px] block">Eligible Verified</span>
                <span className="text-emerald-900 font-mono font-bold text-lg">
                  {oracleStatus.readiness_report.eligible_records_count}
                </span>
              </div>
              <div className="bg-amber-50/60 p-3.5 rounded-2xl border border-amber-200/70">
                <span className="text-amber-700 text-[11px] block">Quarantined / Excluded</span>
                <span className="text-amber-900 font-mono font-bold text-lg">
                  {oracleStatus.readiness_report.rejected_records_count}
                </span>
              </div>
              <div className="bg-blue-50/60 p-3.5 rounded-2xl border border-blue-200/70">
                <span className="text-blue-700 text-[11px] block">Active Forecast Model</span>
                <span className="text-blue-900 font-mono font-bold text-xs truncate block mt-1">
                  {oracleStatus.active_model_version}
                </span>
              </div>
            </div>

            {Object.keys(oracleStatus.readiness_report.rejections_by_reason).length > 0 && (
              <div className="mt-3 text-xs text-gray-600 flex flex-wrap items-center gap-1.5">
                <span className="text-gray-500 font-medium">Exclusions Breakdown:</span>
                {Object.entries(oracleStatus.readiness_report.rejections_by_reason).map(([k, v]) => (
                  <span key={k} className="inline-block bg-gray-100 px-2.5 py-0.5 rounded-full font-mono text-[11px] text-gray-700 border border-gray-200">
                    {k}: {String(v)}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {errorMessage && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-2xl text-xs font-medium">
          {errorMessage}
        </div>
      )}

      {/* Forecast Query Form & Results */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 bg-white border border-gray-200/80 rounded-3xl p-6 shadow-xs space-y-4 text-[#111215]">
          <h3 className="text-base font-bold text-[#111215]">Forecast Target</h3>
          <form onSubmit={handleForecastSubmit} className="space-y-4 text-xs">
            <div>
              <label className="block text-gray-700 mb-1.5 font-semibold">Target Programme</label>
              <select
                value={selectedProgrammeId}
                onChange={(e) => setSelectedProgrammeId(e.target.value)}
                className="w-full bg-gray-50/80 border border-gray-200 rounded-2xl p-2.5 text-gray-900 text-xs focus:outline-none focus:ring-2 focus:ring-[#111215]/20 focus:border-[#111215]"
              >
                {programmes.map((p) => (
                  <option key={p.programme_id} value={p.programme_id}>
                    {p.title} ({p.institution_name})
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-gray-700 mb-1 font-medium">Target Year</label>
                <input
                  type="number"
                  value={futureYear}
                  onChange={(e) => setFutureYear(parseInt(e.target.value) || 2027)}
                  className="w-full bg-gray-50/80 border border-gray-200 rounded-xl p-2 text-gray-900 text-xs focus:outline-none focus:ring-1 focus:ring-gray-400"
                />
              </div>
              <div>
                <label className="block text-gray-700 mb-1 font-medium">Counselling Round</label>
                <input
                  type="number"
                  value={counsellingRound}
                  onChange={(e) => setCounsellingRound(parseInt(e.target.value) || 1)}
                  className="w-full bg-gray-50/80 border border-gray-200 rounded-xl p-2 text-gray-900 text-xs focus:outline-none focus:ring-1 focus:ring-gray-400"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-gray-700 mb-1 font-medium">Exam</label>
                <select
                  value={examName}
                  onChange={(e) => setExamName(e.target.value)}
                  className="w-full bg-gray-50/80 border border-gray-200 rounded-xl p-2 text-gray-900 text-xs focus:outline-none focus:ring-1 focus:ring-gray-400"
                >
                  <option value="JEE Advanced">JEE Advanced</option>
                  <option value="JEE Main">JEE Main</option>
                </select>
              </div>
              <div>
                <label className="block text-gray-700 mb-1 font-medium">Rank Basis</label>
                <select
                  value={rankBasis}
                  onChange={(e) => setRankBasis(e.target.value)}
                  className="w-full bg-gray-50/80 border border-gray-200 rounded-xl p-2 text-gray-900 text-xs focus:outline-none focus:ring-1 focus:ring-gray-400"
                >
                  <option value="CRL">CRL</option>
                  <option value="CATEGORY_RANK">Category Rank</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="block text-gray-700 mb-1 font-medium text-[11px]">Seat Type</label>
                <select
                  value={seatType}
                  onChange={(e) => setSeatType(e.target.value)}
                  className="w-full bg-gray-50/80 border border-gray-200 rounded-xl p-1.5 text-gray-900 text-xs"
                >
                  <option value="OPEN">OPEN</option>
                  <option value="OBC-NCL">OBC-NCL</option>
                  <option value="SC">SC</option>
                  <option value="ST">ST</option>
                  <option value="GEN-EWS">GEN-EWS</option>
                </select>
              </div>
              <div>
                <label className="block text-gray-700 mb-1 font-medium text-[11px]">Quota</label>
                <select
                  value={quota}
                  onChange={(e) => setQuota(e.target.value)}
                  className="w-full bg-gray-50/80 border border-gray-200 rounded-xl p-1.5 text-gray-900 text-xs"
                >
                  <option value="AI">AI (All India)</option>
                  <option value="HS">HS (Home State)</option>
                  <option value="OS">OS (Other State)</option>
                </select>
              </div>
              <div>
                <label className="block text-gray-700 mb-1 font-medium text-[11px]">Gender</label>
                <select
                  value={genderPool}
                  onChange={(e) => setGenderPool(e.target.value)}
                  className="w-full bg-gray-50/80 border border-gray-200 rounded-xl p-1.5 text-gray-900 text-xs"
                >
                  <option value="Gender-Neutral">Neutral</option>
                  <option value="Female-only (including Supernumerary)">Female</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={querying || !selectedProgrammeId}
              className="w-full py-3 px-4 rounded-full bg-[#111215] text-[#E8F84A] font-bold text-xs tracking-wide hover:bg-black transition-all shadow-xs disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
            >
              {querying ? 'Computing Forecast...' : 'Query Cutoff Forecast'}
            </button>
          </form>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-2 space-y-4">
          {!forecast && !querying && (
            <div className="bg-white border border-gray-200/80 rounded-3xl p-10 text-center text-gray-500 shadow-xs flex flex-col items-center justify-center min-h-[320px]">
              <span className="text-4xl block mb-3">📈</span>
              <p className="text-sm font-semibold text-gray-800">Select a target programme to forecast closing ranks</p>
              <p className="text-xs text-gray-500 mt-1 max-w-md">
                The Oracle Agent calculates calibrated uncertainty intervals [p10, p90] when verified historical trend data is present.
              </p>
            </div>
          )}

          {forecast && (
            <div className="bg-white border border-gray-200/80 rounded-3xl p-6 shadow-xs space-y-5 text-[#111215]">
              <div className="flex items-center justify-between border-b border-gray-100 pb-4">
                <div>
                  <h3 className="text-base font-bold text-[#111215]">Forecast Advisory Outcome</h3>
                  <span className="text-xs text-gray-500">
                    Target Year: {forecast.target.future_academic_year} | Round {forecast.target.counselling_round} ({forecast.target.seat_type}/{forecast.target.quota})
                  </span>
                </div>
                <span
                  className={`text-xs px-3 py-1 rounded-full font-mono font-bold ${
                    forecast.status === 'READY'
                      ? 'bg-emerald-50 text-emerald-800 border border-emerald-300'
                      : 'bg-amber-50 text-amber-800 border border-amber-300'
                  }`}
                >
                  ● {forecast.status}
                </span>
              </div>

              {forecast.status === 'READY' && forecast.point_prediction !== null ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-gray-50/80 p-4 rounded-2xl border border-gray-200/80 text-center">
                      <span className="text-[11px] text-gray-500 uppercase tracking-wider block font-semibold">Point Prediction</span>
                      <span className="text-3xl font-black text-[#111215] font-mono mt-1 block">
                        ~{forecast.point_prediction}
                      </span>
                      <span className="text-[11px] text-gray-500">Projected Closing Rank</span>
                    </div>
                    <div className="bg-gray-50/80 p-4 rounded-2xl border border-gray-200/80 text-center">
                      <span className="text-[11px] text-gray-500 uppercase tracking-wider block font-semibold">90% Confidence Interval</span>
                      <span className="text-xl font-bold text-blue-700 font-mono mt-2 block">
                        [{forecast.interval_p10} — {forecast.interval_p90}]
                      </span>
                      <span className="text-[11px] text-gray-500">Uncertainty: ±{Math.round((forecast.uncertainty_band || 0) / 2)} ranks</span>
                    </div>
                    <div className="bg-gray-50/80 p-4 rounded-2xl border border-gray-200/80 text-center">
                      <span className="text-[11px] text-gray-500 uppercase tracking-wider block font-semibold">Model Performance</span>
                      <span className="text-xl font-bold text-emerald-700 font-mono mt-2 block">
                        MAE: {forecast.metrics ? forecast.metrics.mae : 'N/A'}
                      </span>
                      <span className="text-[11px] text-gray-500">
                        Baseline MAE: {forecast.metrics ? forecast.metrics.baseline_mae : 'N/A'}
                      </span>
                    </div>
                  </div>

                  <div className="bg-gray-50/60 p-4 rounded-2xl border border-gray-200/70 text-xs space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Model Version:</span>
                      <span className="font-mono text-gray-800 font-semibold">{forecast.model_version}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Training Samples:</span>
                      <span className="font-mono text-gray-800 font-semibold">{forecast.training_records_count} verified historical observations</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Features Used:</span>
                      <span className="font-mono text-gray-800 font-semibold">{forecast.features_used.join(', ')}</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-amber-50/80 border border-amber-200 rounded-2xl p-5 space-y-2.5">
                  <div className="flex items-center gap-2 text-amber-900 font-bold text-sm">
                    <span>⚠️</span>
                    <span>Admissions Data Inadequacy Notice</span>
                  </div>
                  <p className="text-xs text-amber-800 leading-relaxed">
                    Hydra enforces zero-fabrication integrity. A forecast was not computed because verified authoritative admissions records for this cohort are currently unavailable. Synthetic demonstration fixtures and unverified sources are quarantined to prevent fictitious machine learning predictions.
                  </p>
                  {forecast.warnings.length > 0 && (
                    <ul className="text-xs text-amber-900 list-disc list-inside space-y-1 font-medium">
                      {forecast.warnings.map((w: string, idx: number) => (
                        <li key={idx}>{w}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}

              {/* Legal Disclaimer */}
              <div className="p-3 bg-gray-50 rounded-xl border border-gray-200/70 text-[11px] text-gray-500 italic">
                {forecast.disclaimer}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

