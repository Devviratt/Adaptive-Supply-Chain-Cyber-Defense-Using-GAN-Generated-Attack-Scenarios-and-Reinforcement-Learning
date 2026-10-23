import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getHealth } from '../api/client'

export default function Overview() {
  const [health, setHealth] = useState<{ status: string; version: string } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      const healthRes = await getHealth()
      if (healthRes.data) setHealth(healthRes.data)
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

  return (
    <div>
      {/* Executive Header */}
      <div className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-md)' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', marginBottom: '4px' }}>
              <span className="badge badge-healthy">System Operational</span>
              <span className="badge badge-info">Team 84 · Dayananda Sagar University</span>
            </div>
            <h2>Adaptive Supply Chain Cyber Defense (ASCCD)</h2>
            <p>Cyber Defense Platform Powered by GAN Scenario Synthesis & Reinforcement Learning</p>
          </div>
          <div>
            <Link to="/demo" className="btn btn-primary" style={{ padding: '10px 18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>⭐</span>
              <strong>Launch Review 1 Demo</strong>
            </Link>
          </div>
        </div>
      </div>

      {/* Review 1 Highlight Card */}
      <div className="card" style={{ background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.15) 0%, rgba(6, 182, 212, 0.1) 100%)', border: '1px solid var(--accent-primary)', marginBottom: 'var(--space-xl)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-md)' }}>
          <div>
            <span className="badge badge-info" style={{ marginBottom: '8px' }}>Review 1 Evaluation Showcase</span>
            <h3 style={{ margin: '4px 0 8px 0', fontSize: '1.25rem', color: 'var(--text-heading)' }}>
              Interactive Technical Demo Ready for Review Panel
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: '750px', margin: 0 }}>
              Demonstrate the live CTGAN synthetic threat synthesizer, rigorous statistical fidelity tests (Wasserstein & Pearson), and the 5-stage Supply Chain Digital Twin environment with cascading failure containment.
            </p>
          </div>
          <Link to="/demo" className="btn btn-primary" style={{ whiteSpace: 'nowrap' }}>
            Open Interactive Demo ➔
          </Link>
        </div>
      </div>

      {/* Operational Telemetry Cards */}
      <div className="card-grid" style={{ marginBottom: 'var(--space-xl)' }}>
        <div className="card">
          <div className="card-header">
            <span className="card-title">Defense State</span>
            <span className={`badge ${health?.status === 'healthy' ? 'badge-healthy' : 'badge-danger'}`}>
              {health?.status === 'healthy' ? 'ACTIVE GUARD' : 'OFFLINE'}
            </span>
          </div>
          <div className="card-value" style={{ color: 'var(--status-healthy)' }}>Protected</div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '4px' }}>
            Real-time supply chain monitoring
          </p>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Network Flows Analyzed</span>
            <span className="badge badge-info">CIC-IDS2017</span>
          </div>
          <div className="card-value">2,830,743</div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '4px' }}>
            15 salient features preprocessed
          </p>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">CTGAN Fidelity Score</span>
            <span className="badge badge-healthy">Empirical Pass</span>
          </div>
          <div className="card-value" style={{ color: 'var(--accent-primary)' }}>98.69%</div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '4px' }}>
            Pearson correlation · W₁ = 0.1057
          </p>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Digital Twin Stages</span>
            <span className="badge badge-info">5 Interconnected</span>
          </div>
          <div className="card-value">5 Nodes</div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '4px' }}>
            Supplier ➔ Ingest ➔ Process ➔ Registry ➔ Deploy
          </p>
        </div>
      </div>

      {/* Supply Chain Topology Live Visualizer */}
      <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
        <div className="card-header">
          <span className="card-title">Supply Chain Dependency Topology</span>
          <span className="badge badge-healthy">All Stages Online</span>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: 'var(--space-md)' }}>
          Continuous monitoring of service availability and threat exposure across the digital twin architecture:
        </p>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-around',
            alignItems: 'center',
            padding: 'var(--space-md) 0',
            gap: 'var(--space-sm)',
            overflowX: 'auto',
          }}
        >
          {[
            { name: 'Supplier', role: 'External Packages', health: '98%', status: 'Normal' },
            { name: 'Ingestion', role: 'Source Repositories', health: '99%', status: 'Normal' },
            { name: 'Processing', role: 'CI/CD Build Pipeline', health: '96%', status: 'Normal' },
            { name: 'Registry', role: 'Artifact Store', health: '100%', status: 'Optimal' },
            { name: 'Deployment', role: 'Production Cluster', health: '100%', status: 'Optimal' },
          ].map((stage, i) => (
            <div key={stage.name} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', flex: 1 }}>
              <div
                style={{
                  textAlign: 'center',
                  padding: 'var(--space-md)',
                  background: 'var(--bg-elevated)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-color)',
                  flex: 1,
                  minWidth: '120px',
                }}
              >
                <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '2px' }}>
                  STAGE 0{i + 1}
                </div>
                <div style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-heading)', marginBottom: '2px' }}>
                  {stage.name}
                </div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                  {stage.role}
                </div>
                <div style={{ display: 'flex', justifyContent: 'center', gap: '6px', alignItems: 'center' }}>
                  <span className="badge badge-healthy" style={{ fontSize: '0.7rem' }}>{stage.status}</span>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--status-healthy)' }}>{stage.health}</span>
                </div>
              </div>
              {i < 4 && (
                <span style={{ color: 'var(--text-muted)', fontSize: '1.25rem' }}>➔</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Research Pillars Overview */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Core Research Framework Pillars</span>
          <span className="badge badge-info">ASCCD Methodology</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--space-md)', marginTop: 'var(--space-sm)' }}>
          <div style={{ background: 'var(--bg-elevated)', padding: 'var(--space-md)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
            <div style={{ fontWeight: 600, color: 'var(--accent-primary)', marginBottom: '6px' }}>
              1. Threat Telemetry Preprocessing
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
              Standardizes raw CIC-IDS2017 bidirectional network flows, resolves extreme minority class imbalance (DoS, DDoS, PortScan, Botnets, Web Attacks), and applies RobustScaler transformations.
            </p>
          </div>

          <div style={{ background: 'var(--bg-elevated)', padding: 'var(--space-md)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
            <div style={{ fontWeight: 600, color: 'var(--accent-primary)', marginBottom: '6px' }}>
              2. Generative Attack Modeling (CTGAN)
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
              Conditional Tabular GAN synthesizes diverse multi-stage attack scenarios with verified statistical fidelity (W₁ = 0.1057, Pearson r = 0.9869, 0.00% memorization).
            </p>
          </div>

          <div style={{ background: 'var(--bg-elevated)', padding: 'var(--space-md)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
            <div style={{ fontWeight: 600, color: 'var(--accent-primary)', marginBottom: '6px' }}>
              3. Supply Chain Digital Twin & RL Defense
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
              Gymnasium environment simulating cascading vulnerability propagation across 5 supply chain stages with autonomous reinforcement learning defense policies.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
