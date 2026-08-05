export type MessageType = 'user' | 'ai' | 'error';

export type ConnectionStatus = 'checking' | 'connected' | 'error';

export interface Message {
  id: number;
  type: MessageType;
  content: string;
  timestamp: Date;
  chartBase64?: string;
  chartTitle?: string;
}

export interface ChatRequest {
  query: string;
  session_id: string;
}

export interface ChatResponse {
  response: string;
  success: boolean;
  chart_base64?: string;
  chart_title?: string;
}
