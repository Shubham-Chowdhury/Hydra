import React, { useState } from 'react';
import {
  TrendingUp,
  Compass,
  FileText,
  ThumbsUp,
  Send,
  Sparkles,
  User,
  History,
  ChevronDown,
} from 'lucide-react';
import type { StudentProfileRequest } from '../../api/types';

interface FloatingCommandConsoleProps {
  isAnalysisOpen: boolean;
  onToggleAnalysis: () => void;
  onSearch: (query: string) => void;
  profile?: StudentProfileRequest;
  onSelectPreset: (preset: 'eligible' | 'ineligible' | 'needs_review' | 'unaffordable') => void;
  eligibleRate: number;
  totalProgrammes: number;
  verifiedFactsCount: number;
  affordabilityRate: number;
}

export const FloatingCommandConsole: React.FC<FloatingCommandConsoleProps> = ({
  isAnalysisOpen,
  onToggleAnalysis,
  onSearch,
  profile,
  onSelectPreset,
  eligibleRate = 91,
  totalProgrammes = 165,
  verifiedFactsCount = 154,
  affordabilityRate = 75,
}) => {
  const [inputVal, setInputVal] = useState('');
  const [isTwinMenuOpen, setIsTwinMenuOpen] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputVal.trim()) {
      onSearch(inputVal.trim());
    }
  };

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 w-[760px] max-w-[95vw] z-40 select-none">
      <div className="bg-[#0C1518]/90 backdrop-blur-2xl border border-[#1E343D] rounded-3xl p-4 shadow-2xl space-y-3 glow-border-cyan">
        {/* Top KPI Metrics Row */}
        <div className="grid grid-cols-4 divide-x divide-[#1E343D] text-center py-1">
          {/* Metric 1: Compliance / Eligibility Rate */}
          <div className="px-2">
            <div className="text-[10px] uppercase tracking-wider text-[#8DA1A8] font-medium truncate">
              Compliance Rate
            </div>
            <div className="flex items-center justify-center gap-1.5 mt-0.5">
              <TrendingUp className="w-3.5 h-3.5 text-[#3DD9C4]" />
              <span className="text-sm font-black font-mono text-[#F0F4F5]">
                {eligibleRate}%
              </span>
            </div>
          </div>

          {/* Metric 2: Total Programmes */}
          <div className="px-2">
            <div className="text-[10px] uppercase tracking-wider text-[#8DA1A8] font-medium truncate">
              Total Catalog
            </div>
            <div className="flex items-center justify-center gap-1.5 mt-0.5">
              <Compass className="w-3.5 h-3.5 text-[#E5B869]" />
              <span className="text-sm font-black font-mono text-[#F0F4F5]">
                {totalProgrammes} <span className="text-[10px] font-normal text-[#8DA1A8]">K</span>
              </span>
            </div>
          </div>

          {/* Metric 3: Verified Facts */}
          <div className="px-2">
            <div className="text-[10px] uppercase tracking-wider text-[#8DA1A8] font-medium truncate">
              Public Engagement
            </div>
            <div className="flex items-center justify-center gap-1.5 mt-0.5">
              <FileText className="w-3.5 h-3.5 text-[#4A90E2]" />
              <span className="text-sm font-black font-mono text-[#F0F4F5]">
                {verifiedFactsCount} <span className="text-[10px] font-normal text-[#8DA1A8]">K</span>
              </span>
            </div>
          </div>

          {/* Metric 4: Affordability Rate */}
          <div className="px-2">
            <div className="text-[10px] uppercase tracking-wider text-[#8DA1A8] font-medium truncate">
              Implementation Rate
            </div>
            <div className="flex items-center justify-center gap-1.5 mt-0.5">
              <ThumbsUp className="w-3.5 h-3.5 text-[#3DD9C4]" />
              <span className="text-sm font-black font-mono text-[#F0F4F5]">
                {affordabilityRate}%
              </span>
            </div>
          </div>
        </div>

        {/* Search / Action Input Bar */}
        <form onSubmit={handleSubmit} className="relative">
          <input
            type="text"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            placeholder="Ask a question, enter rank, or search programmes..."
            className="w-full pl-5 pr-14 py-3 rounded-2xl bg-[#E8EFF0] text-[#0C1518] placeholder-[#6A7F85] text-xs sm:text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#3DD9C4] transition-all shadow-inner"
          />

          <button
            type="submit"
            className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-xl bg-[#16272E] hover:bg-[#203640] text-[#3DD9C4] flex items-center justify-center transition-transform hover:scale-105 active:scale-95 shadow-md"
            aria-label="Submit Question"
          >
            <Send className="w-4 h-4 ml-0.5" />
          </button>
        </form>

        {/* Bottom Toolbar */}
        <div className="flex items-center justify-between pt-0.5">
          {/* Left: Twin Profile Selector */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setIsTwinMenuOpen(!isTwinMenuOpen)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#142227] hover:bg-[#1C2F36] border border-[#233F4A] text-xs font-semibold text-[#8DA1A8] hover:text-[#F0F4F5] transition-colors"
            >
              <User className="w-3.5 h-3.5 text-[#3DD9C4]" />
              <span>{profile?.student_id || 'My Agent'}</span>
              <ChevronDown className="w-3 h-3 text-[#576A70]" />
            </button>

            {isTwinMenuOpen && (
              <div className="absolute left-0 bottom-10 w-72 bg-[#0C1417] border border-[#1E343D] rounded-2xl p-2 shadow-2xl space-y-1 z-50">
                <div className="px-2 py-1 text-[10px] uppercase font-bold text-[#576A70]">
                  Testing / Demo Scenarios (Synthetic):
                </div>
                <button
                  onClick={() => {
                    onSelectPreset('eligible');
                    setIsTwinMenuOpen(false);
                  }}
                  className="w-full text-left px-3 py-1.5 rounded-lg text-xs hover:bg-[#16272E] text-[#3DD9C4] flex items-center justify-between"
                  title="Loads synthetic test profile matching all prerequisites"
                >
                  <span>Demo: Full Match (88% Math, JEE 18.5k)</span>
                </button>
                <button
                  onClick={() => {
                    onSelectPreset('ineligible');
                    setIsTwinMenuOpen(false);
                  }}
                  className="w-full text-left px-3 py-1.5 rounded-lg text-xs hover:bg-[#16272E] text-[#E05263] flex items-center justify-between"
                  title="Loads synthetic test profile with prerequisite deficit"
                >
                  <span>Demo: Deficit (65% Math, JEE 38k)</span>
                </button>
                <button
                  onClick={() => {
                    onSelectPreset('needs_review');
                    setIsTwinMenuOpen(false);
                  }}
                  className="w-full text-left px-3 py-1.5 rounded-lg text-xs hover:bg-[#16272E] text-[#E5B869] flex items-center justify-between"
                  title="Loads synthetic test profile with missing facts"
                >
                  <span>Demo: Missing Fact (Omit Subject)</span>
                </button>
                <button
                  onClick={() => {
                    onSelectPreset('unaffordable');
                    setIsTwinMenuOpen(false);
                  }}
                  className="w-full text-left px-3 py-1.5 rounded-lg text-xs hover:bg-[#16272E] text-[#8DA1A8] flex items-center justify-between"
                  title="Loads synthetic test profile with budget limit"
                >
                  <span>Demo: Budget Shortfall (₹4.5L Total)</span>
                </button>
              </div>
            )}
          </div>

          {/* Center: Scenario History pill */}
          <div className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-[#142227] border border-[#233F4A] text-xs font-mono text-[#8DA1A8]">
            <History className="w-3.5 h-3.5 text-[#E5B869]" />
            <span>+3 Scenarios</span>
          </div>

          {/* Right: RI / Pathway Analysis Toggle Button */}
          <button
            type="button"
            onClick={onToggleAnalysis}
            className={`flex items-center gap-1.5 px-4 py-1.5 rounded-xl text-xs font-bold transition-all shadow-md ${
              isAnalysisOpen
                ? 'bg-[#3DD9C4] text-[#070B0E] glow-cyan'
                : 'bg-[#142227] hover:bg-[#1C2F36] border border-[#233F4A] text-[#3DD9C4]'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>RI Analysis</span>
          </button>
        </div>
      </div>
    </div>
  );
};

