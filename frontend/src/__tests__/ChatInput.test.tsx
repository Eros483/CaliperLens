import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ChatInput from '../components/ChatInput';

describe('ChatInput', () => {
  it('renders textarea and send button', () => {
    render(<ChatInput onSendMessage={vi.fn()} disabled={false} />);
    expect(
      screen.getByPlaceholderText('Ask a question about your database...')
    ).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('button is disabled when input is empty', () => {
    render(<ChatInput onSendMessage={vi.fn()} disabled={false} />);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('calls onSendMessage on submit', () => {
    const onSend = vi.fn();
    render(<ChatInput onSendMessage={onSend} disabled={false} />);
    const textarea = screen.getByPlaceholderText('Ask a question about your database...');
    fireEvent.change(textarea, { target: { value: 'test query' } });
    fireEvent.submit(textarea.closest('form')!);
    expect(onSend).toHaveBeenCalledWith('test query');
  });

  it('disables textarea when disabled prop is true', () => {
    render(<ChatInput onSendMessage={vi.fn()} disabled={true} />);
    expect(screen.getByPlaceholderText('Ask a question about your database...')).toBeDisabled();
  });
});
