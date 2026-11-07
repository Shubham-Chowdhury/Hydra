import React from 'react';
import {
  LayoutDashboard,
  UserCheck,
  GraduationCap,
  Scale,
  Route,
  Briefcase,
  ShieldCheck,
  HelpCircle,
} from 'lucide-react';
import type { NavigationDestination } from './StudentSidebar';

interface MobileNavigationProps {
  currentDestination: NavigationDestination;
  onNavigate: (destination: NavigationDestination) => void;
  comparedCount: number;
}

export const MobileNavigation: React.FC<MobileNavigationProps> = ({
  currentDestination,
  onNavigate,
  comparedCount,
}) => {
  const tabs: Array<{
    id: NavigationDestination;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    badge?: number;
  }> = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'profile', label: 'Profile', icon: UserCheck },
    { id: 'programmes', label: 'Explore', icon: GraduationCap },
    { id: 'compare', label: 'Compare', icon: Scale, badge: comparedCount > 0 ? comparedCount : undefined },
    { id: 'plan', label: 'Plan', icon: Route },
    { id: 'careers', label: 'Careers', icon: Briefcase },
    { id: 'sources', label: 'Evidence', icon: ShieldCheck },
    { id: 'help', label: 'Help', icon: HelpCircle },
  ];

  return (
    <nav
      className="md:hidden bg-[#0C1518]/95 backdrop-blur-xl border-b border-[#1E343D] overflow-x-auto scrollbar-none sticky top-14 z-30 shadow-md"
      aria-label="Mobile Navigation"
    >
      <div className="flex items-center px-2 py-1.5 space-x-1 min-w-max">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = currentDestination === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onNavigate(tab.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all ${
                isActive
                  ? 'bg-[#3DD9C4] text-[#070B0E] glow-cyan shadow-sm'
                  : 'text-[#8DA1A8] hover:text-[#F0F4F5] hover:bg-[#142227]'
              }`}
            >
              <Icon className="w-3.5 h-3.5 shrink-0" />
              <span>{tab.label}</span>
              {tab.badge !== undefined && (
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded-full font-black ${
                    isActive ? 'bg-[#070B0E] text-[#3DD9C4]' : 'bg-[#E5B869] text-[#070B0E]'
                  }`}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
};

