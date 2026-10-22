import { useState, useEffect } from 'react'
import {
  resetSimulation,
  stepSimulation,
  predictDefenseAction,
} from '../api/client'
import type {
  SimulationStepResponse,
  StageStatus,
} from '../api/client'

export default function SupplyChain() {
  const [simState, setSimState] = useState<SimulationStepResponse | null>(null)
  const [totalReward, setTotalReward] = useState(0)
  const [stepCount, setStepCount] = useState(0)
  const [history, setHistory] = useState<Array<{ step: number; action: string; reward: number; health: number }>>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    handleReset()
  }, [])

  async function handleReset(seed?: number) {
    setLoading(true)
    const res = await resetSimulation(seed)
    if (res.data) {
      setSimState(res.data)
      setTotalReward(0)
      setStepCount(0)
      setHistory([])
    }
    setLoading(false)
  }

  async function handleStep(action: number) {
    if (!simState || simState.terminated || simState.truncated) return
    setLoading(true)
    const res = await stepSimulation(action)
    if (res.data) {
      const data = res.data
      const newStep = stepCount + 1
      const newTotal = totalReward + data.reward
      setSimState(data)
      setTotalReward(newTotal)
      setStepCount(newStep)

      const meanHealth =
        Object.values(data.stages).reduce((acc, s) => acc + s.health, 0) /
        Math.max(1, Object.keys(data.stages).length)

      setHistory((prev) => [
        ...prev.slice(-15),
        { step: newStep, action: data.action_taken, reward: data.reward, health: meanHealth },
      ])
    }
    setLoading(false)
  }

  async function handleAgentRecommend() {
    if (!simState) return
    setLoading(true)
    const pred = await predictDefenseAction(simState.observation, 'dqn')
    if (pred.data) {
      await handleStep(pred.data.action)
    }
    setLoading(false)
  }

  const STAGE_ORDER = ['supplier', 'build', 'registry', 'deployment']
  const ACTIONS = [
    { id: 0, name: 'Monitor', icon: '👁️', color: 'var(--status-info)', desc: 'Telemetry' },
    { id: 1, name: 'Isolate', icon: '🔒', color: 'var(--status-warning)', desc: 'Quarantine' },
    { id: 2, name: 'Block', icon: '⛔', color: 'var(--status-danger)', desc: 'Drop Vector' },
    { id: 3, name: 'Rebuild', icon: '🔄', color: 'var(--accent-secondary)', desc: 'Reconstruct' },
    { id: 4, name: 'Recover', icon: '💚', color: 'var(--status-healthy)', desc: 'Restore' },
  ]

  function getHealthColor(health: number) {
    if (health >= 0.8) return 'var(--status-healthy)'
    if (health >= 0.4) return 'var(--status-warning)'
    return 'var(--status-danger)'
  }

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2>Supply Chain Digital Twin Simulator</h2>
          <p>
            Interactive Software Supply-Chain Gymnasium environment (`asccd/SupplyChain-v0`).
            Simulates dynamic cyber attack propagation and defense containment.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
          <button className="btn btn-secondary" onClick={() => handleReset()} disabled={loading}>
            🔄 Reset Episode
          </button>
          <button className="btn btn-primary" onClick={handleAgentRecommend} disabled={loading || !simState || simState.terminated || simState.truncated}>
            🤖 Let DQN Choose Action
          </button>
        </div>
      </div>

      {/* Episode Metrics Banner */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 'var(--space-md)', marginBottom: 'var(--space-xl)' }}>
        <div className="metric-card">
          <div className="metric-label">Episode Step</div>
          <div className="metric-value">{stepCount} / 50</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Cumulative Reward</div>
          <div className="metric-value" style={{ color: totalReward >= 0 ? 'var(--status-healthy)' : 'var(--status-danger)' }}>
            {totalReward.toFixed(2)}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Latest Action</div>
          <div className="metric-value" style={{ fontSize: '1.25rem', color: 'var(--accent-secondary)' }}>
            {simState?.action_taken || 'None'}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Status</div>
          <div className="metric-value" style={{ fontSize: '1.25rem' }}>
            {simState?.terminated ? (
              <span style={{ color: simState.step_info?.mitigated ? 'var(--status-healthy)' : 'var(--status-danger)' }}>
                {simState.step_info?.mitigated ? '✅ Mitigated' : '💥 Compromised'}
              </span>
            ) : simState?.truncated ? (
              <span style={{ color: 'var(--status-warning)' }}>⏱️ Timeout</span>
            ) : (
              <span style={{ color: 'var(--accent-primary)' }}>⚡ Active Threat</span>
            )}
          </div>
        </div>
      </div>

      {/* Supply Chain Topology Cards */}
      <h3 style={{ marginBottom: 'var(--space-md)' }}>⛓️ Software Supply Chain Stage Topology</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--space-md)', marginBottom: 'var(--space-xl)' }}>
        {STAGE_ORDER.map((stageKey, idx) => {
          const stage: StageStatus | undefined = simState?.stages[stageKey]
          const isTarget = simState?.step_info?.active_scenario?.affected_stage === stageKey
          return (
            <div
              key={stageKey}
              className="card"
              style={{
                position: 'relative',
                borderTop: `4px solid ${stage ? getHealthColor(stage.health) : 'var(--border-color)'}`,
                boxShadow: isTarget ? '0 0 15px rgba(239, 68, 68, 0.3)' : 'var(--shadow-sm)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-sm)' }}>
                <span style={{ textTransform: 'uppercase', fontWeight: 700, fontSize: '0.875rem' }}>
                  {idx + 1}. {stageKey}
                </span>
                {stage?.is_isolated && (
                  <span className="badge" style={{ backgroundColor: 'rgba(245, 158, 11, 0.2)', color: 'var(--status-warning)' }}>
                    Quarantined
                  </span>
                )}
                {stage?.is_blocked && (
                  <span className="badge" style={{ backgroundColor: 'rgba(239, 68, 68, 0.2)', color: 'var(--status-danger)' }}>
                    Blocked
                  </span>
                )}
              </div>

              {/* Health Bar */}
              <div style={{ marginBottom: 'var(--space-sm)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.25rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Service Health</span>
                  <span style={{ fontWeight: 600 }}>{((stage?.health ?? 1) * 100).toFixed(0)}%</span>
                </div>
                <div style={{ height: '6px', background: 'var(--bg-secondary)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${(stage?.health ?? 1) * 100}%`,
                      height: '100%',
                      background: getHealthColor(stage?.health ?? 1),
                      transition: 'width 300ms ease',
                    }}
                  />
                </div>
              </div>

              {/* Threat Risk Bar */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.25rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Threat Risk</span>
                  <span style={{ fontWeight: 600, color: (stage?.risk ?? 0) > 0.3 ? 'var(--status-danger)' : 'var(--text-muted)' }}>
                    {((stage?.risk ?? 0) * 100).toFixed(0)}%
                  </span>
                </div>
                <div style={{ height: '6px', background: 'var(--bg-secondary)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${(stage?.risk ?? 0) * 100}%`,
                      height: '100%',
                      background: (stage?.risk ?? 0) > 0.6 ? 'var(--status-danger)' : (stage?.risk ?? 0) > 0.3 ? 'var(--status-warning)' : 'var(--status-healthy)',
                      transition: 'width 300ms ease',
                    }}
                  />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Defensive Action Buttons Panel */}
      <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
        <h3 style={{ marginBottom: 'var(--space-sm)' }}>🛡️ Defensive Control Operations</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: 'var(--space-md)' }}>
          Trigger real-time defensive interventions in the supply chain environment:
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 'var(--space-md)' }}>
          {ACTIONS.map((act) => (
            <button
              key={act.id}
              onClick={() => handleStep(act.id)}
              disabled={loading || !simState || simState.terminated || simState.truncated}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                padding: 'var(--space-md)',
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-md)',
                cursor: 'pointer',
                color: 'var(--text-primary)',
                transition: 'all 200ms ease',
              }}
            >
              <span style={{ fontSize: '1.75rem', marginBottom: '0.25rem' }}>{act.icon}</span>
              <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{act.name}</span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{act.desc}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Telemetry Rollout Log */}
      {history.length > 0 && (
        <div className="card">
          <h3 style={{ marginBottom: 'var(--space-md)' }}>📋 Episode Step Telemetry Stream</h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '0.5rem 1rem', textAlign: 'left' }}>Step</th>
                  <th style={{ padding: '0.5rem 1rem', textAlign: 'left' }}>Action Executed</th>
                  <th style={{ padding: '0.5rem 1rem', textAlign: 'left' }}>Step Reward</th>
                  <th style={{ padding: '0.5rem 1rem', textAlign: 'left' }}>Mean Service Availability</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '0.5rem 1rem', fontFamily: 'var(--font-mono)' }}>#{h.step}</td>
                    <td style={{ padding: '0.5rem 1rem', fontWeight: 600 }}>{h.action}</td>
                    <td style={{ padding: '0.5rem 1rem', color: h.reward >= 0 ? 'var(--status-healthy)' : 'var(--status-danger)' }}>
                      {h.reward >= 0 ? `+${h.reward.toFixed(2)}` : h.reward.toFixed(2)}
                    </td>
                    <td style={{ padding: '0.5rem 1rem' }}>{(h.health * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
