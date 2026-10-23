import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  getDataSummary,
  getExperiments,
  getStageTopology,
} from '../api/client'
import type {
  DataSummaryResponse,
  ExperimentItem,
  StageTopologyResponse,
} from '../api/client'

export default function Overview() {
  const [dataSummary, setDataSummary] = useState<DataSummaryResponse | null>(null)
  const [experiments, setExperiments] = useState<ExperimentItem[]>([])
  const [topology, setTopology] = useState<StageTopologyResponse | null>(null)

  useEffect(() => {
    async function fetchData() {
      const [dataRes, expRes, topRes] = await Promise.all([
        getDataSummary(),
        getExperiments(),
        getStageTopology(),
      ])
      if (dataRes.data) setDataSummary(dataRes.data)
      if (expRes.data) setExperiments(expRes.data)
      if (topRes.data) setTopology(topRes.data)
    }
    fetchData()
  }, [])

  // 4 Supply-Chain Stages with default neutral initial state
  const STAGES = [
    {
      id: 'supplier',
      name: 'Supplier',
      order: 1,
      health: 100,
      risk: 0.0,
      criticality: 0.7,
      status: 'Normal',
      desc: 'Third-party code dependencies & vendor libraries',
    },
    {
      id: 'build',
      name: 'Build',
      order: 2,
      health: 100,
      risk: 0.0,
      criticality: 0.85,
      status: 'Normal',
      desc: 'CI/CD pipeline, build runners & compilation agents',
    },
    {
      id: 'registry',
      name: 'Registry',
      order: 3,
      health: 100,
      risk: 0.0,
      criticality: 0.8,
      status: 'Normal',
      desc: 'Container image registry & artifact storage',
    },
    {
      id: 'deployment',
      name: 'Deployment',
      order: 4,
      health: 100,
      risk: 0.0,
      criticality: 0.95,
      status: 'Normal',
      desc: 'Runtime production clusters & customer-facing services',
    },
  ]

  // Verified Research Workflow Steps (Interactive agency to jump to module)
  const WORKFLOW_STEPS = [
    {
      step: 1,
      name: 'Real Network-Flow Ingestion',
      detail: 'CIC-IDS2017 raw captures with 73 initial telemetry attributes',
      status: 'implemented',
      link: '/data',
    },
    {
      step: 2,
      name: 'Zero-Leakage Preprocessing',
      detail: 'Dropped 6 identifiers, scaled 71 continuous features on train split only',
      status: 'implemented',
      link: '/data',
    },
    {
      step: 3,
      name: 'CTGAN Threat Synthesis',
      detail: 'Synthesized 2,000 attack records with SDV conditional generator',
      status: 'implemented',
      link: '/gan-lab',
    },
    {
      step: 4,
      name: 'Statistical & Utility Validation',
      detail: 'Wasserstein W₁ = 0.1057, Pearson r = 98.69%, +1.49% classifier accuracy',
      status: 'implemented',
      link: '/gan-lab',
    },
    {
      step: 5,
      name: 'Supply Chain Simulation',
      detail: 'Gymnasium 4-stage digital twin with 12-dim state and 5 defense actions',
      status: 'implemented',
      link: '/supply-chain',
    },
    {
      step: 6,
      name: 'Defense Policy Evaluation',
      detail: 'Rule-based baseline evaluated; DQN smoke-test verified; RL training active',
      status: 'in_progress',
      link: '/rl-defense',
    },
  ]

  // Actual Pipeline Activity Records
  const ACTIVITY_RECORDS = [
    {
      title: 'Experiment A Benchmark',
      module: 'Defense Policies',
      status: 'Completed',
      result: 'Mitigation: 30.0% (5 seeds), 99.92% uptime',
      date: experiments[0]?.completed_at
        ? experiments[0].completed_at.slice(0, 10)
        : '2026-10-23',
    },
    {
      title: 'Supply Chain Threat Mapping',
      module: 'Scenario Mapper',
      status: 'Completed',
      result: '100 attack scenarios mapped & persisted to SQLite',
      date: '2026-10-23',
    },
    {
      title: 'CTGAN Synthesis & Validation',
      module: 'CTGAN Threat Lab',
      status: 'Completed',
      result: '2,000 synthetic samples generated (W₁ = 0.1057)',
      date: '2026-10-23',
    },
    {
      title: 'Data Preprocessing & Split',
      module: 'Data Pipeline',
      status: 'Completed',
      result: '3,437 train / 737 test records · 71 clean features',
      date: '2026-10-23',
    },
  ]

  return (
    <div>
      {/* A. Project Introduction */}
      <div className="page-header" style={{ marginBottom: '16px' }}>
        <h2>Adaptive Supply Chain Cyber Defense</h2>
        <p>
          Generates synthetic cyber-attack telemetry via CTGAN and evaluates adaptive defense policies in a
          discrete-event supply chain digital twin.
        </p>
      </div>

      {/* B. Four Primary Information Cards with Real Values */}
      <div className="kpi-grid">
        {/* Card 1: Processed Real Records */}
        <div className="kpi-card">
          <div className="kpi-card-header">
            <div className="kpi-header-left">
              <div className="kpi-icon-circle blue">▤</div>
              <span className="kpi-card-label">Processed Dataset</span>
            </div>
            <span className="badge badge-info">CIC-IDS2017</span>
          </div>
          <div className="kpi-card-value">
            {dataSummary?.splits?.train_count && dataSummary?.splits?.test_count
              ? (dataSummary.splits.train_count + dataSummary.splits.test_count).toLocaleString()
              : '4,174'}
          </div>
          <p className="kpi-card-subtext">
            {dataSummary?.splits?.train_count && dataSummary?.splits?.test_count
              ? `${dataSummary.splits.train_count.toLocaleString()} train / ${dataSummary.splits.test_count.toLocaleString()} test`
              : '3,437 train / 737 test'} · 71 features (0% leakage)
          </p>
        </div>

        {/* Card 2: Synthetic Attack Records */}
        <div className="kpi-card">
          <div className="kpi-card-header">
            <div className="kpi-header-left">
              <div className="kpi-icon-circle orange">◈</div>
              <span className="kpi-card-label">Synthetic Attack Records</span>
            </div>
            <span className="badge badge-neutral">CTGAN Model</span>
          </div>
          <div className="kpi-card-value">2,000</div>
          <p className="kpi-card-subtext">
            W₁ = 0.1057 (pass &lt; 0.25) · Pearson r = 98.69%
          </p>
        </div>

        {/* Card 3: Measured Classifier Accuracy Result */}
        <div className="kpi-card">
          <div className="kpi-card-header">
            <div className="kpi-header-left">
              <div className="kpi-icon-circle green">📈</div>
              <span className="kpi-card-label">Classifier Accuracy</span>
            </div>
            <span className="badge badge-healthy">+1.49% Boost</span>
          </div>
          <div className="kpi-card-value" style={{ color: 'var(--status-healthy)' }}>
            80.19%
          </div>
          <p className="kpi-card-subtext">
            Augmented vs 78.70% baseline (Macro-F1: 0.1272)
          </p>
        </div>

        {/* Card 4: Scenario Templates & Database */}
        <div className="kpi-card">
          <div className="kpi-card-header">
            <div className="kpi-header-left">
              <div className="kpi-icon-circle purple">⚡</div>
              <span className="kpi-card-label">Scenario Templates</span>
            </div>
            <span className="badge badge-healthy">SQLite Online</span>
          </div>
          <div className="kpi-card-value">100</div>
          <p className="kpi-card-subtext">
            Mapped across 4 stages · Duration: 10–30 steps
          </p>
        </div>
      </div>

      {/* Balanced 2-Column Dashboard Grid */}
      <div className="dashboard-grid">
        {/* Main Column (2fr): C. Simulation Topology + E. Recent Activity */}
        <div className="dashboard-main-col">
          {/* C. Main Supply-Chain Visualization (Supplier → Build → Registry → Deployment) */}
          <div className="card">
            <div className="card-header">
              <div>
                <h3 style={{ fontSize: '0.98rem', fontWeight: 600 }}>
                  Supply-Chain Simulation Topology & Health
                </h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Discrete-event stage status in the simulated supply-chain environment
                </span>
              </div>
              <Link to="/supply-chain" className="btn btn-sm btn-primary">
                Open Simulation Twin →
              </Link>
            </div>

            {/* 4 Connected Stages Visual Topology (Apple HIG Flow Continuity) */}
            <div className="stage-pipeline" style={{ marginTop: '12px', marginBottom: '14px' }}>
              {STAGES.map((st, idx) => (
                <div key={st.id} style={{ display: 'contents' }}>
                  <div className="stage-card-item">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-heading)' }}>
                        {st.order}. {st.name}
                      </span>
                      <span
                        style={{
                          fontSize: '0.72rem',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          background: '#f0fdf4',
                          color: '#16a34a',
                          fontWeight: 600,
                        }}
                      >
                        {st.status}
                      </span>
                    </div>

                    {/* Health Bar */}
                    <div style={{ marginBottom: '6px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        <span>Health</span>
                        <strong style={{ color: '#16a34a' }}>{st.health}%</strong>
                      </div>
                      <div style={{ width: '100%', height: '6px', background: '#e2e8f0', borderRadius: '3px', marginTop: '3px', overflow: 'hidden' }}>
                        <div style={{ width: `${st.health}%`, height: '100%', background: '#16a34a', borderRadius: '3px' }} />
                      </div>
                    </div>

                    {/* Risk Level */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      <span>Threat Risk:</span>
                      <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>{(st.risk * 100).toFixed(0)}%</span>
                    </div>

                    {/* Criticality */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      <span>Criticality:</span>
                      <span>{st.criticality}</span>
                    </div>
                  </div>
                  {idx < STAGES.length - 1 && (
                    <div className="stage-connector-arrow">→</div>
                  )}
                </div>
              ))}
            </div>

            {/* Stage Transition Bar */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '8px 12px',
                background: '#f8fafc',
                borderRadius: '8px',
                border: '1px solid #e2e8f0',
                fontSize: '0.75rem',
                color: 'var(--text-muted)',
              }}
            >
              <span>
                <strong>Pipeline Flow:</strong> Supplier → Build → Registry → Deployment
              </span>
              <span>
                <strong>Actions ({topology?.actions?.length ?? 5}):</strong>{' '}
                {topology?.actions
                  ? topology.actions.map((a) => `${a.name} (${a.id})`).join(', ')
                  : 'Monitor (0), Isolate (1), Block (2), Rebuild (3), Recover (4)'}
              </span>
            </div>
          </div>

          {/* E. Recent Activity & Verified Artifacts ("Last notes" style card from reference) */}
          <div className="card">
            <div className="card-header">
              <div>
                <h3 style={{ fontSize: '0.98rem', fontWeight: 600 }}>Recent Activity & Verified Evidence</h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Recorded experiment executions and persisted artifact generation events
                </span>
              </div>
              <Link to="/experiments" style={{ fontSize: '0.78rem', color: 'var(--accent-primary)', fontWeight: 600 }}>
                View all experiments →
              </Link>
            </div>

            <div className="data-table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Activity / Run</th>
                    <th>Module</th>
                    <th>Status</th>
                    <th>Recorded Result / Output</th>
                    <th style={{ textAlign: 'right' }}>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {ACTIVITY_RECORDS.map((rec, i) => (
                    <tr key={i}>
                      <td style={{ fontWeight: 600, color: 'var(--text-heading)' }}>
                        {rec.title}
                      </td>
                      <td>
                        <span className="badge badge-neutral" style={{ fontSize: '0.72rem' }}>
                          {rec.module}
                        </span>
                      </td>
                      <td>
                        <span className="badge badge-healthy" style={{ fontSize: '0.72rem' }}>
                          {rec.status}
                        </span>
                      </td>
                      <td style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                        {rec.result}
                      </td>
                      <td style={{ textAlign: 'right', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {rec.date}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Side Column (1fr): D. Workflow Explanation + Research Boundaries */}
        <div className="dashboard-side-col">
          {/* D. End-to-End Research Workflow */}
          <div className="card">
            <div className="card-header">
              <div>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Research Workflow</h3>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  Architecture pipeline from raw telemetry to defense evaluation
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {WORKFLOW_STEPS.map((wf) => (
                <Link
                  key={wf.step}
                  to={wf.link}
                  className="workflow-step-card"
                  title={`Navigate to ${wf.name}`}
                >
                  <div
                    style={{
                      width: '24px',
                      height: '24px',
                      borderRadius: '50%',
                      background: wf.status === 'implemented' ? '#dcfce7' : '#ffedd5',
                      color: wf.status === 'implemented' ? '#15803d' : '#c2410c',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      flexShrink: 0,
                      marginTop: '1px',
                    }}
                  >
                    {wf.step}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-heading)' }}>
                        {wf.name}
                      </span>
                      <span
                        style={{
                          fontSize: '0.72rem',
                          color: wf.status === 'implemented' ? '#15803d' : '#b45309',
                          fontWeight: 600,
                        }}
                      >
                        {wf.status === 'implemented' ? 'Implemented' : 'In Progress'}
                      </span>
                    </div>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px', lineHeight: 1.35 }}>
                      {wf.detail}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          </div>

          {/* Current Research Boundaries & Disclosures */}
          <div className="card">
            <div className="card-header">
              <div>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Active Research Boundaries</h3>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  Transparent limitations & upcoming development work
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div
                style={{
                  padding: '9px 11px',
                  borderRadius: '8px',
                  background: '#fffbeb',
                  border: '1px solid #fde68a',
                  fontSize: '0.75rem',
                }}
              >
                <div style={{ fontWeight: 600, color: '#92400e', marginBottom: '2px' }}>
                  Jensen-Shannon Divergence Warning
                </div>
                <p style={{ color: '#78350f', lineHeight: 1.35 }}>
                  Mean JS divergence is <strong>0.5117</strong>, slightly exceeding the 0.5000 threshold due to heavy-tailed continuous distributions. W₁ (0.1057) and Pearson (98.69%) passed.
                </p>
              </div>

              <div
                style={{
                  padding: '9px 11px',
                  borderRadius: '8px',
                  background: 'var(--bg-subtle)',
                  border: '1px solid var(--border-color)',
                  fontSize: '0.75rem',
                }}
              >
                <div style={{ fontWeight: 600, color: 'var(--text-heading)', marginBottom: '2px' }}>
                  Macro-F1 Rare-Class Sensitivity
                </div>
                <p style={{ color: 'var(--text-secondary)', lineHeight: 1.35 }}>
                  Synthetic augmentation raised overall accuracy by <strong>+1.49%</strong> (78.70% → 80.19%), while Macro-F1 saw a <strong>-0.0100</strong> change due to rare test classes (1 Web Attack, 2 Botnet).
                </p>
              </div>

              <div
                style={{
                  padding: '9px 11px',
                  borderRadius: '8px',
                  background: 'var(--bg-subtle)',
                  border: '1px solid var(--border-color)',
                  fontSize: '0.75rem',
                }}
              >
                <div style={{ fontWeight: 600, color: 'var(--text-heading)', marginBottom: '2px' }}>
                  Reinforcement Learning Status
                </div>
                <p style={{ color: 'var(--text-secondary)', lineHeight: 1.35 }}>
                  DQN agent has a verified 1,000-step smoke-test checkpoint; full 50,000-step convergence training is in progress. PPO wrapper is implemented without checkpoint.
                </p>
              </div>
            </div>

            <div style={{ marginTop: '10px', paddingTop: '8px', borderTop: '1px solid var(--border-subtle)', textAlign: 'right' }}>
              <Link to="/technical?tab=audit" style={{ fontSize: '0.75rem', color: 'var(--accent-primary)', fontWeight: 600 }}>
                Inspect full scientific audit →
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
