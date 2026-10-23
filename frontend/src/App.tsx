import { Routes, Route, NavLink } from 'react-router-dom'
import Overview from './pages/Overview'
import Review1Demo from './pages/Review1Demo'
import Scenarios from './pages/Scenarios'
import SupplyChain from './pages/SupplyChain'
import GanLab from './pages/GanLab'
import RLDefense from './pages/RLDefense'
import Experiments from './pages/Experiments'
import Evaluation from './pages/Evaluation'
import SystemLogs from './pages/SystemLogs'
import Settings from './pages/Settings'

const NAV_SECTIONS = [
  {
    title: 'Evaluation & Demo',
    items: [
      { path: '/demo', label: 'Review 1 Live Demo', icon: '⭐' },
      { path: '/', label: 'Overview', icon: '◉' },
    ],
  },
  {
    title: 'Threat Modeling & GAN',
    items: [
      { path: '/scenarios', label: 'Attack Scenarios', icon: '⚡' },
      { path: '/gan-lab', label: 'GAN Threat Lab', icon: '🧬' },
    ],
  },
  {
    title: 'Digital Twin & Defense',
    items: [
      { path: '/supply-chain', label: 'Supply Chain Twin', icon: '⛓' },
      { path: '/rl-defense', label: 'Adaptive Defense', icon: '🛡' },
    ],
  },
  {
    title: 'Scientific Audit',
    items: [
      { path: '/experiments', label: 'Experiments', icon: '🔬' },
      { path: '/evaluation', label: 'Evaluation Matrix', icon: '📊' },
      { path: '/logs', label: 'Telemetry Logs', icon: '📋' },
      { path: '/settings', label: 'Settings', icon: '⚙' },
    ],
  },
]

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
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
            textAlign: 'center',
          }}
        >
          <div style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Team 84 · DSU</div>
          <div>Cyber Defense System</div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/demo" element={<Review1Demo />} />
          <Route path="/scenarios" element={<Scenarios />} />
          <Route path="/supply-chain" element={<SupplyChain />} />
          <Route path="/gan-lab" element={<GanLab />} />
          <Route path="/rl-defense" element={<RLDefense />} />
          <Route path="/experiments" element={<Experiments />} />
          <Route path="/evaluation" element={<Evaluation />} />
          <Route path="/logs" element={<SystemLogs />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}
