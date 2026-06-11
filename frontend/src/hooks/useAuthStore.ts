import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: number
  username: string
  email: string
  full_name: string
  role: 'student' | 'teacher' | 'admin'
}

interface AuthState {
  hasHydrated: boolean
  token: string | null
  user: User | null
  setAuth: (token: string, user: User) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      hasHydrated: false,
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    {
      name: 'eduai-auth',
      onRehydrateStorage: () => (_state, error) => {
        if (!error) {
          useAuthStore.setState({ hasHydrated: true })
          return
        }
        useAuthStore.setState({ hasHydrated: true, token: null, user: null })
      },
    }
  )
)
