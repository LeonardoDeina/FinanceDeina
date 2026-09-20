import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { ForecastRun, SavingsCapacity } from '../api/types'
import { formatDate, formatMoney } from '../lib/money'
import { Loading, ErrorMessage } from '../components/Feedback'
import { useProfile } from '../context/ProfileContext'

const HORIZONS = [
  { label: '30 dias', days: 30 },
  { label: '60 dias', days: 60 },
  { label: '90 dias', days: 90 },
  { label: '6 meses', days: 180 },
  { label: '12 meses', days: 365 },
]

export function Forecast() {
  const { profile } = useProfile()
  const [horizonDays, setHorizonDays] = useState(90)
  const [result, setResult] = useState<ForecastRun | null>(null)
  const [capacity, setCapacity] = useState<SavingsCapacity | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const baseCurrency = profile?.base_currency ?? 'EUR'

  useEffect(() => {
    api.get<SavingsCapacity>('/forecasts/savings-capacity/estimate').then(setCapacity).catch(() => {})
  }, [])

  async function runForecast() {
    setLoading(true)
    setError(null)
    try {
      const res = await api.post<ForecastRun>('/forecasts/run', { horizon_days: horizonDays })
      setResult(res)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Previsão</h1>
      </div>

      <section className="card">
        <h2>Capacidade de poupança observada</h2>
        {capacity && (
          <div className="stat-grid">
            <div className="stat-card">
              <div className="stat-label">Média 3 meses</div>
              <div className="stat-value">{formatMoney(capacity.average_3m, capacity.currency)}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Média 6 meses</div>
              <div className="stat-value">{formatMoney(capacity.average_6m, capacity.currency)}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Mediana 6 meses</div>
              <div className="stat-value">{formatMoney(capacity.median_6m, capacity.currency)}</div>
            </div>
            <div className="stat-card accent">
              <div className="stat-label">Recomendado (robusto)</div>
              <div className="stat-value">{formatMoney(capacity.recommended, capacity.currency)}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Tendência</div>
              <div className="stat-value">{capacity.trend}</div>
            </div>
          </div>
        )}
      </section>

      <section className="card">
        <h2>Simular projeção de saldo</h2>
        <div className="button-row">
          {HORIZONS.map((h) => (
            <button key={h.days} className={horizonDays === h.days ? 'active' : ''} onClick={() => setHorizonDays(h.days)}>
              {h.label}
            </button>
          ))}
          <button onClick={runForecast} disabled={loading}>
            {loading ? 'Calculando...' : 'Calcular previsão'}
          </button>
        </div>

        {error && <ErrorMessage message={error} />}
        {loading && <Loading />}

        {result && (
          <>
            <div className="stat-grid">
              <div className="stat-card">
                <div className="stat-label">Saldo atual</div>
                <div className="stat-value">{formatMoney(result.starting_balance, result.currency)}</div>
              </div>
              <div className="stat-card accent">
                <div className="stat-label">Saldo projetado em {formatDate(result.horizon_end)}</div>
                <div className="stat-value">{formatMoney(result.projected_ending_balance, result.currency)}</div>
              </div>
            </div>

            <table>
              <thead>
                <tr>
                  <th>Mês</th>
                  <th>Receita projetada</th>
                  <th>Despesa projetada</th>
                  <th>Economia projetada</th>
                  <th>Saldo final projetado</th>
                </tr>
              </thead>
              <tbody>
                {result.monthly_items.map((item) => (
                  <tr key={item.reference_month}>
                    <td>{item.reference_month}</td>
                    <td>{formatMoney(item.projected_income, baseCurrency)}</td>
                    <td>{formatMoney(item.projected_expenses, baseCurrency)}</td>
                    <td>{formatMoney(item.projected_savings, baseCurrency)}</td>
                    <td>{formatMoney(item.projected_end_balance, baseCurrency)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </section>
    </div>
  )
}
