'use client'

import { Message } from '@/lib/constants'
import { BlockMath, InlineMath } from 'react-katex'
import 'katex/dist/katex.min.css'

interface ChatMessageProps {
  message: Message
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'
  const avatarBg = isUser ? 'bg-[#132320]' : 'bg-[#0A2518]'
  const avatarText = isUser ? 'text-[#4D6B5D]' : 'text-[#00ff9d]'
  const avatarLetter = isUser ? 'U' : 'R'

  // Function to render message content with LaTeX support
  const renderContent = (content: string) => {
    const parts = content.split(/(\$\$.*?\$\$|\$.*?\$)/g)
    return parts.map((part, index) => {
      if (part.startsWith('$$') && part.endsWith('$$')) {
        return <BlockMath key={index}>{part.slice(2, -2)}</BlockMath>
      } else if (part.startsWith('$') && part.endsWith('$')) {
        return <InlineMath key={index}>{part.slice(1, -1)}</InlineMath>
      } else {
        return <span key={index}>{part}</span>
      }
    })
  }

  return (
    <div className={`flex items-start gap-6 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className={`w-10 h-10 rounded-xl ${avatarBg} flex items-center justify-center flex-shrink-0`}>
          <span className={avatarText}>{avatarLetter}</span>
        </div>
      )}
      <div className={`glass-card rounded-2xl p-6 max-w-3xl ${isUser ? 'bg-[#132320]/50' : 'bg-[#0A2518]/50'}`}>
        <div className="prose prose-invert max-w-none">
          {renderContent(message.content)}
        </div>
        <div className="mt-2 text-xs text-[#4D6B5D]">
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
      {isUser && (
        <div className={`w-10 h-10 rounded-xl ${avatarBg} flex items-center justify-center flex-shrink-0`}>
          <span className={avatarText}>{avatarLetter}</span>
        </div>
      )}
    </div>
  )
} 
