import { useState, useEffect } from 'react'
import { Routes, Route, NavLink, useLocation, Link } from 'react-router-dom'
import Overview from './pages/Overview'
import Review1Demo from './pages/Review1Demo'
import DataPipeline from './pages/DataPipeline'
import Scenarios from './pages/Scenarios'
import SupplyChain from './pages/SupplyChain'
import GanLab from './pages/GanLab'
import RLDefense from './pages/RLDefense'
import Experiments from './pages/Experiments'
import Evaluation from './pages/Evaluation'
import SystemLogs from './pages/SystemLogs'
import Settings from './pages/Settings'
import { getHealth } from './api/client'

const NAV_SECTIONS = [
  {
    title: 'Overview & Demo',
    items: [
      { path: '/', label: 'Project Overview', icon: '📋' },
      { path: '/demo', label: 'Faculty Demo Runner', icon: '⭐' },
    ],
  },
  {
    title: 'Data & Threat Synthesis',
    items: [
      { path: '/data', label: 'Data Preprocessing', icon: '📊' },
      { path: '/gan-lab', label: 'CTGAN Threat Lab', icon: '🧬' },
      { path: '/scenarios', label: 'Attack Scenarios', icon: '⚡' },
    ],
  },
  {
    title: 'Digital Twin & Defense',
    items: [
      { path: '/supply-chain', label: 'Supply Chain Twin', icon: '⛓️' },
      { path: '/rl-defense', label: 'Adaptive Defense', icon: '🛡️' },
      { path: '/experiments', label: 'Controlled Benchmarks', icon: '🔬' },
    ],
  },
  {
    title: 'Scientific Audit',
    items: [
      { path: '/evaluation', label: 'Audit & Limitations', icon: '📈' },
      { path: '/logs', label: 'Telemetry & Commands', icon: '💻' },
      { path: '/settings', label: 'Settings', icon: '⚙️' },
    ],
  },
]

export default function App() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [apiConnected, setApiConnected] = useState<boolean | null>(null)
  const location = useLocation()

  useEffect(() => {
    async function checkHealth() {
      const res = await getHealth()
      setApiConnected(Boolean(res.data && res.data.status === 'healthy'))
    }
    checkHealth()
  }, [])

  // Close mobile sidebar on route change
  useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/':
        return 'Project Overview & Verified Status'
      case '/demo':
        return 'Review 1 Faculty Demo Runner'
      case '/data':
        return 'Data Ingestion & Preprocessing Foundation'
      case '/gan-lab':
        return 'CTGAN Threat Lab & Statistical Validation'
      case '/scenarios':
        return 'Attack Scenario Mapper & Vectors'
      case '/supply-chain':
        return 'Supply Chain Digital Twin Simulation'
      case '/rl-defense':
        return 'Adaptive Cyber Defense Policies'
      case '/experiments':
        return 'Controlled Benchmark Experiments Hub'
      case '/evaluation':
        return 'Scientific Audit, Metrics & Limitations'
      case '/logs':
        return 'System Telemetry & Reproducible Trace'
      case '/settings':
        return 'System Configuration'
      default:
        return 'ASCCD Cyber Defense'
    }
  }

  return (
    <div className="app-layout">
      {/* Mobile backdrop */}
      <div
        className={`sidebar-backdrop ${mobileOpen ? 'mobile-open' : ''}`}
        onClick={() => setMobileOpen(false)}
      />

      {/* Sidebar Navigation */}
      <aside className={`sidebar ${mobileOpen ? 'mobile-open' : ''}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <div className="logo-icon">🛡️</div>
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
                  className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                  end={item.path === '/'}
                >
                  <span className="nav-icon">{item.icon}</span>
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div style={{ fontWeight: 600, color: 'var(--text-heading)' }}>Team 84 · DSU CSE</div>
          <div style={{ marginTop: '2px', color: 'var(--text-muted)' }}>Guide: Prof. Namyapriya D</div>
          <div style={{ marginTop: '4px', fontSize: '0.7rem', color: 'var(--accent-primary)', fontWeight: 600 }}>
            v0.4.0 · 40% Review Milestone
          </div>
        </div>
      </aside>

      {/* Main Content Area with Sticky Header */}
      <div className="main-wrapper">
        <header className="top-header">
          <div className="header-left">
            <button
              className="menu-toggle"
              onClick={() => setMobileOpen(!mobileOpen)}
              aria-label="Toggle navigation"
            >
              ☰
            </button>
            <div className="header-title-box">
              <h2>{getPageTitle()}</h2>
              <span>Adaptive Supply Chain Cyber Defense Using GAN & RL</span>
            </div>
          </div>

          <div className="header-right">
            {apiConnected === null ? (
              <span className="badge badge-neutral">Checking API...</span>
            ) : apiConnected ? (
              <span className="badge badge-healthy">
                <span className="status-dot healthy"></span> API Online (v0.4.0)
              </span>
            ) : (
              <span className="badge badge-warning">
                <span className="status-dot warning"></span> API Offline (Mock Mode)
              </span>
            )}

            <span className="badge badge-info">
              40% Milestone
            </span>

            <Link to="/demo" className="btn btn-primary btn-sm">
              ⭐ Faculty Demo
            </Link>
          </div>
        </header>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/demo" element={<Review1Demo />} />
            <Route path="/data" element={<DataPipeline />} />
            <Route path="/gan-lab" element={<GanLab />} />
            <Route path="/scenarios" element={<Scenarios />} />
            <Route path="/supply-chain" element={<SupplyChain />} />
            <Route path="/rl-defense" element={<RLDefense />} />
            <Route path="/experiments" element={<Experiments />} />
            <Route path="/evaluation" element={<Evaluation />} />
            <Route path="/logs" element={<SystemLogs />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
