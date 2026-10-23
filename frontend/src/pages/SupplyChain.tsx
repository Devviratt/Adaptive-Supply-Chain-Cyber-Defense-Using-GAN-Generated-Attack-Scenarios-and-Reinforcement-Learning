import { useState, useEffect } from 'react'
import { resetSimulation, stepSimulation, predictDefenseAction } from '../api/client'
import type { SimulationStepResponse, StageStatus } from '../api/client'

export default function SupplyChain() {
  const [simState, setSimState] = useState<SimulationStepResponse | null>(null)
  const [totalReward, setTotalReward] = useState(0)
  const [stepCount, setStepCount] = useState(0)
  const [history, setHistory] = useState<Array<{ step: number; action: string; reward: number; health: number }>>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activePolicy, setActivePolicy] = useState<'rule_based' | 'dqn'>('rule_based')

  useEffect(() => {
    handleReset()
  }, [])

  async function handleReset(seed?: number) {
    setLoading(true)
    setError(null)
    const res = await resetSimulation(seed)
    if (res.data) {
      setSimState(res.data)
      setTotalReward(0)
      setStepCount(0)
      setHistory([])
    } else if (res.error) {
      setError(res.error)
    }
    setLoading(false)
  }

  async function handleStep(action: number) {
    if (!simState || simState.terminated || simState.truncated) return
    setLoading(true)
    setError(null)
    const res = await stepSimulation(action)
    if (res.data) {
      const data = res.data
      const newStep = stepCount + 1
      const newTotal = totalReward + data.reward
      setSimState(data)
      setTotalReward(newTotal)
      setStepCount(newStep)

      const stagesArr = Object.values(data.stages) as StageStatus[]
      const meanHealth =
        stagesArr.reduce((acc, s) => acc + s.health, 0) / Math.max(1, stagesArr.length)

      setHistory((prev) => [
        ...prev.slice(-15),
        { step: newStep, action: data.action_taken, reward: data.reward, health: meanHealth },
      ])
    } else if (res.error) {
      setError(res.error)
    }
    setLoading(false)
  }

  async function handlePolicyRecommendAndStep() {
    if (!simState) return
    setLoading(true)
    setError(null)
    const pred = await predictDefenseAction(simState.observation, activePolicy)
    if (pred.data) {
      await handleStep(pred.data.action)
    } else if (pred.error) {
      setError(pred.error)
      setLoading(false)
    }
  }

  const STAGE_ORDER = ['supplier', 'build', 'registry', 'deployment']
  const ACTIONS = [
    { id: 0, name: 'Monitor', icon: '👁️', color: 'var(--status-info)', desc: 'Passive Telemetry (Cost: 0.01)' },
    { id: 1, name: 'Isolate', icon: '🔒', color: 'var(--status-warning)', desc: 'Quarantine Stage (Cost: 0.15)' },
    { id: 2, name: 'Block', icon: '⛔', color: 'var(--status-danger)', desc: 'Drop Vector (Cost: 0.25)' },
    { id: 3, name: 'Rebuild', icon: '🔄', color: 'var(--accent-secondary)', desc: 'Reconstruct State (Cost: 0.35)' },
    { id: 4, name: 'Recover', icon: '💚', color: 'var(--status-healthy)', desc: 'Restore Throughput (Cost: 0.20)' },
  ]

  function getHealthColor(health: number) {
    if (health >= 0.8) return 'var(--status-healthy)'
    if (health >= 0.4) return 'var(--status-warning)'
    return 'var(--status-danger)'
  }

  return (
    <div>
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '4px' }}>
          <span className="badge badge-info">Digital Twin Simulation</span>
          <span className="badge badge-neutral">Gymnasium Environment (12-dim State)</span>
        </div>
        <h2>Supply Chain Digital Twin & Interactive Defense</h2>
        <p>
          Discrete-event simulation environment modeling inter-stage compromise propagation, service degradation,
          and sequential defensive containment across 4 software supply-chain stages.
        </p>
      </div>

      {error && (
        <div className="alert alert-warning">
          <strong>Backend Notice:</strong> {error}. Ensure FastAPI backend is running on http://127.0.0.1:8000.
        </div>
      )}

      {/* Control & KPI Header */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-card-header">
            <div className="kpi-header-left">
              <div className="kpi-icon-circle blue">⏱</div>
              <span className="kpi-card-label">Simulation Step</span>
            </div>
            <span className="badge badge-neutral">Horizon: 50</span>
          </div>
          <div className="kpi-card-value">{stepCount} <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>/ 50</span></div>
          <p className="kpi-card-subtext">
            Discrete-event step progression
          </p>
        </div>

        <div className="kpi-card">
          <div className="kpi-card-header">
            <div className="kpi-header-left">
              <div className="kpi-icon-circle green">★</div>
              <span className="kpi-card-label">Cumulative Reward</span>
            </div>
            <span className="badge badge-info">RL Objective</span>
          </div>
          <div className="kpi-card-value" style={{ color: totalReward >= 0 ? 'var(--status-healthy)' : 'var(--status-danger)' }}>
            {totalReward.toFixed(2)}
          </div>
          <p className="kpi-card-subtext">
            Availability minus defense action costs
          </p>
        </div>

        <div className="kpi-card">
          <div className="kpi-card-header">
            <div className="kpi-header-left">
              <div className="kpi-icon-circle purple">🛡</div>
              <span className="kpi-card-label">Last Action</span>
            </div>
            <span className="badge badge-neutral">Action Taken</span>
          </div>
          <div className="kpi-card-value" style={{ fontSize: '1.4rem' }}>
            {simState?.action_taken || 'NONE'}
          </div>
          <p className="kpi-card-subtext">
            Reward Delta: {simState ? simState.reward.toFixed(2) : '0.00'}
          </p>
        </div>

        <div className="kpi-card">
          <div className="kpi-card-header">
            <div className="kpi-header-left">
              <div className="kpi-icon-circle orange">⚡</div>
              <span className="kpi-card-label">Episode State</span>
            </div>
            <span className={`badge ${simState?.terminated ? 'badge-healthy' : simState?.truncated ? 'badge-warning' : 'badge-info'}`}>
              {simState?.terminated ? 'MITIGATED' : simState?.truncated ? 'TRUNCATED' : 'ACTIVE'}
            </span>
          </div>
          <div className="kpi-card-value" style={{ fontSize: '1.3rem' }}>
            {simState?.terminated ? 'Attack Contained' : simState?.truncated ? 'Horizon Reached' : 'Simulating...'}
          </div>
          <p className="kpi-card-subtext">
            {simState?.step_info?.attack_mitigated ? 'Full threat mitigation verified' : 'Threat active in pipeline'}
          </p>
        </div>
      </div>

      {/* 4-Stage Digital Twin Topology Visualizer */}
      <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
        <div className="card-header">
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Supply Chain Stage Health & Compromise State</h3>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Live stage telemetry extracted from environment observation vector
            </span>
          </div>
          <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
            <button className="btn btn-secondary btn-sm" onClick={() => handleReset()}>
              🔄 Reset Simulation
            </button>
            <button className="btn btn-secondary btn-sm" onClick={() => handleReset(42)}>
              Seed 42 (Reproducible)
            </button>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 'var(--space-md)' }}>
          {STAGE_ORDER.map((stageKey) => {
            const st: StageStatus | undefined = simState?.stages?.[stageKey]
            const health = st?.health ?? 1.0
            const risk = st?.risk ?? 0.0
            const isCompromised = st?.is_compromised ?? false
            const isIsolated = st?.is_isolated ?? false
            const isBlocked = st?.is_blocked ?? false

            return (
              <div
                key={stageKey}
                style={{
                  padding: 'var(--space-md)',
                  background: isCompromised ? '#fef2f2' : 'var(--bg-subtle)',
                  border: isCompromised ? '1px solid #fecaca' : '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-md)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-sm)' }}>
                  <strong style={{ fontSize: '0.95rem', textTransform: 'capitalize' }}>{stageKey}</strong>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    {isIsolated && <span className="badge badge-warning">ISOLATED</span>}
                    {isBlocked && <span className="badge badge-danger">BLOCKED</span>}
                    {isCompromised && <span className="badge badge-danger">COMPROMISED</span>}
                    {!isCompromised && !isIsolated && !isBlocked && <span className="badge badge-healthy">NORMAL</span>}
                  </div>
                </div>

                {/* Health Bar */}
                <div style={{ marginBottom: 'var(--space-sm)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '2px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Service Health</span>
                    <strong style={{ color: getHealthColor(health) }}>{(health * 100).toFixed(0)}%</strong>
                  </div>
                  <div style={{ width: '100%', height: '8px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${Math.max(0, Math.min(100, health * 100))}%`,
                        height: '100%',
                        background: getHealthColor(health),
                        transition: 'width 200ms ease',
                      }}
                    />
                  </div>
                </div>

                {/* Risk Bar */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '2px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Compromise Risk</span>
                    <strong style={{ color: risk > 0.5 ? 'var(--status-danger)' : 'var(--text-secondary)' }}>
                      {(risk * 100).toFixed(0)}%
                    </strong>
                  </div>
                  <div style={{ width: '100%', height: '6px', background: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${Math.max(0, Math.min(100, risk * 100))}%`,
                        height: '100%',
                        background: risk > 0.5 ? 'var(--status-danger)' : 'var(--status-warning)',
                        transition: 'width 200ms ease',
                      }}
                    />
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Interactive Defensive Action Dispatcher */}
      <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
        <div className="card-header">
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Interactive Defensive Control Panel</h3>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Dispatch discrete mitigation actions directly to the Gymnasium environment
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Policy:</span>
            <select
              className="form-select"
              value={activePolicy}
              onChange={(e) => setActivePolicy(e.target.value as 'rule_based' | 'dqn')}
              style={{ width: '150px', padding: '0.3rem 0.5rem' }}
            >
              <option value="rule_based">Rule Baseline</option>
              <option value="dqn">DQN Agent</option>
            </select>
            <button
              className="btn btn-primary btn-sm"
              onClick={handlePolicyRecommendAndStep}
              disabled={loading || simState?.terminated || simState?.truncated}
            >
              ⚡ Step with {activePolicy === 'rule_based' ? 'Rule Policy' : 'DQN Agent'}
            </button>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 'var(--space-md)' }}>
          {ACTIONS.map((act) => (
            <button
              key={act.id}
              className="btn btn-secondary"
              onClick={() => handleStep(act.id)}
              disabled={loading || simState?.terminated || simState?.truncated}
              style={{
                flexDirection: 'column',
                padding: 'var(--space-md)',
                height: 'auto',
                textAlign: 'center',
                alignItems: 'center',
              }}
            >
              <span style={{ fontSize: '1.4rem', marginBottom: '4px' }}>{act.icon}</span>
              <strong style={{ fontSize: '0.9rem' }}>{act.name}</strong>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>{act.desc}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Step History Log Table */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Episode Step Execution History</span>
          <span className="badge badge-neutral">{history.length} Steps Recorded</span>
        </div>
        {history.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 'var(--space-lg)', color: 'var(--text-muted)' }}>
            Click an action button above or use "Step with Policy" to execute simulation steps.
          </div>
        ) : (
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Step</th>
                  <th>Action Taken</th>
                  <th style={{ textAlign: 'right' }}>Step Reward</th>
                  <th style={{ textAlign: 'right' }}>Pipeline Health</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h) => (
                  <tr key={h.step}>
                    <td>Step #{h.step}</td>
                    <td style={{ fontWeight: 600 }}>{h.action}</td>
                    <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{h.reward.toFixed(2)}</td>
                    <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{(h.health * 100).toFixed(0)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
