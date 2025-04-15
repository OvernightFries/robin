'use client'

import { useState } from 'react'
import ChatBox from '@/components/ChatBox'
import ModelDownloadProgress from '@/components/ModelDownloadProgress'
import Image from 'next/image'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Message } from '@/types'
import LoadingState from '@/components/LoadingState'
import { APIError, api } from '@/lib/api'
import ChatMessage from '@/components/ChatMessage'

interface ExtendedMessage extends Message {
  className?: string;
}

export default function Home() {
  const router = useRouter()
  const [symbol, setSymbol] = useState<string>('')
  const [messages, setMessages] = useState<ExtendedMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [modelStatus, setModelStatus] = useState<'downloading' | 'ready' | 'error'>('ready')
  const [currentSymbol, setCurrentSymbol] = useState<string>('')

  const initializeTicker = async (symbol: string) => {
    try {
      setLoading(true);
      const data = await api.initializeTicker(symbol);
      setCurrentSymbol(symbol);
      setMessages([{
        role: 'assistant',
        content: data.message,
        timestamp: new Date(),
        marketContext: data.market_context,
        knowledgeContext: data.options_context
      }]);
    } catch (error) {
      console.error('Error initializing ticker:', error);
      const errorMessage = error instanceof APIError
        ? error.message
        : 'Sorry, there was an error initializing the ticker. Please try again.';
      setMessages([{
        role: 'assistant',
        content: errorMessage,
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  }

  const handleSymbolSubmit = async (submittedSymbol: string) => {
    setSymbol(submittedSymbol.toUpperCase())
    setLoading(true)
    try {
      await initializeTicker(submittedSymbol.toUpperCase())
    } finally {
      setLoading(false)
    }
  }

  const handleSendMessage = async (content: string) => {
    if (!currentSymbol) {
      setMessages([{
        role: 'assistant',
        content: 'Please enter a stock symbol first.',
        timestamp: new Date()
      }]);
      return;
    }

    try {
      setLoading(true);
      const data = await api.query({
        symbol: currentSymbol,
        query: content
      });

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
        marketContext: data.market_context,
        knowledgeContext: data.knowledge_context
      }]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = error instanceof APIError
        ? error.message
        : 'Sorry, there was an error processing your request. Please try again.';
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: errorMessage,
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  }

  const handleCompanyClick = async (ticker: string) => {
    setSymbol(ticker)
    await initializeTicker(ticker)
  }

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const input = form.querySelector('input') as HTMLInputElement;
    const symbol = input.value.trim();

    if (symbol) {
      await handleSymbolSubmit(symbol);
      router.push(`/analyze/${symbol}`);
    }
  };

  return (
    <main className="min-h-screen bg-wizard-background text-wizard-text-primary overflow-hidden">
      {/* Gradient Background */}
      <div className="absolute inset-0 bg-gradient-radial from-wizard-background-lighter to-transparent opacity-50 z-0" />

      {/* Floating Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(30)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-wizard-green rounded-full animate-float"
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
      <div className="relative z-10">
        {/* Navigation */}
        <nav className="fixed top-0 left-0 right-0 bg-wizard-background/80 backdrop-blur-xl border-b border-wizard-neutral-dark/30">
          <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
            <div className="text-2xl font-bold wizard-gradient">
              robin
            </div>
            <Link
              href="/docs"
              className="px-6 py-2 rounded-lg text-sm font-medium text-wizard-green hover:text-wizard-accent transition-colors"
            >
              Documentation →
            </Link>
          </div>
        </nav>

        {/* Hero Section */}
        <section className="pt-32 pb-20 px-6">
          <div className="max-w-7xl mx-auto text-center">
            <h1 className="text-6xl font-bold mb-8 wizard-gradient">
              Meet Robin,<br />Your Personal Quant
            </h1>
            <p className="text-2xl text-wizard-text-muted mb-12 max-w-2xl mx-auto">
              Institutional-grade options analysis powered by artificial intelligence
            </p>
            <form onSubmit={handleAnalyze} className="inline-flex items-center gap-4 bg-wizard-background-lighter/50 p-1 rounded-2xl backdrop-blur border border-wizard-neutral-dark/30">
              <input
                type="text"
                placeholder="Enter any stock symbol..."
                className="input-field min-w-[300px]"
              />
              <button type="submit" className="wizard-button">
                Analyze
              </button>
            </form>
          </div>
        </section>

        {/* Analysis Section */}
        <section className="py-20 px-6 bg-wizard-background-lighter/30">
          <div className="max-w-6xl mx-auto">
            <div className="flex flex-col gap-8">
              {loading ? (
                <LoadingState />
              ) : messages.length > 0 ? (
                <div className="space-y-6">
                  {messages.map((message, index) => (
                    <ChatMessage key={index} message={message} />
                  ))}
                </div>
              ) : (
                <div className="text-center text-wizard-text-muted">
                  Enter a stock symbol to begin analysis
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Future Plans */}
        <section className="py-20 px-6 bg-[#0A2518]/10">
          <div className="max-w-6xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-12 wizard-gradient">
              Future Roadmap
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                {
                  title: "QuantWorld Integration",
                  icon: (
                    <svg className="w-6 h-6 text-[#00ff9d]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  ),
                  features: [
                    "Advanced backtesting engine",
                    "Custom strategy builder",
                    "Real-time market simulation"
                  ]
                },
                {
                  title: "Robinhood Integration",
                  icon: (
                    <svg className="w-6 h-6 text-[#00ff9d]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  ),
                  features: [
                    "One-click trade execution",
                    "Portfolio synchronization",
                    "Automated trading strategies"
                  ]
                },
                {
                  title: "Backtesting Suite",
                  icon: (
                    <svg className="w-6 h-6 text-[#00ff9d]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  ),
                  features: [
                    "Historical data analysis",
                    "Strategy optimization",
                    "Risk metrics reporting"
                  ]
                }
              ].map((feature, index) => (
                <div key={index} className="feature-card glass-card rounded-2xl p-8 glow-effect">
                  <div className="w-12 h-12 rounded-xl bg-[#0A2518] flex items-center justify-center mb-6">
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-semibold mb-4 text-white">{feature.title}</h3>
                  <ul className="space-y-3 text-[#B4C4BE]">
                    {feature.features.map((item, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-[#00D884]">•</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </main>
  )
}
