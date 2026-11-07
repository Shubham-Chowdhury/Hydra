import React, { useState } from 'react';
import {
  X,
  Scale,
  Landmark,
  Route,
  Swords,
  LineChart,
  Brain,
  UserCheck,
  ShieldAlert,
} from 'lucide-react';
import type {
  ProgrammeEvaluationDto,
  ProgrammeResponse,
  StudentProfileRequest,
} from '../../api/types';
import { CentralRefereeView } from '../referee/CentralRefereeView';
import { StudentDigitalTwinView } from '../twin/StudentDigitalTwinView';
import { FranchiseAuctionView } from '../franchise/FranchiseAuctionView';
import { HeistPlannerView } from '../planner/HeistPlannerView';
import { SimulatorBossFightView } from '../simulation/SimulatorBossFightView';
import { OracleForecastView } from '../oracle/OracleForecastView';
import { InterestDecoderView } from '../interests/InterestDecoderView';

interface TechnicalDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  profile?: StudentProfileRequest;
  programmes: ProgrammeResponse[];
  evaluations: ProgrammeEvaluationDto[];
}

export const TechnicalDrawer: React.FC<TechnicalDrawerProps> = ({
  isOpen,
  onClose,
  profile,
  programmes,
}) => {
  const [activeTab, setActiveTab] = useState<
    'referee' | 'twin' | 'franchise' | 'planner' | 'simulation' | 'oracle' | 'interests'
  >('referee');

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 overflow-hidden bg-[#1C2B2A]/40 backdrop-blur-xs flex justify-end"
      aria-labelledby="technical-drawer-title"
      role="dialog"
      aria-modal="true"
    >
      <div className="w-full max-w-5xl bg-[#FFFFFF] h-full shadow-2xl flex flex-col border-l border-[#DCE5DF]">
        {/* Drawer Header */}
        <div className="p-4 border-b border-[#DCE5DF] bg-[#F6F8F6] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#315C86] text-white flex items-center justify-center">
              <Scale className="w-4 h-4" />
            </div>
            <div>
              <h2 id="technical-drawer-title" className="text-sm font-bold text-[#1C2B2A]">
                Technical Audit & Multi-Agent Inspection
              </h2>
              <p className="text-xs text-[#64736F]">
                Inspection panel for counsellors, auditors, and systems engineers.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#FEF7EC] text-[#8A5B16] text-[11px] font-medium border border-[#E9C46A]/40">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Diagnostic Core View</span>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-[#64736F] hover:bg-[#EDF4F1] hover:text-[#1C2B2A] transition-colors"
              aria-label="Close Technical Drawer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Tab Selector Bar */}
        <div className="px-4 py-2 border-b border-[#DCE5DF] bg-[#FFFFFF] overflow-x-auto scrollbar-none flex gap-1">
          <button
            onClick={() => setActiveTab('referee')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 whitespace-nowrap transition-colors ${
              activeTab === 'referee'
                ? 'bg-[#176B63] text-white'
                : 'text-[#52615E] hover:bg-[#EDF4F1]'
            }`}
          >
            <Scale className="w-3.5 h-3.5" />
            Central Referee
          </button>
          <button
            onClick={() => setActiveTab('twin')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 whitespace-nowrap transition-colors ${
              activeTab === 'twin'
                ? 'bg-[#176B63] text-white'
                : 'text-[#52615E] hover:bg-[#EDF4F1]'
            }`}
          >
            <UserCheck className="w-3.5 h-3.5" />
            Digital Twin
          </button>
          <button
            onClick={() => setActiveTab('franchise')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 whitespace-nowrap transition-colors ${
              activeTab === 'franchise'
                ? 'bg-[#176B63] text-white'
                : 'text-[#52615E] hover:bg-[#EDF4F1]'
            }`}
          >
            <Landmark className="w-3.5 h-3.5" />
            Franchise Auction
          </button>
          <button
            onClick={() => setActiveTab('planner')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 whitespace-nowrap transition-colors ${
              activeTab === 'planner'
                ? 'bg-[#176B63] text-white'
                : 'text-[#52615E] hover:bg-[#EDF4F1]'
            }`}
          >
            <Route className="w-3.5 h-3.5" />
            A* Planner
          </button>
          <button
            onClick={() => setActiveTab('simulation')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 whitespace-nowrap transition-colors ${
              activeTab === 'simulation'
                ? 'bg-[#176B63] text-white'
                : 'text-[#52615E] hover:bg-[#EDF4F1]'
            }`}
          >
            <Swords className="w-3.5 h-3.5" />
            Simulation & Stress-Test
          </button>
          <button
            onClick={() => setActiveTab('oracle')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 whitespace-nowrap transition-colors ${
              activeTab === 'oracle'
                ? 'bg-[#176B63] text-white'
                : 'text-[#52615E] hover:bg-[#EDF4F1]'
            }`}
          >
            <LineChart className="w-3.5 h-3.5" />
            Oracle Cutoff Forecast
          </button>
          <button
            onClick={() => setActiveTab('interests')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 whitespace-nowrap transition-colors ${
              activeTab === 'interests'
                ? 'bg-[#176B63] text-white'
                : 'text-[#52615E] hover:bg-[#EDF4F1]'
            }`}
          >
            <Brain className="w-3.5 h-3.5" />
            Interest Decoder
          </button>
        </div>

        {/* Tab Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 bg-[#F6F8F6]">
          {activeTab === 'referee' && <CentralRefereeView profile={profile} />}
          {activeTab === 'twin' && <StudentDigitalTwinView />}
          {activeTab === 'franchise' && <FranchiseAuctionView profile={profile} />}
          {activeTab === 'planner' && <HeistPlannerView profile={profile} />}
          {activeTab === 'simulation' && <SimulatorBossFightView profile={profile} />}
          {activeTab === 'oracle' && <OracleForecastView programmes={programmes} />}
          {activeTab === 'interests' && <InterestDecoderView />}
        </div>
      </div>
    </div>
  );
};

