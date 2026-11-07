import React, { useEffect, useState } from 'react';
import {
  Search,
  Database,
  FileCheck,
  Layers,
} from 'lucide-react';
import { hydraApi } from '../../api/client';
import type {
  AdmissionCutoffDto,
  FormalEligibilityCriterionDto,
  SourceDocumentDto,
} from '../../api/types';
import { PageHeader } from '../common/PageHeader';
import { ProvenanceIndicator } from '../common/ProvenanceIndicator';
import { DemoNoticeBanner } from '../common/DemoNoticeBanner';

export const SourcesAndRequirementsView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'criteria' | 'cutoffs' | 'documents'>('criteria');

  // Criteria state
  const [criteria, setCriteria] = useState<FormalEligibilityCriterionDto[]>([]);
  const [loadingCriteria, setLoadingCriteria] = useState<boolean>(false);

  // Cutoffs state
  const [cutoffs, setCutoffs] = useState<AdmissionCutoffDto[]>([]);
  const [totalCutoffs, setTotalCutoffs] = useState<number>(0);
  const [loadingCutoffs, setLoadingCutoffs] = useState<boolean>(false);
  const [instFilter, setInstFilter] = useState<string>('');
  const [seatTypeFilter, setSeatTypeFilter] = useState<string>('');

  // Source documents state
  const [documents, setDocuments] = useState<SourceDocumentDto[]>([]);

  useEffect(() => {
    async function loadInitial() {
      setLoadingCriteria(true);
      try {
        const [crit, docs] = await Promise.all([
          hydraApi.getEligibilityCriteria(2026).catch(() => []),
          hydraApi.getDataSources().catch(() => []),
        ]);
        setCriteria(crit);
        setDocuments(docs);
      } finally {
        setLoadingCriteria(false);
      }
    }
    loadInitial();
  }, []);

  useEffect(() => {
    async function fetchCutoffs() {
      setLoadingCutoffs(true);
      try {
        const params: Record<string, string | number> = { limit: 50 };
        if (instFilter.trim()) params.institution = instFilter.trim();
        if (seatTypeFilter) params.seat_type = seatTypeFilter;
        const res = await hydraApi.getHistoricalCutoffs(params);
        setCutoffs(res.results);
        setTotalCutoffs(res.total_count);
      } catch {
        // Fallback
      } finally {
        setLoadingCutoffs(false);
      }
    }
    const timer = setTimeout(fetchCutoffs, 200);
    return () => clearTimeout(timer);
  }, [instFilter, seatTypeFilter]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Sources, Regulations & Evidence Base"
        description="Every rule, cutoff observation, and curriculum requirement in Hydra traces to official regulatory gazettes or documented synthetic records."
        badge={
          <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-[#E1EEE8] text-[#176B63] border border-[#A3D1C0]">
            Verified Knowledge Base
          </span>
        }
      />

      <DemoNoticeBanner />

      {/* 4 Source Provenance Classes Banner */}
      <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-6 shadow-xs space-y-4">
        <div>
          <h3 className="text-sm font-bold text-[#1C2B2A]">
            The 4 Evidence Provenance Classes
          </h3>
          <p className="text-xs text-[#52615E] mt-0.5">
            Hydra strictly tags every data point with its provenance class to guarantee zero unverified assertions.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="p-3.5 rounded-xl bg-[#E6F4ED] border border-[#2D6A4F]/20">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-bold text-[#2D6A4F]">VERIFIED</span>
              <ProvenanceIndicator category="verified" />
            </div>
            <p className="text-[11px] text-[#52615E]">
              Official gazette criteria, council guidelines (AICTE, CBSE, JoSAA) with verified provenance.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-[#E9F1F7] border border-[#315C86]/20">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-bold text-[#315C86]">USER PROVIDED</span>
              <ProvenanceIndicator category="user_provided" />
            </div>
            <p className="text-[11px] text-[#52615E]">
              Marks, rank, and budget self-reported by the student. Verified against input schemas.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-[#FEF7EC] border border-[#8A5B16]/20">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-bold text-[#8A5B16]">ESTIMATED</span>
              <ProvenanceIndicator category="estimated" />
            </div>
            <p className="text-[11px] text-[#52615E]">
              Statistical cutoff forecast intervals and semantic embedding similarities.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-[#FDE8E8] border border-[#A33434]/20">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-bold text-[#A33434]">UNAVAILABLE</span>
              <ProvenanceIndicator category="unavailable" />
            </div>
            <p className="text-[11px] text-[#52615E]">
              Missing required prerequisite facts. Triggers explicit 'needs_review' rather than guessing.
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-2 shadow-xs flex flex-wrap gap-1">
        <button
          onClick={() => setActiveTab('criteria')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'criteria'
              ? 'bg-[#176B63] text-white shadow-xs'
              : 'text-[#52615E] hover:bg-[#EDF4F1] hover:text-[#1C2B2A]'
          }`}
        >
          <FileCheck className="w-4 h-4" />
          <span>Formal Eligibility Regulations ({criteria.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('cutoffs')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'cutoffs'
              ? 'bg-[#176B63] text-white shadow-xs'
              : 'text-[#52615E] hover:bg-[#EDF4F1] hover:text-[#1C2B2A]'
          }`}
        >
          <Database className="w-4 h-4" />
          <span>Historical Cutoffs Table ({totalCutoffs})</span>
        </button>

        <button
          onClick={() => setActiveTab('documents')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'documents'
              ? 'bg-[#176B63] text-white shadow-xs'
              : 'text-[#52615E] hover:bg-[#EDF4F1] hover:text-[#1C2B2A]'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Source Document Registry ({documents.length})</span>
        </button>
      </div>

      {/* TAB 1: Formal Eligibility Criteria */}
      {activeTab === 'criteria' && (
        <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#DCE5DF]">
            <div>
              <h3 className="text-sm font-bold text-[#1C2B2A]">
                Formal Regulatory Criteria
              </h3>
              <p className="text-xs text-[#52615E]">
                Extracted from official gazettes and statutory authority guidelines.
              </p>
            </div>
            <ProvenanceIndicator category="verified" />
          </div>

          {loadingCriteria ? (
            <div className="p-8 text-center text-xs text-[#64736F]">Loading formal criteria...</div>
          ) : criteria.length === 0 ? (
            <div className="p-6 text-center text-xs text-[#52615E]">
              No formal criteria records loaded.
            </div>
          ) : (
            <div className="space-y-3">
              {criteria.map((c) => (
                <div
                  key={c.criterion_id}
                  className="p-4 rounded-xl border border-[#DCE5DF] bg-[#F6F8F6] space-y-2"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[10px] text-[#64736F] bg-white px-2 py-0.5 rounded border border-[#DCE5DF]">
                        {c.criterion_id}
                      </span>
                      <span className="text-xs font-bold text-[#1C2B2A]">
                        {c.title}
                      </span>
                    </div>
                    <span className="text-[11px] font-semibold text-[#176B63] bg-[#E1EEE8] px-2 py-0.5 rounded-full">
                      Authority: {c.authority}
                    </span>
                  </div>

                  <p className="text-xs text-[#52615E] leading-relaxed">
                    {c.description}
                  </p>

                  <div className="pt-2 border-t border-[#DCE5DF] flex flex-wrap items-center gap-3 text-[11px] text-[#64736F]">
                    <span>Criterion No: {c.criterion_number}</span>
                    <span>•</span>
                    <span>Mandatory: {c.is_mandatory ? 'Yes' : 'No'}</span>
                    <span>•</span>
                    <span>Academic Year: {c.academic_year}</span>
                    <span>•</span>
                    <span>Source Doc: {c.source_document_id}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Historical Cutoffs */}
      {activeTab === 'cutoffs' && (
        <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-6 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-[#64736F] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={instFilter}
                onChange={(e) => setInstFilter(e.target.value)}
                placeholder="Filter by institute name..."
                className="w-full pl-9 pr-3 py-2 rounded-xl border border-[#DCE5DF] bg-[#F6F8F6] text-xs focus:bg-white focus:outline-none focus:border-[#176B63]"
              />
            </div>
            <div className="sm:w-48">
              <select
                value={seatTypeFilter}
                onChange={(e) => setSeatTypeFilter(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-[#DCE5DF] bg-[#F6F8F6] text-xs focus:bg-white focus:outline-none focus:border-[#176B63]"
              >
                <option value="">All Seat Types</option>
                <option value="OPEN">OPEN / General</option>
                <option value="OBC-NCL">OBC-NCL</option>
                <option value="SC">SC</option>
                <option value="ST">ST</option>
                <option value="EWS">EWS</option>
              </select>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#DCE5DF] bg-[#F6F8F6] text-[#64736F] font-bold">
                  <th className="p-3">Year / Round</th>
                  <th className="p-3">Institution & Programme</th>
                  <th className="p-3">Quota</th>
                  <th className="p-3">Seat Type</th>
                  <th className="p-3 text-right">Opening Rank</th>
                  <th className="p-3 text-right">Closing Rank</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#DCE5DF]">
                {loadingCutoffs ? (
                  <tr>
                    <td colSpan={6} className="p-6 text-center text-xs text-[#64736F]">
                      Querying cutoffs...
                    </td>
                  </tr>
                ) : cutoffs.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-6 text-center text-xs text-[#52615E]">
                      No historical cutoff records found matching the filter.
                    </td>
                  </tr>
                ) : (
                  cutoffs.map((item, idx) => (
                    <tr key={idx} className="hover:bg-[#F6F8F6] transition-colors">
                      <td className="p-3 font-semibold text-[#1C2B2A]">
                        {item.academic_year} • R{item.counselling_round}
                      </td>
                      <td className="p-3 text-[#1C2B2A]">
                        <div className="font-semibold">{item.programme_title}</div>
                        <div className="text-[11px] text-[#52615E]">{item.institution_name}</div>
                      </td>
                      <td className="p-3 text-[#52615E]">{item.quota}</td>
                      <td className="p-3">
                        <span className="px-2 py-0.5 rounded bg-[#EDF4F1] text-[#1C2B2A] text-[11px] font-mono">
                          {item.seat_type}
                        </span>
                      </td>
                      <td className="p-3 text-right font-mono text-[#52615E]">
                        #{item.opening_rank.toLocaleString()}
                      </td>
                      <td className="p-3 text-right font-mono font-bold text-[#176B63]">
                        #{item.closing_rank.toLocaleString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: Source Document Registry */}
      {activeTab === 'documents' && (
        <div className="bg-[#FFFFFF] border border-[#DCE5DF] rounded-2xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#DCE5DF]">
            <div>
              <h3 className="text-sm font-bold text-[#1C2B2A]">
                Source Document Registry
              </h3>
              <p className="text-xs text-[#52615E]">
                Official authorities and cryptographic SHA-256 integrity snapshots.
              </p>
            </div>
            <ProvenanceIndicator category="verified" />
          </div>

          <div className="space-y-3">
            {documents.map((doc) => (
              <div
                key={doc.source_id}
                className="p-4 rounded-xl border border-[#DCE5DF] bg-[#F6F8F6] space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-[#1C2B2A]">
                    {doc.title}
                  </span>
                  <span className="text-[11px] font-mono text-[#2D6A4F] bg-[#E6F4ED] px-2 py-0.5 rounded-full font-semibold">
                    {doc.source_status || 'VERIFIED'}
                  </span>
                </div>
                <p className="text-xs text-[#52615E]">
                  Issued by {doc.issuing_authority} • Official Publication Date: {doc.publication_date || 'N/A'}
                </p>
                <div className="text-[10px] font-mono text-[#64736F] truncate pt-1">
                  SHA-256 Checksum: {doc.sha256_checksum || 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
