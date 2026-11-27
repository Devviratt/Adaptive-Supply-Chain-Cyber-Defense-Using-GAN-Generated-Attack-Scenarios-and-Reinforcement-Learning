import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  getScenarios,
  resetSimulation,
  stepSimulation,
  predictDefenseAction,
} from '../api/client'
import type {
  PredictResponse,
  ScenarioItem,
  SimulationStepResponse,
  StageStatus,
} from '../api/client'
import type { CountermeasurePlan } from '../api/client'

const STAGE_ORDER = ['supplier', 'build', 'registry', 'deployment']
const ACTIONS = [
  { id: 0, name: 'Monitor', desc: 'Telemetry' },
  { id: 1, name: 'Isolate', desc: 'Quarantine' },
  { id: 2, name: 'Block', desc: 'Drop Vector' },
  { id: 3, name: 'Rebuild', desc: 'Reconstruct' },
  { id: 4, name: 'Recover', desc: 'Restore' },
]
const COUNTERMEASURE_PHASES = [
  {
    id: 'preventive',
    title: 'Prevent before impact',
    description: 'Reduce the chance of this attack reaching the supply chain.',
  },
  {
    id: 'immediate',
    title: 'Contain the incident',
    description: 'Limit spread and protect evidence while the threat is active.',
  },
  {
    id: 'recovery',
    title: 'Recover from trusted sources',
    description: 'Restore the affected stage without trusting compromised assets.',
  },
  {
    id: 'validation',
    title: 'Validate and restore',
    description: 'Verify integrity before returning services to normal operation.',
  },
] as const
const PRIORITY_ORDER: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
}

export default function SupplyChain() {
  const [searchParams] = useSearchParams()
  const requestedScenarioId = searchParams.get('scenario_id')
  const [simState, setSimState] = useState<SimulationStepResponse | null>(null)
  const [stepCount, setStepCount] = useState(0)
  const [history, setHistory] = useState<Array<{ step: number; action: string; reward: number; health: number }>>([])
  const [loading, setLoading] = useState(false)
  const [countermeasures, setCountermeasures] = useState<CountermeasurePlan | null>(null)
  const [attackScenarios, setAttackScenarios] = useState<ScenarioItem[]>([])
  const [selectedScenarioId, setSelectedScenarioId] = useState('')
  const [recommendation, setRecommendation] = useState<PredictResponse | null>(null)
  const [policy, setPolicy] = useState('dqn')
  const [error, setError] = useState('')
  const initialized = useRef(false)

  useEffect(() => {
    if (initialized.current) return
    initialized.current = true

    async function initialize() {
      setLoading(true)
      const scenarios = await getScenarios({ limit: 500 })
      const availableAttacks = (scenarios.data?.scenarios ?? [])
        .filter((scenario) => scenario.attack_category.toLowerCase() !== 'benign')
      const requestedAttack = availableAttacks.find(
        (scenario) => scenario.scenario_id === requestedScenarioId,
      )
      const orderedAttacks = requestedAttack
        ? [requestedAttack, ...availableAttacks.filter((scenario) => scenario !== requestedAttack)]
        : availableAttacks
      const uniqueAttackKeys = new Set<string>()
      const attacks = orderedAttacks
        .filter((scenario) => {
          const key = `${scenario.attack_category}:${scenario.affected_stage}`
          if (uniqueAttackKeys.has(key)) return false
          uniqueAttackKeys.add(key)
          return true
        })
        .sort((a, b) => {
          const severityRank: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 }
          return (severityRank[a.severity.toLowerCase()] ?? 4) - (severityRank[b.severity.toLowerCase()] ?? 4)
        })
      setAttackScenarios(attacks)
      if (scenarios.error) setError(`Could not load stored attacks: ${scenarios.error}`)
      const firstScenarioId = requestedAttack?.scenario_id ?? attacks[0]?.scenario_id ?? ''
      setSelectedScenarioId(firstScenarioId)
      const reset = await resetSimulation(undefined, firstScenarioId || undefined)
      if (reset.data) {
        setSimState(reset.data)
        setCountermeasures(reset.data.step_info?.countermeasures ?? null)
        const sensed = await predictDefenseAction(reset.data.observation, 'dqn')
        if (sensed.data) setRecommendation(sensed.data)
        else if (sensed.error) setError(sensed.error)
      } else if (reset.error) {
        setError(reset.error)
      }
      setLoading(false)
    }

    void initialize()
  }, [requestedScenarioId])

  async function handleReset(seed?: number, scenarioId: string | null = selectedScenarioId || null) {
    setLoading(true)
    setError('')
    const res = await resetSimulation(seed, scenarioId || undefined)
    if (res.data) {
      setSimState(res.data)
      setCountermeasures(res.data.step_info?.countermeasures ?? null)
      setStepCount(0)
      setHistory([])
      const sensed = await predictDefenseAction(res.data.observation, policy)
      if (sensed.data) setRecommendation(sensed.data)
      else if (sensed.error) setError(sensed.error)
    } else if (res.error) {
      setError(res.error)
    }
    setLoading(false)
  }

  async function handleStep(action: number) {
    if (!simState || simState.terminated || simState.truncated) return
    setLoading(true)
    const res = await stepSimulation(action)
    if (res.data) {
      const data = res.data
      if (data.step_info?.countermeasures) {
        setCountermeasures(data.step_info.countermeasures)
      }
      const newStep = stepCount + 1
      setSimState(data)
      setStepCount(newStep)

      setHistory((prev) => [
        ...prev.slice(-15),
        {
          step: newStep,
          action: data.action_taken,
          reward: data.reward,
          health:
            Object.values(data.stages).reduce((acc, stage) => acc + stage.health, 0) /
            Math.max(1, Object.keys(data.stages).length),
        },
      ])
      if (!data.terminated && !data.truncated) {
        const sensed = await predictDefenseAction(data.observation, policy)
        if (sensed.data) setRecommendation(sensed.data)
        else if (sensed.error) setError(sensed.error)
      } else {
        setRecommendation(null)
      }
    } else if (res.error) setError(res.error)
    setLoading(false)
  }

  async function handleSense() {
    if (!simState || simState.terminated || simState.truncated) return
    setLoading(true)
    setError('')
    const pred = await predictDefenseAction(simState.observation, policy)
    if (pred.data) setRecommendation(pred.data)
    else if (pred.error) setError(pred.error)
    setLoading(false)
  }

  async function handlePolicyChange(selectedPolicy: string) {
    setPolicy(selectedPolicy)
    if (!simState || simState.terminated || simState.truncated) return
    setLoading(true)
    const sensed = await predictDefenseAction(simState.observation, selectedPolicy)
    if (sensed.data) setRecommendation(sensed.data)
    else if (sensed.error) setError(sensed.error)
    setLoading(false)
  }

  const activeScenario = simState?.step_info?.active_scenario as ScenarioItem | undefined
  const targetStage = activeScenario?.affected_stage ?? simState?.step_info?.affected_stage
  const highestRiskStage = STAGE_ORDER.reduce((highest, stageName) => {
    const risk = simState?.stages[stageName]?.risk ?? 0
    return risk > (simState?.stages[highest]?.risk ?? 0) ? stageName : highest
  }, STAGE_ORDER[0])
  const highestRisk = simState?.stages[highestRiskStage]?.risk ?? 0
  const detected = activeScenario?.attack_category !== 'benign' && highestRisk >= 0.3
  const recommendedAction = ACTIONS.find((action) => action.id === recommendation?.action)
  const actionGuidance: Record<number, string> = {
    0: 'Keep collecting telemetry and re-assess on the next state transition.',
    1: `Quarantine ${highestRiskStage} and stop its links to neighboring stages.`,
    2: `Block incoming attack vectors at ${highestRiskStage} before the next simulated impact.`,
    3: `Rebuild ${highestRiskStage} from a trusted baseline, then verify its integrity.`,
    4: `Restore ${highestRiskStage} availability after its threat risk is contained.`,
  }

  function getHealthColor(health: number) {
    if (health >= 0.8) return 'var(--status-healthy)'
    if (health >= 0.4) return 'var(--status-warning)'
    return 'var(--status-danger)'
  }

  function getHealthLabel(health: number) {
    if (health >= 0.8) return 'Operating normally'
    if (health >= 0.4) return 'Service disrupted'
    return 'Service unavailable'
  }

  function getRiskLabel(risk: number) {
    if (risk >= 0.6) return 'High threat'
    if (risk >= 0.3) return 'Threat detected'
    return 'Low threat'
  }

  function isPropagationOpen(source: string, destination: string) {
    const sourceStage = simState?.stages[source]
    const destinationStage = simState?.stages[destination]
    return Boolean(
      sourceStage &&
      destinationStage &&
      sourceStage.risk >= 0.3 &&
      !sourceStage.is_isolated &&
      !destinationStage.is_isolated &&
      !destinationStage.is_blocked,
    )
  }

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2>Supply-chain attack simulator</h2>
          <p>
            Watch a synthetic attack affect the supply chain, then choose a response to contain it.
          </p>
        </div>
      </div>

      {error && (
        <div role="alert" className="card" style={{ marginBottom: 'var(--space-md)', borderColor: 'var(--status-danger)', color: 'var(--status-danger)' }}>
          {error}
        </div>
      )}

      <div className="card attack-launcher">
        <div>
          <label htmlFor="attack-scenario" className="metric-label">Choose an attack</label>
          <select
            id="attack-scenario"
            className="form-input"
            value={selectedScenarioId}
            onChange={(event) => setSelectedScenarioId(event.target.value)}
            disabled={loading || attackScenarios.length === 0}
          >
            {attackScenarios.length === 0 ? (
              <option value="">No stored attack scenarios</option>
            ) : attackScenarios.map((scenario) => (
              <option key={scenario.scenario_id} value={scenario.scenario_id}>
                {scenario.attack_category.toUpperCase()} · {scenario.severity} · {scenario.affected_stage} · {scenario.source}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="defense-policy" className="metric-label">How should we suggest a response?</label>
          <select
            id="defense-policy"
            className="form-input"
            value={policy}
            onChange={(event) => void handlePolicyChange(event.target.value)}
            disabled={loading}
          >
            <option value="dqn">Learned response</option>
            <option value="rule_based">Rule-based suggestion</option>
            <option value="ppo">Experimental policy</option>
          </select>
        </div>
        <div className="attack-launcher-actions">
          <button className="btn btn-primary" onClick={() => void handleReset(undefined, selectedScenarioId || undefined)} disabled={loading}>
            {loading ? 'Starting…' : 'Launch selected attack'}
          </button>
          <button className="btn btn-secondary" onClick={() => void handleReset(undefined, null)} disabled={loading}>
            Random attack
          </button>
          <button className="btn btn-secondary" onClick={() => void handleReset()} disabled={loading}>
            Reset episode
          </button>
        </div>
      </div>

      <section className="simulation-status-card" aria-live="polite">
        <span className="countermeasure-eyebrow">Simulation update</span>
        <strong>
          {simState?.terminated
            ? simState.step_info?.mitigated ? 'The simulated attack was contained' : 'The simulated attack caused an impact'
            : simState?.truncated
              ? 'The simulation ended before the threat was contained'
              : 'The simulated incident is active'}
        </strong>
        <p>
          {simState?.action_taken
            ? `Most recent response: ${simState.action_taken}.`
            : 'Launch an attack to see its effects and suggested responses.'}
        </p>
      </section>

      <section className={`threat-sensor ${detected ? 'threat-sensor-active' : ''}`} aria-live="polite">
        <div className="threat-sensor-indicator" aria-hidden="true" />
        <div className="threat-sensor-copy">
          <strong>{detected ? 'Threat detected' : 'Sensor monitoring'}</strong>
          <span>
            {detected
              ? `${activeScenario?.attack_category ?? 'Attack'} · ${activeScenario?.severity ?? 'unknown'} severity · affecting ${highestRiskStage}`
              : 'No active compromise signal detected in the current episode.'}
          </span>
        </div>
        <button className="btn btn-secondary" onClick={() => void handleSense()} disabled={loading || !simState || simState.terminated || simState.truncated}>
          Sense now
        </button>
      </section>

      {recommendation && recommendedAction && (
        <section
          key={`${stepCount}-${recommendation.action}`}
          className="defense-recommendation"
          aria-live="polite"
        >
          <div className="defense-recommendation-copy">
            <span className="metric-label">Suggested next step · {highestRiskStage}</span>
            <strong>{recommendedAction.name}: {recommendedAction.desc}</strong>
            <span>
              {actionGuidance[recommendation.action]}
            </span>
              {countermeasures?.immediate[0] && (
              <span className="recommended-control">
                  Incident-response playbook: {countermeasures.immediate[0].control} — {countermeasures.immediate[0].action}
              </span>
            )}
          </div>
          <button
            className="btn btn-primary"
            onClick={() => void handleStep(recommendation.action)}
            disabled={loading || !simState || simState.terminated || simState.truncated}
          >
            Apply {recommendedAction.name}
          </button>
        </section>
      )}

      <h3 style={{ marginBottom: 'var(--space-md)' }}>Where the attack spreads</h3>
      <div className="supply-chain-topology">
        <div className="attack-flow-caption">
          <span className="attack-source-pulse" />
          Attack starts at <span>→</span> {String(targetStage ?? 'selected stage')}
          {activeScenario?.attack_category && <span className="attack-category-label">{activeScenario.attack_category.toUpperCase()}</span>}
        </div>
        <svg className="topology-connections" viewBox="0 0 1200 100" preserveAspectRatio="none" aria-hidden="true">
          {STAGE_ORDER.slice(0, -1).map((stageName, index) => {
            const nextStage = STAGE_ORDER[index + 1]
            const path = `M ${150 + index * 300} 50 L ${450 + index * 300} 50`
            const active = isPropagationOpen(stageName, nextStage)
            return (
              <g key={stageName}>
                <path d={path} className={`topology-edge ${active ? 'topology-edge-active' : ''}`} />
                {active && (
                  <circle r="7" className="attack-particle">
                    <animateMotion dur="2.8s" repeatCount="indefinite" path={path} />
                  </circle>
                )}
              </g>
            )
          })}
        </svg>
        <div className="topology-stage-grid">
        {STAGE_ORDER.map((stageKey) => {
          const stage: StageStatus | undefined = simState?.stages[stageKey]
          const isTarget = targetStage === stageKey
          const stageStatus = stage?.is_compromised ? 'Compromised' : (stage?.risk ?? 0) >= 0.3 ? 'Suspicious' : 'Healthy'
          const stageHealth = stage?.health ?? 1
          const stageRisk = stage?.risk ?? 0
          return (
            <div
              key={stageKey}
              className={`topology-stage ${isTarget ? 'topology-stage-target' : ''} ${stageStatus.toLowerCase()}`}
              style={{
                borderTop: `4px solid ${stage ? getHealthColor(stage.health) : 'var(--border-color)'}`,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-sm)' }}>
                <span style={{ textTransform: 'uppercase', fontWeight: 700, fontSize: '0.875rem' }}>
                  {stageKey}
                </span>
                <span className={`stage-status-badge ${stageStatus.toLowerCase()}`}>{stageStatus}</span>
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
              <div className="stage-threat-indicator">
                <span>{isTarget ? 'ATTACK TARGET' : 'SUPPLY-CHAIN NODE'}</span>
                <span>{stage?.is_blocked ? 'TRAFFIC BLOCKED' : stage?.is_isolated ? 'NETWORK ISOLATED' : 'CONNECTED'}</span>
              </div>

              {/* Health Bar */}
              <div style={{ marginBottom: 'var(--space-sm)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.25rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Service health</span>
                  <span style={{ fontWeight: 600 }}>{getHealthLabel(stageHealth)}</span>
                </div>
                <div
                  role="progressbar"
                  aria-label={`${stageKey} service health`}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={Math.round(stageHealth * 100)}
                  style={{ height: '6px', background: 'var(--bg-secondary)', borderRadius: '3px', overflow: 'hidden' }}
                >
                  <div
                    style={{
                      width: `${stageHealth * 100}%`,
                      height: '100%',
                      background: getHealthColor(stageHealth),
                      transition: 'width 1.1s cubic-bezier(0.22, 1, 0.36, 1)',
                    }}
                  />
                </div>
              </div>

              {/* Threat Risk Bar */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.25rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Threat level</span>
                  <span style={{ fontWeight: 600, color: stageRisk > 0.3 ? 'var(--status-danger)' : 'var(--text-muted)' }}>
                    {getRiskLabel(stageRisk)}
                  </span>
                </div>
                <div
                  role="progressbar"
                  aria-label={`${stageKey} threat level`}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={Math.round(stageRisk * 100)}
                  style={{ height: '6px', background: 'var(--bg-secondary)', borderRadius: '3px', overflow: 'hidden' }}
                >
                  <div
                    style={{
                      width: `${stageRisk * 100}%`,
                      height: '100%',
                      background: stageRisk > 0.6 ? 'var(--status-danger)' : stageRisk > 0.3 ? 'var(--status-warning)' : 'var(--status-healthy)',
                      transition: 'width 1.1s cubic-bezier(0.22, 1, 0.36, 1)',
                    }}
                  />
                </div>
              </div>
            </div>
          )
        })}
        </div>
      </div>

      {/* Defensive Action Buttons Panel */}
      <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
        <h3 style={{ marginBottom: 'var(--space-sm)' }}>Choose a response</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: 'var(--space-md)' }}>
          Try a response yourself, or use the suggested action above.
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
              <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{act.name}</span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{act.desc}</span>
            </button>
          ))}
        </div>
      </div>

      {countermeasures && (
        <section className="countermeasure-plan" aria-labelledby="countermeasure-title">
          <div className="countermeasure-plan-header">
            <div>
              <span className="countermeasure-eyebrow">Incident response playbook</span>
              <h3 id="countermeasure-title">Recommended countermeasures</h3>
              <p>
                A practical response guide for this simulated {countermeasures.attack_category} scenario.
                Controls for the affected stage and critical priorities are shown first.
              </p>
            </div>
            <div className="countermeasure-context">
              <span className="countermeasure-context-label">Current scenario</span>
              <strong>{countermeasures.attack_category.replace(/_/g, ' ')}</strong>
              <div className="countermeasure-tags">
                <span className="countermeasure-tag">{countermeasures.affected_stage}</span>
                <span className={`countermeasure-tag severity-${countermeasures.severity}`}>
                  {countermeasures.severity} severity
                </span>
              </div>
            </div>
          </div>

          <div className="countermeasure-phases">
            {COUNTERMEASURE_PHASES.map((phase) => {
              const controls = countermeasures[phase.id]
              const orderedControls = [...controls].sort((a, b) => {
                const stageRelevance =
                  Number(b.stage === countermeasures.affected_stage) -
                  Number(a.stage === countermeasures.affected_stage)
                if (stageRelevance !== 0) return stageRelevance
                return (
                  (PRIORITY_ORDER[a.priority.toLowerCase()] ?? 4) -
                  (PRIORITY_ORDER[b.priority.toLowerCase()] ?? 4)
                )
              })
              return (
                <section className={`countermeasure-phase phase-${phase.id}`} key={phase.id}>
                  <div className="countermeasure-phase-header">
                    <div className="countermeasure-phase-copy">
                      <span className="countermeasure-phase-label">Response guide</span>
                      <h4>{phase.title}</h4>
                      <p>{phase.description}</p>
                    </div>
                  </div>

                  {controls.length > 0 ? (
                    <div className="countermeasure-grid">
                      {orderedControls.map((control) => (
                        <article
                          className={`countermeasure-item priority-${control.priority.toLowerCase()}`}
                          key={`${control.control}-${control.stage}`}
                        >
                          <div className="countermeasure-item-meta">
                            <span className="countermeasure-stage">{control.stage}</span>
                            {control.stage === countermeasures.affected_stage && (
                              <span className="countermeasure-target-match">Target stage</span>
                            )}
                            <span className={`countermeasure-priority priority-${control.priority.toLowerCase()}`}>
                              {control.priority} priority
                            </span>
                          </div>
                          <h5>{control.control}</h5>
                          <span className="countermeasure-action-label">Recommended action</span>
                          <p className="countermeasure-action">{control.action}</p>
                          <details className="countermeasure-rationale">
                            <summary>Why this helps</summary>
                            <p>{control.rationale}</p>
                          </details>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <p className="countermeasure-empty">No controls are listed for this phase.</p>
                  )}
                </section>
              )
            })}
          </div>
        </section>
      )}

      {history.length > 0 && (
        <details className="overview-glossary">
          <summary>Show technical simulation details</summary>
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
        </details>
      )}
    </div>
  )
}
