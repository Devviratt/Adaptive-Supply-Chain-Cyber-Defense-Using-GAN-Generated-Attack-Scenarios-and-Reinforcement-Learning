/**
 * ASCCD API Client
 *
 * Centralized API communication layer for the frontend.
 * All API calls go through this module.
 */

const API_BASE = '/api'

interface ApiResponse<T> {
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
// Project
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
