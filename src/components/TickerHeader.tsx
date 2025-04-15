import { MarketContext } from '@/types'
import { formatNumber, formatPercent } from '@/lib/utils'

interface TickerHeaderProps {
  marketContext: MarketContext
}

export default function TickerHeader({ marketContext }: TickerHeaderProps) {
  const { current_data, daily_data, symbol } = marketContext

  if (!current_data || !daily_data || !daily_data.prices || daily_data.prices.length === 0) {
    return <div className="text-wizard-text">Loading market data...</div>
  }

  // Get current price and calculate change
  const currentPrice = current_data.price
  const previousPrice = daily_data.prices[daily_data.prices.length - 2] || daily_data.prices[daily_data.prices.length - 1]
  const priceChange = currentPrice - previousPrice
  const percentChange = previousPrice ? (priceChange / previousPrice) * 100 : 0

  // Format time
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  }

  return (
    <div className="glass-panel p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-wizard-text-primary">
            {symbol}
          </h1>
          <div className="flex items-center gap-3 mt-2">
            <span className="text-2xl text-wizard-text-primary font-semibold">
              ${formatNumber(currentPrice)}
            </span>
            <span className={`text-lg font-medium ${percentChange >= 0 ? 'text-wizard-green' : 'text-wizard-red'}`}>
              {percentChange >= 0 ? '+' : ''}{formatPercent(percentChange)}
            </span>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-6">
          <div>
            <p className="text-wizard-text-secondary">Volume</p>
            <p className="text-lg font-medium text-wizard-text-primary">
              {formatNumber(current_data.volume)}
            </p>
          </div>
          <div>
            <p className="text-wizard-text-secondary">Market Cap</p>
            <p className="text-lg font-medium text-wizard-text-primary">
              ${formatNumber(current_data.market_cap || (currentPrice * current_data.volume))}
            </p>
          </div>
        </div>
      </div>
      <div className="mt-4 text-sm text-wizard-text-secondary text-right">
        Last Update: {formatTime(current_data.timestamp)}
      </div>
    </div>
  )
} 
