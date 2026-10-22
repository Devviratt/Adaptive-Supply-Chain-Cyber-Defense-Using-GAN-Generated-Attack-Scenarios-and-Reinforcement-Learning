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
        <h2>System Configuration & Environment Settings</h2>
        <p>
          Configure runtime environment variables, simulation dynamics thresholds,
          and model checkpoint storage paths.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 'var(--space-lg)' }}>
        {/* Runtime Settings Card */}
        <div className="card">
          <h3 style={{ marginBottom: 'var(--space-md)' }}>⚙️ Runtime Environment Parameters</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Accelerated Development Mode</label>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', marginTop: '0.25rem' }}>
                <input
                  type="checkbox"
                  id="devMode"
                  checked={devMode}
                  onChange={(e) => setDevMode(e.target.checked)}
                  style={{ width: '1.2rem', height: '1.2rem' }}
                />
                <label htmlFor="devMode" style={{ fontSize: '0.875rem', cursor: 'pointer' }}>
                  Enable Dev Mode (shorter buffer, 10k timesteps for rapid testing)
                </label>
              </div>
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Global Random Seed</label>
              <input
                type="number"
                value={randomSeed}
                onChange={(e) => setRandomSeed(Number(e.target.value))}
                style={{ width: '100%', marginTop: '0.25rem', padding: '0.5rem', background: 'var(--bg-input)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: 'var(--radius-sm)' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Logging Verbosity</label>
              <select
                value={logLevel}
                onChange={(e) => setLogLevel(e.target.value)}
                style={{ width: '100%', marginTop: '0.25rem', padding: '0.5rem', background: 'var(--bg-input)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', borderRadius: 'var(--radius-sm)' }}
              >
                <option value="DEBUG">DEBUG (Detailed telemetry)</option>
                <option value="INFO">INFO (Standard production)</option>
                <option value="WARNING">WARNING (Only warnings and errors)</option>
              </select>
            </div>

            <button className="btn btn-primary" onClick={handleSave} style={{ alignSelf: 'flex-start', marginTop: 'var(--space-sm)' }}>
              Save Settings
            </button>
            {savedMsg && (
              <span style={{ fontSize: '0.8rem', color: 'var(--status-healthy)' }}>✅ Settings updated successfully</span>
            )}
          </div>
        </div>

        {/* Directory Paths Card */}
        <div className="card">
          <h3 style={{ marginBottom: 'var(--space-md)' }}>📁 System Storage Paths</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)', fontSize: '0.85rem' }}>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Raw Datasets:</div>
              <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>data/raw/</div>
            </div>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Processed Clean Partitions:</div>
              <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>data/processed/</div>
            </div>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>CTGAN Generated Synthetic:</div>
              <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>data/generated/</div>
            </div>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>DQN & PPO Model Weights:</div>
              <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-primary)' }}>artifacts/models/</div>
            </div>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Benchmark Reports:</div>
              <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-secondary)' }}>artifacts/reports/</div>
            </div>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Database File:</div>
              <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--status-healthy)' }}>asccd.db (SQLite)</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
