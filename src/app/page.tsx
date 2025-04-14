'use client'

import { useState } from 'react'
import ChatBox from '@/components/ChatBox'
import ModelDownloadProgress from '@/components/ModelDownloadProgress'
import Image from 'next/image'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { SAMPLE_CONVERSATION, Message } from '@/lib/constants'

export default function Home() {
  const router = useRouter()
  const [symbol, setSymbol] = useState<string>('')
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [modelStatus, setModelStatus] = useState<'downloading' | 'ready' | 'error'>('ready')

  const initializeTicker = async (symbol: string) => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/initialize_ticker?symbol=${symbol}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      const data = await res.json();

      // Add welcome message with market context
      setMessages([{
        role: 'assistant',
        content: `Welcome! I've loaded ${symbol} data:
• Current Price: $${data.market_context.current_price}
• Open: $${data.market_context.open}
• High: $${data.market_context.high}
• Low: $${data.market_context.low}
• Volume: ${data.market_context.volume.toLocaleString()}
• RSI: ${data.market_context.rsi.toFixed(1)}
• MACD: ${data.market_context.macd.toFixed(2)}

What would you like to analyze?`,
        timestamp: new Date()
      }]);
    } catch (error) {
      setMessages([{
        role: 'assistant',
        content: `Welcome! I'm ready to help you analyze ${symbol}. What would you like to know?`,
        timestamp: new Date()
      }]);
    }
  };

  const handleSymbolSubmit = async (submittedSymbol: string) => {
    setSymbol(submittedSymbol.toUpperCase())
    await initializeTicker(submittedSymbol.toUpperCase())
  }

  const handleSendMessage = async (content: string) => {
    // If content looks like a stock symbol and we don't have a symbol set yet
    if (!symbol && content.match(/^[A-Za-z]{1,5}$/)) {
      return handleSymbolSubmit(content)
    }

    const userMessage: Message = {
      role: 'user',
      content,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMessage])
    setLoading(true)

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbol,
          query: content
        }),
      })
      const data = await res.json()

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response,
        timestamp: new Date()
      }])
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${error}`,
        timestamp: new Date()
      }])
    }
    setLoading(false)
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
    <main className="min-h-screen bg-[#0A1512] text-white overflow-hidden">
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
      <div className="relative z-10">
        {/* Navigation */}
        <nav className="fixed top-0 left-0 right-0 bg-[#0A1512]/80 backdrop-blur-xl border-b border-[#1C3830]/30">
          <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
            <div className="text-2xl font-bold wizard-gradient">
              robin
            </div>
            <Link
              href="/docs"
              className="px-6 py-2 rounded-lg text-sm font-medium text-[#00ff9d] hover:text-[#00D884] transition-colors"
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
            <p className="text-2xl text-[#4D6B5D] mb-12 max-w-2xl mx-auto">
              Institutional-grade options analysis powered by artificial intelligence
            </p>
            <form onSubmit={handleAnalyze} className="inline-flex items-center gap-4 bg-[#132320]/50 p-1 rounded-2xl backdrop-blur border border-[#1C3830]/30">
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

        {/* Sample Analysis */}
        <section className="py-20 px-6 bg-[#132320]/30">
          <div className="max-w-6xl mx-auto">
            <div className="flex flex-col gap-8">
              <div className="space-y-6">
                <div className="flex items-start gap-6">
                  <div className="w-10 h-10 rounded-xl bg-[#132320]/80 flex items-center justify-center flex-shrink-0">
                    <span className="text-[#4D6B5D]">Q</span>
                  </div>
                  <div className="text-xl text-[#B4C4BE] leading-relaxed">
                    Analyze AAPL options chain for potential iron condor setup considering current IV and earnings.
                  </div>
                </div>

                <div className="flex items-start gap-6">
                  <div className="w-10 h-10 rounded-xl bg-[#0A2518] flex items-center justify-center flex-shrink-0">
                    <span className="text-[#00ff9d]">R</span>
                  </div>
                  <div className="flex-1">
                    <div className="glass-card rounded-2xl p-8 space-y-8">
                      {/* Market Context */}
                      <div>
                        <h3 className="text-[#00ff9d] text-lg font-medium mb-4">Market Context</h3>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                          {[
                            { label: 'IV Percentile', value: '67th' },
                            { label: 'Current Price', value: '$169.75' },
                            { label: 'Expected Move', value: '±$8.45' },
                            { label: 'Historical Vol', value: '22.4%' },
                            { label: 'Implied Vol', value: '28.7%' },
                            { label: 'Earnings', value: '35d' }
                          ].map((item, i) => (
                            <div key={i} className="bg-[#0A2518]/50 rounded-lg p-4">
                              <div className="text-[#4D6B5D] text-sm mb-1">{item.label}</div>
                              <div className="text-white font-medium">{item.value}</div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Trade Setup */}
                      <div>
                        <h3 className="text-[#00ff9d] text-lg font-medium mb-4">Iron Condor Setup</h3>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-3">
                            <div className="flex justify-between items-center text-sm">
                              <span className="text-[#4D6B5D]">Sell Put</span>
                              <span className="text-white">165 @ $2.15</span>
                              <span className="text-[#00D884]">Δ 0.32</span>
                            </div>
                            <div className="flex justify-between items-center text-sm">
                              <span className="text-[#4D6B5D]">Buy Put</span>
                              <span className="text-white">160 @ $1.10</span>
                              <span className="text-[#00D884]">Δ 0.22</span>
                            </div>
                          </div>
                          <div className="space-y-3">
                            <div className="flex justify-between items-center text-sm">
                              <span className="text-[#4D6B5D]">Sell Call</span>
                              <span className="text-white">175 @ $2.30</span>
                              <span className="text-[#00D884]">Δ 0.35</span>
                            </div>
                            <div className="flex justify-between items-center text-sm">
                              <span className="text-[#4D6B5D]">Buy Call</span>
                              <span className="text-white">180 @ $1.20</span>
                              <span className="text-[#00D884]">Δ 0.25</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Key Metrics */}
                      <div>
                        <h3 className="text-[#00ff9d] text-lg font-medium mb-4">Key Metrics</h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {[
                            { label: 'Max Profit', value: '$215' },
                            { label: 'Max Loss', value: '$285' },
                            { label: 'Prob. Profit', value: '72%' },
                            { label: 'Risk/Reward', value: '1.32' }
                          ].map((item, i) => (
                            <div key={i} className="bg-[#0A2518]/50 rounded-lg p-4">
                              <div className="text-[#4D6B5D] text-sm mb-1">{item.label}</div>
                              <div className="text-white font-medium">{item.value}</div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Risk Management */}
                      <div>
                        <h3 className="text-[#00ff9d] text-lg font-medium mb-4">Risk Management</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="bg-[#0A2518]/50 rounded-lg p-4">
                            <div className="text-[#4D6B5D] text-sm mb-2">Take Profit</div>
                            <div className="text-white">Close at 50% profit ($107.50)</div>
                          </div>
                          <div className="bg-[#0A2518]/50 rounded-lg p-4">
                            <div className="text-[#4D6B5D] text-sm mb-2">Stop Loss</div>
                            <div className="text-white">Exit at 2x credit ($430)</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
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
