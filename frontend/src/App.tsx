import { useEffect, useState } from 'react'
import { Routes, Route, NavLink } from 'react-router-dom'
import Overview from './pages/Overview'
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
    title: 'Start here',
    items: [
      { path: '/', label: 'Overview' },
    ],
  },
  {
    title: 'Create and explore attacks',
    items: [
      { path: '/gan-lab', label: 'Generate Synthetic Attack' },
      { path: '/scenarios', label: 'Prepared Attack Scenarios' },
    ],
  },
  {
    title: 'Run a simulation',
    items: [
      { path: '/supply-chain', label: 'Supply Chain Simulator' },
      { path: '/rl-defense', label: 'Defense Policies' },
    ],
  },
  {
    title: 'Review results',
    items: [
      { path: '/experiments', label: 'Experiments' },
      { path: '/evaluation', label: 'Performance Results' },
      { path: '/logs', label: 'System Status' },
      { path: '/settings', label: 'Settings' },
    ],
  },
]

export default function App() {
  const [theme, setTheme] = useState<'light' | 'dark'>(() =>
    window.localStorage.getItem('asccd-theme') === 'dark' ? 'dark' : 'light'
  )

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    window.localStorage.setItem('asccd-theme', theme)
    const themeColor = document.querySelector<HTMLMetaElement>('meta[name="theme-color"]')
    if (themeColor) themeColor.content = theme === 'dark' ? '#090d13' : '#f3f7fd'
  }, [theme])

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
          <div>Cyber Defense System</div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header className="app-topbar">
          <button
            type="button"
            className="theme-toggle"
            aria-label={`Switch to ${theme === 'light' ? 'night' : 'day'} theme`}
            aria-pressed={theme === 'dark'}
            onClick={() => setTheme((current) => current === 'light' ? 'dark' : 'light')}
          >
            <span className="theme-toggle-track" aria-hidden="true">
              <span className="theme-toggle-thumb" />
            </span>
            <span>{theme === 'light' ? 'Night mode' : 'Day mode'}</span>
          </button>
        </header>
        <Routes>
          <Route path="/" element={<Overview />} />
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
