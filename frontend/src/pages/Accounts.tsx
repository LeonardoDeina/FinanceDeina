import { useEffect, useState, type FormEvent } from 'react'
import { api } from '../api/client'
import type { AccountWithBalance } from '../api/types'
import { formatMoney } from '../lib/money'
import { Loading, ErrorMessage } from '../components/Feedback'
import { useProfile } from '../context/ProfileContext'

const ACCOUNT_TYPES = ['CHECKING', 'SAVINGS', 'CASH', 'INVESTMENT', 'WALLET']

export function Accounts() {
  const { currencies, profile } = useProfile()
  const [accounts, setAccounts] = useState<AccountWithBalance[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)

  const [name, setName] = useState('')
  const [accountType, setAccountType] = useState(ACCOUNT_TYPES[0])
  const [currency, setCurrency] = useState('EUR')
  const [initialBalance, setInitialBalance] = useState('0.00')
  const [initialDate, setInitialDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [submitting, setSubmitting] = useState(false)

  function load() {
    setLoading(true)
    api
      .get<AccountWithBalance[]>('/accounts')
      .then(setAccounts)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])
  useEffect(() => {
    if (currencies.length > 0 && !currencies.some((c) => c.code === currency)) {
      setCurrency(profile?.base_currency ?? currencies[0].code)
    }
  }, [currencies, profile])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      await api.post('/accounts', {
        name,
        account_type: accountType,
        currency,
        initial_balance: initialBalance,
        initial_balance_date: initialDate,
      })
      setName('')
      setInitialBalance('0.00')
      setShowForm(false)
      load()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSubmitting(false)
    }
  }

  async function toggleArchive(account: AccountWithBalance) {
    await api.patch(`/accounts/${account.id}`, { is_active: !account.is_active })
    load()
  }

  return (
    <div>
      <div className="page-header">
        <h1>Contas</h1>
        <button onClick={() => setShowForm((v) => !v)}>{showForm ? 'Cancelar' : 'Nova conta'}</button>
      </div>

      {showForm && (
        <form className="card form" onSubmit={handleSubmit}>
          <label>
            Nome
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </label>
          <label>
            Tipo
            <select value={accountType} onChange={(e) => setAccountType(e.target.value)}>
              {ACCOUNT_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </label>
          <label>
            Moeda
            <select value={currency} onChange={(e) => setCurrency(e.target.value)}>
              {currencies.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.code} — {c.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Saldo inicial
            <input type="number" step="0.01" value={initialBalance} onChange={(e) => setInitialBalance(e.target.value)} />
          </label>
          <label>
            Data do saldo inicial
            <input type="date" value={initialDate} onChange={(e) => setInitialDate(e.target.value)} />
          </label>
          <button type="submit" disabled={submitting}>
            Criar conta
          </button>
        </form>
      )}

      {loading && <Loading />}
      {error && <ErrorMessage message={error} />}

      {!loading && (
        <table>
          <thead>
            <tr>
              <th>Nome</th>
              <th>Tipo</th>
              <th>Moeda</th>
              <th>Saldo</th>
              <th>Convertido</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {accounts.map((account) => (
              <tr key={account.id} className={account.is_active ? '' : 'muted'}>
                <td>{account.name}</td>
                <td>{account.account_type}</td>
                <td>{account.currency}</td>
                <td>{formatMoney(account.balance, account.currency)}</td>
                <td>
                  {account.balance_in_base_currency !== null
                    ? formatMoney(account.balance_in_base_currency, account.base_currency)
                    : 'sem taxa'}
                </td>
                <td>{account.is_active ? 'Ativa' : 'Arquivada'}</td>
                <td>
                  <button className="link-button" onClick={() => toggleArchive(account)}>
                    {account.is_active ? 'Arquivar' : 'Reativar'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
