import { useState, useEffect } from 'react'
import { getExperimentsSummary, runExperiments } from '../api/client'
import type { ExperimentSummaryReport } from '../api/client'

export default function Experiments() {
  const [summary, setSummary] = useState<ExperimentSummaryReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const runEpisodes = 10
  const devMode = true

  useEffect(() => {
    fetchSummary()
  }, [])

  async function fetchSummary() {
    setLoading(true)
    const res = await getExperimentsSummary()
    if (res.data) {
      setSummary(res.data)
    }
    setLoading(false)
  }

  async function handleRunExperiments() {
    setRunning(true)
    const res = await runExperiments(['A', 'B', 'C'], runEpisodes, devMode)
    if (res.data) {
      setSummary(res.data)
    }
    setRunning(false)
  }

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2>Controlled Benchmark Experiments Hub</h2>
          <p>
            Systematic comparative evaluation across Experiment A (Rule-Based Baseline),
            Experiment B (DQN Real Only), and Experiment C (DQN + CTGAN Augmented).
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={handleRunExperiments}
          disabled={running}
        >
          {running ? 'Executing Experiments...' : '🔬 Run Benchmark Suite'}
        </button>
      </div>

      {/* Relative Gains Summary Cards */}
      {summary?.relative_gains && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 'var(--space-md)', marginBottom: 'var(--space-xl)' }}>
          {summary.relative_gains.C_vs_A && (
            <div className="card" style={{ borderLeft: '4px solid var(--status-healthy)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Scientific Value-Add (C vs A)</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, marginTop: '0.25rem' }}>DQN+GAN vs Rule Baseline</div>
              <div style={{ marginTop: 'var(--space-sm)', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Mitigation Gain:</span>
                  <span style={{ fontWeight: 700, color: 'var(--status-healthy)' }}>
                    +{summary.relative_gains.C_vs_A.mitigation_delta_pct}%
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Availability Delta:</span>
                  <span style={{ fontWeight: 600 }}>
                    +{summary.relative_gains.C_vs_A.availability_delta_pct}%
                  </span>
                </div>
              </div>
            </div>
          )}

          {summary.relative_gains.C_vs_B && (
            <div className="card" style={{ borderLeft: '4px solid var(--accent-primary)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>GAN Augmentation Value-Add (C vs B)</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, marginTop: '0.25rem' }}>DQN+GAN vs DQN Real Only</div>
              <div style={{ marginTop: 'var(--space-sm)', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Mitigation Delta:</span>
                  <span style={{ fontWeight: 700, color: 'var(--status-healthy)' }}>
                    +{summary.relative_gains.C_vs_B.mitigation_delta_pct}%
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Availability Delta:</span>
                  <span style={{ fontWeight: 600 }}>
                    +{summary.relative_gains.C_vs_B.availability_delta_pct}%
                  </span>
                </div>
              </div>
            </div>
          )}

          {summary.relative_gains.B_vs_A && (
            <div className="card" style={{ borderLeft: '4px solid var(--accent-secondary)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>RL Autonomy Value-Add (B vs A)</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, marginTop: '0.25rem' }}>DQN Real vs Rule Baseline</div>
              <div style={{ marginTop: 'var(--space-sm)', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Mitigation Delta:</span>
                  <span style={{ fontWeight: 700, color: 'var(--status-healthy)' }}>
                    +{summary.relative_gains.B_vs_A.mitigation_delta_pct}%
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Main Benchmark Comparison Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden', marginBottom: 'var(--space-xl)' }}>
        <div style={{ padding: 'var(--space-md)', background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, fontSize: '1rem' }}>Comparative Scientific Benchmark Matrix</h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Last updated: {summary?.timestamp ? new Date(summary.timestamp).toLocaleString() : 'N/A'}
          </span>
        </div>

        {loading ? (
          <div style={{ padding: 'var(--space-xl)', textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading benchmark evaluation matrix...
          </div>
        ) : !summary || !summary.experiments ? (
          <div className="empty-state">
            <div className="empty-icon">🔬</div>
            <h3>No experiment results found</h3>
            <p>Click "Run Benchmark Suite" above or execute `python scripts/run_experiments.py` on the CLI.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>ID</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Condition Name</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Model Architecture</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Training Dataset</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Mitigation Rate</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Containment Rate</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Service Availability</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Mean Cumulative Reward</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(summary.experiments).map(([expId, exp]) => (
                  <tr key={expId} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '0.75rem 1rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-primary)' }}>
                      {expId}
                    </td>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>{exp.name}</td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <span className="badge" style={{ backgroundColor: 'rgba(59, 130, 246, 0.15)', color: 'var(--accent-primary)' }}>
                        {exp.model_type}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem 1rem', color: 'var(--text-secondary)' }}>{exp.dataset}</td>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 700, color: exp.security.mitigation_success_rate >= 0.7 ? 'var(--status-healthy)' : 'var(--text-primary)' }}>
                      {(exp.security.mitigation_success_rate * 100).toFixed(1)}%
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      {(exp.security.containment_rate * 100).toFixed(1)}%
                    </td>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 600, color: 'var(--status-healthy)' }}>
                      {(exp.availability.service_availability * 100).toFixed(1)}%
                    </td>
                    <td style={{ padding: '0.75rem 1rem', fontFamily: 'var(--font-mono)' }}>
                      {exp.rl.mean_reward.toFixed(2)} ± {exp.rl.std_reward.toFixed(1)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Artifact Export Links Card */}
      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-md)' }}>
        <div>
          <h4>📄 Scientific Reports & Plot Exports</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '0.2rem' }}>
            Data and publication charts saved to `artifacts/reports/` and `artifacts/figures/`.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
          <a
            href="/api/experiments/summary"
            target="_blank"
            rel="noreferrer"
            className="btn btn-secondary"
            style={{ textDecoration: 'none' }}
          >
            📥 View JSON Summary
          </a>
        </div>
      </div>
    </div>
  )
}
