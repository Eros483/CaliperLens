import type { Message } from '../types';

interface ChatMessageProps {
  message: Message;
}

function ChatMessage({ message }: ChatMessageProps) {
  const avatarEmoji =
    message.type === 'user' ? '\u{1F464}' : message.type === 'error' ? '\u26A0\uFE0F' : '\u{1F916}';

  return (
    <div
      className={`flex gap-3 items-start animate-slide-in ${message.type === 'user' ? 'flex-row-reverse' : ''}`}
    >
      <div
        className={`w-9 h-9 rounded-full flex items-center justify-center text-lg flex-shrink-0 ${
          message.type === 'user'
            ? 'bg-gradient-to-br from-blue-600 to-blue-900 text-white'
            : message.type === 'error'
              ? 'bg-red-50 text-red-500'
              : 'bg-slate-100 text-blue-600'
        }`}
      >
        {avatarEmoji}
      </div>
      <div className="flex flex-col gap-1 max-w-full">
        <div
          className={`px-4 py-3 rounded-lg text-sm leading-relaxed border whitespace-pre-wrap break-words ${
            message.type === 'user'
              ? 'bg-gradient-to-br from-blue-600 to-blue-900 text-white border-transparent'
              : message.type === 'error'
                ? 'bg-red-50 text-red-900 border-red-200 border-l-2 border-l-red-500'
                : 'bg-gradient-to-r from-slate-50 to-rose-50 border-rose-100 text-slate-900'
          }`}
        >
          {message.content}
        </div>
        <span className="text-xs text-slate-400 pl-1 font-medium">
          {message.timestamp.toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
}

export default ChatMessage;
