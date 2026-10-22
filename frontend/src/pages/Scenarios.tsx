import { useState, useEffect } from 'react'
import { getScenarios, mapFlowRecord } from '../api/client'
import type { ScenarioItem } from '../api/client'

export default function Scenarios() {
  const [scenarios, setScenarios] = useState<ScenarioItem[]>([])
  const [loading, setLoading] = useState(true)
  const [categoryFilter, setCategoryFilter] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')
  const [totalCount, setTotalCount] = useState(0)

  // Interactive Flow Mapper State
  const [testPackets, setTestPackets] = useState(1500)
  const [testDuration, setTestDuration] = useState(120000)
  const [testSyn, setTestSyn] = useState(25)
  const [testLabel, setTestLabel] = useState('DDoS')
  const [mappedResult, setMappedResult] = useState<ScenarioItem | null>(null)
  const [mappingLoading, setMappingLoading] = useState(false)

  useEffect(() => {
    fetchScenarios()
  }, [categoryFilter, sourceFilter])

  async function fetchScenarios() {
    setLoading(true)
    const res = await getScenarios({
      category: categoryFilter || undefined,
      source: sourceFilter || undefined,
      limit: 50,
    })
    if (res.data) {
      setScenarios(res.data.scenarios)
      setTotalCount(res.data.total)
    }
    setLoading(false)
  }

  async function handleMapRecord() {
    setMappingLoading(true)
    const res = await mapFlowRecord(
      {
        'Total Fwd Packets': testPackets,
        'Flow Duration': testDuration,
        'SYN Flag Count': testSyn,
      },
      testLabel
    )
    if (res.data) {
      setMappedResult(res.data)
    }
    setMappingLoading(false)
  }

  function getSeverityBadge(sev: string) {
    const s = sev.toLowerCase()
    if (s === 'critical') return <span className="badge" style={{ backgroundColor: 'rgba(239, 68, 68, 0.2)', color: '#ef4444' }}>Critical</span>
    if (s === 'high') return <span className="badge" style={{ backgroundColor: 'rgba(249, 115, 22, 0.2)', color: '#f97316' }}>High</span>
    if (s === 'medium') return <span className="badge" style={{ backgroundColor: 'rgba(245, 158, 11, 0.2)', color: '#f59e0b' }}>Medium</span>
    return <span className="badge" style={{ backgroundColor: 'rgba(16, 185, 129, 0.2)', color: '#10b981' }}>Low</span>
  }

  return (
    <div>
      <div className="page-header">
        <h2>Attack Scenario Mapper</h2>
        <p>
          Domain-mapped software supply-chain cyber threat vectors derived from CIC-IDS2017
          telemetry and CTGAN generative models.
        </p>
      </div>

      {/* Interactive Mapper Card */}
      <div className="card" style={{ marginBottom: 'var(--space-xl)', borderLeft: '4px solid var(--accent-primary)' }}>
        <h3 style={{ marginBottom: 'var(--space-sm)' }}>⚡ Live Dynamic Scenario Mapper</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: 'var(--space-md)' }}>
          Test the logarithmic volume and flag modulation algorithm: convert continuous network traffic into supply-chain risk parameters.
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 'var(--space-md)', marginBottom: 'var(--space-md)' }}>
          <div>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Attack Category</label>
            <select
              className="form-input"
              value={testLabel}
              onChange={(e) => setTestLabel(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', background: 'var(--bg-input)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: 'var(--radius-sm)' }}
            >
              <option value="DDoS">DDoS</option>
              <option value="DoS">DoS</option>
              <option value="PortScan">PortScan</option>
              <option value="Botnet">Botnet</option>
              <option value="Brute Force">Brute Force</option>
              <option value="Web Attack">Web Attack</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Total Packets</label>
            <input
              type="number"
              value={testPackets}
              onChange={(e) => setTestPackets(Number(e.target.value))}
              style={{ width: '100%', padding: '0.5rem', background: 'var(--bg-input)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: 'var(--radius-sm)' }}
            />
          </div>
          <div>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Duration (µs)</label>
            <input
              type="number"
              value={testDuration}
              onChange={(e) => setTestDuration(Number(e.target.value))}
              style={{ width: '100%', padding: '0.5rem', background: 'var(--bg-input)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: 'var(--radius-sm)' }}
            />
          </div>
          <div>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>SYN Flag Count</label>
            <input
              type="number"
              value={testSyn}
              onChange={(e) => setTestSyn(Number(e.target.value))}
              style={{ width: '100%', padding: '0.5rem', background: 'var(--bg-input)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: 'var(--radius-sm)' }}
            />
          </div>
        </div>
        <button
          className="btn btn-primary"
          onClick={handleMapRecord}
          disabled={mappingLoading}
        >
          {mappingLoading ? 'Computing Mapping...' : '⚡ Generate Attack Scenario'}
        </button>

        {mappedResult && (
          <div style={{ marginTop: 'var(--space-md)', padding: 'var(--space-md)', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 'var(--space-md)' }}>
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Target Stage</div>
              <div style={{ fontWeight: 600, color: 'var(--accent-primary)', textTransform: 'uppercase' }}>{mappedResult.affected_stage}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Severity</div>
              <div>{getSeverityBadge(mappedResult.severity)}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Propagation Risk</div>
              <div style={{ fontWeight: 600 }}>{(mappedResult.propagation_risk * 100).toFixed(1)}%</div>
            </div>
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Availability Impact</div>
              <div style={{ fontWeight: 600 }}>{(mappedResult.availability_impact * 100).toFixed(1)}%</div>
            </div>
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Duration Steps</div>
              <div style={{ fontWeight: 600 }}>{mappedResult.duration_steps} steps</div>
            </div>
          </div>
        )}
      </div>

      {/* Filter Toolbar */}
      <div style={{ display: 'flex', gap: 'var(--space-md)', marginBottom: 'var(--space-lg)', flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Category:</span>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            style={{ padding: '0.4rem 0.8rem', background: 'var(--bg-card)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: 'var(--radius-sm)' }}
          >
            <option value="">All Categories</option>
            <option value="ddos">DDoS</option>
            <option value="dos">DoS</option>
            <option value="portscan">PortScan</option>
            <option value="botnet">Botnet</option>
            <option value="brute_force">Brute Force</option>
            <option value="web_attack">Web Attack</option>
          </select>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Source:</span>
          <select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            style={{ padding: '0.4rem 0.8rem', background: 'var(--bg-card)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: 'var(--radius-sm)' }}
          >
            <option value="">All Sources</option>
            <option value="real">Real (CIC-IDS2017)</option>
            <option value="synthetic">Synthetic (CTGAN)</option>
          </select>
        </div>

        <div style={{ marginLeft: 'auto', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          Showing {scenarios.length} of {totalCount} mapped scenarios
        </div>
      </div>

      {/* Scenarios Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: 'var(--space-xl)', textAlign: 'center', color: 'var(--text-muted)' }}>
            Loading attack scenarios...
          </div>
        ) : scenarios.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🛡</div>
            <h3>No scenarios found</h3>
            <p>Run scenario mapping via CLI (`python scripts/run_scenario_mapping.py`) or use the mapper above.</p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', background: 'var(--bg-secondary)' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>ID</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Category</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Target Stage</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Severity</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Propagation</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Avail. Impact</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Duration</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Source</th>
                </tr>
              </thead>
              <tbody>
                {scenarios.map((scen) => (
                  <tr key={scen.scenario_id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '0.75rem 1rem', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--accent-secondary)' }}>{scen.scenario_id}</td>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 500 }}>{scen.attack_category}</td>
                    <td style={{ padding: '0.75rem 1rem', textTransform: 'capitalize' }}>{scen.affected_stage}</td>
                    <td style={{ padding: '0.75rem 1rem' }}>{getSeverityBadge(scen.severity)}</td>
                    <td style={{ padding: '0.75rem 1rem' }}>{(scen.propagation_risk * 100).toFixed(0)}%</td>
                    <td style={{ padding: '0.75rem 1rem' }}>{(scen.availability_impact * 100).toFixed(0)}%</td>
                    <td style={{ padding: '0.75rem 1rem' }}>{scen.duration_steps} steps</td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <span className="badge" style={{ backgroundColor: scen.source === 'real' ? 'rgba(59, 130, 246, 0.15)' : 'rgba(168, 85, 247, 0.15)', color: scen.source === 'real' ? '#60a5fa' : '#c084fc' }}>
                        {scen.source}
                      </span>
                    </td>
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
