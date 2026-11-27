import { useState } from 'react'
import { Link } from 'react-router-dom'
import { generateSyntheticAttack } from '../api/client'
import type { SyntheticAttackGenerateResponse } from '../api/client'

export default function GanLab() {
  const [samplesToGenerate, setSamplesToGenerate] = useState(10)
  const [selectedClass, setSelectedClass] = useState('ddos')
  const [selectedStage, setSelectedStage] = useState('deployment')
  const [generating, setGenerating] = useState(false)
  const [generatedAttack, setGeneratedAttack] = useState<SyntheticAttackGenerateResponse | null>(null)
  const [error, setError] = useState('')

  async function handleTriggerGenerate() {
    setGenerating(true)
    setGeneratedAttack(null)
    setError('')
    const result = await generateSyntheticAttack(selectedClass, samplesToGenerate, selectedStage)
    setGenerating(false)
    if (result.data) setGeneratedAttack(result.data)
    else setError(result.error ?? 'Could not generate the synthetic attack.')
  }

  return (
    <div>
      <div className="page-header">
        <h2>Create a synthetic attack</h2>
        <p>
          Choose an attack type and a supply-chain stage, create artificial examples, then open the
          incident in the simulator and try to stop it. These examples do not target real systems.
        </p>
      </div>

      <section className="card synthetic-generator-card">
        <div className="synthetic-generator-intro">
          <span className="overview-eyebrow">Create and test</span>
          <h3>Make a practice attack</h3>
          <p>
            The generator creates artificial network examples, then maps them to the node you choose
            and saves an incident that you can open in the simulator.
          </p>
        </div>

        <div className="synthetic-generator-form">
          <div>
            <label htmlFor="attack-type">Choose an attack type</label>
            <select
              id="attack-type"
              value={selectedClass}
              onChange={(event) => setSelectedClass(event.target.value)}
              disabled={generating}
            >
              <option value="ddos">DDoS — overwhelm a service with traffic</option>
              <option value="dos">DoS — make a service unavailable</option>
              <option value="portscan">Port scan — search for exposed services</option>
              <option value="botnet">Botnet — coordinate compromised devices</option>
              <option value="brute_force">Password guessing — attempt account access</option>
            </select>
          </div>
          <div>
            <label htmlFor="attack-stage">Where should the attack happen?</label>
            <select
              id="attack-stage"
              value={selectedStage}
              onChange={(event) => setSelectedStage(event.target.value)}
              disabled={generating}
            >
              <option value="supplier">Supplier — component providers</option>
              <option value="build">Build — CI/CD pipeline</option>
              <option value="registry">Registry — package storage</option>
              <option value="deployment">Deployment — software in use</option>
            </select>
          </div>
          <div>
            <label htmlFor="sample-count">How many examples?</label>
            <input
              id="sample-count"
              type="number"
              min={1}
              max={200}
              value={samplesToGenerate}
              onChange={(event) => setSamplesToGenerate(Number(event.target.value))}
              disabled={generating}
            />
          </div>
        </div>

        <button
          className="btn btn-primary"
          onClick={() => void handleTriggerGenerate()}
          disabled={generating || samplesToGenerate < 1 || samplesToGenerate > 200}
        >
          {generating ? 'Creating practice attack…' : 'Generate synthetic attack'}
        </button>

        {error && <div role="alert" className="synthetic-result synthetic-result-error">{error}</div>}

        {generatedAttack && (
          <div className="synthetic-result" aria-live="polite">
            <div>
              <span className="countermeasure-eyebrow">Ready to explore</span>
              <h4>Your practice attack is ready</h4>
              <p>
                {generatedAttack.generated_count} artificial{' '}
                {generatedAttack.attack_category.replace(/_/g, ' ')} examples were created and added
                as a {generatedAttack.severity} incident affecting the {generatedAttack.affected_stage} stage.
              </p>
              <p className="synthetic-result-note">
                These are model-generated examples for this simulation, not real attacks.
              </p>
            </div>
            <Link
              className="btn btn-primary"
              to={`/supply-chain?scenario_id=${encodeURIComponent(generatedAttack.scenario_id)}`}
            >
              Try to prevent it
            </Link>
          </div>
        )}
      </section>

      <details className="overview-glossary synthetic-generator-details">
        <summary>How does the generator work?</summary>
        <p>
          It learns patterns from prepared training data and produces new, artificial examples.
          The simulator maps an example to a supply-chain stage and provides defensive choices.
          This research prototype does not send traffic or test real systems.
        </p>
      </details>
    </div>
  )
}
