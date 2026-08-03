import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ChatMessage from '../components/ChatMessage';
import type { Message } from '../types';

describe('ChatMessage', () => {
  const baseMessage: Omit<Message, 'type' | 'content'> = {
    id: 1,
    timestamp: new Date('2025-01-01T12:00:00'),
  };

  it('renders user message', () => {
    render(<ChatMessage message={{ ...baseMessage, type: 'user', content: 'Hello' }} />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('renders ai message', () => {
    render(<ChatMessage message={{ ...baseMessage, type: 'ai', content: 'Hi there' }} />);
    expect(screen.getByText('Hi there')).toBeInTheDocument();
  });

  it('renders error message', () => {
    render(
      <ChatMessage message={{ ...baseMessage, type: 'error', content: 'Something went wrong' }} />
    );
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('shows timestamp', () => {
    render(<ChatMessage message={{ ...baseMessage, type: 'ai', content: 'test' }} />);
    expect(screen.getByText('12:00:00 PM')).toBeInTheDocument();
  });
});
