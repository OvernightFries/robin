import { KnowledgeContext, OptionsContract } from '@/types'

interface OptionsDisplayProps {
  optionsData: KnowledgeContext
  type: 'calls' | 'puts'
}

export default function OptionsDisplay({ optionsData, type }: OptionsDisplayProps) {
  const { current_price, contracts } = optionsData

  if (!contracts || !current_price || contracts.length === 0) {
    return (
      <div className="text-wizard-text-secondary text-center py-4">
        No options data available
      </div>
    )
  }

  // Format large numbers with K/M/B suffix
  const formatLargeNumber = (num: number) => {
    if (num >= 1e6) return `${(num / 1e6).toFixed(1)}M`
    if (num >= 1e3) return `${(num / 1e3).toFixed(1)}K`
    return num.toString()
  }

  // Get nearest expiration date
  const expirationDates = [...new Set(contracts.map(c => c.expiration_date))].sort()
  const nearestExpiry = expirationDates[0]

  if (!nearestExpiry) {
    return (
      <div className="text-wizard-text-secondary text-center py-4">
        No options available
      </div>
    )
  }

  // Get relevant contracts
  const relevantContracts = contracts
    .filter((c: OptionsContract) =>
      c.expiration_date === nearestExpiry &&
      c.type === (type === 'calls' ? 'call' : 'put')
    )
    .map(c => ({
      ...c,
      strike_price_num: parseFloat(c.strike_price),
      last_price: parseFloat(c.close_price || '0'),
      volume: parseInt(c.size || '0'),
      open_interest: parseInt(c.open_interest || '0')
    }))
    .sort((a, b) => {
      const strikeA = a.strike_price_num
      const strikeB = b.strike_price_num
      return type === 'calls' ? strikeA - strikeB : strikeB - strikeA
    })

  // Get a reasonable range of strikes to display
  const strikes = relevantContracts.map(c => c.strike_price_num)
  const minStrike = Math.min(...strikes)
  const maxStrike = Math.max(...strikes)
  const strikeRange = maxStrike - minStrike

  // Select contracts to display based on current price and available strikes
  let displayContracts = relevantContracts
  if (relevantContracts.length > 5) {
    // Find the closest strikes to current price
    const sortedByDistance = [...relevantContracts].sort((a, b) =>
      Math.abs(a.strike_price_num - current_price) - Math.abs(b.strike_price_num - current_price)
    )

    // Take 2 strikes above and 2 below the current price, plus the closest strike
    const closestToCurrentPrice = sortedByDistance[0]
    const aboveStrikes = relevantContracts.filter(c => c.strike_price_num > current_price).slice(0, 2)
    const belowStrikes = relevantContracts.filter(c => c.strike_price_num < current_price).slice(-2)

    displayContracts = [...belowStrikes, closestToCurrentPrice, ...aboveStrikes]
      .sort((a, b) => type === 'calls' ? a.strike_price_num - b.strike_price_num : b.strike_price_num - a.strike_price_num)
      .slice(0, 5)
  }

  // Format date
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  // Calculate option metrics
  const getOptionMetrics = (contract: any) => {
    const strike = contract.strike_price_num
    const lastPrice = contract.last_price || 0
    const isITM = type === 'calls' ? current_price > strike : current_price < strike
    const intrinsicValue = isITM
      ? type === 'calls'
        ? current_price - strike
        : strike - current_price
      : 0
    const timeValue = Math.max(0, lastPrice - intrinsicValue)

    return {
      strike,
      lastPrice,
      isITM,
      intrinsicValue,
      timeValue
    }
  }

  return (
    <div>
      <div className="mb-4 text-wizard-text-secondary text-sm">
        Expiring {formatDate(nearestExpiry)}
      </div>
      <div className="space-y-4">
        {displayContracts.map((contract) => {
          const metrics = getOptionMetrics(contract)
          return (
            <div
              key={contract.symbol}
              className={`p-4 rounded-lg ${Math.abs(metrics.strike - current_price) < 1
                ? 'bg-wizard-surface/20 border border-wizard-border'
                : ''
                }`}
            >
              <div className="flex justify-between items-center mb-2">
                <div>
                  <span className="text-lg font-medium text-wizard-text-primary">
                    ${metrics.strike.toFixed(2)}
                  </span>
                  <span className={`ml-2 text-sm font-medium ${metrics.isITM ? 'text-wizard-green' : 'text-wizard-red'
                    }`}>
                    {metrics.isITM ? 'ITM' : 'OTM'}
                  </span>
                </div>
                <div className="text-right">
                  <div className="text-sm text-wizard-text-secondary">Last</div>
                  <div className="font-medium text-wizard-text-primary">
                    ${metrics.lastPrice.toFixed(2)}
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm mt-3">
                <div>
                  <span className="text-wizard-text-secondary">Volume</span>
                  <p className="text-wizard-text-primary">
                    {contract.volume ? formatLargeNumber(contract.volume) : '-'}
                  </p>
                </div>
                <div>
                  <span className="text-wizard-text-secondary">Open Interest</span>
                  <p className="text-wizard-text-primary">
                    {contract.open_interest ? formatLargeNumber(contract.open_interest) : '-'}
                  </p>
                </div>
                <div>
                  <span className="text-wizard-text-secondary">Intrinsic</span>
                  <p className="text-wizard-text-primary">
                    ${metrics.intrinsicValue.toFixed(2)}
                  </p>
                </div>
                <div>
                  <span className="text-wizard-text-secondary">Time Value</span>
                  <p className="text-wizard-text-primary">
                    ${metrics.timeValue.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
} 
