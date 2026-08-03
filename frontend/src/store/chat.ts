import { create } from 'zustand';
import type { Message, ConnectionStatus } from '../types';

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  connectionStatus: ConnectionStatus;
  sessionId: string;
}

interface ChatActions {
  addMessage: (message: Message) => void;
  setIsLoading: (loading: boolean) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;
  setSessionId: (id: string) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState & ChatActions>((set) => ({
  messages: [],
  isLoading: false,
  connectionStatus: 'checking',
  sessionId: '',

  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),

  setIsLoading: (isLoading) => set({ isLoading }),

  setConnectionStatus: (connectionStatus) => set({ connectionStatus }),

  setSessionId: (sessionId) => set({ sessionId }),

  clearMessages: () => {
    const newSessionId = crypto.randomUUID();
    localStorage.setItem('chat_session_id', newSessionId);
    set({ messages: [], sessionId: newSessionId });
  },
}));
