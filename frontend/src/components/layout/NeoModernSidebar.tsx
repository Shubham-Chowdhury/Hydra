import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  Network,
  Layers,
  Link as LinkIcon,
  Globe,
  MoreHorizontal,
  BookOpen,
  Rocket,
  HelpCircle,
  Route,
  Swords,
  LineChart,
  Brain,
  Scale,
  Mic,
  Volume2,
} from 'lucide-react';
import type { NavigationDestination } from './StudentSidebar';
import { voiceManager, type VoiceState } from '../../services/voiceManager';

interface NeoModernSidebarProps {
  currentDestination: NavigationDestination;
  onNavigate: (dest: NavigationDestination) => void;
  onOpenProfile: () => void;
  comparedCount: number;
}

export const NeoModernSidebar: React.FC<NeoModernSidebarProps> = ({
  currentDestination,
  onNavigate,
  onOpenProfile,
  comparedCount,
}) => {
  const [showMoreMenu, setShowMoreMenu] = useState<boolean>(false);
  const [voiceState, setVoiceState] = useState<VoiceState>(voiceManager.getState());

  useEffect(() => {
    return voiceManager.subscribeState((state) => {
      setVoiceState(state);
    });
  }, []);

  const mainNavItems = [
    { id: 'overview', icon: LayoutDashboard, label: 'Overview' },
    { id: 'referee', icon: Network, label: 'Central Referee' },
    { id: 'programmes', icon: Layers, label: 'Catalogue' },
    { id: 'twin', icon: LinkIcon, label: 'Twin Engine' },
    { id: 'franchise', icon: Globe, label: 'Franchise Auction' },
  ];

  const agentSubmenu = [
    { id: 'planner', icon: Route, label: 'Heist Planner' },
    { id: 'simulation', icon: Swords, label: 'Simulator & Boss-Fight' },
    { id: 'oracle', icon: LineChart, label: 'Oracle Forecast' },
    { id: 'interests', icon: Brain, label: 'Interest Decoder' },
    { id: 'compare', icon: Scale, label: `Compare (${comparedCount})` },
  ];

  return (
    <aside className="hidden md:flex flex-col items-center justify-between w-16 sm:w-[68px] bg-[#111215] text-white rounded-3xl py-5 px-2 shadow-lg shrink-0 select-none z-30 h-full">
      {/* Top App Icon Squircle */}
      <div className="flex flex-col items-center gap-3">
        <button
          onClick={() => onNavigate('overview')}
          className="w-11 h-11 rounded-2xl bg-[#202227] hover:bg-[#282B32] flex items-center justify-center text-white shadow-2xs transition-transform hover:scale-105"
          title="Hydra Academic AI"
          aria-label="Hydra Home"
        >
          <div className="w-5 h-5 rounded-full border-2 border-emerald-400 flex items-center justify-center text-[10px] font-black text-emerald-400">
            H
          </div>
        </button>

        {/* Primary Navigation Stack */}
        <div className="flex flex-col items-center gap-1.5 mt-2">
          {mainNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentDestination === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setShowMoreMenu(false);
                  onNavigate(item.id as NavigationDestination);
                }}
                className={`w-11 h-11 rounded-2xl flex items-center justify-center transition-all ${
                  isActive
                    ? 'bg-[#24262C] text-white shadow-xs scale-100'
                    : 'text-gray-400 hover:text-white hover:bg-white/10'
                }`}
                title={item.label}
                aria-label={item.label}
              >
                <Icon className="w-5 h-5" />
              </button>
            );
          })}

          {/* More Agents Popover Trigger */}
          <div className="relative">
            <button
              onClick={() => setShowMoreMenu(!showMoreMenu)}
              className={`w-11 h-11 rounded-2xl flex items-center justify-center transition-all ${
                showMoreMenu || ['planner', 'simulation', 'oracle', 'interests', 'compare'].includes(currentDestination)
                  ? 'bg-[#24262C] text-white'
                  : 'text-gray-400 hover:text-white hover:bg-white/10'
              }`}
              title="More Agents & Tools"
              aria-label="More Agents"
            >
              <MoreHorizontal className="w-5 h-5" />
            </button>

            {/* Floating popover for agents */}
            {showMoreMenu && (
              <div
                className="absolute left-14 top-0 w-52 bg-[#1A1C21] border border-gray-700/80 rounded-2xl shadow-2xl p-2 text-xs z-50 animate-in fade-in zoom-in-95 duration-100"
                onMouseLeave={() => setShowMoreMenu(false)}
              >
                <div className="px-2 py-1.5 text-[10px] font-bold uppercase tracking-wider text-gray-400 border-b border-gray-800">
                  Specialized Agents
                </div>
                <div className="space-y-1 mt-1">
                  {agentSubmenu.map((sub) => {
                    const SubIcon = sub.icon;
                    const isSubActive = currentDestination === sub.id;
                    return (
                      <button
                        key={sub.id}
                        onClick={() => {
                          setShowMoreMenu(false);
                          onNavigate(sub.id as NavigationDestination);
                        }}
                        className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-left transition-colors ${
                          isSubActive
                            ? 'bg-[#E8F84A] text-[#111215] font-bold'
                            : 'text-gray-300 hover:bg-white/10 hover:text-white'
                        }`}
                      >
                        <SubIcon className="w-4 h-4" />
                        <span>{sub.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Dedicated Voice Assistant Button (Beneath More Agents & Tools) */}
          <button
            onClick={() => {
              setShowMoreMenu(false);
              voiceManager.toggleListening();
            }}
            className={`w-11 h-11 rounded-2xl flex items-center justify-center transition-all relative group cursor-pointer ${
              voiceState === 'listening'
                ? 'bg-[#111215] text-[#CCFF00] border border-[#CCFF00] shadow-[0_0_12px_rgba(204,255,0,0.6)]'
                : voiceState === 'speaking'
                ? 'bg-[#0284C7] text-white shadow-[0_0_12px_rgba(2,132,199,0.5)]'
                : voiceState === 'requesting'
                ? 'bg-amber-400 text-black animate-pulse'
                : 'bg-[#202227] hover:bg-[#282B32] text-gray-300 hover:text-white border border-gray-700/60 shadow-2xs'
            }`}
            title="Hydra Voice Guide (Click to Speak anywhere)"
            aria-label="Hydra Voice Guide"
          >
            {voiceState === 'listening' ? (
              <Mic className="w-5 h-5 text-[#CCFF00]" />
            ) : voiceState === 'speaking' ? (
              <Volume2 className="w-5 h-5 text-white" />
            ) : (
              <Mic className="w-5 h-5 text-[#E8F84A] group-hover:scale-110 transition-transform" />
            )}
            <span
              className={`absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full border-2 border-[#111215] ${
                voiceState === 'listening'
                  ? 'bg-[#CCFF00]'
                  : voiceState === 'speaking'
                  ? 'bg-sky-400'
                  : 'bg-emerald-500'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Lower Navigation Section: Knowledge, Simulation, Help & Profile Avatar */}
      <div className="flex flex-col items-center gap-2">
        <button
          onClick={() => onNavigate('sources')}
          className={`w-11 h-11 rounded-2xl flex items-center justify-center transition-all ${
            currentDestination === 'sources'
              ? 'bg-[#24262C] text-white'
              : 'text-gray-400 hover:text-white hover:bg-white/10'
          }`}
          title="Admissions Directory & Sources"
          aria-label="Admissions Directory"
        >
          <BookOpen className="w-5 h-5" />
        </button>

        <button
          onClick={() => onNavigate('simulation')}
          className={`w-11 h-11 rounded-2xl flex items-center justify-center transition-all ${
            currentDestination === 'simulation'
              ? 'bg-[#24262C] text-white'
              : 'text-gray-400 hover:text-white hover:bg-white/10'
          }`}
          title="Simulator & Boss-Fight"
          aria-label="Simulation"
        >
          <Rocket className="w-5 h-5" />
        </button>

        <button
          onClick={() => onNavigate('help')}
          className={`w-11 h-11 rounded-2xl flex items-center justify-center transition-all ${
            currentDestination === 'help'
              ? 'bg-[#24262C] text-white'
              : 'text-gray-400 hover:text-white hover:bg-white/10'
          }`}
          title="Help & Guidance"
          aria-label="Help"
        >
          <HelpCircle className="w-5 h-5" />
        </button>

        {/* Student Profile Portrait Avatar */}
        <button
          onClick={onOpenProfile}
          className="relative w-10 h-10 rounded-full overflow-hidden border-2 border-white/20 hover:border-[#E8F84A] hover:scale-105 transition-all mt-2 focus:outline-none"
          title="Student Profile Settings"
          aria-label="Student Profile"
        >
          <svg viewBox="0 0 100 100" className="w-full h-full object-cover bg-amber-900">
            <circle cx="50" cy="50" r="50" fill="#2E1A47" />
            <circle cx="50" cy="38" r="20" fill="#D97706" />
            <path d="M 20 90 C 20 65, 80 65, 80 90 Z" fill="#F59E0B" />
            <circle cx="43" cy="36" r="3" fill="#1E1B4B" />
            <circle cx="57" cy="36" r="3" fill="#1E1B4B" />
            {/* Curly hair outline */}
            <circle cx="34" cy="28" r="7" fill="#1E1B4B" />
            <circle cx="45" cy="22" r="8" fill="#1E1B4B" />
            <circle cx="56" cy="22" r="8" fill="#1E1B4B" />
            <circle cx="66" cy="28" r="7" fill="#1E1B4B" />
          </svg>
          <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-400 border border-[#111215]" />
        </button>
      </div>
    </aside>
  );
};
