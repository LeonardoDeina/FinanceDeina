import { useEffect, useState, type FormEvent } from 'react'
import { api } from '../api/client'
import type { Account, Category, RecurringRule, UpcomingOccurrence } from '../api/types'
import { formatDate, formatMoney } from '../lib/money'
import { Loading, ErrorMessage, EmptyState } from '../components/Feedback'

const FREQUENCIES = ['WEEKLY', 'BIWEEKLY', 'MONTHLY', 'QUARTERLY', 'SEMIANNUAL', 'ANNUAL']

export function Recurring() {
  const [rules, setRules] = useState<RecurringRule[]>([])
  const [upcoming, setUpcoming] = useState<UpcomingOccurrence[]>([])
  const [accounts, setAccounts] = useState<Account[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)

  const [form, setForm] = useState({
    account_id: '',
    category_id: '',
    transaction_type: 'EXPENSE',
    description: '',
    amount: '',
    frequency: 'MONTHLY',
    start_date: new Date().toISOString().slice(0, 10),
    end_date: '',
  })

  function load() {
    setLoading(true)
    Promise.all([api.get<RecurringRule[]>('/recurring-rules'), api.get<UpcomingOccurrence[]>('/recurring-rules/upcoming?horizon_days=60')])
      .then(([r, u]) => {
        setRules(r)
        setUpcoming(u)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])
  useEffect(() => {
    api.get<Account[]>('/accounts').then(setAccounts)
    api.get<Category[]>('/categories').then(setCategories)
  }, [])

  const accountById = Object.fromEntries(accounts.map((a) => [a.id, a]))

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await api.post('/recurring-rules', {
        account_id: Number(form.account_id),
        category_id: form.category_id ? Number(form.category_id) : null,
        transaction_type: form.transaction_type,
        description: form.description,
        amount: form.amount,
        frequency: form.frequency,
        start_date: form.start_date,
        end_date: form.end_date || null,
      })
      setShowForm(false)
      setForm({ ...form, description: '', amount: '' })
      load()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  async function toggleActive(rule: RecurringRule) {
    await api.patch(`/recurring-rules/${rule.id}`, { is_active: !rule.is_active })
    load()
  }

  return (
    <div>
      <div className="page-header">
        <h1>Recorrências</h1>
        <button onClick={() => setShowForm((v) => !v)}>{showForm ? 'Cancelar' : 'Nova recorrência'}</button>
      </div>

      {showForm && (
        <form className="card form" onSubmit={handleSubmit}>
          <label>
            Conta
            <select value={form.account_id} onChange={(e) => setForm({ ...form, account_id: e.target.value })} required>
              <option value="" disabled>
                Selecione
              </option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Categoria
            <select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })}>
              <option value="">Sem categoria</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Tipo
            <select value={form.transaction_type} onChange={(e) => setForm({ ...form, transaction_type: e.target.value })}>
              <option value="INCOME">Receita</option>
              <option value="EXPENSE">Despesa</option>
            </select>
          </label>
          <label>
            Descrição
            <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} required />
          </label>
          <label>
            Valor
            <input type="number" step="0.01" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
          </label>
          <label>
            Frequência
            <select value={form.frequency} onChange={(e) => setForm({ ...form, frequency: e.target.value })}>
              {FREQUENCIES.map((f) => (
                <option key={f} value={f}>
                  {f}
                </option>
              ))}
            </select>
          </label>
          <label>
            Início
            <input type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} required />
          </label>
          <label>
            Fim (opcional)
            <input type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} />
          </label>
          <button type="submit">Salvar</button>
        </form>
      )}

      {loading && <Loading />}
      {error && <ErrorMessage message={error} />}

      {!loading && (
        <>
          <section className="card">
            <h2>Regras ativas</h2>
            {rules.length === 0 && <EmptyState message="Nenhuma recorrência cadastrada." />}
            {rules.length > 0 && (
              <table>
                <thead>
                  <tr>
                    <th>Descrição</th>
                    <th>Conta</th>
                    <th>Tipo</th>
                    <th>Valor</th>
                    <th>Frequência</th>
                    <th>Próxima</th>
                    <th>Status</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {rules.map((rule) => (
                    <tr key={rule.id} className={rule.is_active ? '' : 'muted'}>
                      <td>{rule.description}</td>
                      <td>{accountById[rule.account_id]?.name ?? rule.account_id}</td>
                      <td>{rule.transaction_type}</td>
                      <td>{formatMoney(rule.amount, accountById[rule.account_id]?.currency ?? 'EUR')}</td>
                      <td>{rule.frequency}</td>
                      <td>{formatDate(rule.next_occurrence)}</td>
                      <td>{rule.is_active ? 'Ativa' : 'Inativa'}</td>
                      <td>
                        <button className="link-button" onClick={() => toggleActive(rule)}>
                          {rule.is_active ? 'Pausar' : 'Reativar'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>

          <section className="card">
            <h2>Próximas ocorrências (60 dias)</h2>
            {upcoming.length === 0 && <EmptyState message="Nenhuma ocorrência prevista." />}
            {upcoming.length > 0 && (
              <table>
                <thead>
                  <tr>
                    <th>Data</th>
                    <th>Descrição</th>
                    <th>Tipo</th>
                    <th>Valor</th>
                  </tr>
                </thead>
                <tbody>
                  {upcoming.map((occ, idx) => (
                    <tr key={idx}>
                      <td>{formatDate(occ.occurrence_date)}</td>
                      <td>{occ.description}</td>
                      <td>{occ.transaction_type}</td>
                      <td>{occ.amount}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </>
      )}
    </div>
  )
}
