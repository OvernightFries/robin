import { create } from 'zustand'
import { Message, AnalysisContext, ChatState, ChatActions } from '@/types'

const useChatStore = create<ChatState & { actions: ChatActions }>((set) => ({
  messages: [],
  loading: false,
  error: null,
  context: null,
  actions: {
    addMessage: (message: Message) =>
      set((state) => ({
        messages: [...state.messages, message]
      })),
    setLoading: (loading: boolean) =>
      set(() => ({
        loading
      })),
    setError: (error: string | null) =>
      set(() => ({
        error
      })),
    setContext: (context: AnalysisContext) =>
      set(() => ({
        context
      })),
    clearMessages: () =>
      set(() => ({
        messages: []
      }))
  }
}))

export default useChatStore 
