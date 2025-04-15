import React from 'react'
import { DailyData, MarketData } from '@/types'
import { formatNumber, formatPercent } from '@/lib/utils'

interface MarketSummaryProps {
  dailyData: DailyData
  currentData: MarketData
}

const safeCalculateChange = (current: number | undefined, previous: number | undefined): number => {
  if (!current || !previous || previous === 0) return 0
  return ((current - previous) / previous) * 100
}

const TrendIndicator = ({ value }: { value: number }) => {
  const isPositive = value >= 0
  return (
    <div className={`flex items-center space-x-1 ${isPositive ? 'text-wizard-green' : 'text-wizard-red'}`}>
      <svg
        className={`w-4 h-4 ${isPositive ? '' : 'transform rotate-180'}`}
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
      </svg>
      <span className="font-medium">{formatPercent(value)}</span>
    </div>
  )
}

export const MarketSummary: React.FC<MarketSummaryProps> = ({ dailyData, currentData }) => {
  if (!dailyData || !currentData || !dailyData.prices || dailyData.prices.length === 0) {
    return <div className="text-wizard-text">Loading market data...</div>
  }

  const { prices, volumes } = dailyData
  const currentPrice = currentData.price
  const previousPrice = prices[prices.length - 2] || prices[prices.length - 1]
  const priceChange = currentPrice - previousPrice
  const percentChange = safeCalculateChange(currentPrice, previousPrice)

  const high52Week = Math.max(...prices)
  const low52Week = Math.min(...prices)
  const volume = currentData.volume || volumes[volumes.length - 1] || 0
  const marketCap = currentData.market_cap || (currentPrice * volume)

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-wizard-text">Market Summary</h2>

      <div className="grid grid-cols-2 gap-4">
        <div className="glass-panel p-4">
          <h3 className="text-wizard-text/80">Current Price</h3>
          <p className="text-2xl font-bold text-wizard-text">${formatNumber(currentPrice)}</p>
          <TrendIndicator value={percentChange} />
        </div>

        <div className="glass-panel p-4">
          <h3 className="text-wizard-text/80">52 Week Range</h3>
          <p className="text-xl font-bold text-wizard-text">
            ${formatNumber(low52Week)} - ${formatNumber(high52Week)}
          </p>
        </div>

        <div className="glass-panel p-4">
          <h3 className="text-wizard-text/80">Market Cap</h3>
          <p className="text-xl font-bold text-wizard-text">
            ${formatNumber(marketCap)}
          </p>
        </div>

        <div className="glass-panel p-4">
          <h3 className="text-wizard-text/80">Volume</h3>
          <p className="text-xl font-bold text-wizard-text">
            {formatNumber(volume)}
          </p>
        </div>
      </div>
    </div>
  )
} 
