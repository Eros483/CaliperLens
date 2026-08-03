import type { ChatResponse } from '../types';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export async function checkHealth(): Promise<{ status: string; agent: string }> {
  const response = await fetch(`${API_URL}/api/v1/health`);
  if (!response.ok) throw new Error('Backend health check failed');
  return response.json();
}

export async function sendMessage(query: string, sessionId: string): Promise<ChatResponse> {
  const response = await fetch(`${API_URL}/api/v1/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, session_id: sessionId }),
  });

  if (!response.ok) throw new Error('Failed to send message');
  return response.json();
}
