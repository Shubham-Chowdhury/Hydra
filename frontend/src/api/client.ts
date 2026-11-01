/**
 * Typed API client for Hydra using the native Fetch API.
 */

import type {
  DatasetSnapshotDto,
  EvaluationResponse,
  FormalEligibilityCriterionDto,
  HealthResponse,
  PaginatedCutoffsResponse,
  PaginatedProgrammesResponse,
  ProgrammeResponse,
  SourceDocumentDto,
  StudentProfileRequest,
  StudentTwinResponse,
} from './types';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') || 'http://127.0.0.1:8000';

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
   * Catalogue retrieval of all synthetic programmes.
   * GET /api/v1/programmes
   */
  async getProgrammes(): Promise<ProgrammeResponse[]> {
    const res = await fetch(`${API_BASE_URL}/api/v1/programmes`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    return handleResponse<ProgrammeResponse[]>(res);
  },

  /**
   * Evaluates student profile against academic catalogue.
   * POST /api/v1/recommendations/evaluate
   */
  async evaluateProfile(
    request: StudentProfileRequest
  ): Promise<EvaluationResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/recommendations/evaluate`, {
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
};

