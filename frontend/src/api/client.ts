/**
 * ASCCD API Client
 *
 * Centralized API communication layer for the frontend dashboard.
 * Connects React UI to FastAPI backend endpoints for Scenarios, Simulation,
 * Defense, Experiments, and Project status.
 */

const API_BASE = '/api'

export interface ApiResponse<T> {
  data: T | null
  error: string | null
}

async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return {
        data: null,
        error: errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
      }
    }

    const data = await response.json()
    return { data, error: null }
  } catch (err) {
    return {
      data: null,
      error: err instanceof Error ? err.message : 'Network error',
    }
  }
}

// ============================================================
// Health
// ============================================================

export async function getHealth() {
  return apiFetch<{
    status: string
    service: string
    version: string
    timestamp: string
  }>('/health')
}

export async function getReadiness() {
  return apiFetch<{
    status: string
    checks: { database: string }
  }>('/health/ready')
}

// ============================================================
// Project & Team
// ============================================================

export interface ModuleStatus {
  status: string
  description: string
}

export interface ProjectStatusResponse {
  project: string
  team_number: number
  college: string
  guide: string
  version: string
  current_phase: string
  progress: {
    completed_modules: number
    in_progress_modules: number
    total_modules: number
    percentage: number
  }
  modules: Record<string, ModuleStatus>
  timestamp: string
}

export interface TeamMember {
  name: string
  usn: string
  section: string
  primary_responsibilities: string[]
}

export interface TeamResponse {
  team_number: number
  members: TeamMember[]
  shared_responsibilities: string[]
}

export async function getProjectStatus() {
  return apiFetch<ProjectStatusResponse>('/project/status')
}

export async function getTeamInfo() {
  return apiFetch<TeamResponse>('/project/team')
}

// ============================================================
// Attack Scenarios
// ============================================================

export interface ScenarioItem {
  scenario_id: string
  name?: string
  attack_category: string
  affected_stage: string
  severity: string
  propagation_risk: float
  availability_impact: float
  integrity_impact: float
  confidentiality_impact: float
  source: string
  duration_steps: number
  description: string
}

type float = number

export interface ScenarioListResponse {
  total: number
  scenarios: ScenarioItem[]
}

export async function getScenarios(params?: {
  category?: string
  source?: string
  limit?: number
  offset?: number
}) {
  const query = new URLSearchParams()
  if (params?.category) query.set('category', params.category)
  if (params?.source) query.set('source', params.source)
  if (params?.limit) query.set('limit', String(params.limit))
  if (params?.offset) query.set('offset', String(params.offset))

  const qs = query.toString() ? `?${query.toString()}` : ''
  return apiFetch<ScenarioListResponse>(`/scenarios${qs}`)
}

export async function mapFlowRecord(features: Record<string, any>, label: string = 'DDoS') {
  return apiFetch<ScenarioItem>('/scenarios/map', {
    method: 'POST',
    body: JSON.stringify({ features, label, source: 'ui_mapper' }),
  })
}

// ============================================================
// Supply Chain Simulation
// ============================================================

export interface StageStatus {
  name: string
  health: number
  risk: number
  criticality: number
  is_compromised: boolean
  is_isolated: boolean
  is_blocked: boolean
}

export interface SimulationStepResponse {
  observation: number[]
  reward: number
  terminated: boolean
  truncated: boolean
  stages: Record<string, StageStatus>
  action_taken: string
  step_info: Record<string, any>
}

export interface StageTopologyResponse {
  stages: string[]
  dependencies: { from: string; to: string }[]
  actions: { id: number; name: string; cost: number; description: string }[]
}

export async function getStageTopology() {
  return apiFetch<StageTopologyResponse>('/simulation/stages')
}

export async function resetSimulation(seed?: number, scenario_id?: string) {
  return apiFetch<SimulationStepResponse>('/simulation/reset', {
    method: 'POST',
    body: JSON.stringify({ seed, scenario_id }),
  })
}

export async function stepSimulation(action: number) {
  return apiFetch<SimulationStepResponse>('/simulation/step', {
    method: 'POST',
    body: JSON.stringify({ action }),
  })
}

// ============================================================
// Defense Policies & Models
// ============================================================

export interface PredictResponse {
  action: number
  action_name: string
  model_type: string
  timestamp: string
}

export interface ModelInfo {
  name: string
  algorithm: string
  path: string
  size_bytes: number
  modified_at: string
}

export async function predictDefenseAction(
  observation: number[],
  modelType: string = 'dqn',
  deterministic: boolean = true
) {
  return apiFetch<PredictResponse>('/defense/predict', {
    method: 'POST',
    body: JSON.stringify({
      observation,
      model_type: modelType,
      deterministic,
    }),
  })
}

export async function getDefenseModels() {
  return apiFetch<ModelInfo[]>('/defense/models')
}

// ============================================================
// Controlled Experiments & Evaluation
// ============================================================

export interface ExperimentItem {
  id: number
  experiment_id: string
  model_type: string
  status: string
  started_at?: string
  completed_at?: string
  metrics: Record<string, number>
}

export interface ExperimentSummaryReport {
  timestamp: string
  experiments: Record<
    string,
    {
      experiment_id: string
      name: string
      model_type: string
      dataset: string
      n_episodes: number
      security: {
        mitigation_success_rate: number
        containment_rate: number
        attack_impact_score: number
        catastrophic_failures: number
      }
      availability: {
        service_availability: number
        total_downtime_steps: number
      }
      decision_quality: {
        unnecessary_intervention_rate: number
        avg_response_steps: number
        action_distribution: Record<string, number>
      }
      rl: {
        mean_reward: number
        std_reward: number
        reward_variance: number
      }
      performance_by_attack_class: Record<string, any>
    }
  >
  relative_gains: Record<string, Record<string, number>>
}

export async function getExperiments() {
  return apiFetch<ExperimentItem[]>('/experiments')
}

export async function getExperimentsSummary() {
  return apiFetch<ExperimentSummaryReport>('/experiments/summary')
}

export async function runExperiments(
  experiments: string[] = ['A', 'B', 'C'],
  episodes: number = 10,
  devMode: boolean = true
) {
  return apiFetch<ExperimentSummaryReport>('/experiments/run', {
    method: 'POST',
    body: JSON.stringify({ experiments, episodes, dev_mode: devMode }),
  })
}

// ============================================================
// Data & GAN Summaries
// ============================================================

export interface DataSummaryResponse {
  metadata: {
    total_rows?: number
    total_columns?: number
    label_distribution?: Record<string, number>
    column_names?: string[]
  }
  splits: {
    train_count?: number
    val_count?: number
    test_count?: number
    stratified?: boolean
    splits?: Record<string, number>
  }
  validation: {
    passed_checks?: number
    failed_checks?: number
    all_passed?: boolean
    checks?: Array<{ name: string; status: string; detail?: string }>
  }
}

export interface GanSummaryResponse {
  validation: {
    total_real_samples?: number
    total_synthetic_samples?: number
    num_features?: number
    mean_wasserstein_distance?: number
    correlation_similarity?: number
    mean_js_divergence?: number
    schema_passed?: boolean
    no_nan_or_inf_passed?: boolean
  }
  utility: {
    model_a_real_only?: {
      accuracy?: number
      macro_f1?: number
      weighted_f1?: number
      training_sample_count?: number
    }
    model_b_augmented?: {
      accuracy?: number
      macro_f1?: number
      weighted_f1?: number
      training_sample_count?: number
    }
    accuracy_delta?: number
    macro_f1_delta?: number
    augmentation_utility_positive?: boolean
  }
  figures: string[]
}

export async function getDataSummary() {
  return apiFetch<DataSummaryResponse>('/project/data-summary')
}

export async function getGanSummary() {
  return apiFetch<GanSummaryResponse>('/project/gan-summary')
}

