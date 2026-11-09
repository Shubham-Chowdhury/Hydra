import React, { useState, useEffect, useCallback } from 'react';
import type {
  ComprehensiveAssessmentReportDto,
  EvaluationResponse,
  ProgrammeEvaluationDto,
  ProgrammeResponse,
  StudentProfileRequest,
} from './api/types';
import { hydraApi, ApiError } from './api/client';
import { activityTracker } from './services/activityTracker';
import { ComprehensiveAssessmentModal } from './components/assessment/ComprehensiveAssessmentModal';

import { NeoModernSidebar } from './components/layout/NeoModernSidebar';
import { NeoModernDashboard } from './components/dashboard/NeoModernDashboard';
import { MobileNavigation } from './components/layout/MobileNavigation';
import { type NavigationDestination } from './components/layout/StudentSidebar';
import { TechnicalDrawer } from './components/layout/TechnicalDrawer';
import { FloatingVoiceAssistant } from './components/voice/FloatingVoiceAssistant';
import { voiceManager } from './services/voiceManager';

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
  const [assessmentReport, setAssessmentReport] = useState<ComprehensiveAssessmentReportDto | null>(null);
  const [isReportModalOpen, setIsReportModalOpen] = useState<boolean>(false);

  useEffect(() => {
    voiceManager.setCurrentDestination(currentDestination);
    activityTracker.trackEvent('page_view', currentDestination);
  }, [currentDestination]);

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

    const unsubNav = voiceManager.subscribeNavigation((intent: string) => {
      // 1. Full website view navigation
      if (intent === 'navigate_catalog') {
        setCurrentDestination('programmes');
      } else if (intent === 'navigate_compare') {
        setCurrentDestination('compare');
      } else if (intent === 'navigate_referee') {
        setCurrentDestination('referee');
      } else if (intent === 'navigate_action_plan' || intent === 'navigate_plan') {
        setCurrentDestination('plan');
      } else if (intent === 'navigate_career') {
        setCurrentDestination('careers');
      } else if (intent === 'navigate_overview') {
        setCurrentDestination('overview');
      } else if (intent === 'navigate_franchise') {
        setCurrentDestination('franchise');
      } else if (intent === 'navigate_twin') {
        setCurrentDestination('twin');
      } else if (intent === 'navigate_planner') {
        setCurrentDestination('planner');
      } else if (intent === 'navigate_simulation') {
        setCurrentDestination('simulation');
      } else if (intent === 'navigate_oracle') {
        setCurrentDestination('oracle');
      } else if (intent === 'navigate_interests') {
        setCurrentDestination('interests');
      } else if (intent === 'navigate_sources') {
        setCurrentDestination('sources');
      } else if (intent === 'navigate_help') {
        setCurrentDestination('help');
      } else if (intent === 'navigate_profile') {
        setCurrentDestination('profile');
      }
      // 2. Active tasks execution
      else if (intent === 'action_generate_assessment_report') {
        activityTracker.trackEvent('generate_report', 'assessment_report');
        hydraApi
          .generateAssessmentReport(currentProfile, activityTracker.getHistory())
          .then((report) => {
            setAssessmentReport(report);
            setIsReportModalOpen(true);
            voiceManager.speak(report.voice_script);
          })
          .catch((err) => {
            console.error('Failed to generate assessment report:', err);
            setError('Failed to generate comprehensive assessment report.');
          });
      } else if (intent === 'action_run_franchise_auction') {
        setCurrentDestination('franchise');
        activityTracker.trackEvent('run_action', 'franchise', 'run_auction');
        setTimeout(() => {
          window.dispatchEvent(new CustomEvent('hydra:run_auction'));
        }, 150);
      } else if (intent === 'action_run_planner') {
        setCurrentDestination('planner');
        activityTracker.trackEvent('run_action', 'planner', 'run_planner');
        setTimeout(() => {
          window.dispatchEvent(new CustomEvent('hydra:run_planner'));
        }, 150);
      } else if (intent === 'action_run_simulation') {
        setCurrentDestination('simulation');
        activityTracker.trackEvent('run_action', 'simulation', 'run_simulation');
        setTimeout(() => {
          window.dispatchEvent(new CustomEvent('hydra:run_simulation'));
        }, 150);
      } else if (intent === 'action_run_boss_fight') {
        setCurrentDestination('simulation');
        activityTracker.trackEvent('run_action', 'simulation', 'run_boss_fight');
        setTimeout(() => {
          window.dispatchEvent(new CustomEvent('hydra:run_boss_fight'));
        }, 150);
      } else if (intent === 'action_run_forecast') {
        setCurrentDestination('oracle');
        activityTracker.trackEvent('run_action', 'oracle', 'run_forecast');
        setTimeout(() => {
          window.dispatchEvent(new CustomEvent('hydra:run_forecast'));
        }, 150);
      } else if (intent === 'action_run_referee') {
        setCurrentDestination('referee');
        activityTracker.trackEvent('run_action', 'referee', 'run_referee');
        setTimeout(() => {
          window.dispatchEvent(new CustomEvent('hydra:run_referee'));
        }, 150);
      } else if (intent === 'action_run_decode') {
        setCurrentDestination('interests');
        activityTracker.trackEvent('run_action', 'interests', 'run_decode');
        setTimeout(() => {
          window.dispatchEvent(new CustomEvent('hydra:run_decode'));
        }, 150);
      } else if (intent === 'action_evaluate') {
        runEvaluation(currentProfile);
      } else if (intent === 'action_open_settings') {
        setIsTechnicalDrawerOpen(true);
      } else if (intent === 'action_clear_compare') {
        setComparedProgrammeIds([]);
      } else if (intent === 'action_compare_top') {
        setEvaluations((latest) => {
          const top = latest.slice(0, 3).map((e) => e.programme_id);
          if (top.length > 0) {
            setComparedProgrammeIds(top);
            setCurrentDestination('compare');
          }
          return latest;
        });
      }
    });

    return () => {
      clearInterval(timer);
      unsubNav();
    };
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

      {/* Floating Voice Assistant (Active across all views when leaving overview) */}
      <FloatingVoiceAssistant
        currentDestination={currentDestination}
        onNavigate={(dest) => setCurrentDestination(dest)}
      />

      {/* Comprehensive Assessment & Deep Learning Trajectory Report Modal */}
      <ComprehensiveAssessmentModal
        report={assessmentReport}
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
      />
    </div>
  );
};

export default App;
