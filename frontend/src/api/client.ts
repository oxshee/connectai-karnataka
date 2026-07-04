import axios, { AxiosError } from 'axios';
import type {
  HealthResponse, Corridor, CorridorHealth, CorridorGenerateRequest,
  CorridorGenerateResponse, GNNAnalysis, HabitatPatch, HabitatSuitabilityResponse,
  HighwaySimulateRequest, ImpactScenario, ScenarioSummary, RestorationZone,
  RestorationPlan, AIAskResponse, PolicyBriefResponse,
} from '@/types';

// ── Axios instance ────────────────────────────────────────────────────────────

const BASE = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000/v1';

const api = axios.create({
  baseURL: BASE,
  timeout: 45_000,
  headers: { 'Content-Type': 'application/json' },
});

// Retry on network errors (3 attempts, exponential backoff)
api.interceptors.response.use(undefined, async (error: AxiosError) => {
  const config = error.config as typeof error.config & { _retry?: number };
  if (!config) return Promise.reject(error);
  config._retry = (config._retry ?? 0) + 1;
  if (config._retry <= 3 && (!error.response || error.response.status >= 500)) {
    await new Promise(r => setTimeout(r, 400 * config._retry!));
    return api(config);
  }
  return Promise.reject(error);
});

// ── System ────────────────────────────────────────────────────────────────────

export const systemApi = {
  health: () =>
    api.get<HealthResponse>('/health', { baseURL: BASE.replace('/v1', '') })
       .then(r => r.data),
};

// ── Corridors ─────────────────────────────────────────────────────────────────

export const corridorsApi = {
  list: (priority?: string) =>
    api.get<Corridor[]>('/corridors/', { params: priority ? { priority } : {} })
       .then(r => r.data),

  get: (id: number) =>
    api.get<Corridor>(`/corridors/${id}`).then(r => r.data),

  health: (id: number) =>
    api.get<CorridorHealth>(`/corridors/${id}/health`).then(r => r.data),

  gnn: (id: number, species = 'all') =>
    api.get<GNNAnalysis>(`/corridors/${id}/gnn`, { params: { species } })
       .then(r => r.data),

  generate: (req: CorridorGenerateRequest) =>
    api.post<CorridorGenerateResponse>('/corridors/generate', req).then(r => r.data),
};

// ── Habitat ───────────────────────────────────────────────────────────────────

export const habitatApi = {
  patches: (corridorId?: number, minSuitability?: number) =>
    api.get<HabitatPatch[]>('/habitat/patches', {
      params: {
        ...(corridorId !== undefined && { corridor_id: corridorId }),
        ...(minSuitability !== undefined && { min_suitability: minSuitability }),
      },
    }).then(r => r.data),

  patch: (id: number) =>
    api.get<HabitatPatch & { computed_suitability: number; feature_contributions: Record<string, number>; explanation: string }>
       (`/habitat/patches/${id}`).then(r => r.data),

  suitability: (points: object[], species = 'all') =>
    api.post<HabitatSuitabilityResponse>('/habitat/suitability', { species, points })
       .then(r => r.data),
};

// ── Impact Simulation ─────────────────────────────────────────────────────────

export const simulateApi = {
  highway: (req: HighwaySimulateRequest) =>
    api.post<ImpactScenario>('/simulate/highway', req).then(r => r.data),

  scenarios: () =>
    api.get<ScenarioSummary[]>('/simulate/scenarios').then(r => r.data),

  scenario: (id: number) =>
    api.get<ImpactScenario>(`/simulate/scenarios/${id}`).then(r => r.data),
};

// ── Restoration ───────────────────────────────────────────────────────────────

export const restorationApi = {
  recommend: (corridorId: number, budgetCr: number, priorityMethod = 'ecological_benefit') =>
    api.post<RestorationPlan>('/restoration/recommend', {
      corridor_id: corridorId,
      budget_cr: budgetCr,
      priority_method: priorityMethod,
    }).then(r => r.data),

  zones: (corridorId?: number, method?: string) =>
    api.get<RestorationZone[]>('/restoration/zones', {
      params: {
        ...(corridorId !== undefined && { corridor_id: corridorId }),
        ...(method && { method }),
      },
    }).then(r => r.data),

  zone: (id: number) =>
    api.get<RestorationZone>(`/restoration/zones/${id}`).then(r => r.data),
};

// ── AI ────────────────────────────────────────────────────────────────────────

export const aiApi = {
  ask: (question: string, context?: string) =>
    api.post<AIAskResponse>('/ai/ask', { question, context }).then(r => r.data),

  explainCorridor: (corridorId: number) =>
    api.post<{ corridor_id: number; explanation: string }>('/ai/explain/corridor', { corridor_id: corridorId })
       .then(r => r.data),

  explainImpact: (payload: object) =>
    api.post<{ explanation: string }>('/ai/explain/impact', payload).then(r => r.data),

  policyBrief: (corridorId?: number, audience?: string) =>
    api.post<PolicyBriefResponse>('/ai/policy-brief', {
      corridor_id: corridorId,
      audience: audience ?? 'Karnataka Forest Department',
    }).then(r => r.data),
};

export default api;
