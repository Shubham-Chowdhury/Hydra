/**
 * Typed API client for Hydra using the native Fetch API.
 */

import type {
  AuctionRequestDto,
  AuctionResultDto,
  BossFightReportDto,
  BossFightRequestDto,
  ComprehensiveAssessmentReportDto,
  ConfirmedInterestResponseDto,
  CutoffForecastDto,
  DatasetSnapshotDto,
  EvaluationResponse,
  ForecastTargetDto,
  FormalEligibilityCriterionDto,
  FranchiseInfoDto,
  HealthResponse,
  InterestDecodingResponseDto,
  InterestModelStatusDto,
  OracleStatusResponseDto,
  PaginatedCutoffsResponse,
  PaginatedProgrammesResponse,
  PlanningRequestDto,
  PlanningResultDto,
  ProgrammeResponse,
  RefereeEvaluateRequestDto,
  RefereeEvaluationResponseDto,
  SimulationRequestDto,
  SimulationResultDto,
  SourceDocumentDto,
  StudentProfileRequest,
  StudentTwinResponse,
  UserInteractionEventDto,
} from './types';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') ?? '';

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorData: unknown;
    try {
      errorData = await response.json();
    } catch {
      errorData = await response.text();
    }
    const message =
      typeof errorData === 'object' && errorData !== null && 'detail' in errorData
        ? String((errorData as { detail: unknown }).detail)
        : `Request failed with status ${response.status}`;
    throw new ApiError(message, response.status, errorData);
  }
  return response.json() as Promise<T>;
}

export const hydraApi = {
  /**
   * Health and service liveness check.
   * GET /api/health
   */
  async checkHealth(): Promise<HealthResponse> {
    const res = await fetch(`${API_BASE_URL}/api/health`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    return handleResponse<HealthResponse>(res);
  },

  /**
   * Catalogue retrieval of all programmes across domains.
   * GET /api/v1/programmes
   */
  async getProgrammes(allDomains: boolean = true): Promise<ProgrammeResponse[]> {
    const res = await fetch(`${API_BASE_URL}/api/v1/programmes?all_domains=${allDomains}`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    return handleResponse<ProgrammeResponse[]>(res);
  },

  /**
   * Evaluates student profile against academic catalogue across domains.
   * POST /api/v1/recommendations/evaluate
   */
  async evaluateProfile(
    request: StudentProfileRequest,
    allDomains: boolean = true
  ): Promise<EvaluationResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/recommendations/evaluate?all_domains=${allDomains}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(request),
    });
    return handleResponse<EvaluationResponse>(res);
  },

  /**
   * Retrieves registered admissions data source documents.
   * GET /api/v1/data-sources
   */
  async getDataSources(status?: string): Promise<SourceDocumentDto[]> {
    const url = new URL(`${API_BASE_URL}/api/v1/data-sources`);
    if (status) {
      url.searchParams.append('status', status);
    }
    const res = await fetch(url.toString(), {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    return handleResponse<SourceDocumentDto[]>(res);
  },

  /**
   * Retrieves snapshots for a given source document.
   * GET /api/v1/data-sources/{sourceId}/snapshots
   */
  async getDataSourceSnapshots(sourceId: string): Promise<DatasetSnapshotDto[]> {
    const res = await fetch(
      `${API_BASE_URL}/api/v1/data-sources/${encodeURIComponent(sourceId)}/snapshots`,
      {
        method: 'GET',
        headers: { Accept: 'application/json' },
      }
    );
    return handleResponse<DatasetSnapshotDto[]>(res);
  },

  /**
   * Queries historical cutoff observations.
   * GET /api/v1/admissions/cutoffs
   */
  async getHistoricalCutoffs(
    params?: Record<string, string | number>
  ): Promise<PaginatedCutoffsResponse> {
    const url = new URL(`${API_BASE_URL}/api/v1/admissions/cutoffs`);
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') {
          url.searchParams.append(k, String(v));
        }
      });
    }
    const res = await fetch(url.toString(), {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    return handleResponse<PaginatedCutoffsResponse>(res);
  },

  /**
   * Queries unique academic programmes derived from admissions records.
   * GET /api/v1/admissions/programmes
   */
  async getAdmissionsProgrammes(
    params?: Record<string, string | number>
  ): Promise<PaginatedProgrammesResponse> {
    const url = new URL(`${API_BASE_URL}/api/v1/admissions/programmes`);
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') {
          url.searchParams.append(k, String(v));
        }
      });
    }
    const res = await fetch(url.toString(), {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    return handleResponse<PaginatedProgrammesResponse>(res);
  },

  /**
   * Retrieves verified formal eligibility criteria from official authorities.
   * GET /api/v1/admissions/eligibility-criteria
   */
  async getEligibilityCriteria(
    academicYear?: number
  ): Promise<FormalEligibilityCriterionDto[]> {
    const url = new URL(`${API_BASE_URL}/api/v1/admissions/eligibility-criteria`);
    if (academicYear) {
      url.searchParams.append('academic_year', String(academicYear));
    }
    const res = await fetch(url.toString(), {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    return handleResponse<FormalEligibilityCriterionDto[]>(res);
  },

  /**
   * Constructs an auditable Student Digital Twin snapshot using symbolic AI.
   * POST /api/v1/twin/construct
   */
  async constructTwin(
    request: StudentProfileRequest
  ): Promise<StudentTwinResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/twin/construct`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(request),
    });
    return handleResponse<StudentTwinResponse>(res);
  },

  /**
   * Retrieves an existing Student Digital Twin snapshot by ID.
   * GET /api/v1/twin/{twin_id}
   */
  async getTwin(twinId: string): Promise<StudentTwinResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/twin/${encodeURIComponent(twinId)}`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    return handleResponse<StudentTwinResponse>(res);
  },

  /**
   * Retrieves available Programme Franchise Agents.
   * GET /api/v1/franchises/programmes
   */
  async getAvailableFranchises(): Promise<FranchiseInfoDto[]> {
    const res = await fetch(`${API_BASE_URL}/api/v1/franchises/programmes`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    return handleResponse<FranchiseInfoDto[]>(res);
  },

  /**
   * Runs a deterministic simulated programme auction.
   * POST /api/v1/franchises/auction
   */
  async runProgrammeAuction(request: AuctionRequestDto): Promise<AuctionResultDto> {
    const res = await fetch(`${API_BASE_URL}/api/v1/franchises/auction`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(request),
    });
    return handleResponse<AuctionResultDto>(res);
  },

  /**
   * Executes A* search pathway planning toward a target programme.
   * POST /api/v1/planner/plan
   */
  async planPathway(request: PlanningRequestDto): Promise<PlanningResultDto> {
    const res = await fetch(`${API_BASE_URL}/api/v1/planner/plan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(request),
    });
    return handleResponse<PlanningResultDto>(res);
  },

  /**
   * Runs a counterfactual or Monte Carlo simulation.
   * POST /api/v1/simulation/run
   */
  async runSimulation(request: SimulationRequestDto): Promise<SimulationResultDto> {
    const res = await fetch(`${API_BASE_URL}/api/v1/simulation/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(request),
    });
    return handleResponse<SimulationResultDto>(res);
  },

  /**
   * Runs an adversarial Boss-Fight stress test against a programme.
   * POST /api/v1/simulation/stress-test
   */
  async runBossFight(request: BossFightRequestDto): Promise<BossFightReportDto> {
    const res = await fetch(`${API_BASE_URL}/api/v1/simulation/stress-test`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(request),
    });
    return handleResponse<BossFightReportDto>(res);
  },

  /**
   * Retrieves operational status and architecture of the neural embedding model.
   * GET /api/v1/interests/model-status
   */
  async getInterestModelStatus(): Promise<InterestModelStatusDto> {
    const res = await fetch(`${API_BASE_URL}/api/v1/interests/model-status`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    return handleResponse<InterestModelStatusDto>(res);
  },

  /**
   * Translates natural language interest text into ranked canonical concepts.
   * POST /api/v1/interests/decode
   */
  async decodeInterests(interestText: string): Promise<InterestDecodingResponseDto> {
    const res = await fetch(`${API_BASE_URL}/api/v1/interests/decode`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({ interest_text: interestText }),
    });
    return handleResponse<InterestDecodingResponseDto>(res);
  },

  /**
   * Explicitly accepts an advisory candidate concept into the student twin.
   * POST /api/v1/interests/confirm
   */
  async confirmInterest(
    conceptId: string,
    similarityScore: number
  ): Promise<ConfirmedInterestResponseDto> {
    const res = await fetch(`${API_BASE_URL}/api/v1/interests/confirm`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        concept_id: conceptId,
        similarity_score: similarityScore,
      }),
    });
    return handleResponse<ConfirmedInterestResponseDto>(res);
  },

  /**
   * Retrieves diagnostic status and data readiness report from Oracle Agent.
   * GET /api/v1/oracle/status
   */
  async getOracleStatus(): Promise<OracleStatusResponseDto> {
    const res = await fetch(`${API_BASE_URL}/api/v1/oracle/status`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    return handleResponse<OracleStatusResponseDto>(res);
  },

  /**
   * Requests an advisory admissions cutoff forecast from Oracle Agent.
   * POST /api/v1/oracle/forecast
   */
  async getOracleForecast(target: ForecastTargetDto): Promise<CutoffForecastDto> {
    const res = await fetch(`${API_BASE_URL}/api/v1/oracle/forecast`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(target),
    });
    return handleResponse<CutoffForecastDto>(res);
  },

  async generateCutoffForecast(target: ForecastTargetDto): Promise<CutoffForecastDto> {
    return this.getOracleForecast(target);
  },

  /**
   * Retrieves predefined cohort forecast targets.
   * GET /api/v1/oracle/targets
   */
  async getForecastTargets(): Promise<ForecastTargetDto[]> {
    const res = await fetch(`${API_BASE_URL}/api/v1/oracle/targets`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    return handleResponse<ForecastTargetDto[]>(res);
  },

  /**
   * Executes multi-agent evaluation synthesized by Central Referee.
   * POST /api/v1/referee/evaluate
   */
  async evaluateWithReferee(
    request: RefereeEvaluateRequestDto
  ): Promise<RefereeEvaluationResponseDto> {
    const res = await fetch(`${API_BASE_URL}/api/v1/referee/evaluate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(request),
    });
    return handleResponse<RefereeEvaluationResponseDto>(res);
  },

  /**
   * Generates a comprehensive assessment & career trajectory report
   * powered by the deep sequence neural model.
   * POST /api/v1/assessment/comprehensive-report
   */
  async generateAssessmentReport(
    profile: StudentProfileRequest,
    interactionHistory?: UserInteractionEventDto[]
  ): Promise<ComprehensiveAssessmentReportDto> {
    const res = await fetch(`${API_BASE_URL}/api/v1/assessment/comprehensive-report`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        profile,
        interaction_history: interactionHistory || [],
      }),
    });
    return handleResponse<ComprehensiveAssessmentReportDto>(res);
  },
};

export const apiClient = hydraApi;

