import { useState, useEffect } from 'react'
import { getHealth, getProjectStatus, type ProjectStatusResponse } from '../api/client'

export default function Overview() {
  const [health, setHealth] = useState<{ status: string; version: string } | null>(null)
  const [project, setProject] = useState<ProjectStatusResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      const [healthRes, projectRes] = await Promise.all([
        getHealth(),
        getProjectStatus(),
      ])

      if (healthRes.error) setError(healthRes.error)
      if (healthRes.data) setHealth(healthRes.data)
      if (projectRes.data) setProject(projectRes.data)
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

  if (error) {
    return (
      <div>
        <div className="page-header">
          <h2>Dashboard Overview</h2>
          <p>System health and key metrics</p>
        </div>
        <div className="card">
          <div className="empty-state">
            <div className="empty-icon">⚠️</div>
            <h3>Backend Unavailable</h3>
            <p>
              Could not connect to the API server. Please ensure the backend is
              running at <code>http://localhost:8000</code>.
            </p>
            <p style={{ marginTop: '0.5rem', fontSize: '0.8rem' }}>
              Error: {error}
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <h2>Dashboard Overview</h2>
        <p>Adaptive Supply Chain Cyber Defense — System Status</p>
      </div>

      {/* Status Cards */}
      <div className="card-grid">
        <div className="card">
          <div className="card-header">
            <span className="card-title">System Health</span>
            <span
              className={`badge ${
                health?.status === 'healthy' ? 'badge-healthy' : 'badge-danger'
              }`}
            >
              {health?.status || 'unknown'}
            </span>
          </div>
          <div className="card-value">Operational</div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '4px' }}>
            v{health?.version}
          </p>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Project Phase</span>
            <span className="badge badge-info">Active</span>
          </div>
          <div className="card-value" style={{ fontSize: '1.25rem' }}>
            {project?.current_phase || 'Unknown'}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Module Progress</span>
          </div>
          <div className="card-value">
            {project?.progress.percentage ?? 0}%
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '4px' }}>
            {project?.progress.completed_modules ?? 0} /{' '}
            {project?.progress.total_modules ?? 0} modules
          </p>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Experiments</span>
          </div>
          <div className="card-value" style={{ fontSize: '1.25rem', color: 'var(--text-muted)' }}>
            No experiment data available
          </div>
        </div>
      </div>

      {/* Supply Chain Quick View */}
      <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
        <div className="card-header">
          <span className="card-title">Supply Chain Status</span>
          <span className="badge badge-muted">Simulation Not Running</span>
        </div>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-around',
            alignItems: 'center',
            padding: 'var(--space-lg) 0',
            gap: 'var(--space-md)',
          }}
        >
          {['Supplier', 'Build', 'Registry', 'Deployment'].map(
            (stage, i) => (
              <div key={stage} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
                <div
                  style={{
                    textAlign: 'center',
                    padding: 'var(--space-md) var(--space-lg)',
                    background: 'var(--bg-elevated)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-color)',
                    minWidth: '100px',
                  }}
                >
                  <div
                    style={{
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      color: 'var(--text-secondary)',
                      marginBottom: '4px',
                    }}
                  >
                    {stage}
                  </div>
                  <span className="badge badge-muted">Idle</span>
                </div>
                {i < 3 && (
                  <span style={{ color: 'var(--text-muted)', fontSize: '1.25rem' }}>→</span>
                )}
              </div>
            )
          )}
        </div>
      </div>

      {/* Module Status Table */}
      {project?.modules && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Module Status</span>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Module</th>
                <th>Description</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(project.modules).map(([key, mod]) => (
                <tr key={key}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                    {key}
                  </td>
                  <td>{mod.description}</td>
                  <td>
                    <span
                      className={`badge ${
                        mod.status === 'done'
                          ? 'badge-healthy'
                          : mod.status === 'in_progress'
                          ? 'badge-warning'
                          : 'badge-muted'
                      }`}
                    >
                      {mod.status.replace('_', ' ')}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
