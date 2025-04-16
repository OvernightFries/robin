import { Message } from '@/types';

export const SAMPLE_CONVERSATION: Message[] = [
  {
    role: 'user',
    content: 'Analyze AAPL options chain for potential iron condor setup considering current IV and earnings.',
    id: '1',
    timestamp: Date.now() - 300000
  },
  {
    role: 'assistant',
    content: `Based on AAPL's current options chain analysis:

Market Context
• IV Percentile: 67th (relatively high)
• Earnings: 35 days out (February 1st)
• Current Price: $169.75
• Expected Move (30d): ±$8.45
• Historical Volatility: 22.4%
• Implied Volatility: 28.7%

Technical Analysis
• RSI (14): 62.8 - Slightly overbought
• MACD: Bullish crossover
• 50 DMA: $165.32 (Support)
• 200 DMA: $162.45 (Strong support)
• Volume Profile: High resistance at $175

Recommended Iron Condor Setup
- Sell 165 Put @ $2.15 (0.32 delta)
- Buy 160 Put @ $1.10 (0.22 delta)
- Sell 175 Call @ $2.30 (0.35 delta)
- Buy 180 Call @ $1.20 (0.25 delta)

Key Metrics
• Max Profit: $215 (net credit)
• Max Loss: $285
• Probability of Profit: 72%
• Greeks:
  - Delta: neutral (±0.02)
  - Gamma: -0.002
  - Theta: +0.45
  - Vega: -0.15

Strategic Rationale
1. Elevated IV with expected mean reversion post-earnings
2. Clear technical support at 160 (coincides with 200 DMA)
3. Resistance at 175 pre-earnings (confirmed by volume profile)
4. 1 standard deviation wings for optimal risk/reward
5. Positive theta decay during pre-earnings period

Risk Management
- Close at 50% profit ($107.50)
- Stop loss at 2x credit received ($430)
- Adjust wings if price breaks support/resistance
- Consider rolling position if touched before earnings

Would you like me to analyze specific aspects of this setup in more detail, such as the Greeks or adjustment strategies?`,
    id: '2',
    timestamp: Date.now() - 240000
  },
  {
    role: 'user',
    content: 'Yes, could you explain the adjustment strategies in more detail, particularly around earnings?',
    id: '3',
    timestamp: Date.now() - 180000
  },
  {
    role: 'assistant',
    content: `Let me break down the adjustment strategies, particularly focusing on earnings management:

Pre-Earnings Adjustments
• Delta Management
  - If delta exceeds ±0.10: Roll tested wing up/down
  - Maintain 0.30-0.35 delta on short strikes
  - Keep minimum 0.15 delta difference between long/short

• Time Management (14-21 DTE)
  1. If P/L > 25%: Consider rolling entire position out
  2. If P/L < -15%: Evaluate early adjustment
  3. Target new position for post-earnings expiration

Earnings-Specific Strategy
• Pre-Earnings (T-5 days)
  - Reduce position size by 50% if still holding
  - Consider converting to butterfly for gamma reduction
  - Target 25% max portfolio exposure

• During Earnings
  - No adjustments during announcement
  - Prepare orders for gap scenarios:
    › Gap Up > 5%: Roll call spread up
    › Gap Down > 5%: Roll put spread down
    › Either case: Widen wings for credit

• Post-Earnings Management
  1. IV Crush Scenario (Expected)
    - Allow theta decay to accelerate gains
    - Maintain position if within expected range
    - Consider adding size on IV normalization

  2. Price Movement Scenario
    - Breach of Short Strike:
      › Roll tested wing for credit
      › Maintain 1:1.5 risk/reward minimum
    - Breach of Long Strike:
      › Close position immediately
      › Re-evaluate setup after volatility settles

Risk Parameters for Adjustments
• Maximum Adjustment Cost: 25% of max profit
• Minimum Credit Required: 20% of width
• Maximum Position Delta: ±0.15
• Stop Loss: Original credit + adjustment cost

Would you like me to provide specific examples of these adjustments with current option prices?`,
    id: '4',
    timestamp: Date.now() - 120000
  }
]; 
