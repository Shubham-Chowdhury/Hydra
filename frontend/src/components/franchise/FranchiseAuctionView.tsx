import React, { useState, useEffect } from 'react';
import type {
  AuctionResultDto,
  AuctionRankingItemDto,
  StudentProfileRequest,
  TwinSnapshotDto,
} from '../../api/types';
import { hydraApi, ApiError } from '../../api/client';
import {
  Play,
  RotateCw,
  CheckCircle2,
  AlertCircle,
  XCircle,
} from 'lucide-react';

interface FranchiseAuctionViewProps {
  currentSnapshot?: TwinSnapshotDto | null;
  profile?: StudentProfileRequest;
}

export const FranchiseAuctionView: React.FC<FranchiseAuctionViewProps> = ({
  currentSnapshot,
  profile,
}) => {
  const [auctionResult, setAuctionResult] = useState<AuctionResultDto | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedBidId, setExpandedBidId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'all' | 'unconditional' | 'conditional' | 'no_bid'>('all');

  useEffect(() => {
    const handleVoiceAuctionRun = () => {
      runAuction();
    };
    window.addEventListener('hydra:run_auction', handleVoiceAuctionRun);
    return () => window.removeEventListener('hydra:run_auction', handleVoiceAuctionRun);
  }, [currentSnapshot, profile]);

  const runAuction = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = currentSnapshot?.snapshot_id
        ? { snapshot_id: currentSnapshot.snapshot_id }
        : profile
        ? { profile }
        : {};

      const result = await hydraApi.runProgrammeAuction(payload);
      setAuctionResult(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`Auction failed: ${err.message}`);
      } else {
        setError('Failed to run simulated programme auction.');
      }
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'unconditional_candidate':
        return (
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500 text-white shadow-2xs">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Unconditional Candidate</span>
          </span>
        );
      case 'conditional_candidate':
        return (
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-900 border border-amber-300 shadow-2xs">
            <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
            <span>Conditional (Needs Review)</span>
          </span>
        );
      case 'no_bid':
        return (
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-300 shadow-2xs">
            <XCircle className="w-3.5 h-3.5 text-rose-600" />
            <span>No Bid (Ineligible)</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-700">
            {status}
          </span>
        );
    }
  };

  const filteredBids: AuctionRankingItemDto[] = auctionResult
    ? activeTab === 'all'
      ? auctionResult.ranked_bids
      : activeTab === 'unconditional'
      ? auctionResult.unconditional_candidates
      : activeTab === 'conditional'
      ? auctionResult.conditional_candidates
      : auctionResult.no_bid_candidates
    : [];

  return (
    <div className="space-y-6 text-[#111215]">
      {/* Control & Twin Context Panel */}
      <div className="bg-white rounded-3xl p-6 border border-gray-200/70 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl">🏛️</span>
              <h2 className="text-2xl font-bold tracking-tight text-[#111215]">
                Franchise Agents & Simulated Programme Auction
              </h2>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Autonomous Franchise Agents bid on candidates based on academic prerequisites, preference alignment, and tuition affordability.
            </p>
          </div>

          <button
            onClick={runAuction}
            disabled={loading || (!currentSnapshot && !profile)}
            className="px-6 py-3 rounded-full bg-[#111215] hover:bg-black text-white font-bold text-xs shadow-md transition-all hover:scale-105 active:scale-95 disabled:opacity-50 flex items-center gap-2 shrink-0 cursor-pointer"
          >
            {loading ? (
              <>
                <RotateCw className="w-4 h-4 animate-spin text-[#E8F84A]" />
                <span>Simulating Multi-Agent Bids...</span>
              </>
            ) : (
              <>
                <span>Run Simulated Auction</span>
                <Play className="w-3.5 h-3.5 fill-[#E8F84A] text-[#E8F84A]" />
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="mt-4 p-3 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium">
            {error}
          </div>
        )}
      </div>

      {/* Auction Results View */}
      {auctionResult && (
        <div className="space-y-6 animate-in fade-in duration-300">
          {/* Summary Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-3xl border border-gray-200/70 p-5 shadow-xs">
              <div className="text-xs font-semibold text-gray-500">Total Bids</div>
              <div className="text-3xl font-extrabold text-[#111215] mt-1">{auctionResult.total_bids}</div>
              <div className="text-[11px] text-gray-400 mt-0.5">Policy: {auctionResult.policy_version}</div>
            </div>

            <div className="bg-emerald-50/70 rounded-3xl border border-emerald-200 p-5 shadow-xs">
              <div className="text-xs font-semibold text-emerald-800">Unconditional Candidates</div>
              <div className="text-3xl font-extrabold text-emerald-950 mt-1">
                {auctionResult.unconditional_candidates.length}
              </div>
              <div className="text-[11px] text-emerald-700 mt-0.5">Full Prerequisite Match</div>
            </div>

            <div className="bg-amber-50/70 rounded-3xl border border-amber-200 p-5 shadow-xs">
              <div className="text-xs font-semibold text-amber-800">Conditional Candidates</div>
              <div className="text-3xl font-extrabold text-amber-950 mt-1">
                {auctionResult.conditional_candidates.length}
              </div>
              <div className="text-[11px] text-amber-700 mt-0.5">Verification Pending</div>
            </div>

            <div className="bg-rose-50/70 rounded-3xl border border-rose-200 p-5 shadow-xs">
              <div className="text-xs font-semibold text-rose-800">No Bid (Ineligible)</div>
              <div className="text-3xl font-extrabold text-rose-950 mt-1">
                {auctionResult.no_bid_candidates.length}
              </div>
              <div className="text-[11px] text-rose-700 mt-0.5">Criteria Deficit</div>
            </div>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
            {[
              { id: 'all', label: `All Proposals (${auctionResult.ranked_bids.length})` },
              { id: 'unconditional', label: `Unconditional (${auctionResult.unconditional_candidates.length})` },
              { id: 'conditional', label: `Conditional (${auctionResult.conditional_candidates.length})` },
              { id: 'no_bid', label: `No-Bid (${auctionResult.no_bid_candidates.length})` },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-4 py-2 rounded-full font-semibold transition-all cursor-pointer ${
                  activeTab === tab.id
                    ? 'bg-[#111215] text-white shadow-xs'
                    : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200/60 shadow-2xs'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Ranked Bids List */}
          <div className="space-y-4">
            {filteredBids.map((item) => {
              const { rank, bid, explanation } = item;
              const isExpanded = expandedBidId === bid.bid_id;
              const fitPercent = bid.composite_preference_score !== null ? (bid.composite_preference_score * 100).toFixed(0) : '0';

              return (
                <div
                  key={bid.bid_id}
                  className={`bg-white rounded-3xl border p-5 transition-all shadow-xs hover:shadow-md ${
                    bid.proposal_status === 'unconditional_candidate'
                      ? 'border-gray-200/80 hover:border-gray-300'
                      : 'border-gray-200/60'
                  }`}
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    {/* Left: Rank & Title */}
                    <div className="flex items-start gap-3 flex-1 min-w-0">
                      <div
                        className={`w-10 h-10 rounded-2xl flex items-center justify-center font-bold text-sm shrink-0 shadow-xs ${
                          rank === 1
                            ? 'bg-amber-400 text-black'
                            : rank === 2
                            ? 'bg-gray-300 text-black'
                            : rank === 3
                            ? 'bg-amber-700 text-white'
                            : 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        #{rank}
                      </div>

                      <div className="space-y-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="font-bold text-base text-[#111215] truncate">
                            {bid.programme_title}
                          </h3>
                          {getStatusBadge(bid.proposal_status)}
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">
                            {bid.programme_id}
                          </span>
                        </div>

                        <p className="text-xs text-gray-500 flex items-center gap-1.5">
                          <span>{bid.institution_name}</span>
                          <span>•</span>
                          <span className="font-mono text-[11px] text-gray-400">Agent: {bid.agent_id}</span>
                        </p>
                      </div>
                    </div>

                    {/* Right: Score, Tuition & Action */}
                    <div className="flex items-center gap-5 self-end md:self-auto shrink-0">
                      {/* Preference Fit */}
                      <div className="text-right">
                        <div className="text-[11px] text-gray-500 font-semibold">Preference Fit</div>
                        <div className="text-lg font-extrabold text-[#111215]">{fitPercent}%</div>
                      </div>

                      {/* Tuition */}
                      <div className="text-right">
                        <div className="text-[11px] text-gray-500 font-semibold">Total Tuition</div>
                        <div className="text-sm font-bold text-[#111215]">
                          ₹{(bid.estimated_total_tuition_inr / 100000).toFixed(2)} Lakh
                        </div>
                        <span
                          className={`text-[10px] font-bold ${
                            bid.affordability_status ? 'text-emerald-600' : 'text-rose-600'
                          }`}
                        >
                          {bid.affordability_status ? '✓ Affordable' : '⚠ Exceeds Budget'}
                        </span>
                      </div>

                      {/* Expand Audit Trace */}
                      <button
                        onClick={() => setExpandedBidId(isExpanded ? null : bid.bid_id)}
                        className="px-3.5 py-2 rounded-2xl bg-gray-50 hover:bg-gray-100 border border-gray-200 text-xs font-semibold text-gray-800 transition-colors cursor-pointer shadow-2xs"
                      >
                        {isExpanded ? 'Hide Trace' : 'Audit Trace ⌄'}
                      </button>
                    </div>
                  </div>

                  {/* Summary Explanation */}
                  <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-600 flex flex-wrap items-center justify-between gap-2">
                    <p className="leading-relaxed">{explanation}</p>
                    <div className="flex items-center gap-1 text-[11px] font-semibold text-gray-500">
                      <span>Dimensions:</span>
                      <span className="px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">
                        {bid.active_dimensions?.length || 4}/4 Verified
                      </span>
                    </div>
                  </div>

                  {/* Expanded Trace Drawer */}
                  {isExpanded && (
                    <div className="mt-4 p-4 bg-gray-50/80 rounded-2xl border border-gray-200/80 text-xs space-y-3 animate-in fade-in duration-150">
                      <div className="font-bold text-gray-900">Franchise Auction Bidding Trace:</div>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px]">
                        <div className="p-2.5 bg-white rounded-xl border border-gray-200/60">
                          <div className="text-gray-400">Proposal</div>
                          <div className="font-bold text-[#111215] mt-0.5">{bid.proposal_status}</div>
                        </div>
                        <div className="p-2.5 bg-white rounded-xl border border-gray-200/60">
                          <div className="text-gray-400">Composite Score</div>
                          <div className="font-bold text-[#111215] mt-0.5">{fitPercent}%</div>
                        </div>
                        <div className="p-2.5 bg-white rounded-xl border border-gray-200/60">
                          <div className="text-gray-400">Evidence Tier</div>
                          <div className="font-bold text-[#111215] mt-0.5">{bid.evidence_tier}</div>
                        </div>
                        <div className="p-2.5 bg-white rounded-xl border border-gray-200/60">
                          <div className="text-gray-400">Tie-Breaker</div>
                          <div className="font-bold text-[#111215] mt-0.5">{item.tie_breaker_applied || 'None'}</div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
