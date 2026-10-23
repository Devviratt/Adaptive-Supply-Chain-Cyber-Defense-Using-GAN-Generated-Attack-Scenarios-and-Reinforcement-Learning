import { useState, useEffect } from 'react'
import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import Overview from './pages/Overview'
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

const NAV_ITEMS = [
  { path: '/', label: 'Overview', icon: '◻' },
  { path: '/data', label: 'Data Processing', icon: '▤' },
  { path: '/gan-lab', label: 'CTGAN Threat Lab', icon: '◈' },
  { path: '/scenarios', label: 'Attack Scenarios', icon: '⚡' },
  { path: '/supply-chain', label: 'Supply Chain Twin', icon: '⛓' },
  { path: '/rl-defense', label: 'Adaptive Defense', icon: '🛡' },
  { path: '/experiments', label: 'Experiments', icon: '🔬' },
  { path: '/evaluation', label: 'Audit & Limitations', icon: '📈' },
  { path: '/logs', label: 'Telemetry & Logs', icon: '⌨' },
  { path: '/settings', label: 'Settings', icon: '⚙' },
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
    const interval = setInterval(checkHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/':
        return 'Project Overview'
      case '/data':
        return 'Data Ingestion & Preprocessing'
      case '/gan-lab':
        return 'CTGAN Threat Lab & Validation'
      case '/scenarios':
        return 'Attack Scenario Mapper'
      case '/supply-chain':
        return 'Supply Chain Digital Twin'
      case '/rl-defense':
        return 'Adaptive Defense Policies'
      case '/experiments':
        return 'Controlled Benchmark Experiments'
      case '/evaluation':
        return 'Scientific Audit & Limitations'
      case '/logs':
        return 'System Telemetry & Logs'
      case '/settings':
        return 'Configuration'
      default:
        return 'Cyber Defense Platform'
    }
  }

  return (
    <div className="app-layout">
      {/* Mobile backdrop */}
      <div
        className={`sidebar-backdrop ${mobileOpen ? 'mobile-open' : ''}`}
        onClick={() => setMobileOpen(false)}
      />

      {/* Compact Dark Capsule Sidebar */}
      <aside className={`sidebar ${mobileOpen ? 'mobile-open' : ''}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <div className="logo-icon">🛡</div>
            <div>
              <h1>ASCCD</h1>
              <span>Cyber Defense</span>
            </div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section">
            <div className="nav-section-title">Navigation</div>
            {NAV_ITEMS.map((item) => (
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
        </nav>

        <div className="sidebar-footer">
          <div style={{ fontWeight: 600, color: '#f8fafc' }}>Team 84 · DSU CSE</div>
          <div style={{ color: '#64748b' }}>Guide: Prof. Namyapriya D</div>
        </div>
      </aside>

      {/* Main Content Area */}
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
              <div className="greeting">
                <h2>{getPageTitle()}</h2>
              </div>
              <span className="header-subtitle">
                Adaptive Supply Chain Cyber Defense Using GAN & RL
              </span>
            </div>
          </div>

          <div className="header-right">
            {/* Backend Connection Status Pill */}
            <div className="header-pill">
              {apiConnected === null ? (
                <span style={{ color: 'var(--text-muted)' }}>Connecting API...</span>
              ) : apiConnected ? (
                <>
                  <span className="status-dot healthy"></span>
                  <span style={{ color: 'var(--status-healthy)', fontWeight: 600 }}>
                    API Online (v0.4.0)
                  </span>
                </>
              ) : (
                <>
                  <span className="status-dot warning"></span>
                  <span style={{ color: 'var(--status-warning)', fontWeight: 600 }}>
                    API Offline
                  </span>
                </>
              )}
            </div>

            {/* Review Milestone Pill */}
            <div className="header-pill" style={{ background: '#f0fdf4', borderColor: '#bbf7d0' }}>
              <span style={{ color: '#16a34a', fontWeight: 600 }}>
                Review 1 Checkpoint: 40% Target Met
              </span>
            </div>
          </div>
        </header>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Overview />} />
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
