import { KnowledgeContext } from '@/types'
import { formatNumber, formatPercent } from '@/lib/utils'

interface OptionsSummaryProps {
  optionsData: KnowledgeContext
}

export default function OptionsSummary({ optionsData }: OptionsSummaryProps) {
  if (!optionsData) {
    return (
      <div className="glass-panel p-6">
        <h3 className="text-xl font-semibold text-wizard-text-primary mb-4">Options Overview</h3>
        <div className="text-wizard-text-secondary">Loading options data...</div>
      </div>
    )
  }

  const { company_name, sector, industry, market_cap, pe_ratio, beta, dividend_yield } = optionsData

  return (
    <div className="glass-panel p-6">
      <h3 className="text-xl font-semibold text-wizard-text-primary mb-4">Company Overview</h3>
      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <span className="text-wizard-text-secondary text-sm">Company</span>
            <span className="text-wizard-text-primary font-medium">{company_name}</span>
          </div>
          <div className="space-y-1">
            <span className="text-wizard-text-secondary text-sm">Sector</span>
            <span className="text-wizard-text-primary font-medium">{sector}</span>
          </div>
          <div className="space-y-1">
            <span className="text-wizard-text-secondary text-sm">Industry</span>
            <span className="text-wizard-text-primary font-medium">{industry}</span>
          </div>
          <div className="space-y-1">
            <span className="text-wizard-text-secondary text-sm">Market Cap</span>
            <span className="text-wizard-text-primary font-medium">{formatNumber(market_cap)}</span>
          </div>
          <div className="space-y-1">
            <span className="text-wizard-text-secondary text-sm">P/E Ratio</span>
            <span className="text-wizard-text-primary font-medium">{pe_ratio?.toFixed(2) || 'N/A'}</span>
          </div>
          <div className="space-y-1">
            <span className="text-wizard-text-secondary text-sm">Beta</span>
            <span className="text-wizard-text-primary font-medium">{beta?.toFixed(2) || 'N/A'}</span>
          </div>
          <div className="space-y-1">
            <span className="text-wizard-text-secondary text-sm">Dividend Yield</span>
            <span className="text-wizard-text-primary font-medium">{formatPercent(dividend_yield)}</span>
          </div>
        </div>
      </div>
    </div>
  )
} 
