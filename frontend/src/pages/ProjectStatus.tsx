import { useState, useEffect } from 'react'
import { getProjectStatus, getTeamInfo, type ProjectStatusResponse, type TeamResponse } from '../api/client'

export default function ProjectStatus() {
  const [project, setProject] = useState<ProjectStatusResponse | null>(null)
  const [team, setTeam] = useState<TeamResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      const [projectRes, teamRes] = await Promise.all([
        getProjectStatus(),
        getTeamInfo(),
      ])
      if (projectRes.data) setProject(projectRes.data)
      if (teamRes.data) setTeam(teamRes.data)
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

  const statusColor = (status: string) => {
    switch (status) {
      case 'done': return 'badge-healthy'
      case 'in_progress': return 'badge-warning'
      default: return 'badge-muted'
    }
  }

  return (
    <div>
      <div className="page-header">
        <h2>Project Status</h2>
        <p>Team 84 — Module progress and team contributions</p>
      </div>

      {/* Progress Overview */}
      {project && (
        <div className="card-grid">
          <div className="card">
            <div className="card-header">
              <span className="card-title">Overall Progress</span>
            </div>
            <div className="card-value">{project.progress.percentage}%</div>
            <div style={{ marginTop: 'var(--space-sm)' }}>
              <div
                style={{
                  height: '8px',
                  background: 'var(--bg-elevated)',
                  borderRadius: '4px',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    height: '100%',
                    width: `${project.progress.percentage}%`,
                    background: 'linear-gradient(90deg, var(--accent-primary), var(--accent-secondary))',
                    borderRadius: '4px',
                    transition: 'width 0.5s ease',
                  }}
                />
              </div>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '8px' }}>
              {project.progress.completed_modules} completed · {project.progress.in_progress_modules} in progress
            </p>
          </div>

          <div className="card">
            <div className="card-header">
              <span className="card-title">Current Phase</span>
            </div>
            <div className="card-value" style={{ fontSize: '1.125rem' }}>
              {project.current_phase}
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <span className="card-title">Version</span>
            </div>
            <div className="card-value">{project.version}</div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '4px' }}>
              {project.college}
            </p>
          </div>
        </div>
      )}

      {/* Module Status */}
      {project?.modules && (
        <div className="card" style={{ marginBottom: 'var(--space-xl)' }}>
          <div className="card-header">
            <span className="card-title">Module Completion</span>
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
              gap: 'var(--space-md)',
              marginTop: 'var(--space-md)',
            }}
          >
            {Object.entries(project.modules).map(([key, mod]) => (
              <div
                key={key}
                style={{
                  padding: 'var(--space-md)',
                  background: 'var(--bg-elevated)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-color)',
                }}
              >
                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                  {key.replace(/_/g, ' ')}
                </div>
                <span className={`badge ${statusColor(mod.status)}`}>
                  {mod.status.replace('_', ' ')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Team Members */}
      {team && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Team Members</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--space-lg)', marginTop: 'var(--space-md)' }}>
            {team.members.map((member) => (
              <div
                key={member.usn}
                style={{
                  padding: 'var(--space-lg)',
                  background: 'var(--bg-elevated)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-color)',
                }}
              >
                <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-heading)', marginBottom: '2px' }}>
                  {member.name}
                </h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginBottom: 'var(--space-sm)' }}>
                  {member.usn} · Section {member.section}
                </p>
                <div style={{ marginTop: 'var(--space-sm)' }}>
                  <div style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px' }}>
                    Responsibilities
                  </div>
                  <ul style={{ listStyle: 'none', padding: 0 }}>
                    {member.primary_responsibilities.map((r) => (
                      <li
                        key={r}
                        style={{
                          fontSize: '0.8rem',
                          color: 'var(--text-secondary)',
                          padding: '2px 0',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                        }}
                      >
                        <span style={{ color: 'var(--accent-primary)' }}>›</span> {r}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
