import { Routes, Route, NavLink } from 'react-router-dom'
import Overview from './pages/Overview'
import ProjectStatus from './pages/ProjectStatus'

const NAV_SECTIONS = [
  {
    title: 'Dashboard',
    items: [
      { path: '/', label: 'Overview', icon: '◉' },
      { path: '/scenarios', label: 'Attack Scenarios', icon: '⚡' },
      { path: '/supply-chain', label: 'Supply Chain', icon: '⛓' },
    ],
  },
  {
    title: 'ML Pipeline',
    items: [
      { path: '/gan-lab', label: 'GAN Lab', icon: '🧬' },
      { path: '/rl-defense', label: 'RL Defense', icon: '🛡' },
    ],
  },
  {
    title: 'Research',
    items: [
      { path: '/experiments', label: 'Experiments', icon: '🔬' },
      { path: '/evaluation', label: 'Evaluation', icon: '📊' },
    ],
  },
  {
    title: 'System',
    items: [
      { path: '/logs', label: 'System Logs', icon: '📋' },
      { path: '/project', label: 'Project Status', icon: '📈' },
      { path: '/settings', label: 'Settings', icon: '⚙' },
    ],
  },
]

function Placeholder({ title }: { title: string }) {
  return (
    <div>
      <div className="page-header">
        <h2>{title}</h2>
        <p>This page will be implemented in a future phase.</p>
      </div>
      <div className="card">
        <div className="empty-state">
          <div className="empty-icon">🚧</div>
          <h3>Not implemented yet</h3>
          <p>
            This feature is planned and will be built during the dashboard
            implementation phase.
          </p>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <div className="app-layout">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <div className="logo-icon">A</div>
            <div>
              <h1>ASCCD</h1>
              <span>Cyber Defense Platform</span>
            </div>
          </div>
        </div>

        <nav className="sidebar-nav">
          {NAV_SECTIONS.map((section) => (
            <div className="nav-section" key={section.title}>
              <div className="nav-section-title">{section.title}</div>
              {section.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `nav-item ${isActive ? 'active' : ''}`
                  }
                  end={item.path === '/'}
                >
                  <span className="nav-icon">{item.icon}</span>
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        <div
          style={{
            padding: 'var(--space-md)',
            borderTop: '1px solid var(--border-color)',
            fontSize: '0.7rem',
            color: 'var(--text-muted)',
            textAlign: 'center',
          }}
        >
          Team 84 · DSU · v0.1.0
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/project" element={<ProjectStatus />} />
          <Route path="/scenarios" element={<Placeholder title="Attack Scenarios" />} />
          <Route path="/supply-chain" element={<Placeholder title="Supply Chain" />} />
          <Route path="/gan-lab" element={<Placeholder title="GAN Lab" />} />
          <Route path="/rl-defense" element={<Placeholder title="RL Defense" />} />
          <Route path="/experiments" element={<Placeholder title="Experiments" />} />
          <Route path="/evaluation" element={<Placeholder title="Evaluation" />} />
          <Route path="/logs" element={<Placeholder title="System Logs" />} />
          <Route path="/settings" element={<Placeholder title="Settings" />} />
        </Routes>
      </main>
    </div>
  )
}
