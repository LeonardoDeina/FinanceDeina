import { useEffect, useState, type FormEvent } from 'react'
import { api } from '../api/client'
import type { Category, ExchangeRate, MonthlyClosing, Profile } from '../api/types'
import { formatDate } from '../lib/money'
import { ErrorMessage } from '../components/Feedback'
import { useProfile } from '../context/ProfileContext'

export function Settings() {
  const { profile, currencies, refresh } = useProfile()
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const [profileForm, setProfileForm] = useState<Partial<Profile>>({})
  useEffect(() => {
    if (profile) setProfileForm(profile)
  }, [profile])

  async function saveProfile(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await api.put('/profile', profileForm)
      refresh()
      setMessage('Perfil atualizado.')
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Configurações</h1>
      </div>

      {error && <ErrorMessage message={error} />}
      {message && <p className="feedback">{message}</p>}

      <section className="card">
        <h2>Perfil</h2>
        <form className="form" onSubmit={saveProfile}>
          <label>
            Nome
            <input value={profileForm.name ?? ''} onChange={(e) => setProfileForm({ ...profileForm, name: e.target.value })} />
          </label>
          <label>
            Moeda-base
            <select value={profileForm.base_currency ?? ''} onChange={(e) => setProfileForm({ ...profileForm, base_currency: e.target.value })}>
              {currencies.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.code} — {c.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Fuso horário
            <input value={profileForm.timezone ?? ''} onChange={(e) => setProfileForm({ ...profileForm, timezone: e.target.value })} />
          </label>
          <button type="submit">Salvar</button>
        </form>
      </section>

      <CategoriesSection />
      <CurrenciesSection />
      <ExchangeRatesSection />
      <ClosingSection />
      <BackupSection />
    </div>
  )
}

function CategoriesSection() {
  const [categories, setCategories] = useState<Category[]>([])
  const [name, setName] = useState('')
  const [type, setType] = useState<'INCOME' | 'EXPENSE'>('EXPENSE')
  const [error, setError] = useState<string | null>(null)

  function load() {
    api.get<Category[]>('/categories').then(setCategories)
  }
  useEffect(load, [])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await api.post('/categories', { name, category_type: type })
      setName('')
      load()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <section className="card">
      <h2>Categorias</h2>
      {error && <ErrorMessage message={error} />}
      <form className="form inline" onSubmit={handleSubmit}>
        <input placeholder="Nome da categoria" value={name} onChange={(e) => setName(e.target.value)} required />
        <select value={type} onChange={(e) => setType(e.target.value as 'INCOME' | 'EXPENSE')}>
          <option value="EXPENSE">Despesa</option>
          <option value="INCOME">Receita</option>
        </select>
        <button type="submit">Adicionar</button>
      </form>
      <ul className="chip-list">
        {categories.map((c) => (
          <li key={c.id} className={`chip ${c.category_type === 'INCOME' ? 'chip-income' : 'chip-expense'}`}>
            {c.name}
          </li>
        ))}
      </ul>
    </section>
  )
}

function CurrenciesSection() {
  const { currencies, refresh } = useProfile()
  const [code, setCode] = useState('')
  const [name, setName] = useState('')
  const [symbol, setSymbol] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await api.post('/currencies', { code, name, symbol })
      setCode('')
      setName('')
      setSymbol('')
      refresh()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <section className="card">
      <h2>Moedas</h2>
      <p className="muted">Cadastre todas as moedas em que você recebe ou gasta (ex.: EUR, USD, BRL).</p>
      {error && <ErrorMessage message={error} />}
      <form className="form inline" onSubmit={handleSubmit}>
        <input placeholder="Código (ex: JPY)" maxLength={3} value={code} onChange={(e) => setCode(e.target.value.toUpperCase())} required />
        <input placeholder="Nome" value={name} onChange={(e) => setName(e.target.value)} required />
        <input placeholder="Símbolo" value={symbol} onChange={(e) => setSymbol(e.target.value)} required />
        <button type="submit">Adicionar moeda</button>
      </form>
      <ul className="chip-list">
        {currencies.map((c) => (
          <li key={c.code} className="chip">
            {c.symbol} {c.code} — {c.name}
          </li>
        ))}
      </ul>
    </section>
  )
}

function ExchangeRatesSection() {
  const { currencies } = useProfile()
  const [rates, setRates] = useState<ExchangeRate[]>([])
  const [baseCode, setBaseCode] = useState('EUR')
  const [quoteCode, setQuoteCode] = useState('USD')
  const [rateDate, setRateDate] = useState(new Date().toISOString().slice(0, 10))
  const [rate, setRate] = useState('')
  const [error, setError] = useState<string | null>(null)

  function load() {
    api.get<ExchangeRate[]>('/exchange-rates').then(setRates)
  }
  useEffect(load, [])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await api.post('/exchange-rates', { base_code: baseCode, quote_code: quoteCode, rate_date: rateDate, rate })
      setRate('')
      load()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <section className="card">
      <h2>Taxas de câmbio</h2>
      <p className="muted">
        A conversão automática em tempo real não faz parte do V1 (por design); cadastre aqui a taxa vigente para cada
        par de moedas. O sistema usa a taxa mais recente na data de referência e também tenta uma ponte pela sua
        moeda-base quando o par exato não existir.
      </p>
      {error && <ErrorMessage message={error} />}
      <form className="form inline" onSubmit={handleSubmit}>
        <select value={baseCode} onChange={(e) => setBaseCode(e.target.value)}>
          {currencies.map((c) => (
            <option key={c.code} value={c.code}>
              {c.code}
            </option>
          ))}
        </select>
        <span>vale</span>
        <input type="number" step="0.00000001" placeholder="taxa" value={rate} onChange={(e) => setRate(e.target.value)} required />
        <select value={quoteCode} onChange={(e) => setQuoteCode(e.target.value)}>
          {currencies.map((c) => (
            <option key={c.code} value={c.code}>
              {c.code}
            </option>
          ))}
        </select>
        <input type="date" value={rateDate} onChange={(e) => setRateDate(e.target.value)} required />
        <button type="submit">Salvar taxa</button>
      </form>
      <table>
        <thead>
          <tr>
            <th>Data</th>
            <th>Par</th>
            <th>Taxa</th>
            <th>Origem</th>
          </tr>
        </thead>
        <tbody>
          {rates.map((r) => (
            <tr key={r.id}>
              <td>{formatDate(r.rate_date)}</td>
              <td>
                {r.base_code} → {r.quote_code}
              </td>
              <td>{r.rate}</td>
              <td>{r.source}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}

function ClosingSection() {
  const [month, setMonth] = useState(() => new Date().toISOString().slice(0, 8) + '01')
  const [closing, setClosing] = useState<MonthlyClosing | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function preview() {
    setError(null)
    try {
      setClosing(await api.get<MonthlyClosing>(`/closings/${month}/preview`))
    } catch (err) {
      setError((err as Error).message)
    }
  }

  async function close() {
    setError(null)
    try {
      setClosing(await api.post<MonthlyClosing>(`/closings/${month}/close`))
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <section className="card">
      <h2>Fechamento mensal</h2>
      <div className="form inline">
        <input type="month" value={month.slice(0, 7)} onChange={(e) => setMonth(`${e.target.value}-01`)} />
        <button onClick={preview}>Pré-visualizar</button>
        <button onClick={close}>Fechar mês</button>
      </div>
      {error && <ErrorMessage message={error} />}
      {closing && (
        <ul>
          <li>Status: {closing.status}</li>
          <li>Economia planejada: {closing.planned_savings}</li>
          <li>Economia realizada: {closing.actual_savings}</li>
        </ul>
      )}
    </section>
  )
}

function BackupSection() {
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function triggerBackup() {
    setError(null)
    setMessage(null)
    try {
      const res = await api.post<{ filename: string }>('/backup')
      setMessage(`Backup criado: ${res.filename}`)
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <section className="card">
      <h2>Backup e exportação</h2>
      <div className="button-row">
        <button onClick={triggerBackup}>Gerar backup agora</button>
        <a href={`${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'}/transactions/export.csv`}>
          <button type="button">Exportar transações (CSV)</button>
        </a>
      </div>
      {message && <p className="feedback">{message}</p>}
      {error && <ErrorMessage message={error} />}
    </section>
  )
}
