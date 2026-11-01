import React, { useEffect, useState } from 'react';
import {
  Database,
  ExternalLink,
  ShieldCheck,
  AlertTriangle,
  FileCheck,
  Search,
  Layers,
  Info,
} from 'lucide-react';
import { hydraApi } from '../../api/client';
import type {
  AdmissionCutoffDto,
  FormalEligibilityCriterionDto,
  SourceDocumentDto,
} from '../../api/types';

export const AdmissionsEvidenceView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'cutoffs' | 'sources' | 'criteria'>('cutoffs');

  // Cutoffs state
  const [cutoffs, setCutoffs] = useState<AdmissionCutoffDto[]>([]);
  const [totalCutoffs, setTotalCutoffs] = useState(0);
  const [loadingCutoffs, setLoadingCutoffs] = useState(false);
  const [cutoffError, setCutoffError] = useState<string | null>(null);

  // Filters
  const [instFilter, setInstFilter] = useState('');
  const [seatTypeFilter, setSeatTypeFilter] = useState('');
  const [quotaFilter, setQuotaFilter] = useState('');
  const [roundFilter, setRoundFilter] = useState('');

  // Sources state
  const [sources, setSources] = useState<SourceDocumentDto[]>([]);
  const [loadingSources, setLoadingSources] = useState(false);

  // Criteria state
  const [criteria, setCriteria] = useState<FormalEligibilityCriterionDto[]>([]);
  const [loadingCriteria, setLoadingCriteria] = useState(false);

  // Load sources
  useEffect(() => {
    async function fetchSources() {
      setLoadingSources(true);
      try {
        const docs = await hydraApi.getDataSources();
        setSources(docs);
      } catch (err) {
        console.error('Failed to load data sources:', err);
      } finally {
        setLoadingSources(false);
      }
    }
    fetchSources();
  }, []);

  // Load criteria
  useEffect(() => {
    async function fetchCriteria() {
      setLoadingCriteria(true);
      try {
        const list = await hydraApi.getEligibilityCriteria(2026);
        setCriteria(list);
      } catch (err) {
        console.error('Failed to load eligibility criteria:', err);
      } finally {
        setLoadingCriteria(false);
      }
    }
    fetchCriteria();
  }, []);

  // Load cutoffs with debounce or on filter change
  useEffect(() => {
    async function fetchCutoffs() {
      setLoadingCutoffs(true);
      setCutoffError(null);
      try {
        const params: Record<string, string | number> = { limit: 50 };
        if (instFilter.trim()) params.institution = instFilter.trim();
        if (seatTypeFilter) params.seat_type = seatTypeFilter;
        if (quotaFilter) params.quota = quotaFilter;
        if (roundFilter) params.counselling_round = Number(roundFilter);

        const resp = await hydraApi.getHistoricalCutoffs(params);
        setCutoffs(resp.results);
        setTotalCutoffs(resp.total_count);
      } catch (err) {
        setCutoffError(err instanceof Error ? err.message : 'Failed to query historical cutoffs');
      } finally {
        setLoadingCutoffs(false);
      }
    }
    const timer = setTimeout(fetchCutoffs, 250);
    return () => clearTimeout(timer);
  }, [instFilter, seatTypeFilter, quotaFilter, roundFilter]);

  const sourceStatusBadge = (status: string) => {
    switch (status) {
      case 'official_source':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-800 flex items-center gap-1">
            <ShieldCheck className="w-3 h-3" />
            Verified Official Source
          </span>
        );
      case 'derived_from_official':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-cyan-950/80 text-cyan-300 border border-cyan-800 flex items-center gap-1">
            <FileCheck className="w-3 h-3" />
            Derived from Verified Official Artifact
          </span>
        );
      case 'synthetic_demo':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-purple-950/80 text-purple-300 border border-purple-800 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-purple-400" />
            Synthetic Demonstration Fixture (Illustrative Only)
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-950/80 text-amber-300 border border-amber-800 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" />
            Unverified Source (Remote Timeout)
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Database className="w-5 h-5 text-cyan-400" />
              <h2 className="text-xl font-bold text-slate-100">
                Admissions Knowledge Base & Data Provenance
              </h2>
            </div>
            <p className="text-sm text-slate-400">
              Audit authoritative admissions datasets, historical JoSAA cutoff observations, and verified JEE (Advanced) eligibility rules.
            </p>
          </div>

          {/* Sub-tab Navigation */}
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
            <button
              type="button"
              onClick={() => setActiveTab('cutoffs')}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                activeTab === 'cutoffs'
                  ? 'bg-cyan-900/60 text-cyan-300 border border-cyan-800/80'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Historical Cutoffs
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('criteria')}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                activeTab === 'criteria'
                  ? 'bg-cyan-900/60 text-cyan-300 border border-cyan-800/80'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Verified Eligibility Rules
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('sources')}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                activeTab === 'sources'
                  ? 'bg-cyan-900/60 text-cyan-300 border border-cyan-800/80'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Source Manifests ({sources.length})
            </button>
          </div>
        </div>
      </div>

      {/* Mandatory Regulatory & Interpretive Disclaimer */}
      <div className="bg-amber-950/25 border-l-4 border-l-amber-500 border border-amber-900/40 rounded-lg p-4 text-xs text-amber-200 flex items-start gap-3 shadow-sm">
        <Info className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" aria-hidden="true" />
        <div className="space-y-1">
          <p className="font-semibold text-amber-300 tracking-wide">
            IMPORTANT DOMAIN DISTINCTION: HISTORICAL OBSERVATIONS VS. ELIGIBILITY
          </p>
          <p className="text-amber-200/90 leading-relaxed">
            Historical cutoff observations describe past counselling allocation boundaries from prior rounds.
            They <strong className="text-amber-100 font-bold underline">do not guarantee future admission</strong> and are{' '}
            <strong className="text-amber-100 font-bold underline">never converted into mandatory student eligibility rules</strong> in Hydra.
            Eligibility is governed strictly by verified deterministic academic prerequisites.
          </p>
        </div>
      </div>

      {/* TAB 1: Historical Cutoffs */}
      {activeTab === 'cutoffs' && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-4 grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
            {/* Institution Search */}
            <div className="relative">
              <label htmlFor="inst-search" className="block text-slate-400 font-medium mb-1">
                Institution Search
              </label>
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
                <input
                  id="inst-search"
                  type="text"
                  placeholder="e.g. Bombay, Delhi, Tiruchirappalli..."
                  value={instFilter}
                  onChange={(e) => setInstFilter(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-600"
                />
              </div>
            </div>

            {/* Seat Type */}
            <div>
              <label htmlFor="seat-type-select" className="block text-slate-400 font-medium mb-1">
                Seat Type / Category
              </label>
              <select
                id="seat-type-select"
                value={seatTypeFilter}
                onChange={(e) => setSeatTypeFilter(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-slate-950 border border-slate-800 rounded text-slate-200 focus:outline-none focus:border-cyan-600"
              >
                <option value="">All Categories</option>
                <option value="OPEN">OPEN (Common Rank List)</option>
                <option value="GEN-EWS">GEN-EWS</option>
                <option value="OBC-NCL">OBC-NCL</option>
                <option value="SC">SC</option>
                <option value="ST">ST</option>
              </select>
            </div>

            {/* Quota */}
            <div>
              <label htmlFor="quota-select" className="block text-slate-400 font-medium mb-1">
                Counselling Quota
              </label>
              <select
                id="quota-select"
                value={quotaFilter}
                onChange={(e) => setQuotaFilter(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-slate-950 border border-slate-800 rounded text-slate-200 focus:outline-none focus:border-cyan-600"
              >
                <option value="">All Quotas</option>
                <option value="AI">AI (All India)</option>
                <option value="HS">HS (Home State)</option>
                <option value="OS">OS (Other State)</option>
              </select>
            </div>

            {/* Round */}
            <div>
              <label htmlFor="round-select" className="block text-slate-400 font-medium mb-1">
                Counselling Round
              </label>
              <select
                id="round-select"
                value={roundFilter}
                onChange={(e) => setRoundFilter(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-slate-950 border border-slate-800 rounded text-slate-200 focus:outline-none focus:border-cyan-600"
              >
                <option value="">All Rounds</option>
                <option value="1">Round 1</option>
                <option value="2">Round 2</option>
                <option value="3">Round 3</option>
                <option value="4">Round 4</option>
                <option value="5">Round 5</option>
                <option value="6">Round 6</option>
              </select>
            </div>
          </div>

          {/* Notice for Synthetic Test Fixtures */}
          {cutoffs.some((c) => c.is_synthetic) && (
            <div className="bg-purple-950/30 border border-purple-800/60 rounded-lg p-3 text-xs text-purple-200 flex items-start gap-3">
              <AlertTriangle className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
              <div>
                <strong className="text-purple-300 font-semibold block mb-0.5">
                  NOTICE: ILLUSTRATIVE SYNTHETIC TEST FIXTURE DATA (SRC_JOSAA_SYNTHETIC_FIXTURE_2026)
                </strong>
                <p className="text-purple-200/90 leading-relaxed">
                  The cutoff records displayed below are representative test fixtures created to validate tabular parsing and schema invariants.
                  Values (including opening and closing ranks) are <strong>illustrative only</strong> and <strong>must not be interpreted as published JoSAA counselling results</strong>.
                </p>
              </div>
            </div>
          )}

          {/* Results Summary & Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden shadow-sm">
            <div className="px-4 py-3 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium">
                Showing {cutoffs.length} of {totalCutoffs} historical observations
              </span>
              <span className="text-[11px] font-mono text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-900/60">
                Academic Year 2026
              </span>
            </div>

            {loadingCutoffs ? (
              <div className="p-8 text-center text-xs text-slate-500">Querying observations...</div>
            ) : cutoffError ? (
              <div className="p-8 text-center text-xs text-rose-400">{cutoffError}</div>
            ) : cutoffs.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500">
                No historical cutoff observations matched the selected filters. Zero records fabricated.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-slate-950/90 text-slate-400 border-b border-slate-800 font-mono text-[11px]">
                      <th className="py-2.5 px-3">Institution & Programme</th>
                      <th className="py-2.5 px-3">Quota</th>
                      <th className="py-2.5 px-3">Category (Seat Type)</th>
                      <th className="py-2.5 px-3">Gender Pool</th>
                      <th className="py-2.5 px-3 text-right">Opening Rank</th>
                      <th className="py-2.5 px-3 text-right">Closing Rank</th>
                      <th className="py-2.5 px-3 text-center">Round</th>
                      <th className="py-2.5 px-3">Provenance Reference</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {cutoffs.map((item) => (
                      <tr key={item.observation_id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-2.5 px-3">
                          <div className="font-semibold text-slate-200">{item.institution_name}</div>
                          <div className="text-[11px] text-slate-400">{item.programme_title}</div>
                          {item.is_synthetic ? (
                            <span className="inline-flex items-center gap-1 mt-1 px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-purple-950/80 text-purple-300 border border-purple-800/80">
                              Synthetic Test Fixture (Illustrative)
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 mt-1 px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-emerald-950/80 text-emerald-300 border border-emerald-800/80">
                              Verified Official Record
                            </span>
                          )}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-cyan-300">{item.quota}</td>
                        <td className="py-2.5 px-3">
                          <span className="font-mono text-slate-300 font-semibold">{item.seat_type}</span>
                          <span className="block text-[10px] text-slate-500 font-mono">
                            basis: {item.rank_basis}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-400 text-[11px]">{item.gender_pool}</td>
                        <td className="py-2.5 px-3 font-mono text-emerald-400 font-semibold text-right">
                          {item.opening_rank.toLocaleString()}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-cyan-400 font-semibold text-right">
                          {item.closing_rank.toLocaleString()}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-center text-slate-300">
                          R{item.counselling_round}
                        </td>
                        <td className="py-2.5 px-3 text-[10px] font-mono text-slate-400">
                          <span className="text-slate-300">{item.source_row_provenance}</span>
                          <span className="block text-slate-500 truncate max-w-[140px]" title={item.source_document_id}>
                            {item.source_document_id}
                          </span>
                          <span className="block text-slate-600 truncate max-w-[140px]" title={item.snapshot_id}>
                            {item.snapshot_id}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: Verified Eligibility Rules */}
      {activeTab === 'criteria' && (
        <div className="space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-2">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
              <h3 className="font-bold text-slate-200 text-sm flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                Verified Eligibility Criteria — JEE (Advanced) 2026 Examination Appearance
              </h3>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-cyan-950 text-cyan-300 border border-cyan-800 flex items-center gap-1 font-mono w-fit">
                <Info className="w-3 h-3" />
                Scope: Examination Appearance
              </span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Directly extracted from the authentic official publication by the Joint Admission Board (JAB).
              <strong className="text-slate-300"> Important scope distinction:</strong> These criteria govern eligibility to <em>appear for the JEE (Advanced) 2026 examination</em>. They do not constitute universal institutional degree admission rules or override programme prerequisites.
            </p>
          </div>

          {loadingCriteria ? (
            <div className="p-8 text-center text-xs text-slate-500">Loading criteria...</div>
          ) : (
            <div className="grid grid-cols-1 gap-3">
              {criteria.map((c) => (
                <div
                  key={c.criterion_id}
                  className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-2 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-xs font-bold text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-900/60">
                      {c.criterion_number}
                    </span>
                    <div className="flex items-center gap-1.5">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-cyan-950 text-cyan-300 border border-cyan-800">
                        Scope: {c.criterion_scope?.replace(/_/g, ' ') || 'Exam Appearance'}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
                        Mandatory Official Rule
                      </span>
                    </div>
                  </div>

                  <h4 className="font-bold text-slate-200 text-sm">{c.title}</h4>
                  <p className="text-xs text-slate-300 leading-relaxed bg-slate-950 p-2.5 rounded border border-slate-800/80">
                    {c.description}
                  </p>

                  <div className="flex items-center justify-between pt-1 text-[11px] font-mono text-slate-500">
                    <span>Authority: {c.authority}</span>
                    <span>Source Doc: {c.source_document_id}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: Source Manifests */}
      {activeTab === 'sources' && (
        <div className="space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <h3 className="font-bold text-slate-200 text-sm mb-1 flex items-center gap-2">
              <Layers className="w-4 h-4 text-cyan-400" />
              Registered Source Documents and Snapshot Manifests
            </h3>
            <p className="text-xs text-slate-400">
              Each source is registered with canonical URLs, immutable SHA-256 checksums, and explicit verification notes.
            </p>
          </div>

          {loadingSources ? (
            <div className="p-8 text-center text-xs text-slate-500">Loading source manifests...</div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
            {sources.map((s) => (
              <div
                key={s.source_id}
                className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-slate-800 pb-2">
                  <div>
                    <span className="font-mono text-xs text-slate-400">{s.source_id}</span>
                    <h4 className="font-bold text-slate-200 text-sm">{s.title}</h4>
                  </div>
                  <div>{sourceStatusBadge(s.source_status)}</div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-slate-500">Issuing Authority: </span>
                    <span className="text-slate-300 font-medium">{s.issuing_authority}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Canonical URL: </span>
                    <a
                      href={s.canonical_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-cyan-400 hover:underline inline-flex items-center gap-1 font-mono text-[11px]"
                    >
                      {s.canonical_url}
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  <div>
                    <span className="text-slate-500">Retrieval UTC: </span>
                    <span className="font-mono text-slate-300">{s.retrieval_timestamp}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Academic Year: </span>
                    <span className="font-mono text-slate-300">{s.academic_year}</span>
                  </div>
                </div>

                {s.sha256_checksum && (
                  <div className="bg-slate-950 p-2.5 rounded border border-slate-800 text-[11px] font-mono">
                    <span className="text-slate-500 block mb-0.5">SHA-256 Checksum:</span>
                    <span className="text-emerald-400 break-all">{s.sha256_checksum}</span>
                  </div>
                )}

                <div className="text-xs text-slate-400 space-y-1 bg-slate-950/60 p-2.5 rounded border border-slate-850">
                  <p>
                    <strong className="text-slate-300">Access Notes: </strong>
                    {s.access_notes || 'None recorded.'}
                  </p>
                  <p>
                    <strong className="text-slate-300">Verification Notes: </strong>
                    {s.verification_notes || 'None recorded.'}
                  </p>
                </div>
              </div>
            ))}
          </div>
          )}
        </div>
      )}
    </div>
  );
};
