import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { corridorsApi, habitatApi, simulateApi, restorationApi, aiApi, systemApi } from './client';
import type { HighwaySimulateRequest, CorridorGenerateRequest } from '@/types';

// ── Query Keys ────────────────────────────────────────────────────────────────

export const QK = {
  health:        ['health'] as const,
  corridors:     (priority?: string) => ['corridors', priority] as const,
  corridor:      (id: number) => ['corridor', id] as const,
  corridorHealth:(id: number) => ['corridor-health', id] as const,
  gnn:           (id: number, species: string) => ['gnn', id, species] as const,
  patches:       (cid?: number, min?: number) => ['patches', cid, min] as const,
  patch:         (id: number) => ['patch', id] as const,
  scenarios:     ['scenarios'] as const,
  scenario:      (id: number) => ['scenario', id] as const,
  zones:         (cid?: number, method?: string) => ['zones', cid, method] as const,
  zone:          (id: number) => ['zone', id] as const,
} as const;

// ── System ────────────────────────────────────────────────────────────────────

export function useHealth() {
  return useQuery({
    queryKey: QK.health,
    queryFn:  systemApi.health,
    staleTime: 30_000,
    retry: 2,
  });
}

// ── Corridors ─────────────────────────────────────────────────────────────────

export function useCorridors(priority?: string) {
  return useQuery({
    queryKey: QK.corridors(priority),
    queryFn:  () => corridorsApi.list(priority),
    staleTime: 60_000,
  });
}

export function useCorridor(id: number) {
  return useQuery({
    queryKey: QK.corridor(id),
    queryFn:  () => corridorsApi.get(id),
    staleTime: 60_000,
    enabled: id > 0,
  });
}

export function useCorridorHealth(id: number) {
  return useQuery({
    queryKey: QK.corridorHealth(id),
    queryFn:  () => corridorsApi.health(id),
    staleTime: 30_000,
    refetchInterval: 120_000,
    enabled: id > 0,
  });
}

export function useGNNAnalysis(id: number, species = 'all') {
  return useQuery({
    queryKey: QK.gnn(id, species),
    queryFn:  () => corridorsApi.gnn(id, species),
    staleTime: 300_000,
    enabled: id > 0,
  });
}

export function useGenerateCorridor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (req: CorridorGenerateRequest) => corridorsApi.generate(req),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['corridors'] }),
  });
}

// ── Habitat ───────────────────────────────────────────────────────────────────

export function usePatches(corridorId?: number, minSuitability?: number) {
  return useQuery({
    queryKey: QK.patches(corridorId, minSuitability),
    queryFn:  () => habitatApi.patches(corridorId, minSuitability),
    staleTime: 120_000,
  });
}

export function usePatch(id: number) {
  return useQuery({
    queryKey: QK.patch(id),
    queryFn:  () => habitatApi.patch(id),
    staleTime: 300_000,
    enabled: id > 0,
  });
}

export function useHabitatSuitability() {
  return useMutation({
    mutationFn: ({ points, species }: { points: object[]; species?: string }) =>
      habitatApi.suitability(points, species),
  });
}

// ── Simulation ────────────────────────────────────────────────────────────────

export function useScenarios() {
  return useQuery({
    queryKey: QK.scenarios,
    queryFn:  simulateApi.scenarios,
    staleTime: 30_000,
  });
}

export function useScenario(id: number) {
  return useQuery({
    queryKey: QK.scenario(id),
    queryFn:  () => simulateApi.scenario(id),
    staleTime: 300_000,
    enabled: id > 0,
  });
}

export function useSimulateHighway() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (req: HighwaySimulateRequest) => simulateApi.highway(req),
    onSuccess: () => qc.invalidateQueries({ queryKey: QK.scenarios }),
  });
}

// ── Restoration ───────────────────────────────────────────────────────────────

export function useRestorationZones(corridorId?: number, method?: string) {
  return useQuery({
    queryKey: QK.zones(corridorId, method),
    queryFn:  () => restorationApi.zones(corridorId, method),
    staleTime: 120_000,
  });
}

export function useRestorationPlan() {
  return useMutation({
    mutationFn: ({ corridorId, budgetCr, priorityMethod }: {
      corridorId: number; budgetCr: number; priorityMethod?: string;
    }) => restorationApi.recommend(corridorId, budgetCr, priorityMethod),
  });
}

// ── AI ────────────────────────────────────────────────────────────────────────

export function useAIAsk() {
  return useMutation({
    mutationFn: ({ question, context }: { question: string; context?: string }) =>
      aiApi.ask(question, context),
  });
}

export function useAIExplainCorridor() {
  return useMutation({
    mutationFn: (corridorId: number) => aiApi.explainCorridor(corridorId),
  });
}

export function usePolicyBrief() {
  return useMutation({
    mutationFn: ({ corridorId, audience }: { corridorId?: number; audience?: string }) =>
      aiApi.policyBrief(corridorId, audience),
  });
}
