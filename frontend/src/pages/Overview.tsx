import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getHealth } from '../api/client'

export default function Overview() {
  const [health, setHealth] = useState<{ status: string; version: string } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      const healthRes = await getHealth()
      if (healthRes.data) setHealth(healthRes.data)
      setLoading(false)
    }
    fetchData()
  }, [])

  const projectSteps = [
    { title: 'Create a synthetic attack', description: 'Choose an attack type and generate artificial examples for a safe demo.', to: '/gan-lab', link: 'Generate an attack' },
    { title: 'See what it affects', description: 'Open the generated incident in the supply-chain simulator.', to: '/supply-chain', link: 'Open simulator' },
    { title: 'Try to prevent it', description: 'Review the suggested response and apply a defensive action.', to: '/supply-chain', link: 'Explore defenses' },
  ]

  if (loading) {
    return (
      <div className="loading-spinner">
        <div className="spinner" />
      </div>
    )
  }

  return (
    <div className="overview-page">
      <section className="overview-hero">
        <div>
          <span className="overview-eyebrow">Supply chain security learning lab</span>
          <h2>Generate a synthetic attack. Try to stop it.</h2>
          <p>
            Create an artificial attack scenario, see how it affects a sample software supply chain,
            and apply a defensive response in a safe simulation.
          </p>
          <div className="overview-actions">
            <Link to="/gan-lab" className="btn btn-primary">Generate synthetic attack</Link>
            <Link to="/supply-chain" className="btn btn-secondary">Open simulator</Link>
          </div>
          <p className="overview-disclaimer">
            This is a research simulation. It does not connect to or protect real systems.
          </p>
        </div>
        <div className={`overview-service-status ${health?.status === 'healthy' ? 'is-healthy' : 'is-offline'}`}>
          <span className="overview-status-dot" />
          <span>{health?.status === 'healthy' ? 'Demo services are running' : 'Demo service is unavailable'}</span>
        </div>
      </section>

      <section className="overview-section" aria-labelledby="overview-journey-title">
        <div className="overview-section-heading">
          <h3 id="overview-journey-title">How to explore the demo</h3>
          <p>Start with an incident, watch the simulation, and try a defense.</p>
        </div>
        <div className="overview-journey-grid">
          {projectSteps.map((step) => (
            <article className="overview-journey-card" key={step.title}>
              <h4>{step.title}</h4>
              <p>{step.description}</p>
              <Link to={step.to}>{step.link}</Link>
            </article>
          ))}
        </div>
      </section>

      <section className="overview-supply-chain" aria-labelledby="overview-chain-title">
        <div className="overview-section-heading">
          <h3 id="overview-chain-title">What does “software supply chain” mean?</h3>
          <p>
            Software passes through these stages before it reaches users. The simulator shows how a
            problem at one stage can affect the next.
          </p>
        </div>
        <div className="overview-flow">
          {[
            { name: 'Supplier', description: 'Where software components come from' },
            { name: 'Build', description: 'Where components are assembled' },
            { name: 'Registry', description: 'Where finished packages are stored' },
            { name: 'Deployment', description: 'Where software is put into use' },
          ].map((stage) => (
            <div className="overview-flow-stage" key={stage.name}>
              <strong>{stage.name}</strong>
              <span>{stage.description}</span>
            </div>
          ))}
        </div>
      </section>

      <details className="overview-glossary">
        <summary>What do the technical terms mean?</summary>
        <dl>
          <div>
            <dt>Synthetic attack data</dt>
            <dd>Artificial example records used to test the research pipeline; they are not real incidents.</dd>
          </div>
          <div>
            <dt>Defense policy</dt>
            <dd>A set of choices the simulator can use to respond, such as monitoring, blocking, or isolating a stage.</dd>
          </div>
          <div>
            <dt>Simulation result</dt>
            <dd>An outcome inside this model only. It is not a guarantee about real-world security.</dd>
          </div>
        </dl>
      </details>
    </div>
  )
}
