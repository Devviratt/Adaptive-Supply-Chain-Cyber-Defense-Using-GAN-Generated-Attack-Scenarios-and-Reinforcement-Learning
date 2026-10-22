import { useState, useEffect } from 'react'
import { getDefenseModels, predictDefenseAction } from '../api/client'
import type { ModelInfo, PredictResponse } from '../api/client'

export default function RLDefense() {
  const [models, setModels] = useState<ModelInfo[]>([])
  const [selectedAlgo, setSelectedAlgo] = useState<'dqn' | 'ppo' | 'rule_based'>('dqn')
  const [prediction, setPrediction] = useState<PredictResponse | null>(null)
  const [predictLoading, setPredictLoading] = useState(false)

  // Preset state vectors for interactive decision making
  const PRESETS: Record<string, { label: string; obs: number[]; desc: string }> = {
    clean: {
      label: 'Normal Production Operation',
      obs: [1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.1],
      desc: 'All supply chain stages healthy (100%), no threat risk.',
    },
    critical_build: {
      label: 'Critically Compromised CI/CD Build Agent',
      obs: [1.0, 0.0, 0.4, 0.85, 1.0, 0.0, 1.0, 0.0, 0.8, 0.33, 0.7, 0.3],
      desc: 'Build stage integrity severely damaged with 85% compromise risk.',
    },
    ddos_deployment: {
      label: 'Volumetric DDoS Attack on Production',
      obs: [1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.2, 0.95, 1.0, 1.0, 0.2, 0.4],
      desc: 'Deployment cluster overwhelmed by massive traffic volume.',
    },
    lateral_propagation: {
      label: 'Early Lateral Spread Threat',
      obs: [0.8, 0.45, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.6, 0.0, 0.85, 0.15],
      desc: 'Supplier stage has moderate compromise with 85% lateral propagation risk.',
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
        <h2>Reinforcement Learning Defense Agents</h2>
        <p>
          Deep Q-Network (DQN) and Proximal Policy Optimization (PPO) autonomous cyber-defense policies
          trained in the supply-chain digital twin.
        </p>
      </div>

      {/* Architecture & Hyperparameters Comparison */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 'var(--space-lg)', marginBottom: 'var(--space-xl)' }}>
        {/* DQN Card */}
        <div className="card" style={{ borderTop: '4px solid var(--accent-primary)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-sm)' }}>
            <h3>Deep Q-Network (DQN)</h3>
            <span className="badge" style={{ backgroundColor: 'rgba(59, 130, 246, 0.2)', color: 'var(--accent-primary)' }}>Primary Policy</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: 'var(--space-md)' }}>
            Value-based Q-learning architecture with prioritized experience replay and target network stabilization.
          </p>
          <div style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Network Architecture:</span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>MLP [256, 256]</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Learning Rate:</span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>1.0e-4</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Replay Buffer Size:</span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>100,000 steps</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Discount Factor (γ):</span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>0.99</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Target Update Interval:</span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>1,000 steps</span>
            </div>
          </div>
        </div>

        {/* PPO Card */}
        <div className="card" style={{ borderTop: '4px solid #8b5cf6' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-sm)' }}>
            <h3>Proximal Policy Opt. (PPO)</h3>
            <span className="badge" style={{ backgroundColor: 'rgba(139, 92, 246, 0.2)', color: '#8b5cf6' }}>Comparison Policy</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: 'var(--space-md)' }}>
            On-policy actor-critic algorithm utilizing clipped surrogate objective functions for policy gradient stability.
          </p>
          <div style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Actor / Critic Arch:</span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>π:[256, 256], V:[256, 256]</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Learning Rate:</span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>3.0e-4</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Clip Range (ε):</span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>0.20</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Rollout Steps (n_steps):</span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>2,048</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Entropy Coefficient:</span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>0.01</span>
            </div>
          </div>
        </div>
      </div>

      {/* Interactive Policy Decision Simulator */}
      <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
        <h3 style={{ marginBottom: 'var(--space-sm)' }}>🎮 Interactive Defense Decision Simulator</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: 'var(--space-md)' }}>
          Select an incident scenario state and query the defense agent to observe its autonomous tactical decision.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--space-md)', marginBottom: 'var(--space-md)' }}>
          <div>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Preset Supply-Chain Incident</label>
            <select
              value={currentPreset}
              onChange={(e) => setCurrentPreset(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', background: 'var(--bg-input)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: 'var(--radius-sm)' }}
            >
              {Object.entries(PRESETS).map(([key, item]) => (
                <option key={key} value={key}>{item.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Evaluating Defense Policy</label>
            <select
              value={selectedAlgo}
              onChange={(e) => setSelectedAlgo(e.target.value as any)}
              style={{ width: '100%', padding: '0.5rem', background: 'var(--bg-input)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: 'var(--radius-sm)' }}
            >
              <option value="dqn">Deep Q-Network (DQN)</option>
              <option value="ppo">Proximal Policy Optimization (PPO)</option>
              <option value="rule_based">Rule-Based Heuristic Baseline</option>
            </select>
          </div>
        </div>

        <div style={{ padding: 'var(--space-md)', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', marginBottom: 'var(--space-md)' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Scenario Description:</div>
          <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
            {PRESETS[currentPreset].desc}
          </div>
        </div>

        <button
          className="btn btn-primary"
          onClick={handlePredict}
          disabled={predictLoading}
        >
          {predictLoading ? 'Evaluating Q-Values...' : '🧠 Predict Autonomous Defense Action'}
        </button>

        {prediction && (
          <div style={{ marginTop: 'var(--space-md)', padding: 'var(--space-md)', background: 'rgba(59, 130, 246, 0.1)', border: '1px solid var(--border-accent)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: 'var(--space-lg)' }}>
            <div style={{ fontSize: '2.5rem' }}>
              {prediction.action_name === 'Monitor' && '👁️'}
              {prediction.action_name === 'Isolate' && '🔒'}
              {prediction.action_name === 'Block' && '⛔'}
              {prediction.action_name === 'Rebuild' && '🔄'}
              {prediction.action_name === 'Recover' && '💚'}
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--accent-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>
                Selected Defensive Response ({prediction.model_type.toUpperCase()})
              </div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-heading)' }}>
                Action {prediction.action}: {prediction.action_name}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Model Checkpoint Artifacts */}
      <h3 style={{ marginBottom: 'var(--space-md)' }}>💾 Saved Model Weights & Checkpoints</h3>
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {models.length === 0 ? (
          <div style={{ padding: 'var(--space-lg)', textAlign: 'center', color: 'var(--text-muted)' }}>
            No models found in artifacts/models/. Run training scripts to generate model weights.
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)' }}>
                <th style={{ padding: '0.75rem 1rem' }}>Model File</th>
                <th style={{ padding: '0.75rem 1rem' }}>Algorithm</th>
                <th style={{ padding: '0.75rem 1rem' }}>File Size</th>
                <th style={{ padding: '0.75rem 1rem' }}>Last Modified</th>
              </tr>
            </thead>
            <tbody>
              {models.map((m) => (
                <tr key={m.path} style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '0.75rem 1rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--accent-primary)' }}>{m.name}</td>
                  <td style={{ padding: '0.75rem 1rem' }}>
                    <span className="badge" style={{ backgroundColor: 'rgba(59, 130, 246, 0.15)', color: 'var(--accent-primary)' }}>
                      {m.algorithm}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem 1rem' }}>{(m.size_bytes / 1024).toFixed(1)} KB</td>
                  <td style={{ padding: '0.75rem 1rem', color: 'var(--text-muted)' }}>{new Date(m.modified_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
