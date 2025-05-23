'use client'

import { Message } from '@/types'
import { BlockMath, InlineMath } from 'react-katex'
import 'katex/dist/katex.min.css'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

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
    // Safely match inline ($...$) and block ($$...$$) LaTeX without grabbing currency
    const parts = content.split(/(\$\$[^$]*\$\$|\$(?!\d)[^$\n]*?\$)/g)

    return parts.map((part, i) => {
      try {
        if (part.startsWith('$$') && part.endsWith('$$')) {
          return <BlockMath key={i}>{part.slice(2, -2)}</BlockMath>
        } else if (part.startsWith('$') && part.endsWith('$')) {
          return <InlineMath key={i}>{part.slice(1, -1)}</InlineMath>
        } else {
          return <ReactMarkdown key={i} remarkPlugins={[remarkGfm]}>
            {part}
          </ReactMarkdown>
        }
      } catch (err) {
        console.error('Math render failed:', err)
        return <ReactMarkdown key={i} remarkPlugins={[remarkGfm]}>
          {part}
        </ReactMarkdown>
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
          {new Date(message.timestamp).toLocaleTimeString()}
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
