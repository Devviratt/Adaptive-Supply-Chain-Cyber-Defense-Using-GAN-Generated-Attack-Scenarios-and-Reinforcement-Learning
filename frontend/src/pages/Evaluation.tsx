import { useState, useEffect } from 'react'
import { getExperimentsSummary } from '../api/client'
import type { ExperimentSummaryReport } from '../api/client'

export default function Evaluation() {
  const [summary, setSummary] = useState<ExperimentSummaryReport | null>(null)
  const [selectedExp, setSelectedExp] = useState<string>('C')

  useEffect(() => {
    fetchSummary()
  }, [])

  async function fetchSummary() {
    const res = await getExperimentsSummary()
    if (res.data) {
      setSummary(res.data)
      if (res.data.experiments && !res.data.experiments['C'] && Object.keys(res.data.experiments).length > 0) {
        setSelectedExp(Object.keys(res.data.experiments)[0])
      }
    }
  }

  const expData = summary?.experiments[selectedExp]

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2>Evaluation & Tactical Metrics Engine</h2>
          <p>
            Multi-objective performance audit covering security containment, service availability,
            decision efficiency, and per-attack class robustness.
          </p>
        </div>
        {summary?.experiments && (
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Condition:</span>
            <select
              value={selectedExp}
              onChange={(e) => setSelectedExp(e.target.value)}
              style={{ padding: '0.4rem 0.8rem', background: 'var(--bg-card)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: 'var(--radius-sm)' }}
            >
              {Object.entries(summary.experiments).map(([id, exp]) => (
                <option key={id} value={id}>Exp {id}: {exp.name}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      {!expData ? (
        <div className="card">
          <div className="empty-state">
            <div className="empty-icon">📊</div>
            <h3>No evaluation metrics available</h3>
            <p>Run experiments on the Experiments page or CLI to populate evaluation telemetry.</p>
          </div>
        </div>
      ) : (
        <div>
          {/* Top 4 Multi-Objective Pillars */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--space-md)', marginBottom: 'var(--space-xl)' }}>
            <div className="metric-card" style={{ borderLeft: '4px solid var(--status-healthy)' }}>
              <div className="metric-label">Mitigation Success Rate</div>
              <div className="metric-value" style={{ color: 'var(--status-healthy)' }}>
                {(expData.security.mitigation_success_rate * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                Neutralized without catastrophic collapse
              </div>
            </div>

            <div className="metric-card" style={{ borderLeft: '4px solid var(--accent-primary)' }}>
              <div className="metric-label">Service Availability</div>
              <div className="metric-value" style={{ color: 'var(--accent-primary)' }}>
                {(expData.availability.service_availability * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                Mean supply-chain service uptime
              </div>
            </div>

            <div className="metric-card" style={{ borderLeft: '4px solid var(--accent-secondary)' }}>
              <div className="metric-label">Containment Rate</div>
              <div className="metric-value" style={{ color: 'var(--accent-secondary)' }}>
                {(expData.security.containment_rate * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                Halted lateral inter-stage propagation
              </div>
            </div>

            <div className="metric-card" style={{ borderLeft: '4px solid var(--status-warning)' }}>
              <div className="metric-label">Avg Response Delay</div>
              <div className="metric-value">
                {expData.decision_quality.avg_response_steps.toFixed(1)} <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>steps</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                Steps elapsed before first intervention
              </div>
            </div>
          </div>

          {/* Action Distribution Breakdown */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 'var(--space-lg)', marginBottom: 'var(--space-xl)' }}>
            <div className="card">
              <h3 style={{ marginBottom: 'var(--space-md)' }}>🛡️ Defensive Action Allocation</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
                {Object.entries(expData.decision_quality.action_distribution).map(([action, count]) => {
                  const total = Object.values(expData.decision_quality.action_distribution).reduce((a, b) => a + b, 0)
                  const pct = total > 0 ? (count / total) * 100 : 0
                  return (
                    <div key={action}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.25rem' }}>
                        <span style={{ fontWeight: 600 }}>{action}</span>
                        <span>{count} calls ({pct.toFixed(1)}%)</span>
                      </div>
                      <div style={{ height: '6px', background: 'var(--bg-secondary)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ width: `${pct}%`, height: '100%', background: 'var(--accent-primary)' }} />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            <div className="card">
              <h3 style={{ marginBottom: 'var(--space-md)' }}>⚖️ Operational Efficiency & Cost Quality</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Unnecessary Intervention Rate:</span>
                    <span style={{ fontWeight: 600, color: expData.decision_quality.unnecessary_intervention_rate < 0.1 ? 'var(--status-healthy)' : 'var(--status-warning)' }}>
                      {(expData.decision_quality.unnecessary_intervention_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                    Actions taken when threat risk was 0.0 (prevents over-reaction overhead).
                  </p>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Attack Damage Impact Score:</span>
                    <span style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                      {expData.security.attack_impact_score.toFixed(4)}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                    Cumulative health deficit suffered across stages (lower indicates superior defense).
                  </p>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Catastrophic Failures:</span>
                    <span style={{ fontWeight: 600, color: expData.security.catastrophic_failures === 0 ? 'var(--status-healthy)' : 'var(--status-danger)' }}>
                      {expData.security.catastrophic_failures} episodes
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Breakdown by Attack Class */}
          {expData.performance_by_attack_class && Object.keys(expData.performance_by_attack_class).length > 0 && (
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <div style={{ padding: 'var(--space-md)', background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)' }}>
                <h3 style={{ margin: 0, fontSize: '1rem' }}>🎯 Robustness Across Attack Classes</h3>
              </div>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '0.75rem 1rem' }}>Attack Vector Category</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Evaluation Episodes</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Mitigation Success Rate</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Mean Cumulative Reward</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(expData.performance_by_attack_class).map(([cls, stat]: [string, any]) => (
                    <tr key={cls} style={{ borderBottom: '1px solid var(--border-color)' }}>
                      <td style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>{cls}</td>
                      <td style={{ padding: '0.75rem 1rem' }}>{stat.total_episodes}</td>
                      <td style={{ padding: '0.75rem 1rem', fontWeight: 700, color: stat.mitigation_rate >= 0.7 ? 'var(--status-healthy)' : 'var(--text-primary)' }}>
                        {(stat.mitigation_rate * 100).toFixed(1)}%
                      </td>
                      <td style={{ padding: '0.75rem 1rem', fontFamily: 'var(--font-mono)' }}>
                        {stat.mean_reward.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
