import React, { useState, useEffect, useCallback } from 'react';
import type {
  EvaluationResponse,
  ProgrammeEvaluationDto,
  ProgrammeResponse,
  StudentProfileRequest,
} from './api/types';
import { hydraApi, ApiError } from './api/client';

import { NeoModernSidebar } from './components/layout/NeoModernSidebar';
import { NeoModernDashboard } from './components/dashboard/NeoModernDashboard';
import { MobileNavigation } from './components/layout/MobileNavigation';
import { type NavigationDestination } from './components/layout/StudentSidebar';
import { TechnicalDrawer } from './components/layout/TechnicalDrawer';

// Agent Views
import { CentralRefereeView } from './components/referee/CentralRefereeView';
import { StudentDigitalTwinView } from './components/twin/StudentDigitalTwinView';
import { FranchiseAuctionView } from './components/franchise/FranchiseAuctionView';
import { HeistPlannerView } from './components/planner/HeistPlannerView';
import { SimulatorBossFightView } from './components/simulation/SimulatorBossFightView';
import { OracleForecastView } from './components/oracle/OracleForecastView';
import { InterestDecoderView } from './components/interests/InterestDecoderView';
import { CareerExplorationView } from './components/interests/CareerExplorationView';

// Core Academic Views
import { ProgrammeDiscoveryView } from './components/programmes/ProgrammeDiscoveryView';
import { ProgrammeCompareView } from './components/programmes/ProgrammeCompareView';
import { StudentActionPlanView } from './components/plan/StudentActionPlanView';
import { SourcesAndRequirementsView } from './components/admissions/SourcesAndRequirementsView';
import { HelpAndGuidanceView } from './components/help/HelpAndGuidanceView';
import { GuidedProfileView } from './components/profile/GuidedProfileView';

const DEFAULT_PROFILE: StudentProfileRequest = {
  student_id: 'STU_MASTER_REF',
  subject_scores: [
    { subject_code: 'MATH', subject_name: 'Mathematics', score: 88, max_score: 100, grading_scale: 'percentage' },
    { subject_code: 'ENG', subject_name: 'English', score: 78, max_score: 100, grading_scale: 'percentage' },
    { subject_code: 'PHYS', subject_name: 'Physics', score: 82, max_score: 100, grading_scale: 'percentage' },
  ],
  entrance_exam_name: 'JEE Main',
  entrance_rank: 18500,
  total_budget_inr: 800000,
  preferred_locations: ['Karnataka', 'Maharashtra'],
  preferred_disciplines: ['Computer Science', 'Data Science'],
  career_goals: ['Software Engineer', 'Systems Architect'],
};

export const App: React.FC = () => {
  const [currentDestination, setCurrentDestination] = useState<NavigationDestination>('overview');
  const [currentProfile, setCurrentProfile] = useState<StudentProfileRequest>(DEFAULT_PROFILE);
  const [evaluations, setEvaluations] = useState<ProgrammeEvaluationDto[]>([]);
  const [catalogProgrammes, setCatalogProgrammes] = useState<ProgrammeResponse[]>([]);
  const [comparedProgrammeIds, setComparedProgrammeIds] = useState<string[]>([]);
  const [isTechnicalDrawerOpen, setIsTechnicalDrawerOpen] = useState<boolean>(false);

  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = useCallback(async () => {
    try {
      const res = await hydraApi.checkHealth();
      setBackendHealthy(res.status === 'ok');
    } catch {
      setBackendHealthy(false);
    }
  }, []);

  const runEvaluation = useCallback(async (profileToEvaluate: StudentProfileRequest) => {
    setIsEvaluating(true);
    setError(null);
    try {
      const res: EvaluationResponse = await hydraApi.evaluateProfile(profileToEvaluate);
      setEvaluations(res.evaluations);
      setBackendHealthy(true);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(`Evaluation returned ${err.status}: ${err.message}`);
      } else if (err instanceof Error) {
        setError(`Cannot reach backend: ${err.message}. Ensure backend is running at http://127.0.0.1:8000.`);
      } else {
        setError('An unexpected error occurred while evaluating.');
      }
    } finally {
      setIsEvaluating(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    hydraApi
      .getProgrammes()
      .then((progs) => setCatalogProgrammes(progs))
      .catch(() => {});

    runEvaluation(DEFAULT_PROFILE);

    const timer = setInterval(checkHealth, 30000);
    return () => clearInterval(timer);
  }, [checkHealth, runEvaluation]);

  const handleProfileSubmit = (newProfile: StudentProfileRequest) => {
    setCurrentProfile(newProfile);
    runEvaluation(newProfile);
    setCurrentDestination('overview');
  };

  const handleToggleCompare = (id: string) => {
    setComparedProgrammeIds((prev) => {
      if (prev.includes(id)) {
        return prev.filter((p) => p !== id);
      }
      if (prev.length >= 4) {
        return prev;
      }
      return [...prev, id];
    });
  };

  const handleRemoveCompare = (id: string) => {
    setComparedProgrammeIds((prev) => prev.filter((p) => p !== id));
  };

  const handleAddCompare = (id: string) => {
    setComparedProgrammeIds((prev) => {
      if (prev.includes(id) || prev.length >= 4) return prev;
      return [...prev, id];
    });
  };

  const handleClearCompare = () => {
    setComparedProgrammeIds([]);
  };

  const comparedEvaluations = evaluations.filter((e) =>
    comparedProgrammeIds.includes(e.programme_id)
  );

  return (
    <div className="h-screen w-screen overflow-hidden bg-[#ECEEE7] text-[#111215] font-sans antialiased flex flex-col p-3 sm:p-5">
      {/* Global Error Banner */}
      {error && (
        <div
          className="mb-4 p-3 rounded-2xl bg-[#FEE2E2] border border-[#FCA5A5] text-[#991B1B] text-xs flex items-center justify-between shadow-xs z-50 shrink-0"
          role="alert"
        >
          <span>{error}</span>
          <button
            onClick={() => setError(null)}
            className="font-bold underline text-[11px] ml-2 hover:opacity-80 cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Main Workspace Frame with Sidebar & Dashboard */}
      <div className="flex-1 flex gap-4 min-w-0 h-full overflow-hidden">
        {/* Slim Black Vertical Sidebar (Desktop) */}
        <NeoModernSidebar
          currentDestination={currentDestination}
          onNavigate={(dest) => setCurrentDestination(dest)}
          onOpenProfile={() => setCurrentDestination('profile')}
          comparedCount={comparedProgrammeIds.length}
        />

        {/* Dashboard Shell with Header & Horizontal Tabs */}
        <NeoModernDashboard
          currentDestination={currentDestination}
          onNavigate={(dest) => setCurrentDestination(dest)}
          profile={currentProfile}
          evaluations={evaluations}
          catalogProgrammes={catalogProgrammes}
          comparedProgrammeIds={comparedProgrammeIds}
          onToggleCompare={handleToggleCompare}
          onEvaluateProfile={() => runEvaluation(currentProfile)}
          isEvaluating={isEvaluating}
          backendHealthy={backendHealthy}
          onRetryHealth={checkHealth}
          onOpenSettings={() => setIsTechnicalDrawerOpen(true)}
          onOpenProfile={() => setCurrentDestination('profile')}
        >
          {/* Sub-view switcher rendered inside the dashboard container */}
          {currentDestination === 'referee' && (
            <CentralRefereeView profile={currentProfile} />
          )}

          {currentDestination === 'programmes' && (
            <ProgrammeDiscoveryView
              evaluations={evaluations}
              catalogProgrammes={catalogProgrammes}
              comparedProgrammeIds={comparedProgrammeIds}
              onToggleCompare={handleToggleCompare}
              onNavigateToCompare={() => setCurrentDestination('compare')}
              onEvaluate={() => runEvaluation(currentProfile)}
              isEvaluating={isEvaluating}
            />
          )}

          {currentDestination === 'twin' && <StudentDigitalTwinView />}

          {currentDestination === 'franchise' && (
            <FranchiseAuctionView profile={currentProfile} />
          )}

          {currentDestination === 'planner' && (
            <HeistPlannerView profile={currentProfile} />
          )}

          {currentDestination === 'simulation' && (
            <SimulatorBossFightView profile={currentProfile} />
          )}

          {currentDestination === 'oracle' && (
            <OracleForecastView programmes={catalogProgrammes} />
          )}

          {currentDestination === 'interests' && <InterestDecoderView />}

          {currentDestination === 'careers' && <CareerExplorationView />}

          {currentDestination === 'compare' && (
            <ProgrammeCompareView
              comparedProgrammes={comparedEvaluations}
              allEvaluations={evaluations}
              onRemoveCompare={handleRemoveCompare}
              onAddCompare={handleAddCompare}
              onClearCompare={handleClearCompare}
              onNavigateToExplore={() => setCurrentDestination('programmes')}
            />
          )}

          {currentDestination === 'plan' && (
            <StudentActionPlanView
              profile={currentProfile}
              evaluations={evaluations}
              onNavigateToProfile={() => setCurrentDestination('profile')}
            />
          )}

          {currentDestination === 'sources' && <SourcesAndRequirementsView />}

          {currentDestination === 'help' && <HelpAndGuidanceView />}

          {currentDestination === 'profile' && (
            <GuidedProfileView
              currentProfile={currentProfile}
              onSubmit={handleProfileSubmit}
              isLoading={isEvaluating}
              onNavigateToExplore={() => setCurrentDestination('overview')}
            />
          )}
        </NeoModernDashboard>
      </div>

      {/* Mobile Sticky Navigation */}
      <MobileNavigation
        currentDestination={currentDestination}
        onNavigate={(dest) => setCurrentDestination(dest)}
        comparedCount={comparedProgrammeIds.length}
      />

      {/* Technical Audit Drawer for Counselors & Engineers */}
      <TechnicalDrawer
        isOpen={isTechnicalDrawerOpen}
        onClose={() => setIsTechnicalDrawerOpen(false)}
        profile={currentProfile}
        programmes={catalogProgrammes}
        evaluations={evaluations}
      />
    </div>
  );
};

export default App;
