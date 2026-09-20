import { useEffect, useState, type FormEvent } from 'react'
import { api, qs } from '../api/client'
import type { Account, Category, Transaction } from '../api/types'
import { formatDate, formatMoney } from '../lib/money'
import { Loading, ErrorMessage, EmptyState } from '../components/Feedback'

const STATUSES = ['PLANNED', 'PENDING', 'CLEARED', 'CANCELLED']

export function Transactions() {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [accounts, setAccounts] = useState<Account[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [accountFilter, setAccountFilter] = useState<string>('')
  const [mode, setMode] = useState<'none' | 'transaction' | 'transfer'>('none')

  const [form, setForm] = useState({
    account_id: '',
    category_id: '',
    transaction_type: 'EXPENSE',
    status: 'CLEARED',
    description: '',
    amount: '',
    date: new Date().toISOString().slice(0, 10),
    tags: '',
  })

  const [transferForm, setTransferForm] = useState({
    source_account_id: '',
    destination_account_id: '',
    amount: '',
    transfer_date: new Date().toISOString().slice(0, 10),
    description: '',
  })

  function load() {
    setLoading(true)
    setError(null)
    api
      .get<Transaction[]>(`/transactions${qs({ account_id: accountFilter || undefined })}`)
      .then(setTransactions)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(load, [accountFilter])
  useEffect(() => {
    api.get<Account[]>('/accounts?include_archived=false').then(setAccounts)
    api.get<Category[]>('/categories').then(setCategories)
  }, [])

  const accountById = Object.fromEntries(accounts.map((a) => [a.id, a]))
  const categoryById = Object.fromEntries(categories.map((c) => [c.id, c]))

  async function submitTransaction(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      const isPlanned = form.status === 'PLANNED' || form.status === 'PENDING'
      await api.post('/transactions', {
        account_id: Number(form.account_id),
        category_id: form.category_id ? Number(form.category_id) : null,
        transaction_type: form.transaction_type,
        status: form.status,
        description: form.description,
        planned_amount: isPlanned ? form.amount : undefined,
        actual_amount: !isPlanned ? form.amount : undefined,
        planned_date: isPlanned ? form.date : undefined,
        actual_date: !isPlanned ? form.date : undefined,
        tags: form.tags ? form.tags.split(',').map((t) => t.trim()).filter(Boolean) : [],
      })
      setMode('none')
      setForm({ ...form, description: '', amount: '', tags: '' })
      load()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  async function submitTransfer(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await api.post('/transfers', {
        source_account_id: Number(transferForm.source_account_id),
        destination_account_id: Number(transferForm.destination_account_id),
        amount: transferForm.amount,
        transfer_date: transferForm.transfer_date,
        description: transferForm.description || null,
      })
      setMode('none')
      setTransferForm({ ...transferForm, amount: '', description: '' })
      load()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Transações</h1>
        <div className="button-row">
          <button onClick={() => setMode(mode === 'transaction' ? 'none' : 'transaction')}>
            {mode === 'transaction' ? 'Cancelar' : 'Nova transação'}
          </button>
          <button onClick={() => setMode(mode === 'transfer' ? 'none' : 'transfer')}>
            {mode === 'transfer' ? 'Cancelar' : 'Nova transferência'}
          </button>
        </div>
      </div>

      {mode === 'transaction' && (
        <form className="card form" onSubmit={submitTransaction}>
          <label>
            Conta
            <select value={form.account_id} onChange={(e) => setForm({ ...form, account_id: e.target.value })} required>
              <option value="" disabled>
                Selecione
              </option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} ({a.currency})
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
            Status
            <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              {STATUSES.filter((s) => s !== 'CANCELLED').map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
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
            Data
            <input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} required />
          </label>
          <label>
            Tags (separadas por vírgula)
            <input value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} />
          </label>
          <button type="submit">Salvar</button>
        </form>
      )}

      {mode === 'transfer' && (
        <form className="card form" onSubmit={submitTransfer}>
          <label>
            Conta de origem
            <select
              value={transferForm.source_account_id}
              onChange={(e) => setTransferForm({ ...transferForm, source_account_id: e.target.value })}
              required
            >
              <option value="" disabled>
                Selecione
              </option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} ({a.currency})
                </option>
              ))}
            </select>
          </label>
          <label>
            Conta de destino
            <select
              value={transferForm.destination_account_id}
              onChange={(e) => setTransferForm({ ...transferForm, destination_account_id: e.target.value })}
              required
            >
              <option value="" disabled>
                Selecione
              </option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} ({a.currency})
                </option>
              ))}
            </select>
          </label>
          <label>
            Valor (na moeda da conta de origem)
            <input
              type="number"
              step="0.01"
              value={transferForm.amount}
              onChange={(e) => setTransferForm({ ...transferForm, amount: e.target.value })}
              required
            />
          </label>
          <label>
            Data
            <input
              type="date"
              value={transferForm.transfer_date}
              onChange={(e) => setTransferForm({ ...transferForm, transfer_date: e.target.value })}
              required
            />
          </label>
          <label>
            Descrição
            <input value={transferForm.description} onChange={(e) => setTransferForm({ ...transferForm, description: e.target.value })} />
          </label>
          <p className="muted">
            Se as contas tiverem moedas diferentes, a conversão usa a taxa de câmbio cadastrada para a data da
            transferência.
          </p>
          <button type="submit">Transferir</button>
        </form>
      )}

      <div className="filter-row">
        <label>
          Filtrar por conta
          <select value={accountFilter} onChange={(e) => setAccountFilter(e.target.value)}>
            <option value="">Todas</option>
            {accounts.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      {loading && <Loading />}
      {error && <ErrorMessage message={error} />}
      {!loading && transactions.length === 0 && <EmptyState message="Nenhuma transação encontrada." />}

      {!loading && transactions.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Data</th>
              <th>Conta</th>
              <th>Categoria</th>
              <th>Descrição</th>
              <th>Tipo</th>
              <th>Status</th>
              <th>Valor</th>
              <th>Tags</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((t) => (
              <tr key={t.id}>
                <td>{formatDate(t.actual_date ?? t.planned_date)}</td>
                <td>{accountById[t.account_id]?.name ?? t.account_id}</td>
                <td>{t.category_id ? categoryById[t.category_id]?.name ?? '—' : '—'}</td>
                <td>{t.description}</td>
                <td className={t.transaction_type === 'INCOME' ? 'text-income' : 'text-expense'}>{t.transaction_type}</td>
                <td>{t.status}</td>
                <td>{formatMoney(t.actual_amount ?? t.planned_amount, t.currency)}</td>
                <td>{t.tags.join(', ')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
