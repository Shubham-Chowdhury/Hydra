import React, { useState, useEffect, useCallback } from 'react';
import {
  Sparkles,
  AlertCircle,
  Compass,
  CheckCircle2,
  HelpCircle,
  XCircle,
  RefreshCw,
  SlidersHorizontal,
} from 'lucide-react';
import type {
  EvaluationResponse,
  ProgrammeEvaluationDto,
  StudentProfileRequest,
} from './api/types';
import { hydraApi, ApiError } from './api/client';
import { Navbar } from './components/layout/Navbar';
import { Footer } from './components/layout/Footer';
import { ProfileForm } from './components/profile/ProfileForm';
import { ProgrammeCard } from './components/programmes/ProgrammeCard';
import { AdmissionsEvidenceView } from './components/admissions/AdmissionsEvidenceView';
import { StudentDigitalTwinView } from './components/twin/StudentDigitalTwinView';
import { Database, UserCheck } from 'lucide-react';

export const App: React.FC = () => {
  const [mainView, setMainView] = useState<'evaluation' | 'twin' | 'admissions'>('evaluation');
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);
  const [evaluations, setEvaluations] = useState<ProgrammeEvaluationDto[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [hasEvaluated, setHasEvaluated] = useState<boolean>(false);
  const [evaluatedAt, setEvaluatedAt] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<'all' | 'eligible' | 'needs_review' | 'ineligible'>('all');

  const checkHealth = useCallback(async () => {
    try {
      const res = await hydraApi.checkHealth();
      setBackendHealthy(res.status === 'ok');
    } catch {
      setBackendHealthy(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    // Periodically re-check health every 30s
    const timer = setInterval(checkHealth, 30000);
    return () => clearInterval(timer);
  }, [checkHealth]);

  const handleProfileSubmit = async (profile: StudentProfileRequest) => {
    setIsLoading(true);
    setError(null);

    try {
      const response: EvaluationResponse = await hydraApi.evaluateProfile(profile);
      setEvaluations(response.evaluations);
      setEvaluatedAt(response.audit_timestamp);
      setHasEvaluated(true);
      // If backend was previously offline, it responded, so update status
      setBackendHealthy(true);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`Evaluation failed (${err.status}): ${err.message}`);
      } else if (err instanceof Error) {
        setError(`Connection failed: ${err.message}. Is the backend running at http://127.0.0.1:8000?`);
      } else {
        setError('An unexpected error occurred during evaluation.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const filteredEvaluations = evaluations.filter((evaluation) => {
    if (statusFilter === 'all') return true;
    return evaluation.eligibility_status === statusFilter;
  });

  const eligibleCount = evaluations.filter((e) => e.eligibility_status === 'eligible').length;
  const needsReviewCount = evaluations.filter((e) => e.eligibility_status === 'needs_review').length;
  const ineligibleCount = evaluations.filter((e) => e.eligibility_status === 'ineligible').length;

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      <Navbar isBackendHealthy={backendHealthy} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Intro Hero Header */}
        <div className="mb-8">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-950/80 border border-cyan-800 text-cyan-300 text-xs font-mono mb-2">
                <Sparkles className="w-3.5 h-3.5 text-cyan-400" aria-hidden="true" />
                Deterministic Symbolic Reasoning & Graph Inference
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
                Academic Pathway Evaluation
              </h1>
              <p className="mt-2 text-slate-400 max-w-3xl text-sm leading-relaxed">
                Hydra evaluates applicant eligibility using deterministic IF–THEN rules and discovers career
                and skill trajectories via NetworkX semantic network traversal. Results remain strictly
                traceable with zero probabilistic hallucinations.
              </p>
            </div>

            {backendHealthy === false && (
              <div className="flex items-center gap-2 px-3 py-2 bg-rose-950/60 border border-rose-800 rounded-lg text-rose-300 text-xs self-start md:self-auto">
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" aria-hidden="true" />
                <span>Backend appears offline at <code className="font-mono bg-rose-900/40 px-1 py-0.5 rounded">127.0.0.1:8000</code></span>
                <button
                  onClick={checkHealth}
                  className="ml-2 underline text-rose-200 hover:text-white inline-flex items-center gap-1"
                  title="Retry connection"
                >
                  <RefreshCw className="w-3 h-3" /> Retry
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Global Error Notice */}
        {error && (
          <div
            className="mb-6 p-4 rounded-xl bg-rose-950/70 border border-rose-800/80 text-rose-200 flex items-start gap-3 shadow-lg"
            role="alert"
          >
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" aria-hidden="true" />
            <div className="flex-1 text-sm">
              <p className="font-semibold text-rose-100">Evaluation Error</p>
              <p className="mt-0.5">{error}</p>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-rose-400 hover:text-rose-200 text-xs font-mono px-2 py-1"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Main View Mode Selector (Phase 3 & Phase 4) */}
        <div className="mb-6 flex items-center justify-between border-b border-slate-850 pb-4">
          <div className="flex items-center gap-2 bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs">
            <button
              type="button"
              onClick={() => setMainView('evaluation')}
              className={`px-4 py-2 rounded-lg font-semibold flex items-center gap-2 transition-all ${
                mainView === 'evaluation'
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/80 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Compass className="w-4 h-4" />
              Student Evaluation & Recommendations
            </button>
            <button
              type="button"
              onClick={() => setMainView('twin')}
              className={`px-4 py-2 rounded-lg font-semibold flex items-center gap-2 transition-all ${
                mainView === 'twin'
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/80 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <UserCheck className="w-4 h-4" />
              Student Digital Twin (Agent)
            </button>
            <button
              type="button"
              onClick={() => setMainView('admissions')}
              className={`px-4 py-2 rounded-lg font-semibold flex items-center gap-2 transition-all ${
                mainView === 'admissions'
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/80 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Database className="w-4 h-4" />
              Admissions Knowledge Base & Data Provenance
            </button>
          </div>
        </div>

        {mainView === 'admissions' ? (
          <AdmissionsEvidenceView />
        ) : mainView === 'twin' ? (
          <StudentDigitalTwinView />
        ) : (
          /* Main Grid: Left Profile Form, Right Recommendations */
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Profile Form (Left Column, 5 cols) */}
          <div className="lg:col-span-5">
            <div className="sticky top-24">
              <ProfileForm onSubmit={handleProfileSubmit} isLoading={isLoading} />
            </div>
          </div>

          {/* Results Display (Right Column, 7 cols) */}
          <div className="lg:col-span-7">
            {isLoading ? (
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-12 text-center flex flex-col items-center justify-center min-h-[420px]">
                <div className="relative">
                  <div className="w-14 h-14 rounded-full border-4 border-cyan-500/20 border-t-cyan-500 animate-spin" />
                  <Compass className="w-6 h-6 text-cyan-400 absolute inset-0 m-auto" aria-hidden="true" />
                </div>
                <h3 className="text-lg font-bold text-white mt-6">Evaluating Academic Pathways</h3>
                <p className="text-sm text-slate-400 mt-2 max-w-sm">
                  Applying deterministic eligibility rules, calculating INR affordability, and traversing
                  NetworkX semantic graph for skills and career pathways...
                </p>
              </div>
            ) : hasEvaluated ? (
              <div className="space-y-6">
                {/* Summary / Filter Bar */}
                <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <SlidersHorizontal className="w-4 h-4 text-slate-400" aria-hidden="true" />
                    <span className="text-xs font-medium text-slate-300">Filter by Status:</span>
                  </div>

                  <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label="Filter evaluations">
                    <button
                      type="button"
                      onClick={() => setStatusFilter('all')}
                      className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                        statusFilter === 'all'
                          ? 'bg-slate-800 text-white border border-slate-600'
                          : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
                      }`}
                    >
                      All ({evaluations.length})
                    </button>
                    <button
                      type="button"
                      onClick={() => setStatusFilter('eligible')}
                      className={`px-3 py-1 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                        statusFilter === 'eligible'
                          ? 'bg-emerald-950 text-emerald-300 border border-emerald-700'
                          : 'bg-slate-950 text-slate-400 hover:text-emerald-300 border border-slate-800'
                      }`}
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      Eligible ({eligibleCount})
                    </button>
                    <button
                      type="button"
                      onClick={() => setStatusFilter('needs_review')}
                      className={`px-3 py-1 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                        statusFilter === 'needs_review'
                          ? 'bg-amber-950 text-amber-300 border border-amber-700'
                          : 'bg-slate-950 text-slate-400 hover:text-amber-300 border border-slate-800'
                      }`}
                    >
                      <HelpCircle className="w-3.5 h-3.5 text-amber-400" />
                      Needs Review ({needsReviewCount})
                    </button>
                    <button
                      type="button"
                      onClick={() => setStatusFilter('ineligible')}
                      className={`px-3 py-1 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                        statusFilter === 'ineligible'
                          ? 'bg-rose-950 text-rose-300 border border-rose-700'
                          : 'bg-slate-950 text-slate-400 hover:text-rose-300 border border-slate-800'
                      }`}
                    >
                      <XCircle className="w-3.5 h-3.5 text-rose-400" />
                      Ineligible ({ineligibleCount})
                    </button>
                  </div>
                </div>

                {/* Audit Timestamp Banner */}
                {evaluatedAt && (
                  <div className="text-[11px] font-mono text-slate-500 flex items-center justify-between px-1">
                    <span>Evaluated via deterministic core: {evaluations.length} programmes ranked</span>
                    <span>Audit Timestamp: {new Date(evaluatedAt).toLocaleTimeString()}</span>
                  </div>
                )}

                {/* Filter Empty Result */}
                {filteredEvaluations.length === 0 && (
                  <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-8 text-center">
                    <p className="text-sm text-slate-400">
                      No programmes match the filter status <strong className="text-white capitalize">{statusFilter.replace('_', ' ')}</strong>.
                    </p>
                    <button
                      onClick={() => setStatusFilter('all')}
                      className="mt-3 text-xs text-cyan-400 hover:underline"
                    >
                      Reset filter to Show All
                    </button>
                  </div>
                )}

                {/* Programme Cards List */}
                <div className="space-y-4">
                  {filteredEvaluations.map((evaluation) => (
                    <ProgrammeCard key={evaluation.programme_id} evaluation={evaluation} />
                  ))}
                </div>
              </div>
            ) : (
              /* Initial Empty State */
              <div className="bg-slate-900/40 border border-dashed border-slate-800 rounded-2xl p-12 text-center flex flex-col items-center justify-center min-h-[460px]">
                <div className="w-16 h-16 rounded-2xl bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center mb-4 text-cyan-400">
                  <Compass className="w-8 h-8" aria-hidden="true" />
                </div>
                <h3 className="text-xl font-bold text-white">Ready for Profile Evaluation</h3>
                <p className="text-sm text-slate-400 mt-2 max-w-md leading-relaxed">
                  Enter student academic marks, entrance exam credentials, and INR budget in the form,
                  or click one of the quick preset buttons above the form to test different eligibility outcomes.
                </p>
                <div className="mt-6 flex flex-wrap gap-2 justify-center text-xs text-slate-400 font-mono">
                  <span className="px-2.5 py-1 rounded bg-slate-800/80 border border-slate-700">3-State Eligibility</span>
                  <span className="px-2.5 py-1 rounded bg-slate-800/80 border border-slate-700">INR Budget Validation</span>
                  <span className="px-2.5 py-1 rounded bg-slate-800/80 border border-slate-700">Semantic Pathways</span>
                  <span className="px-2.5 py-1 rounded bg-slate-800/80 border border-slate-700">Full Rule Traces</span>
                </div>
              </div>
            )}
          </div>
        </div>
        )}
      </main>

      <Footer />
    </div>
  );
};

export default App;
