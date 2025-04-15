'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import PriceChart from '@/components/PriceChart'
import { MarketContext } from '@/types'
import { initializeTicker } from '@/lib/api'

export default function HomePage() {
  const router = useRouter()
  const [symbol, setSymbol] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!symbol.trim() || isLoading) return

    setIsLoading(true)
    try {
      const ticker = symbol.trim().toUpperCase()
      console.log('Initializing ticker:', ticker)
      await initializeTicker(ticker)
      router.push(`/analyze/${ticker}`)
    } catch (error) {
      console.error('Failed to initialize ticker:', error)
      setIsLoading(false)
    }
  }

  const sampleMarketContext = {
    symbol: 'AAPL',
    current_data: {
      price: 185.32,
      volume: 45200000,
      timestamp: new Date().toISOString(),
      bid: 185.30,
      ask: 185.34,
      bid_size: 100,
      ask_size: 100
    },
    daily_data: {
      dates: Array.from({ length: 30 }, (_, i) =>
        new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString()
      ),
      prices: Array.from({ length: 30 }, (_, i) => {
        const basePrice = 180;
        const trend = i * 0.2; // Slight upward trend
        const noise = (Math.random() - 0.5) * 2; // Random noise
        return basePrice + trend + noise;
      }),
      volumes: Array.from({ length: 30 }, (_, i) => {
        const baseVolume = 40000000;
        const noise = (Math.random() - 0.5) * 10000000;
        return baseVolume + noise;
      })
    },
    technical_indicators: {
      sma_20: Array(30).fill(183),
      sma_50: Array(30).fill(182),
      rsi: Array(30).fill(65),
      macd: {
        macd: Array(30).fill(2),
        signal: Array(30).fill(1),
        histogram: Array(30).fill(1)
      },
      volume_ma: Array(30).fill(45000000)
    },
    high_52_week: 186.78,
    low_52_week: 181.23
  } as MarketContext;

  // Calculate percent change
  const percentChange = ((sampleMarketContext.daily_data.prices[29] - sampleMarketContext.daily_data.prices[0]) * 100 / sampleMarketContext.daily_data.prices[0]);

  return (
    <main className="min-h-screen flex flex-col">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 bg-background/80 backdrop-blur-xl border-b border-border/50 z-50">
        <div className="container flex justify-between items-center h-16">
          <Link href="/" className="text-2xl font-bold heading-gradient">
            robin
          </Link>
          <div className="flex items-center gap-4">
            <Link
              href="/docs"
              className="text-sm font-medium text-primary hover:text-primary/90 transition-colors"
            >
              Documentation →
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-[80vh] flex items-center justify-center overflow-hidden pt-20">
        <div className="absolute inset-0 bg-gradient-to-br from-wizard-background to-wizard-background-darker" />
        <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-20" />

        <div className="container relative z-10">
          <div className="max-w-6xl mx-auto text-center space-y-12">
            <div className="space-y-8">
              <h1 className="text-6xl md:text-8xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-wizard-green to-wizard-blue">
                Your AI Trading Assistant
              </h1>
              <p className="text-2xl text-wizard-text-secondary max-w-3xl mx-auto">
                Get real-time market analysis, options insights, and trading strategies powered by AI
              </p>
            </div>

            <form onSubmit={handleSubmit} className="flex gap-4 max-w-md mx-auto">
              <input
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                placeholder="Enter a symbol (e.g., AAPL)"
                className="flex-1 bg-wizard-background-darker text-wizard-text-primary border border-wizard-neutral-dark focus:border-wizard-green/50 focus:ring-wizard-green/20 rounded-xl px-4 py-3 placeholder:text-wizard-text-muted"
              />
              <button
                type="submit"
                disabled={isLoading || !symbol.trim()}
                className="wizard-button"
              >
                {isLoading ? 'Analyzing...' : 'Analyze'}
              </button>
            </form>

            {/* Quick Access */}
            <div className="pt-8">
              <p className="text-xl text-wizard-text-secondary mb-6">Try analyzing a popular stock:</p>
              <div className="flex flex-wrap justify-center gap-4">
                {['AAPL', 'TSLA', 'NVDA', 'AMZN'].map((ticker) => (
                  <button
                    key={ticker}
                    onClick={() => router.push(`/analyze/${ticker}`)}
                    className="px-6 py-3 bg-wizard-background-darker text-wizard-text-primary rounded-xl hover:bg-wizard-background-lighter/50 transition-colors text-lg font-medium"
                  >
                    {ticker}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Sample Data Section */}
      <section className="py-20">
        <div className="container">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Sample Chart */}
            <div className="glass-panel p-6">
              <h3 className="text-2xl font-semibold text-wizard-text-primary mb-6">Sample Market Analysis</h3>
              <div className="aspect-[16/9] bg-wizard-background-darker rounded-lg p-4">
                <div className="h-full flex flex-col">
                  <div className="flex justify-between items-center mb-4">
                    <div>
                      <h4 className="text-wizard-text-primary font-medium">AAPL - Apple Inc.</h4>
                      <p className="text-wizard-text-secondary text-sm">Last updated: 2 minutes ago</p>
                    </div>
                    <div className="text-right">
                      <p className="text-wizard-text-primary text-xl font-medium">${sampleMarketContext.current_data.price.toFixed(2)}</p>
                      <p className="text-wizard-green text-sm">+{percentChange.toFixed(2)}%</p>
                    </div>
                  </div>
                  <div className="flex-1 relative">
                    <PriceChart
                      dailyData={sampleMarketContext.daily_data}
                      symbol={sampleMarketContext.symbol}
                    />
                  </div>
                  <div className="grid grid-cols-4 gap-4 mt-4">
                    <div className="text-center">
                      <p className="text-wizard-text-secondary text-sm">Open</p>
                      <p className="text-wizard-text-primary">${sampleMarketContext.daily_data.prices[0].toFixed(2)}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-wizard-text-secondary text-sm">High</p>
                      <p className="text-wizard-text-primary">${sampleMarketContext.daily_data.prices[29].toFixed(2)}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-wizard-text-secondary text-sm">Low</p>
                      <p className="text-wizard-text-primary">${sampleMarketContext.daily_data.prices[0].toFixed(2)}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-wizard-text-secondary text-sm">Volume</p>
                      <p className="text-wizard-text-primary">{(sampleMarketContext.daily_data.volumes[0] / 1000000).toFixed(1)}M</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Sample Chat */}
            <div className="glass-panel p-6">
              <h3 className="text-2xl font-semibold text-wizard-text-primary mb-6">Sample AI Analysis</h3>
              <div className="h-[500px] overflow-y-auto space-y-4">
                <div className="bg-wizard-background-darker/50 rounded-lg p-4">
                  <p className="text-wizard-text-secondary">What's the current market sentiment for AAPL?</p>
                </div>
                <div className="bg-wizard-green/10 rounded-lg p-4">
                  <p className="text-wizard-text-primary font-medium">Based on comprehensive market analysis, AAPL shows:</p>
                  <ul className="list-disc list-inside mt-4 space-y-2 text-wizard-text-secondary">
                    <li>Strong technical indicators with RSI at 65, indicating healthy momentum</li>
                    <li>MACD showing bullish crossover with increasing histogram bars</li>
                    <li>Volume profile showing institutional accumulation over the past week</li>
                    <li>Key support at $175 and resistance at $185, with potential breakout above $190</li>
                    <li>Options flow showing heavy call buying in the $190-200 strike range</li>
                  </ul>
                </div>
                <div className="bg-wizard-background-darker/50 rounded-lg p-4">
                  <p className="text-wizard-text-secondary">What options strategies would you recommend based on this analysis?</p>
                </div>
                <div className="bg-wizard-green/10 rounded-lg p-4">
                  <p className="text-wizard-text-primary font-medium">Given the current market conditions, here are strategic options plays:</p>
                  <ul className="list-disc list-inside mt-4 space-y-2 text-wizard-text-secondary">
                    <li>Bull call spread: Buy $185 call, sell $195 call (expiring in 30 days)</li>
                    <li>Covered call strategy: Sell $190 calls against existing shares for income</li>
                    <li>Protective put: Buy $180 puts as insurance against potential pullback</li>
                    <li>Calendar spread: Sell near-term $185 calls, buy longer-term $185 calls</li>
                  </ul>
                  <p className="mt-4 text-wizard-text-primary">Risk Management Note: Consider position sizing based on your risk tolerance and portfolio allocation.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-wizard-background-darker">
        <div className="container">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Market Analysis */}
            <div className="glass-panel p-6 space-y-4">
              <div className="w-12 h-12 rounded-lg bg-wizard-green/10 flex items-center justify-center">
                <svg className="w-6 h-6 text-wizard-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-wizard-text-primary">Market Analysis</h3>
              <p className="text-wizard-text-secondary">Get real-time technical analysis, market trends, and price predictions</p>
            </div>

            {/* Options Insights */}
            <div className="glass-panel p-6 space-y-4">
              <div className="w-12 h-12 rounded-lg bg-wizard-blue/10 flex items-center justify-center">
                <svg className="w-6 h-6 text-wizard-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-wizard-text-primary">Options Insights</h3>
              <p className="text-wizard-text-secondary">Analyze options chains, volatility, and potential strategies</p>
            </div>

            {/* AI Assistant */}
            <div className="glass-panel p-6 space-y-4">
              <div className="w-12 h-12 rounded-lg bg-wizard-purple/10 flex items-center justify-center">
                <svg className="w-6 h-6 text-wizard-purple" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-wizard-text-primary">AI Assistant</h3>
              <p className="text-wizard-text-secondary">Ask questions and get intelligent insights about any stock or option</p>
            </div>
          </div>
        </div>
      </section>

      {/* Future Integrations */}
      <section className="py-20">
        <div className="container">
          <h2 className="text-3xl font-bold text-wizard-text-primary text-center mb-12">Coming Soon</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* QuantWorld Integration */}
            <div className="glass-panel p-6 space-y-4">
              <div className="w-12 h-12 rounded-lg bg-wizard-green/10 flex items-center justify-center">
                <svg className="w-6 h-6 text-wizard-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-wizard-text-primary">QuantWorld Integration</h3>
              <p className="text-wizard-text-secondary">Seamlessly connect with QuantWorld for advanced algorithmic trading strategies and backtesting</p>
            </div>

            {/* Broker Integration */}
            <div className="glass-panel p-6 space-y-4">
              <div className="w-12 h-12 rounded-lg bg-wizard-blue/10 flex items-center justify-center">
                <svg className="w-6 h-6 text-wizard-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-wizard-text-primary">Broker Integration</h3>
              <p className="text-wizard-text-secondary">Sync your portfolios with Robinhood and Charles Schwab for unified portfolio management and analysis</p>
            </div>

            {/* Advanced Analytics */}
            <div className="glass-panel p-6 space-y-4">
              <div className="w-12 h-12 rounded-lg bg-wizard-purple/10 flex items-center justify-center">
                <svg className="w-6 h-6 text-wizard-purple" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-wizard-text-primary">Advanced Analytics</h3>
              <p className="text-wizard-text-secondary">Access institutional-grade analytics, including order flow analysis, dark pool data, and market microstructure insights</p>
            </div>
          </div>
        </div>
      </section>
    </main>
  )
}
