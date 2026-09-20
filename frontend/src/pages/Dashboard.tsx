import { useEffect, useState } from 'react'
import { api, qs } from '../api/client'
import type { DashboardResponse } from '../api/types'
import { formatMoney, formatPercent, monthInputValue } from '../lib/money'
import { Loading, ErrorMessage } from '../components/Feedback'
import { useProfile } from '../context/ProfileContext'

export function Dashboard() {
  const { profile } = useProfile()
  const [month, setMonth] = useState(() => monthInputValue(new Date()))
  const [data, setData] = useState<DashboardResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    api
      .get<DashboardResponse>(`/dashboard${qs({ month })}`)
      .then((res) => !cancelled && setData(res))
      .catch((err) => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [month])

  const baseCurrency = profile?.base_currency ?? 'EUR'

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
        <input type="month" value={month.slice(0, 7)} onChange={(e) => setMonth(`${e.target.value}-01`)} />
      </div>

      {loading && <Loading />}
      {error && <ErrorMessage message={error} />}

      {data && (
        <>
          <div className="stat-grid">
            <StatCard label="Saldo total (convertido)" value={formatMoney(data.total_balance_base_currency, baseCurrency)} />
            <StatCard label="Receita realizada" value={formatMoney(data.actual_income, baseCurrency)} />
            <StatCard label="Despesa realizada" value={formatMoney(data.actual_expenses, baseCurrency)} />
            <StatCard label="Economia realizada" value={formatMoney(data.actual_savings, baseCurrency)} accent />
            <StatCard label="Taxa de poupança" value={formatPercent(data.savings_rate)} />
            <StatCard label="Economia planejada" value={formatMoney(data.planned_savings, baseCurrency)} muted />
          </div>

          <section className="card">
            <h2>Contas</h2>
            <table>
              <thead>
                <tr>
                  <th>Conta</th>
                  <th>Moeda</th>
                  <th>Saldo</th>
                  <th>Convertido ({baseCurrency})</th>
                </tr>
              </thead>
              <tbody>
                {data.accounts.map((account) => (
                  <tr key={account.id}>
                    <td>{account.name}</td>
                    <td>{account.currency}</td>
                    <td>{formatMoney(account.balance, account.currency)}</td>
                    <td>
                      {account.balance_in_base_currency !== null
                        ? formatMoney(account.balance_in_base_currency, baseCurrency)
                        : <span className="muted" title="Cadastre uma taxa de câmbio para consolidar esta moeda">sem taxa cadastrada</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="card">
            <h2>Por moeda</h2>
            <div className="two-col">
              <div>
                <h3>Realizado</h3>
                <CurrencyTable rows={data.actual_by_currency} />
              </div>
              <div>
                <h3>Planejado</h3>
                <CurrencyTable rows={data.planned_by_currency} />
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  )
}

function StatCard({ label, value, accent, muted }: { label: string; value: string; accent?: boolean; muted?: boolean }) {
  return (
    <div className={`stat-card ${accent ? 'accent' : ''} ${muted ? 'muted' : ''}`}>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
    </div>
  )
}

function CurrencyTable({ rows }: { rows: { currency: string; income: string; expenses: string }[] }) {
  if (rows.length === 0) return <p className="muted">Sem movimentações.</p>
  return (
    <table>
      <thead>
        <tr>
          <th>Moeda</th>
          <th>Receita</th>
          <th>Despesa</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.currency}>
            <td>{row.currency}</td>
            <td>{formatMoney(row.income, row.currency)}</td>
            <td>{formatMoney(row.expenses, row.currency)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
