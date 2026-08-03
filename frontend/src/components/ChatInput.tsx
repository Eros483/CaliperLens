import { useState, useRef, useEffect, type FormEvent, type KeyboardEvent } from 'react';

interface ChatInputProps {
  onSendMessage: (text: string) => void;
  disabled: boolean;
}

function ChatInput({ onSendMessage, disabled }: ChatInputProps) {
  const [inputValue, setInputValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  }, [inputValue]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !disabled) {
      onSendMessage(inputValue);
      setInputValue('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form className="w-full" onSubmit={handleSubmit}>
      <div className="flex gap-3 items-end bg-gradient-to-r from-slate-50 to-rose-50 border border-rose-100 rounded-lg p-3 transition-all duration-200 focus-within:border-blue-600 focus-within:bg-gradient-to-r focus-within:from-white focus-within:to-rose-50 focus-within:ring-2 focus-within:ring-blue-600/10">
        <textarea
          ref={textareaRef}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your database..."
          disabled={disabled}
          rows={1}
          className="flex-1 border-none outline-none resize-none bg-transparent text-sm text-slate-900 leading-relaxed min-h-[24px] max-h-[150px] placeholder:text-slate-400 disabled:opacity-50 disabled:cursor-not-allowed font-[inherit]"
        />
        <button
          type="submit"
          disabled={disabled || !inputValue.trim()}
          className="w-9 h-9 rounded-md bg-gradient-to-br from-blue-600 to-blue-900 text-white flex items-center justify-center flex-shrink-0 transition-all duration-200 hover:not-disabled:-translate-y-0.5 hover:not-disabled:shadow-lg hover:not-disabled:shadow-blue-600/30 disabled:opacity-40 disabled:cursor-not-allowed active:not-disabled:translate-y-0"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" strokeWidth={2}>
            <path
              d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13"
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </div>
    </form>
  );
}

export default ChatInput;
