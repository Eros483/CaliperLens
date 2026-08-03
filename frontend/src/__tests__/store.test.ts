import { describe, it, expect } from 'vitest';
import { useChatStore } from '../store/chat';

describe('useChatStore', () => {
  it('starts with empty messages', () => {
    const { messages } = useChatStore.getState();
    expect(messages).toEqual([]);
  });

  it('adds messages', () => {
    const store = useChatStore.getState();
    store.addMessage({ id: 1, type: 'user', content: 'hello', timestamp: new Date() });
    expect(useChatStore.getState().messages).toHaveLength(1);
    expect(useChatStore.getState().messages[0].content).toBe('hello');
  });

  it('sets loading state', () => {
    useChatStore.getState().setIsLoading(true);
    expect(useChatStore.getState().isLoading).toBe(true);
  });

  it('sets connection status', () => {
    useChatStore.getState().setConnectionStatus('connected');
    expect(useChatStore.getState().connectionStatus).toBe('connected');
  });

  it('clears messages and generates new sessionId', () => {
    const store = useChatStore.getState();
    store.addMessage({ id: 1, type: 'user', content: 'test', timestamp: new Date() });
    store.setSessionId('old-session');
    store.clearMessages();
    const state = useChatStore.getState();
    expect(state.messages).toEqual([]);
    expect(state.sessionId).not.toBe('old-session');
    expect(state.sessionId).toBeTruthy();
  });
});
