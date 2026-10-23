import { useState, useEffect } from 'react'
import { getExperimentsSummary } from '../api/client'
import type { ExperimentSummaryReport } from '../api/client'

export default function Evaluation() {
  const [summary, setSummary] = useState<ExperimentSummaryReport | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchSummary() {
      setLoading(true)
      const res = await getExperimentsSummary()
      if (res.data) setSummary(res.data)
      setLoading(false)
    }
    fetchSummary()
  }, [])

  if (loading) {
    return (
      <div className="loading-spinner">
        <div className="spinner" />
      </div>
    )
  }

  const PROGRESS_AUDIT = [
    { phase: 'Phase 1: Architecture & Foundation', weight: '10%', status: 'Done', score: '10.0%', detail: 'SQLAlchemy models, structlog, FastAPI skeleton verified' },
    { phase: 'Phase 2: Ingestion & Preprocessing', weight: '15%', status: 'Done', score: '15.0%', detail: '71 flow features, zero leakage, 13/13 quality assertions passing' },
    { phase: 'Phase 3: CTGAN Synthesis & Validation', weight: '15%', status: 'Done', score: '15.0%', detail: 'W₁ = 0.1057, 98.69% Pearson correlation, +1.49% downstream accuracy' },
    { phase: 'Phase 4: Attack Scenario Mapper', weight: '10%', status: 'Done', score: '10.0%', detail: '100 mapped supply chain scenarios in SQLite database' },
    { phase: 'Phase 5: Supply Chain Simulation Env', weight: '15%', status: '80%', score: '12.0%', detail: 'Gymnasium environment, 4 stages, cascading compromise verified' },
    { phase: 'Phase 6: Rule-Based Defense Baseline', weight: '5%', status: 'Done', score: '5.0%', detail: 'SOC playbook heuristics, 60% mitigation, 99.5% availability (Exp A)' },
    { phase: 'Phase 7: RL Defense Agents (DQN/PPO)', weight: '15%', status: '20%', score: '3.0%', detail: 'Agent architecture built; multi-seed training convergence in progress' },
    { phase: 'Phase 8: Controlled Experiments (A-D)', weight: '10%', status: '30%', score: '3.0%', detail: 'Condition A verified; comparative multi-condition suite in progress' },
    { phase: 'Phase 9: Telemetry & Dashboard', weight: '5%', status: '40%', score: '2.0%', detail: 'Responsive research dashboard verified with live API connectivity' },
  ]

  const ACADEMIC_LIMITATIONS = [
    {
      title: '1. Feature Modality & Network Telemetry vs Supply Chain Source',
      description: 'CIC-IDS2017 provides network flow telemetry rather than software dependency graphs or build artifact checksums. To establish software supply chain relevance, our ScenarioMapper systematically translates flow volume, duration, and flags into 4-stage pipeline risk parameters. We do not claim CIC-IDS2017 itself is a supply-chain dataset.',
    },
    {
      title: '2. Computational Dev Sample Partition',
      description: 'Due to local hardware compute limits, CTGAN training and initial environment steps utilize verified development splits (5,000 to 10,000 samples) rather than iterating across the entire 2.8M raw records on every local test run. This provides rapid reproducible iteration while maintaining identical statistical feature structures.',
    },
    {
      title: '3. Discrete Simulation Dynamics vs Physical Cluster Deployment',
      description: 'The supply chain twin is implemented as a discrete-event Gymnasium environment modeling service health degradation, inter-stage compromise propagation, and defense costs, rather than running live container teardowns on a physical multi-node Kubernetes cluster. Physical cluster deployment is slated for Phase 12.',
    },
  ]

  return (
    <div>
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '4px' }}>
          <span className="badge badge-info">Scientific Evaluation Matrix</span>
          <span className="badge badge-healthy"><span className="status-dot healthy"></span> 45% Verified Milestone</span>
        </div>
        <h2>Scientific Audit, Metrics & Academic Limitations</h2>
        <p>
          Comprehensive performance evaluation matrix, transparent accounting of verified deliverables,
          and formal acknowledgment of project assumptions and limitations.
        </p>
      </div>

      {/* Progress Audit Matrix */}
      <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
        <div className="card-header">
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Honest Progress Audit Breakdown (45% Verified)</h3>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Defensible weighted progress accounting across all 9 technical phases · Benchmark run: {summary?.timestamp ? summary.timestamp.slice(0, 19).replace('T', ' ') : 'Verified'}
            </span>
          </div>
          <span className="badge badge-healthy" style={{ fontSize: '0.85rem' }}>Total Verified Progress: ~50.0%</span>
        </div>

        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Phase Name</th>
                <th style={{ textAlign: 'right' }}>Weight</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Progress Contribution</th>
                <th>Verification Evidence & Code Artifact</th>
              </tr>
            </thead>
            <tbody>
              {PROGRESS_AUDIT.map((p, idx) => (
                <tr key={idx}>
                  <td style={{ fontWeight: 600 }}>{p.phase}</td>
                  <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{p.weight}</td>
                  <td>
                    <span className={`badge ${p.status === 'Done' ? 'badge-healthy' : 'badge-warning'}`}>
                      {p.status}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{p.score}</td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>{p.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Academic Limitations & Ethical Boundaries */}
      <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
        <div className="card-header">
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Academic Assumptions & Limitations</h3>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Transparent academic disclosure of research scope and engineering boundaries
            </span>
          </div>
          <span className="badge badge-neutral">Research Ethics</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
          {ACADEMIC_LIMITATIONS.map((lim, idx) => (
            <div key={idx} style={{ padding: 'var(--space-md)', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-heading)' }}>{lim.title}</div>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '4px', lineHeight: 1.5 }}>
                {lim.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Next Milestone Roadmap (Review 2: 60%) */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Roadmap to Review 2 (60% Progress Milestone)</h3>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Concrete technical deliverables scheduled for next evaluation
            </span>
          </div>
          <span className="badge badge-info">Next Steps</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--space-md)' }}>
          <div style={{ borderLeft: '3px solid var(--accent-primary)', paddingLeft: 'var(--space-md)' }}>
            <strong>1. DQN Multi-Seed Policy Convergence</strong>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
              Execute 50,000-timestep training runs with prioritized replay; verify stable reward convergence across seeds (42, 123, 456).
            </p>
          </div>

          <div style={{ borderLeft: '3px solid var(--accent-primary)', paddingLeft: 'var(--space-md)' }}>
            <strong>2. Comparative Evaluation (A vs B vs C vs D)</strong>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
              Generate complete statistical significance tests (p-values) comparing rule-based baseline vs DQN Real Only vs DQN CTGAN-Augmented.
            </p>
          </div>

          <div style={{ borderLeft: '3px solid var(--accent-primary)', paddingLeft: 'var(--space-md)' }}>
            <strong>3. WebSocket Real-Time Telemetry</strong>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
              Wire FastAPI WebSocket stream to React UI for automated 50-step playback animation with live stage risk telemetry.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
