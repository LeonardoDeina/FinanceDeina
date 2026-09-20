import { useEffect, useState, type FormEvent } from 'react'
import { api } from '../api/client'
import type { Budget, BudgetProgress, Category } from '../api/types'
import { formatMoney, formatPercent } from '../lib/money'
import { Loading, ErrorMessage, EmptyState } from '../components/Feedback'
import { useProfile } from '../context/ProfileContext'

export function Budgets() {
  const { profile } = useProfile()
  const [budgets, setBudgets] = useState<Budget[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [progress, setProgress] = useState<Record<number, BudgetProgress>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)

  const [name, setName] = useState('')
  const [periodStart, setPeriodStart] = useState(new Date().toISOString().slice(0, 8) + '01')
  const [periodEnd, setPeriodEnd] = useState('')
  const [lines, setLines] = useState<{ category_id: string; planned_amount: string }[]>([{ category_id: '', planned_amount: '' }])

  function load() {
    setLoading(true)
    api
      .get<Budget[]>('/budgets')
      .then(async (list) => {
        setBudgets(list)
        const progressEntries = await Promise.all(
          list.map((b) => api.get<BudgetProgress>(`/budgets/${b.id}/progress`).then((p) => [b.id, p] as const)),
        )
        setProgress(Object.fromEntries(progressEntries))
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])
  useEffect(() => {
    api.get<Category[]>('/categories').then(setCategories)
  }, [])

  function updateLine(idx: number, field: 'category_id' | 'planned_amount', value: string) {
    setLines((prev) => prev.map((line, i) => (i === idx ? { ...line, [field]: value } : line)))
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await api.post('/budgets', {
        name,
        period_start: periodStart,
        period_end: periodEnd,
        lines: lines.filter((l) => l.category_id && l.planned_amount).map((l) => ({ category_id: Number(l.category_id), planned_amount: l.planned_amount })),
      })
      setShowForm(false)
      setName('')
      setLines([{ category_id: '', planned_amount: '' }])
      load()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const categoryById = Object.fromEntries(categories.map((c) => [c.id, c]))
  const baseCurrency = profile?.base_currency ?? 'EUR'

  return (
    <div>
      <div className="page-header">
        <h1>Orçamentos</h1>
        <button onClick={() => setShowForm((v) => !v)}>{showForm ? 'Cancelar' : 'Novo orçamento'}</button>
      </div>

      {showForm && (
        <form className="card form" onSubmit={handleSubmit}>
          <label>
            Nome
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </label>
          <label>
            Início do período
            <input type="date" value={periodStart} onChange={(e) => setPeriodStart(e.target.value)} required />
          </label>
          <label>
            Fim do período
            <input type="date" value={periodEnd} onChange={(e) => setPeriodEnd(e.target.value)} required />
          </label>

          <div className="budget-lines">
            <h3>Linhas do orçamento</h3>
            {lines.map((line, idx) => (
              <div className="budget-line-row" key={idx}>
                <select value={line.category_id} onChange={(e) => updateLine(idx, 'category_id', e.target.value)}>
                  <option value="">Categoria</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
                <input
                  type="number"
                  step="0.01"
                  placeholder="Valor planejado"
                  value={line.planned_amount}
                  onChange={(e) => updateLine(idx, 'planned_amount', e.target.value)}
                />
              </div>
            ))}
            <button type="button" className="link-button" onClick={() => setLines([...lines, { category_id: '', planned_amount: '' }])}>
              + adicionar categoria
            </button>
          </div>

          <button type="submit">Salvar orçamento</button>
        </form>
      )}

      {loading && <Loading />}
      {error && <ErrorMessage message={error} />}
      {!loading && budgets.length === 0 && <EmptyState message="Nenhum orçamento cadastrado." />}

      {budgets.map((budget) => (
        <section className="card" key={budget.id}>
          <h2>
            {budget.name} <span className="muted">({budget.period_start} a {budget.period_end})</span>
          </h2>
          <table>
            <thead>
              <tr>
                <th>Categoria</th>
                <th>Planejado</th>
                <th>Gasto</th>
                <th>Restante</th>
                <th>% usado</th>
                <th>Desvio</th>
              </tr>
            </thead>
            <tbody>
              {progress[budget.id]?.lines.map((line) => (
                <tr key={line.category_id}>
                  <td>{categoryById[line.category_id]?.name ?? line.category_id}</td>
                  <td>{formatMoney(line.planned_amount, baseCurrency)}</td>
                  <td>{formatMoney(line.actual_spent, baseCurrency)}</td>
                  <td>{formatMoney(line.remaining, baseCurrency)}</td>
                  <td>{formatPercent(line.used_pct)}</td>
                  <td>{formatMoney(line.variance, baseCurrency)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ))}
    </div>
  )
}
