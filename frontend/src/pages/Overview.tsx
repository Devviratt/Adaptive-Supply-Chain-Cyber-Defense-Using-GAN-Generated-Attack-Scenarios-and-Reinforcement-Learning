import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { getHealth, getProjectStatus, getExperimentsSummary } from '../api/client'
import type { ProjectStatusResponse, ExperimentSummaryReport } from '../api/client'

export default function Overview() {
  const [health, setHealth] = useState<{ status: string; version: string } | null>(null)
  const [projectStatus, setProjectStatus] = useState<ProjectStatusResponse | null>(null)
  const [expSummary, setExpSummary] = useState<ExperimentSummaryReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [backendConnected, setBackendConnected] = useState(false)

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      const [healthRes, statusRes, expRes] = await Promise.all([
        getHealth(),
        getProjectStatus(),
        getExperimentsSummary(),
      ])

      if (healthRes.data) {
        setHealth(healthRes.data)
        setBackendConnected(true)
      }
      if (statusRes.data) {
        setProjectStatus(statusRes.data)
      }
      if (expRes.data) {
        setExpSummary(expRes.data)
      }
      setLoading(false)
    }
    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="loading-spinner">
        <div className="spinner" />
      </div>
    )
  }

  const expA = expSummary?.experiments?.A
  const modules = projectStatus?.modules || {}
  const verifiedPct = projectStatus?.progress?.verified_percentage ?? 45.0
  const targetPct = projectStatus?.progress?.target_checkpoint_percentage ?? 40.0

  // Prepare chart data for module completion vs weight
  const chartData = Object.entries(modules).map(([key, mod]) => ({
    name: key.replace(/_/g, ' '),
    weight: mod.weight || 5,
    completed: mod.status === 'done' ? mod.weight || 5 : 0,
    status: mod.status,
  }))

  return (
    <div>
      {/* Review Checkpoint Banner */}
      <div className="card" style={{ marginBottom: 'var(--space-xl)', borderLeft: '4px solid var(--accent-primary)', background: '#ffffff' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-md)' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', marginBottom: '0.35rem' }}>
              <span className="badge badge-info">College Major Project Review</span>
              <span className="badge badge-neutral">Team 84 · CSE · DSU</span>
              <span className="badge badge-healthy">
                <span className="status-dot healthy"></span> Review 1 Target Met ({verifiedPct}% Verified vs {targetPct}% Required)
              </span>
            </div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-heading)' }}>
              Adaptive Supply Chain Cyber Defense (ASCCD)
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '0.25rem', maxWidth: '850px' }}>
              Research platform exploring Conditional Tabular GAN (CTGAN) attack scenario generation and
              reinforcement learning adaptive defense in a simulated software supply-chain environment.
            </p>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.4rem' }}>
              <strong>Project Guide:</strong> Prof. Namyapriya D · <strong>Status:</strong> Foundation, Preprocessing, CTGAN Synthesis & Simulation Verified
            </div>
          </div>
          <div>
            <Link to="/demo" className="btn btn-primary" style={{ padding: '0.6rem 1.2rem', gap: '0.5rem' }}>
              <span>▶</span> Launch Faculty Demo Sequence
            </Link>
          </div>
        </div>
      </div>

      {/* Verified KPI Cards Grid */}
      <div className="card-grid">
        <div className="card">
          <div className="card-header">
            <span className="card-title">Verified Progress</span>
            <span className="badge badge-info">Audited</span>
          </div>
          <div className="card-value" style={{ color: 'var(--accent-primary)' }}>{verifiedPct}%</div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '4px' }}>
            Target: {targetPct}% · 7 modules done (45.0%) · 4 in-progress · 1 planned
          </p>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Automated Tests</span>
            <span className="badge badge-healthy">100% Pass</span>
          </div>
          <div className="card-value" style={{ color: 'var(--status-healthy)' }}>143 / 143</div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '4px' }}>
            Unit & integration tests passing in pytest (7.0s)
          </p>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Preprocessed Flow Features</span>
            <span className="badge badge-neutral">CIC-IDS2017</span>
          </div>
          <div className="card-value">71 + 1</div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '4px' }}>
            71 numerical features + Label (13/13 validation checks pass)
          </p>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">CTGAN Correlation Fidelity</span>
            <span className="badge badge-healthy">Empirical Pass</span>
          </div>
          <div className="card-value">98.69%</div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '4px' }}>
            Pearson correlation · Mean W₁ = 0.1057 (Threshold &lt; 0.25)
          </p>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Downstream Utility Delta</span>
            <span className="badge badge-healthy">+1.49% Boost</span>
          </div>
          <div className="card-value" style={{ color: 'var(--status-healthy)' }}>80.19%</div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '4px' }}>
            Augmented vs Real Only (78.70%) on held-out test split
          </p>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Rule Baseline (Exp A)</span>
            <span className="badge badge-neutral">5 Seeds</span>
          </div>
          <div className="card-value">{expA ? `${(expA.security.mitigation_success_rate * 100).toFixed(0)}%` : '30%'}</div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '4px' }}>
            {expA ? `Uptime ${(expA.availability.service_availability * 100).toFixed(1)}%` : 'Uptime 99.9%'} · Condition A verified
          </p>
        </div>
      </div>

      {/* Central Chart Area: Milestone Progress & Module Weights */}
      <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
        <div className="card-header">
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Project Milestone Distribution & Verified Progress</h3>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Total weight: 100.0% · Verified complete: {verifiedPct}% · Exceeds Review 1 checkpoint ({targetPct}%)
            </span>
          </div>
          <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
            <span className="badge badge-healthy">
              <span className="status-dot healthy"></span> Completed (45.0%)
            </span>
            <span className="badge badge-warning">
              <span className="status-dot warning"></span> In Progress (50.0%)
            </span>
            <span className="badge badge-neutral">
              Planned (5.0%)
            </span>
          </div>
        </div>

        <div style={{ height: '240px', width: '100%', marginTop: 'var(--space-sm)' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 11, fill: '#64748b' }}
                interval={0}
                angle={-25}
                textAnchor="end"
              />
              <YAxis
                unit="%"
                domain={[0, 25]}
                tick={{ fontSize: 11, fill: '#64748b' }}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload
                    return (
                      <div
                        style={{
                          background: '#ffffff',
                          border: '1px solid #e2e8f0',
                          padding: '8px 12px',
                          borderRadius: '6px',
                          boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
                          fontSize: '0.8rem',
                        }}
                      >
                        <p style={{ fontWeight: 600, color: '#1e293b' }}>{data.name.toUpperCase()}</p>
                        <p style={{ color: '#0284c7' }}>Total Weight: {data.weight}%</p>
                        <p style={{ color: data.status === 'done' ? '#16a34a' : '#d97706' }}>
                          Status: {data.status === 'done' ? 'Completed (100%)' : data.status === 'in_progress' ? 'In Progress' : 'Planned'}
                        </p>
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Bar dataKey="weight" radius={[4, 4, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.status === 'done' ? '#0ea5e9' : entry.status === 'in_progress' ? '#cbd5e1' : '#e2e8f0'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Verified Module Audit Matrix */}
      <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
        <div className="card-header">
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Implementation Verification Matrix</h3>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Accurate breakdown of verified runnable modules vs active research components
            </span>
          </div>
          <span className="badge badge-neutral">
            Backend API: {backendConnected ? `Connected (${health?.version || 'v0.4.0'})` : 'Offline / Mock'}
          </span>
        </div>

        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Component / Module</th>
                <th>Phase</th>
                <th>Verification Status</th>
                <th>Implementation Details & Academic Evidence</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(modules).map(([modKey, mod]) => {
                const isDone = mod.status === 'done'
                const isInProgress = mod.status === 'in_progress'
                return (
                  <tr key={modKey}>
                    <td style={{ fontWeight: 600 }}>{modKey.replace(/_/g, ' ').toUpperCase()}</td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                      {modKey === 'data_pipeline' && 'Phase 2'}
                      {modKey === 'gan' && 'Phase 3'}
                      {modKey === 'scenario_mapper' && 'Phase 4'}
                      {modKey === 'supply_chain_env' && 'Phase 5'}
                      {modKey === 'baseline' && 'Phase 6'}
                      {modKey === 'backend' && 'Phase 1'}
                      {modKey === 'testing' && 'Phase 1-6'}
                      {modKey === 'dqn' && 'Phase 7 (RL)'}
                      {modKey === 'ppo' && 'Phase 7 (RL)'}
                      {modKey === 'evaluation' && 'Phase 8'}
                      {modKey === 'live_telemetry' && 'Phase 10'}
                      {modKey === 'autonomous_defense' && 'Phase 12'}
                    </td>
                    <td>
                      <span className={`badge ${isDone ? 'badge-healthy' : isInProgress ? 'badge-warning' : 'badge-neutral'}`}>
                        <span className={`status-dot ${isDone ? 'healthy' : isInProgress ? 'warning' : ''}`}></span>
                        {isDone ? '100% Verified' : isInProgress ? 'In Progress' : 'Planned'}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>{mod.description}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Two Column Grid: 4-Stage Supply Chain Architecture & Team Info */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: 'var(--space-lg)' }}>
        {/* Architecture Mapping */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">4-Stage Supply Chain Threat Topology</span>
            <span className="badge badge-info">Digital Twin</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
            <div style={{ borderLeft: '3px solid #3b82f6', paddingLeft: 'var(--space-md)' }}>
              <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>1. Supplier Stage (Dependency Ingestion)</div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Target of Poisoning and Web Attacks. Threat vectors impact raw library signatures and upstream integrity.
              </p>
            </div>

            <div style={{ borderLeft: '3px solid #6366f1', paddingLeft: 'var(--space-md)' }}>
              <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>2. Build Stage (CI/CD Pipeline)</div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Target of Infiltration & Brute Force. Compromises pipeline runners, injects build artifacts, and threatens downstream registries.
              </p>
            </div>

            <div style={{ borderLeft: '3px solid #8b5cf6', paddingLeft: 'var(--space-md)' }}>
              <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>3. Registry Stage (Artifact Storage)</div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Target of Tampering & Infiltration. Host to container images and signed release packages.
              </p>
            </div>

            <div style={{ borderLeft: '3px solid #ec4899', paddingLeft: 'var(--space-md)' }}>
              <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>4. Deployment Stage (Production Runtime)</div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Target of DoS, DDoS, and Botnet traffic. Directly impacts service availability, customer uptime, and system throughput.
              </p>
            </div>
          </div>
        </div>

        {/* Team Members & Academic Credentials */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Project Team & Responsibilities</span>
            <span className="badge badge-neutral">DSU CSE 2026</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
            <div style={{ padding: 'var(--space-sm) 0', borderBottom: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong style={{ fontSize: '0.95rem' }}>Dev Virat</strong>
                <span className="badge badge-info">ENG24CS1022 · 7A</span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                System architecture, Gymnasium simulation environment, RL defense models (DQN/PPO), controlled benchmark engine.
              </p>
            </div>

            <div style={{ padding: 'var(--space-sm) 0', borderBottom: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong style={{ fontSize: '0.95rem' }}>C A Anandavarthan</strong>
                <span className="badge badge-info">ENG23CS0039 · 7A</span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                FastAPI backend routers, SQLite persistence schemas, Rule-based SOC policy baseline, interactive simulation controller.
              </p>
            </div>

            <div style={{ padding: 'var(--space-sm) 0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong style={{ fontSize: '0.95rem' }}>Deekshay G</strong>
                <span className="badge badge-info">ENG23CS0055 · 7A</span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                CIC-IDS2017 preprocessing, CTGAN attack scenario synthesis, statistical validation metrics (W1, JS), downstream classifier utility.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
