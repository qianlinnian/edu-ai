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
  token: string | null
  user: User | null
  setAuth: (token: string, user: User) => void
  logout: () => void
}

type PersistedAuthPayload = {
  state?: {
    token?: string | null
    user?: User | null
  }
}

function getInitialAuthState(): Pick<AuthState, 'token' | 'user'> {
  if (typeof window === 'undefined') {
    return { token: null, user: null }
  }

  try {
    const raw = window.localStorage.getItem('eduai-auth')
    if (!raw) {
      return { token: null, user: null }
    }

    const parsed = JSON.parse(raw) as PersistedAuthPayload
    return {
      token: parsed.state?.token ?? null,
      user: parsed.state?.user ?? null,
    }
  } catch {
    return { token: null, user: null }
  }
}

const initialAuthState = getInitialAuthState()

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: initialAuthState.token,
      user: initialAuthState.user,
      setAuth: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: 'eduai-auth' }
  )
)
