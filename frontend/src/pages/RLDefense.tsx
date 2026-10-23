import { useState, useEffect } from 'react'
import { getDefenseModels, predictDefenseAction } from '../api/client'
import type { ModelInfo, PredictResponse } from '../api/client'

export default function RLDefense() {
  const [models, setModels] = useState<ModelInfo[]>([])
  const [selectedAlgo, setSelectedAlgo] = useState<'rule_based' | 'dqn' | 'ppo'>('rule_based')
  const [prediction, setPrediction] = useState<PredictResponse | null>(null)
  const [predictLoading, setPredictLoading] = useState(false)

  // Preset state vectors for interactive decision making
  const PRESETS: Record<string, { label: string; obs: number[]; desc: string }> = {
    clean: {
      label: 'Normal Production Operation',
      obs: [1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.1],
      desc: 'All supply chain stages healthy (100%), 0% threat risk.',
    },
    critical_build: {
      label: 'Critically Compromised CI/CD Build Agent',
      obs: [1.0, 0.0, 0.35, 0.85, 1.0, 0.0, 1.0, 0.0, 0.8, 0.33, 0.7, 0.3],
      desc: 'Build stage integrity severely compromised with 85% risk.',
    },
    ddos_deployment: {
      label: 'Volumetric DDoS Attack on Production',
      obs: [1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.2, 0.95, 1.0, 1.0, 0.2, 0.4],
      desc: 'Deployment cluster overwhelmed by attack traffic.',
    },
    lateral_propagation: {
      label: 'Early Lateral Spread Threat',
      obs: [0.75, 0.5, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.6, 0.0, 0.85, 0.15],
      desc: 'Supplier stage has moderate compromise with lateral risk.',
    },
  }

  const [currentPreset, setCurrentPreset] = useState('critical_build')

  useEffect(() => {
    fetchModels()
  }, [])

  async function fetchModels() {
    const res = await getDefenseModels()
    if (res.data) {
      setModels(res.data)
    }
  }

  async function handlePredict() {
    setPredictLoading(true)
    const obs = PRESETS[currentPreset].obs
    const res = await predictDefenseAction(obs, selectedAlgo)
    if (res.data) {
      setPrediction(res.data)
    }
    setPredictLoading(false)
  }

  return (
    <div>
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '4px' }}>
          <span className="badge badge-healthy"><span className="status-dot healthy"></span> Baseline Verified</span>
          <span className="badge badge-warning"><span className="status-dot warning"></span> RL Convergence In Progress</span>
        </div>
        <h2>Adaptive Cyber Defense Policies</h2>
        <p>
          Comparative defense policy suite featuring industrial SOC rule-based heuristics alongside
          Deep Q-Network (DQN) and Proximal Policy Optimization (PPO) reinforcement learning agents.
        </p>
      </div>

      {/* Honest Research Progress Notice */}
      <div className="alert alert-info">
        <div>
          <strong>Academic Status for Review Checkpoint:</strong> The <strong>Rule-Based Baseline (Condition A)</strong> is 100% verified and evaluated. The <strong>DQN and PPO agent architectures</strong> are fully implemented with verified gym integration and save/load pipelines; multi-seed training convergence and reward shaping under non-stationary attacks are actively in progress for Review 2 (60%).
        </div>
      </div>

      {/* Policy Comparison Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 'var(--space-lg)', marginBottom: 'var(--space-xl)' }}>
        {/* Rule-Based Policy Card */}
        <div className="card" style={{ borderTop: '4px solid var(--status-healthy)' }}>
          <div className="card-header">
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Rule-Based Heuristic (SOC Baseline)</h3>
            <span className="badge badge-healthy">100% Verified</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: 'var(--space-md)' }}>
            Deterministic decision tree modeling standard SOC playbook procedures. Evaluated as benchmark Experiment A.
          </p>
          <div style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Mitigation Rate:</span>
              <strong style={{ color: 'var(--status-healthy)' }}>60.0% (Single Seed) / 30.0% (10 Ep)</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Service Availability:</span>
              <strong>99.5% - 99.9% Uptime</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Primary Action:</span>
              <span>Monitor (91%) · Isolate (3.3%) · Block (4.8%)</span>
            </div>
          </div>
        </div>

        {/* DQN Policy Card */}
        <div className="card" style={{ borderTop: '4px solid var(--accent-primary)' }}>
          <div className="card-header">
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Deep Q-Network (DQN Defense)</h3>
            <span className="badge badge-warning">Tuning In-Progress</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: 'var(--space-md)' }}>
            Value-based Q-learning agent with experience replay, epsilon annealing, and target network stabilization.
          </p>
          <div style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Architecture:</span>
              <code>12 Inputs → [64, 64] MLP → 5 Actions</code>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Replay Buffer:</span>
              <span>10,000 transitions · LR = 1e-4</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Current Status:</span>
              <span style={{ color: 'var(--status-warning)', fontWeight: 600 }}>Model trained; convergence tuning</span>
            </div>
          </div>
        </div>

        {/* PPO Policy Card */}
        <div className="card" style={{ borderTop: '4px solid #8b5cf6' }}>
          <div className="card-header">
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>PPO Comparative Baseline</h3>
            <span className="badge badge-neutral">Experimental</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: 'var(--space-md)' }}>
            On-policy Actor-Critic architecture providing an alternate policy-gradient baseline for comparison against DQN.
          </p>
          <div style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Policy Type:</span>
              <span>Actor-Critic (MlpPolicy)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Clipping Parameter:</span>
              <span>ε = 0.2 · GAE λ = 0.95</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Current Status:</span>
              <span style={{ color: 'var(--text-muted)' }}>SB3 wrapper verified in pytest</span>
            </div>
          </div>
        </div>
      </div>

      {/* Interactive Policy Decision Tester */}
      <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
        <div className="card-header">
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Interactive Policy Decision Matrix</h3>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Test how different policies respond to specific supply-chain threat conditions
            </span>
          </div>
          <span className="badge badge-info">Live API: /api/defense/predict</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--space-md)', marginBottom: 'var(--space-md)' }}>
          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Threat Scenario Preset</label>
            <select
              className="form-select"
              value={currentPreset}
              onChange={(e) => setCurrentPreset(e.target.value)}
              style={{ marginTop: '4px' }}
            >
              {Object.entries(PRESETS).map(([k, v]) => (
                <option key={k} value={k}>{v.label}</option>
              ))}
            </select>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              {PRESETS[currentPreset].desc}
            </p>
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Defense Policy Model</label>
            <select
              className="form-select"
              value={selectedAlgo}
              onChange={(e) => setSelectedAlgo(e.target.value as 'rule_based' | 'dqn' | 'ppo')}
              style={{ marginTop: '4px' }}
            >
              <option value="rule_based">Rule-Based Heuristic (Verified)</option>
              <option value="dqn">Deep Q-Network (DQN)</option>
              <option value="ppo">PPO Baseline</option>
            </select>
          </div>
        </div>

        <button
          className="btn btn-primary"
          onClick={handlePredict}
          disabled={predictLoading}
        >
          {predictLoading ? 'Evaluating Policy...' : '⚡ Predict Optimal Defense Action'}
        </button>

        {prediction && (
          <div style={{ marginTop: 'var(--space-md)', padding: 'var(--space-md)', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Selected Action:</span>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-primary)', marginTop: '2px' }}>
                  Action #{prediction.action}: {prediction.action_name}
                </div>
              </div>
              <span className="badge badge-neutral">Model: {prediction.model_type}</span>
            </div>
          </div>
        )}
      </div>

      {/* Trained Model Artifacts Table */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Saved Model Checkpoints & Artifacts</span>
          <span className="badge badge-neutral">artifacts/models/</span>
        </div>
        {models.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 'var(--space-md)', color: 'var(--text-muted)' }}>
            No trained weights stored yet or backend offline. Checkpoint: artifacts/models/dqn/dqn_real_only_final.zip
          </div>
        ) : (
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Model File</th>
                  <th>Algorithm</th>
                  <th style={{ textAlign: 'right' }}>File Size</th>
                  <th>Last Modified</th>
                </tr>
              </thead>
              <tbody>
                {models.map((m) => (
                  <tr key={m.path}>
                    <td><code>{m.name}</code></td>
                    <td><span className="badge badge-info">{m.algorithm}</span></td>
                    <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{(m.size_bytes / 1024).toFixed(1)} KB</td>
                    <td style={{ color: 'var(--text-muted)' }}>{m.modified_at.slice(0, 19).replace('T', ' ')}</td>
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
