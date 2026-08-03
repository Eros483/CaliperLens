export type MessageType = 'user' | 'ai' | 'error';

export type ConnectionStatus = 'checking' | 'connected' | 'error';

export interface Message {
  id: number;
  type: MessageType;
  content: string;
  timestamp: Date;
}

export interface ChatRequest {
  query: string;
  session_id: string;
}

export interface ChatResponse {
  response: string;
  success: boolean;
}
