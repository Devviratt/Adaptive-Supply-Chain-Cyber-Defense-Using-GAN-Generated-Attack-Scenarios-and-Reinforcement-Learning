import { useState } from 'react'

export default function Settings() {
  const [devMode, setDevMode] = useState(true)
  const [logLevel, setLogLevel] = useState('INFO')
  const [randomSeed, setRandomSeed] = useState(42)
  const [savedMsg, setSavedMsg] = useState(false)

  function handleSave() {
    setSavedMsg(true)
    setTimeout(() => setSavedMsg(false), 2000)
  }

  return (
    <div>
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '4px' }}>
          <span className="badge badge-neutral">Platform Config</span>
        </div>
        <h2>System Configuration & Environment Settings</h2>
        <p>
          Configure runtime environment variables, simulation dynamics thresholds,
          and model checkpoint storage paths.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 'var(--space-lg)' }}>
        {/* Runtime Settings Card */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Runtime Environment Parameters</span>
            <span className="badge badge-info">config/settings.yaml</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Accelerated Development Mode</label>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', marginTop: '0.25rem' }}>
                <input
                  type="checkbox"
                  id="devMode"
                  checked={devMode}
                  onChange={(e) => setDevMode(e.target.checked)}
                  style={{ width: '1.1rem', height: '1.1rem' }}
                />
                <label htmlFor="devMode" style={{ fontSize: '0.85rem', cursor: 'pointer', color: 'var(--text-primary)' }}>
                  Enable Dev Mode (accelerated buffer, 10 episodes for rapid local evaluation)
                </label>
              </div>
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Global Random Seed</label>
              <input
                type="number"
                className="form-input"
                value={randomSeed}
                onChange={(e) => setRandomSeed(Number(e.target.value))}
                style={{ marginTop: '0.25rem' }}
              />
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Default: 42 (Guarantees deterministic replication)</span>
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Logging Verbosity</label>
              <select
                className="form-select"
                value={logLevel}
                onChange={(e) => setLogLevel(e.target.value)}
                style={{ marginTop: '0.25rem' }}
              >
                <option value="DEBUG">DEBUG (Detailed Telemetry)</option>
                <option value="INFO">INFO (Standard Audit)</option>
                <option value="WARNING">WARNING (Issues Only)</option>
                <option value="ERROR">ERROR (Critical Failures)</option>
              </select>
            </div>

            <div style={{ marginTop: 'var(--space-sm)' }}>
              <button className="btn btn-primary" onClick={handleSave}>
                Save Environment Preferences
              </button>
              {savedMsg && (
                <span style={{ marginLeft: 'var(--space-md)', color: 'var(--status-healthy)', fontSize: '0.85rem', fontWeight: 600 }}>
                  ✓ Preferences Saved
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Directory Paths Reference */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Storage & Artifact Directory Structure</span>
            <span className="badge badge-neutral">Local Paths</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)', fontSize: '0.82rem' }}>
            <div style={{ padding: 'var(--space-sm)', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)' }}>
              <strong>Raw Dataset:</strong> <code style={{ fontFamily: 'var(--font-mono)' }}>data/raw/CIC-IDS2017_dev_sample.csv</code>
            </div>
            <div style={{ padding: 'var(--space-sm)', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)' }}>
              <strong>Processed Splits:</strong> <code style={{ fontFamily: 'var(--font-mono)' }}>data/processed/train.csv, val.csv, test.csv</code>
            </div>
            <div style={{ padding: 'var(--space-sm)', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)' }}>
              <strong>Synthesized Attacks:</strong> <code style={{ fontFamily: 'var(--font-mono)' }}>data/generated/synthetic_attacks.csv</code>
            </div>
            <div style={{ padding: 'var(--space-sm)', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)' }}>
              <strong>Scientific Figures:</strong> <code style={{ fontFamily: 'var(--font-mono)' }}>artifacts/figures/*.png</code>
            </div>
            <div style={{ padding: 'var(--space-sm)', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)' }}>
              <strong>Model Checkpoints:</strong> <code style={{ fontFamily: 'var(--font-mono)' }}>artifacts/models/dqn/dqn_real_only_final.zip</code>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
