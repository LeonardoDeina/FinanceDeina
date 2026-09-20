import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api } from '../api/client'
import type { Currency, Profile } from '../api/types'

interface ProfileContextValue {
  profile: Profile | null
  currencies: Currency[]
  loading: boolean
  refresh: () => void
}

const ProfileContext = createContext<ProfileContextValue>({
  profile: null,
  currencies: [],
  loading: true,
  refresh: () => {},
})

export function ProfileProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<Profile | null>(null)
  const [currencies, setCurrencies] = useState<Currency[]>([])
  const [loading, setLoading] = useState(true)
  const [version, setVersion] = useState(0)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    Promise.all([api.get<Profile>('/profile'), api.get<Currency[]>('/currencies')])
      .then(([p, c]) => {
        if (cancelled) return
        setProfile(p)
        setCurrencies(c)
      })
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [version])

  return (
    <ProfileContext.Provider value={{ profile, currencies, loading, refresh: () => setVersion((v) => v + 1) }}>
      {children}
    </ProfileContext.Provider>
  )
}

export function useProfile() {
  return useContext(ProfileContext)
}
