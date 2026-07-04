// ── Shared ────────────────────────────────────────────────────────────────────

export type PriorityLevel = 'critical' | 'high' | 'medium' | 'low';
export type ProjectType   = 'highway' | 'railway' | 'township' | 'mining';
export type RiskLevel     = 'Severe' | 'High' | 'Moderate' | 'Low';
export type TrendDir      = 'improving' | 'stable' | 'declining';

export interface GeoPoint   { lat: number; lon: number; }
export interface BoundingBox { min_lon: number; min_lat: number; max_lon: number; max_lat: number; }

// ── System ────────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string;
  version: string;
  database: string;
  models_loaded: Record<string, boolean>;
  karnataka_corridors: number;
  habitat_patches: number;
  ai_explanations: boolean;
  timestamp: string;
}

// ── Corridors ─────────────────────────────────────────────────────────────────

export interface PermeabilityZone {
  zone: string;
  score: number;
}

export interface Corridor {
  id: number;
  name: string;
  start_name: string;
  end_name: string;
  description: string | null;
  connectivity_score: number;
  permeability_score: number;
  ndvi_mean: number | null;
  forest_cover_pct: number | null;
  length_km: number | null;
  priority: PriorityLevel;
  species_supported: string[];
  start_lat: number | null;
  start_lon: number | null;
  end_lat: number | null;
  end_lon: number | null;
  last_analyzed: string | null;
  geometry_wkt: string | null;
  permeability_zones: PermeabilityZone[];
  alerts: string[];
}

export interface CorridorHealth {
  corridor_id: number;
  name: string;
  score: number;
  ndvi: number | null;
  forest_cover_pct: number | null;
  trend: TrendDir;
  priority: PriorityLevel;
  alerts: string[];
  permeability_by_zone: PermeabilityZone[];
  species_at_risk: string[];
  last_updated: string;
}

export interface CorridorGenerateRequest {
  bbox: BoundingBox;
  species?: string;
  resolution_m?: number;
  include_geometry?: boolean;
}

export interface CorridorGenerateResponse {
  corridor_id: number;
  priority_score: number;
  connectivity_score: number;
  permeability_score: number;
  path_wkt: string | null;
  habitat_patches_count: number;
  graph_nodes: number;
  graph_edges: number;
  computation_time_s: number;
  explanation: string;
}

export interface BottleneckZone {
  patch_id: number;
  name: string;
  lat: number;
  lon: number;
  suitability: number;
  centrality: number;
  bottleneck_score: number;
  intervention: string;
}

export interface LeastCostPath {
  nodes: number[];
  total_resistance: number;
  bottleneck_resistance: number;
  bottleneck_node_id: number;
  length_approx_km: number;
  permeability: number;
}

export interface GNNAnalysis {
  corridor_id: number;
  habitat_patches: number;
  graph_nodes: number;
  graph_edges: number;
  least_cost_paths: LeastCostPath[];
  bottleneck_zones: BottleneckZone[];
  model_accuracy: number;
  connectivity_score: number;
  computation_time_s: number;
  explanation: string;
}

// ── Habitat Patches ───────────────────────────────────────────────────────────

export interface HabitatPatch {
  id: number;
  corridor_id: number | null;
  name: string;
  area_ha: number;
  centroid_lat: number;
  centroid_lon: number;
  suitability_score: number;
  ndvi: number;
  elevation_m: number;
  forest_density: number;
  dist_to_road_m: number;
  dist_to_settlement_m: number;
  land_cover_class: string;
}

export interface HabitatSuitabilityResult {
  lat: number | null;
  lon: number | null;
  suitability_score: number;
  feature_contributions: Record<string, number>;
  explanation: string;
  land_cover: string | null;
}

export interface HabitatSuitabilityResponse {
  species: string;
  results: HabitatSuitabilityResult[];
  model_version: string;
  model_accuracy: number;
}

// ── Impact Simulation ─────────────────────────────────────────────────────────

export interface HighwaySimulateRequest {
  geometry_wkt: string;
  project_type: ProjectType;
  project_name: string;
  corridor_id?: number;
  lanes?: number;
  crossings_planned?: number;
  traffic_volume?: 'low' | 'medium' | 'high' | 'very_high';
}

export interface ImpactMetrics {
  connectivity_loss_pct: number;
  habitat_loss_ha: number;
  fragmentation_index: number;
  elephant_passage_risk: string;
  tiger_corridor_break: boolean;
  restoration_cost_cr: number;
  impact_score: number;
  risk_level: RiskLevel;
}

export interface MitigationRecommendation {
  type: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  description: string;
  cost_cr: number;
  effectiveness_pct: number;
}

export interface ImpactScenario {
  scenario_id: number;
  corridor_affected: string | null;
  metrics: ImpactMetrics;
  mitigation_recommendations: MitigationRecommendation[];
  ai_analysis: string;
  species_at_risk: string[];
  computation_time_s: number;
  project_name: string;
  project_type: ProjectType;
}

export interface ScenarioSummary {
  scenario_id: number;
  project_name: string;
  project_type: ProjectType;
  corridor_affected: string | null;
  impact_score: number;
  risk_level: RiskLevel;
  connectivity_loss_pct: number;
}

// ── Restoration ───────────────────────────────────────────────────────────────

export interface RestorationZone {
  id: number;
  corridor_id: number;
  name: string;
  method: string;
  area_ha: number;
  cost_cr: number;
  ecological_benefit_score: number;
  connectivity_gain_pct: number;
  priority_rank: number;
  native_species: string[];
  implementation_years: number;
  notes?: string;
  geometry_wkt?: string | null;
}

export interface RestorationPlan {
  corridor_id: number;
  budget_cr: number;
  zones: RestorationZone[];
  total_cost_cr: number;
  total_connectivity_gain_pct: number;
  total_area_ha: number;
  ai_plan: string;
  roi_score: number;
}

// ── AI ────────────────────────────────────────────────────────────────────────

export interface AIAskResponse {
  question: string;
  answer: string;
  model: string;
  context: string;
}

export interface PolicyBriefResponse {
  audience: string;
  corridor_id: number | null;
  policy_brief: string;
  classification: string;
}
