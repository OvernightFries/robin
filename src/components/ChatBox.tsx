import { useState, FormEvent } from 'react';
import ChatMessage from './ChatMessage';
import Loader from './Loader';
import { Message } from '@/types';

interface ChatBoxProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  loading?: boolean;
  placeholder?: string;
}

export default function ChatBox({ messages, onSendMessage, loading = false, placeholder = "Type your message..." }: ChatBoxProps) {
  const [message, setMessage] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (message.trim() && !loading) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto space-y-6 mb-6">
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message}
          />
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-[#182828] text-white border border-gray-800 px-6 py-4 rounded-2xl">
              <div className="flex items-center gap-3">
                <Loader />
                <span className="text-gray-400">Analyzing...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="chat-input">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder={placeholder}
          disabled={loading}
          className="flex-1"
        />
        <button
          type="submit"
          disabled={!message.trim() || loading}
        >
          {loading ? (
            <div className="w-6 h-6 border-2 border-black border-t-transparent rounded-full animate-spin" />
          ) : (
            'Send'
          )}
        </button>
      </form>
    </div>
  );
}
