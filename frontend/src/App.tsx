import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { ProfileProvider } from './context/ProfileContext'
import { Dashboard } from './pages/Dashboard'
import { Transactions } from './pages/Transactions'
import { Recurring } from './pages/Recurring'
import { Budgets } from './pages/Budgets'
import { Forecast } from './pages/Forecast'
import { Accounts } from './pages/Accounts'
import { Settings } from './pages/Settings'

function App() {
  return (
    <ProfileProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="transactions" element={<Transactions />} />
            <Route path="recurring" element={<Recurring />} />
            <Route path="budgets" element={<Budgets />} />
            <Route path="forecast" element={<Forecast />} />
            <Route path="accounts" element={<Accounts />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ProfileProvider>
  )
}

export default App
