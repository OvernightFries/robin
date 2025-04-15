'use client'

import { useEffect, useState, useRef } from 'react'
import { useParams } from 'next/navigation'
import { Message, MarketContext, KnowledgeContext } from '@/types'
import { initializeTicker, query } from '@/lib/api'
import useChatStore from '@/lib/store'
import { MarketSummary } from '@/components/MarketSummary'
import OptionsDisplay from '@/components/OptionsDisplay'
import TickerHeader from '@/components/TickerHeader'
import PriceChart from '@/components/PriceChart'

export default function AnalyzePage() {
  const params = useParams()
  const symbol = params.symbol as string
  const { messages, context, actions } = useChatStore()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [inputValue, setInputValue] = useState('')
  const [isQuerying, setIsQuerying] = useState(false)
  const abortControllerRef = useRef<AbortController | null>(null)
  const mountedRef = useRef(true)

  const initialize = async () => {
    try {
      const response = await initializeTicker(symbol, abortControllerRef.current?.signal)
      if (!mountedRef.current) return

      console.log('API Response:', response);

      if (response.status === 'success' && response.market_context && response.options_context) {
        // Validate the data structure
        if (!response.market_context.current_data || !response.market_context.daily_data) {
          throw new Error('Invalid market data structure received from server')
        }

        if (!response.market_context.current_data.price || !response.market_context.current_data.volume) {
          throw new Error('Missing required market data fields')
        }

        if (!response.market_context.daily_data.dates || !response.market_context.daily_data.prices || !response.market_context.daily_data.volumes) {
          throw new Error('Invalid daily data structure received from server')
        }

        if (!response.options_context.contracts) {
          throw new Error('Invalid options data structure received from server')
        }

        console.log('Options Context:', response.options_context);
        console.log('Options Contracts:', response.options_context.contracts);

        // Validate array lengths
        const { dates, prices, volumes } = response.market_context.daily_data
        if (dates.length !== prices.length || dates.length !== volumes.length) {
          throw new Error('Mismatched array lengths in daily data')
        }

        if (dates.length === 0) {
          throw new Error('No historical data available')
        }

        actions.setContext({
          market: response.market_context,
          knowledge: {
            ...response.options_context,
            current_price: response.market_context.current_data.price
          }
        })
        console.log('Context after setting:', {
          market: response.market_context,
          knowledge: {
            ...response.options_context,
            current_price: response.market_context.current_data.price
          }
        });

        actions.addMessage({
          id: 'initial',
          role: 'assistant',
          content: `How can I help you analyze ${symbol}? I can provide insights on:
- Options strategies
- Technical analysis
- Market sentiment
- Risk assessment`,
          timestamp: Date.now(),
          marketContext: response.market_context,
          knowledgeContext: response.options_context
        })
      } else {
        setError(response.message || 'Failed to load market data')
      }
    } catch (error) {
      if (mountedRef.current) {
        if (error instanceof Error) {
          if (error.name === 'AbortError') {
            // Request was aborted, do nothing
            return
          }
          setError(error.message || 'Failed to initialize ticker')
        } else {
          setError('An unexpected error occurred')
        }
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false)
      }
    }
  }

  useEffect(() => {
    mountedRef.current = true
    abortControllerRef.current?.abort() // Abort any existing request
    abortControllerRef.current = new AbortController()

    initialize()

    return () => {
      mountedRef.current = false
      abortControllerRef.current?.abort()
    }
  }, [symbol, actions])

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isQuerying) return

    const userMessage = inputValue.trim()
    setInputValue('')
    setIsQuerying(true)

    try {
      actions.addMessage({
        id: Date.now().toString(),
        role: 'user',
        content: userMessage,
        timestamp: Date.now()
      })

      const response = await query(userMessage, symbol)

      if (response.status === 'success') {
        actions.addMessage({
          id: Date.now().toString(),
          role: 'assistant',
          content: response.response,
          timestamp: Date.now(),
          marketContext: response.market_context,
          knowledgeContext: response.knowledge_context
        })
      } else {
        actions.addMessage({
          id: Date.now().toString(),
          role: 'assistant',
          content: 'I apologize, but I encountered an error processing your request. Please try again.',
          timestamp: Date.now()
        })
      }
    } catch (error) {
      console.error('Error sending message:', error)
      actions.addMessage({
        id: Date.now().toString(),
        role: 'assistant',
        content: 'I apologize, but I encountered an error processing your request. Please try again.',
        timestamp: Date.now()
      })
    } finally {
      setIsQuerying(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-wizard-background relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-20" />
        <div className="absolute inset-0 bg-gradient-to-br from-wizard-green/5 to-wizard-blue/5" />
        <div className="relative text-center space-y-8">
          <div className="flex items-center justify-center gap-6">
            <div className="w-5 h-5 bg-gradient-to-br from-wizard-green to-wizard-blue rounded-full animate-bounce shadow-lg shadow-wizard-green/20" style={{ animationDelay: '0ms' }} />
            <div className="w-5 h-5 bg-gradient-to-br from-wizard-green to-wizard-blue rounded-full animate-bounce shadow-lg shadow-wizard-green/20" style={{ animationDelay: '150ms' }} />
            <div className="w-5 h-5 bg-gradient-to-br from-wizard-green to-wizard-blue rounded-full animate-bounce shadow-lg shadow-wizard-green/20" style={{ animationDelay: '300ms' }} />
          </div>
          <div>
            <h2 className="text-2xl font-bold bg-gradient-to-r from-wizard-green to-wizard-blue bg-clip-text text-transparent mb-2">
              Analyzing {symbol.toUpperCase()}
            </h2>
            <p className="text-wizard-text-secondary text-lg">Fetching market data and options chains...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-wizard-background">
        <div className="glass-panel p-8 max-w-md w-full text-center space-y-4">
          <div className="w-16 h-16 bg-wizard-red/10 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-wizard-red" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-wizard-text-primary">Error Loading Data</h2>
          <p className="text-wizard-red">{error}</p>
          <button
            onClick={() => {
              setError(null)
              setLoading(true)
              initialize()
            }}
            className="mt-4 px-6 py-2 bg-wizard-surface hover:bg-wizard-surface/80 text-wizard-text-primary rounded-lg transition-colors duration-200"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!context?.market?.current_data || !context?.knowledge) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-wizard-background relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-20" />
        <div className="absolute inset-0 bg-gradient-to-br from-wizard-green/5 to-wizard-blue/5" />
        <div className="relative text-center space-y-8">
          <div className="flex items-center justify-center gap-6">
            <div className="w-5 h-5 bg-gradient-to-br from-wizard-green to-wizard-blue rounded-full animate-bounce shadow-lg shadow-wizard-green/20" style={{ animationDelay: '0ms' }} />
            <div className="w-5 h-5 bg-gradient-to-br from-wizard-green to-wizard-blue rounded-full animate-bounce shadow-lg shadow-wizard-green/20" style={{ animationDelay: '150ms' }} />
            <div className="w-5 h-5 bg-gradient-to-br from-wizard-green to-wizard-blue rounded-full animate-bounce shadow-lg shadow-wizard-green/20" style={{ animationDelay: '300ms' }} />
          </div>
          <div>
            <h2 className="text-2xl font-bold bg-gradient-to-r from-wizard-green to-wizard-blue bg-clip-text text-transparent mb-2">
              Loading Market Data
            </h2>
            <p className="text-wizard-text-secondary text-lg">Fetching real-time market data and options chains...</p>
          </div>
        </div>
      </div>
    )
  }

  const { market: marketContext, knowledge: knowledgeContext } = context

  // Ensure we have the required data before rendering
  if (!marketContext?.daily_data?.dates?.length || !marketContext?.daily_data?.prices?.length || !marketContext?.daily_data?.volumes?.length) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-wizard-background relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-20" />
        <div className="absolute inset-0 bg-gradient-to-br from-wizard-green/5 to-wizard-blue/5" />
        <div className="relative text-center space-y-8">
          <div className="flex items-center justify-center gap-6">
            <div className="w-5 h-5 bg-gradient-to-br from-wizard-green to-wizard-blue rounded-full animate-bounce shadow-lg shadow-wizard-green/20" style={{ animationDelay: '0ms' }} />
            <div className="w-5 h-5 bg-gradient-to-br from-wizard-green to-wizard-blue rounded-full animate-bounce shadow-lg shadow-wizard-green/20" style={{ animationDelay: '150ms' }} />
            <div className="w-5 h-5 bg-gradient-to-br from-wizard-green to-wizard-blue rounded-full animate-bounce shadow-lg shadow-wizard-green/20" style={{ animationDelay: '300ms' }} />
          </div>
          <div>
            <h2 className="text-2xl font-bold bg-gradient-to-r from-wizard-green to-wizard-blue bg-clip-text text-transparent mb-2">
              Processing Market Data
            </h2>
            <p className="text-wizard-text-secondary text-lg">Preparing charts and analysis...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen bg-wizard-background relative">
      <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-10 pointer-events-none" />
      <div className="absolute inset-0 bg-gradient-to-br from-wizard-green/5 to-wizard-blue/5 pointer-events-none" />

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 relative">
        <div className="max-w-7xl mx-auto w-full">
          {marketContext && <TickerHeader marketContext={marketContext} />}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
            <div className="glass-panel p-6 hover:shadow-lg hover:shadow-wizard-green/5 transition-all duration-300">
              <PriceChart
                dailyData={marketContext.daily_data}
                symbol={symbol}
              />
            </div>
            <div className="glass-panel p-6 hover:shadow-lg hover:shadow-wizard-blue/5 transition-all duration-300">
              <MarketSummary
                dailyData={marketContext.daily_data}
                currentData={marketContext.current_data}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
            <div className="glass-panel p-6 hover:shadow-lg hover:shadow-wizard-green/5 transition-all duration-300">
              <h3 className="text-xl font-semibold text-wizard-text-primary mb-6 flex items-center">
                <span className="w-2 h-2 bg-wizard-green rounded-full mr-2"></span>
                Calls
              </h3>
              {knowledgeContext && <OptionsDisplay optionsData={knowledgeContext} type="calls" />}
            </div>
            <div className="glass-panel p-6 hover:shadow-lg hover:shadow-wizard-red/5 transition-all duration-300">
              <h3 className="text-xl font-semibold text-wizard-text-primary mb-6 flex items-center">
                <span className="w-2 h-2 bg-wizard-red rounded-full mr-2"></span>
                Puts
              </h3>
              {knowledgeContext && <OptionsDisplay optionsData={knowledgeContext} type="puts" />}
            </div>
          </div>
        </div>
      </div>

      {/* Chat Section */}
      <div className="border-t border-wizard-border bg-wizard-background/50 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto p-6">
          <div className="glass-panel p-6">
            <div className="space-y-4 max-h-[300px] overflow-y-auto mb-6 pr-4 scrollbar-thin scrollbar-thumb-wizard-border scrollbar-track-transparent">
              {messages.map((message: Message) => (
                <div
                  key={message.id}
                  className={`p-4 rounded-xl transition-all duration-300 ${message.role === 'user'
                    ? 'bg-wizard-background/80 border border-wizard-border'
                    : 'bg-gradient-to-r from-wizard-surface to-wizard-surface/80'
                    }`}
                >
                  <div className="text-wizard-text-primary">{message.content}</div>
                </div>
              ))}
            </div>
            <div className="flex gap-4">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about market trends, options strategies, or technical analysis..."
                className="flex-1 bg-wizard-background/80 text-wizard-text-primary rounded-xl px-6 py-3 border border-wizard-border focus:outline-none focus:border-wizard-green focus:ring-2 focus:ring-wizard-green/20 transition-all duration-300"
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isQuerying}
                className={`px-8 py-3 bg-gradient-to-r from-wizard-green to-wizard-blue text-white rounded-xl hover:opacity-90 transition-all duration-300 font-medium shadow-lg shadow-wizard-green/20 ${(!inputValue.trim() || isQuerying) ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
              >
                {isQuerying ? 'Sending...' : 'Send'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 
