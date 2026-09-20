import { NavLink, Outlet } from 'react-router-dom'
import { useProfile } from '../context/ProfileContext'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/transactions', label: 'Transações' },
  { to: '/recurring', label: 'Recorrências' },
  { to: '/budgets', label: 'Orçamentos' },
  { to: '/forecast', label: 'Previsão' },
  { to: '/accounts', label: 'Contas' },
  { to: '/settings', label: 'Configurações' },
]

export function Layout() {
  const { profile } = useProfile()

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">FinanceDeina</div>
        <nav>
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        {profile && (
          <div className="sidebar-footer">
            <div>{profile.name}</div>
            <div className="muted">Moeda-base: {profile.base_currency}</div>
          </div>
        )}
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
