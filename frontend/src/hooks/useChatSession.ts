import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface PersistedMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
}

export interface PersistedSession {
  localId: number
  serverSessionId?: number
  title: string
  courseId: number
  courseName: string
  agentId?: number
  messages: PersistedMessage[]
}

interface SessionState {
  sessions: PersistedSession[]
  activeId: number | null
  setSessions: (sessions: PersistedSession[]) => void
  setActiveId: (id: number | null) => void
  upsertSession: (session: PersistedSession) => void
  updateSession: (localId: number, updater: (s: PersistedSession) => PersistedSession) => void
  removeSession: (localId: number) => void
}

function migrateSessions(raw: unknown): { sessions: PersistedSession[]; activeId: number | null } {
  if (!raw || typeof raw !== 'object') return { sessions: [], activeId: null }
  const state = raw as Record<string, unknown>
  const sessions = Array.isArray(state.sessions)
    ? state.sessions.filter(
        (s): s is PersistedSession =>
          s !== null && typeof s === 'object' && 'localId' in s && typeof (s as any).localId === 'number'
      )
    : []
  const activeId =
    typeof state.activeId === 'number' && sessions.some((s) => s.localId === state.activeId)
      ? (state.activeId as number)
      : sessions[0]?.localId ?? null
  return { sessions, activeId }
}

function onRehydrateStorage() {
  return (state, error) => {
    if (error || !state) return
    const migrated = migrateSessions(state)
    if (migrated.sessions.length !== state.sessions.length || migrated.activeId !== state.activeId) {
      state.sessions.splice(0, state.sessions.length, ...migrated.sessions)
      state.activeId = migrated.activeId
    }
  }
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set) => ({
      sessions: [],
      activeId: null,
      setSessions: (sessions) => set({ sessions }),
      setActiveId: (id) => set({ activeId: id }),
      upsertSession: (session) =>
        set((state) => {
          const idx = state.sessions.findIndex((s) => s.localId === session.localId)
          if (idx >= 0) {
            const next = [...state.sessions]
            next[idx] = session
            return { sessions: next }
          }
          return { sessions: [...state.sessions, session] }
        }),
      updateSession: (localId, updater) =>
        set((state) => {
          const idx = state.sessions.findIndex((s) => s.localId === localId)
          if (idx < 0) return state
          const next = [...state.sessions]
          next[idx] = updater(next[idx])
          return { sessions: next }
        }),
      removeSession: (localId) =>
        set((state) => {
          const next = state.sessions.filter((s) => s.localId !== localId)
          return {
            sessions: next,
            activeId: state.activeId === localId ? (next[0]?.localId ?? null) : state.activeId,
          }
        }),
    }),
    { name: 'eduai-chat-sessions', onRehydrateStorage: onRehydrateStorage }
  )
)
