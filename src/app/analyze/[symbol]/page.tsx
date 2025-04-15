'use client'

import { useEffect, useState, useRef } from 'react'
import { useParams } from 'next/navigation'
import ChatMessage from '@/components/ChatMessage'
import { Message } from '@/lib/constants'
import { api } from '@/lib/api'

export default function AnalyzePage() {
  const params = useParams()
  const symbol = params.symbol as string
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [input, setInput] = useState('')
  const [connectionError, setConnectionError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const checkConnection = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/health`)
      if (!res.ok) throw new Error('Backend server is not responding')
      setConnectionError(null)
    } catch (error) {
      setConnectionError('Unable to connect to the backend server. Please make sure it is running on http://localhost:8000')
    }
  }

  useEffect(() => {
    checkConnection()
  }, [])

  useEffect(() => {
    const initializeTicker = async () => {
      try {
        const data = await api.initializeTicker(symbol);

        // Format market data message
        const marketData = data.market_context;
        let marketMessage = `Welcome! I've loaded ${symbol} data:\n\n`;

        // Current Data
        if (marketData?.current_data) {
          marketMessage += `Current Data:\n`;
          marketMessage += `• Price: $${marketData.current_data.price?.toFixed(2) || 'N/A'}\n`;
          marketMessage += `• Volume: ${marketData.current_data.volume?.toLocaleString() || 'N/A'}\n`;
          marketMessage += `• Bid: $${marketData.current_data.bid?.toFixed(2) || 'N/A'}\n`;
          marketMessage += `• Ask: $${marketData.current_data.ask?.toFixed(2) || 'N/A'}\n\n`;
        }

        // Daily Data
        if (marketData?.daily_data) {
          marketMessage += `Daily Data:\n`;
          marketMessage += `• Open: $${marketData.daily_data.open?.[marketData.daily_data.open.length - 1]?.toFixed(2) || 'N/A'}\n`;
          marketMessage += `• High: $${marketData.daily_data.high?.[marketData.daily_data.high.length - 1]?.toFixed(2) || 'N/A'}\n`;
          marketMessage += `• Low: $${marketData.daily_data.low?.[marketData.daily_data.low.length - 1]?.toFixed(2) || 'N/A'}\n`;
          marketMessage += `• Close: $${marketData.daily_data.close?.[marketData.daily_data.close.length - 1]?.toFixed(2) || 'N/A'}\n`;
          marketMessage += `• Volume: ${marketData.daily_data.volume?.[marketData.daily_data.volume.length - 1]?.toLocaleString() || 'N/A'}\n\n`;
        }

        // Technical Indicators
        if (marketData?.technical_indicators) {
          const tech = marketData.technical_indicators;
          marketMessage += `Technical Indicators:\n`;

          // Trend Indicators
          if (tech.trend) {
            marketMessage += `• SMA 20: ${tech.trend.sma_20?.[tech.trend.sma_20.length - 1]?.toFixed(2) || 'N/A'}\n`;
            marketMessage += `• SMA 50: ${tech.trend.sma_50?.[tech.trend.sma_50.length - 1]?.toFixed(2) || 'N/A'}\n`;
            marketMessage += `• EMA 20: ${tech.trend.ema_20?.[tech.trend.ema_20.length - 1]?.toFixed(2) || 'N/A'}\n`;
            marketMessage += `• Trend Strength: ${tech.trend.trend_strength?.toFixed(2) || 'N/A'}%\n`;
          }

          // Momentum Indicators
          if (tech.momentum) {
            marketMessage += `• RSI: ${tech.momentum.rsi?.[tech.momentum.rsi.length - 1]?.toFixed(1) || 'N/A'}\n`;
            if (tech.momentum.macd) {
              marketMessage += `• MACD: ${tech.momentum.macd.macd_line?.[tech.momentum.macd.macd_line.length - 1]?.toFixed(2) || 'N/A'}\n`;
              marketMessage += `• MACD Signal: ${tech.momentum.macd.signal_line?.[tech.momentum.macd.signal_line.length - 1]?.toFixed(2) || 'N/A'}\n`;
              marketMessage += `• MACD Histogram: ${tech.momentum.macd.histogram?.[tech.momentum.macd.histogram.length - 1]?.toFixed(2) || 'N/A'}\n`;
            }
          }

          // Volatility Indicators
          if (tech.volatility?.bollinger_bands) {
            const bb = tech.volatility.bollinger_bands;
            marketMessage += `• BB Upper: ${bb.upper?.[bb.upper.length - 1]?.toFixed(2) || 'N/A'}\n`;
            marketMessage += `• BB Middle: ${bb.middle?.[bb.middle.length - 1]?.toFixed(2) || 'N/A'}\n`;
            marketMessage += `• BB Lower: ${bb.lower?.[bb.lower.length - 1]?.toFixed(2) || 'N/A'}\n`;
          }
        }

        marketMessage += `\nWhat would you like to analyze?`;

        setMessages([{
          role: 'assistant',
          content: marketMessage,
          timestamp: new Date()
        }]);
      } catch (error) {
        setMessages([{
          role: 'assistant',
          content: `Error: ${error instanceof Error ? error.message : 'Failed to initialize ticker'}. Please make sure the backend server is running.`,
          timestamp: new Date()
        }]);
      }
    };

    initializeTicker();
  }, [symbol]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const data = await api.query({
        symbol,
        query: input
      });

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response,
        timestamp: new Date()
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to send message'}. Please make sure the backend server is running.`,
        timestamp: new Date()
      }]);
    }
    setLoading(false);
  };

  return (
    <main className="min-h-screen bg-[#0A1512] text-white">
      {/* Gradient Background */}
      <div className="absolute inset-0 bg-gradient-radial from-[#132320] to-transparent opacity-50 z-0" />

      {/* Floating Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(30)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-[#00ff9d] rounded-full animate-float"
            style={{
              top: `${Math.random() * 100}%`,
              left: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${5 + Math.random() * 5}s`
            }}
          />
        ))}
      </div>

      {/* Main Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-6 py-24">
        {/* Connection Status */}
        {connectionError && (
          <div className="mb-4 p-4 bg-red-500/20 border border-red-500/50 rounded-lg text-red-300">
            {connectionError}
          </div>
        )}

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold wizard-gradient mb-2">
            Analyzing {symbol}
          </h1>
          <p className="text-[#4D6B5D]">
            Ask me anything about {symbol}'s options, technicals, or fundamentals
          </p>
        </div>

        {/* Chat Interface */}
        <div className="flex flex-col h-[calc(100vh-300px)]">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto space-y-6 mb-6">
            {messages.map((message, index) => (
              <ChatMessage key={index} message={message} />
            ))}
            {loading && (
              <div className="flex items-start gap-6">
                <div className="w-10 h-10 rounded-xl bg-[#0A2518] flex items-center justify-center flex-shrink-0">
                  <span className="text-[#00ff9d]">R</span>
                </div>
                <div className="glass-card rounded-2xl p-6 bg-[#0A2518]/50">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 bg-[#00ff9d] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-[#00ff9d] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-[#00ff9d] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Form */}
          <form onSubmit={handleSendMessage} className="glass-card rounded-2xl p-4">
            <div className="flex gap-4">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about options, technicals, or fundamentals..."
                className="input-field flex-1"
                disabled={!!connectionError}
              />
              <button
                type="submit"
                disabled={loading || !!connectionError}
                className="wizard-button self-stretch"
              >
                Send
              </button>
            </div>
          </form>
        </div>
      </div>
    </main>
  )
} 
