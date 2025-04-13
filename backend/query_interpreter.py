from typing import Dict, Any, Optional, List, Tuple
import re
from datetime import datetime, timedelta
import logging
from enum import Enum
import json
from rag.ollama_client import call_ollama

logger = logging.getLogger(__name__)

class Timeframe(Enum):
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"

class QueryInterpreter:
    def __init__(self):
        # Enhanced trading terms and patterns
        self.patterns = {
            'price': r'(current|latest|current market)?\s*(price|value|worth)\s*(of|for)?',
            'options': r'(options?|calls?|puts?)\s*(chain|data|information)?',
            'volatility': r'(volatility|vol|vols?)\s*(for|of|on)?',
            'timeframe': r'(last|past|previous|recent)\s*(\d+)\s*(days?|weeks?|months?|years?|hours?|minutes?)',
            'comparison': r'(compare|vs|versus|compared to)\s*([A-Z]+)',
            'sentiment': r'(sentiment|mood|feeling)\s*(about|for|on)?',
            'trend': r'(trend|direction|movement)\s*(of|for)?',
            'support_resistance': r'(support|resistance)\s*(levels?|points?)?',
            'volume': r'(volume|trading volume)\s*(for|of)?',
            'technical': r'(technical|technicals?)\s*(analysis|indicators?)?',
            'strategy': r'(strategy|approach|method)\s*(for|to)?',
            'risk': r'(risk|risk management)\s*(for|of)?',
            'position': r'(position|positions?)\s*(size|sizing)?',
            'entry': r'(entry|entries)\s*(point|points)?',
            'exit': r'(exit|exits)\s*(point|points)?',
            'stop': r'(stop|stop loss)\s*(level|levels)?',
            'target': r'(target|take profit)\s*(level|levels)?',
            'options_strategy': r'(options?|calls?|puts?)\s*(strategy|strategies)?',
            'spread': r'(spread|spreads?)\s*(type|types)?',
            'greeks': r'(greeks?|delta|gamma|theta|vega|rho)\s*(for|of)?',
            'implied_volatility': r'(implied volatility|iv)\s*(for|of)?',
            'open_interest': r'(open interest|oi)\s*(for|of)?',
            'volume_oi': r'(volume|open interest)\s*(ratio|ratios)?',
            'moneyness': r'(in the money|itm|out of the money|otm|at the money|atm)',
            'expiration': r'(expiration|expiry)\s*(date|dates)?',
            'strike': r'(strike|strikes?)\s*(price|prices)?',
        }
        
        # Enhanced stock symbols with sectors and industries
        self.common_symbols = {
            # Tech Sector
            'apple': 'AAPL', 'microsoft': 'MSFT', 'amazon': 'AMZN', 'google': 'GOOGL',
            'meta': 'META', 'tesla': 'TSLA', 'nvidia': 'NVDA', 'amd': 'AMD',
            'intel': 'INTC', 'qualcomm': 'QCOM', 'broadcom': 'AVGO', 'adobe': 'ADBE',
            'salesforce': 'CRM', 'oracle': 'ORCL', 'ibm': 'IBM', 'cisco': 'CSCO',
            'netflix': 'NFLX', 'paypal': 'PYPL', 'square': 'SQ', 'coinbase': 'COIN',
            'robinhood': 'HOOD', 'shopify': 'SHOP', 'twilio': 'TWLO', 'datadog': 'DDOG',
            'snowflake': 'SNOW', 'mongodb': 'MDB', 'cloudflare': 'NET', 'fastly': 'FSLY',
            'palo alto': 'PANW', 'crowdstrike': 'CRWD', 'zscaler': 'ZS', 'okta': 'OKTA',
            'splunk': 'SPLK', 'elastic': 'ESTC', 'atlassian': 'TEAM', 'servicenow': 'NOW',
            'workday': 'WDAY', 'autodesk': 'ADSK', 'ansys': 'ANSS', 'cadence': 'CDNS',
            'synopsys': 'SNPS', 'amd': 'AMD', 'nvidia': 'NVDA', 'intel': 'INTC',
            'qualcomm': 'QCOM', 'broadcom': 'AVGO', 'micron': 'MU', 'texas instruments': 'TXN',
            'analog devices': 'ADI', 'maxim': 'MXIM', 'monolithic': 'MPWR', 'onsemi': 'ON',
            'nvidia': 'NVDA', 'amd': 'AMD', 'intel': 'INTC', 'qualcomm': 'QCOM',
            'broadcom': 'AVGO', 'micron': 'MU', 'texas instruments': 'TXN',
            'analog devices': 'ADI', 'maxim': 'MXIM', 'monolithic': 'MPWR', 'onsemi': 'ON',
            
            # Financial Sector
            'jpmorgan': 'JPM', 'goldman': 'GS', 'morgan': 'MS', 'bank': 'BAC',
            'wells': 'WFC', 'visa': 'V', 'mastercard': 'MA', 'american express': 'AXP',
            'discover': 'DFS', 'capital one': 'COF', 'synchrony': 'SYF', 'ally': 'ALLY',
            'citigroup': 'C', 'bank of america': 'BAC', 'wells fargo': 'WFC',
            'us bancorp': 'USB', 'pnc': 'PNC', 'truist': 'TFC', 'regions': 'RF',
            'huntington': 'HBAN', 'keycorp': 'KEY', 'citizens': 'CFG', 'm&t': 'MTB',
            'first republic': 'FRC', 'svb': 'SIVB', 'silicon valley': 'SIVB',
            'signature': 'SBNY', 'pacwest': 'PACW', 'western alliance': 'WAL',
            'first horizon': 'FHN', 'zions': 'ZION', 'comerica': 'CMA',
            
            # ETFs and Indices
            'spy': 'SPY', 'qqq': 'QQQ', 'dia': 'DIA', 'iwm': 'IWM',
            'voo': 'VOO', 'vti': 'VTI', 'vgt': 'VGT', 'xlk': 'XLK',
            'xlf': 'XLF', 'xle': 'XLE', 'xlv': 'XLV', 'xli': 'XLI',
            'xlp': 'XLP', 'xlu': 'XLU', 'xlre': 'XLRE', 'xlb': 'XLB',
            'xly': 'XLY', 'xlk': 'XLK', 'xlc': 'XLC', 'xlf': 'XLF',
            'xle': 'XLE', 'xlv': 'XLV', 'xli': 'XLI', 'xlp': 'XLP',
            'xlu': 'XLU', 'xlre': 'XLRE', 'xlb': 'XLB', 'xly': 'XLY',
            
            # Options-specific terms
            'call': 'CALL', 'put': 'PUT', 'straddle': 'STRADDLE',
            'strangle': 'STRANGLE', 'butterfly': 'BUTTERFLY',
            'iron condor': 'IRON CONDOR', 'calendar': 'CALENDAR',
            'diagonal': 'DIAGONAL', 'vertical': 'VERTICAL',
            'ratio': 'RATIO', 'backspread': 'BACKSPREAD',
            'jade lizard': 'JADE LIZARD', 'broken wing': 'BROKEN WING',
            'condor': 'CONDOR', 'butterfly': 'BUTTERFLY',
            'straddle': 'STRADDLE', 'strangle': 'STRANGLE',
        }

        # Enhanced technical indicators with options-specific parameters
        self.technical_indicators = {
            'rsi': {'name': 'RSI', 'default_period': 14},
            'macd': {'name': 'MACD', 'default_periods': (12, 26, 9)},
            'bollinger': {'name': 'Bollinger Bands', 'default_period': 20},
            'moving average': {'name': 'Moving Average', 'default_periods': [20, 50, 200]},
            'stochastic': {'name': 'Stochastic', 'default_periods': (14, 3, 3)},
            'volume': {'name': 'Volume', 'default_period': None},
            'atr': {'name': 'ATR', 'default_period': 14},
            'adx': {'name': 'ADX', 'default_period': 14},
            'cci': {'name': 'CCI', 'default_period': 20},
            'mfi': {'name': 'MFI', 'default_period': 14},
            'obv': {'name': 'OBV', 'default_period': None},
            'vwap': {'name': 'VWAP', 'default_period': None},
            # Options-specific indicators
            'delta': {'name': 'Delta', 'default_period': None},
            'gamma': {'name': 'Gamma', 'default_period': None},
            'theta': {'name': 'Theta', 'default_period': None},
            'vega': {'name': 'Vega', 'default_period': None},
            'rho': {'name': 'Rho', 'default_period': None},
            'iv': {'name': 'Implied Volatility', 'default_period': None},
            'oi': {'name': 'Open Interest', 'default_period': None},
            'volume_oi': {'name': 'Volume/OI Ratio', 'default_period': None},
            'moneyness': {'name': 'Moneyness', 'default_period': None},
        }

    def _normalize_query(self, query: str) -> str:
        """Normalize the query by handling synonyms and common variations."""
        query = query.lower()
        
        # Common synonym replacements
        synonyms = {
            'expiring': 'expiration',
            'expires': 'expiration',
            'expiry': 'expiration',
            'calls at': 'call strike',
            'puts at': 'put strike',
            'show me': '',
            'what is': '',
            'what are': '',
            'tell me': '',
            'get': '',
            'give me': '',
            'please': '',
            'thanks': '',
            'thank you': '',
            'next month': '1 month',
            'next week': '1 week',
            'next year': '1 year',
            'this month': 'current month',
            'this week': 'current week',
            'this year': 'current year',
            'last month': 'previous month',
            'last week': 'previous week',
            'last year': 'previous year',
            'in the money': 'itm',
            'out of the money': 'otm',
            'at the money': 'atm',
            'delta value': 'delta',
            'gamma value': 'gamma',
            'theta value': 'theta',
            'vega value': 'vega',
            'rho value': 'rho'
        }
        
        for old, new in synonyms.items():
            query = query.replace(old, new)
            
        return query.strip()

    def _parse_with_llm(self, query: str) -> Dict[str, Any]:
        """Use Ollama to parse the query into structured components."""
        try:
            # Create a structured prompt for the LLM
            llm_query = f"""
            Parse this trading query into a structured dictionary. Only respond with the JSON output, no other text.
            
            Query: "{query}"
            
            Required fields (only include if present in query):
            - symbol: stock symbol
            - option_type: 'call' or 'put'
            - strike_price: number
            - greeks: list of greeks requested
            - expiration: date or relative time
            - timeframe: relative time period
            - indicators: list of technical indicators
            - intent: main purpose of query
            
            Example output format:
            {{
              "symbol": "TSLA",
              "option_type": "put",
              "strike_price": 700,
              "greeks": ["delta", "gamma"],
              "expiration": "2 weeks",
              "timeframe": "2 weeks",
              "intent": "options_greeks"
            }}
            """
            
            # Call Ollama with the correct parameters
            response = call_ollama(
                query=llm_query,
                context="",  # No RAG context needed for parsing
                market_context=""  # No market context needed for parsing
            )
            
            # Clean the response to ensure it's valid JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            # Parse the JSON response
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM response as JSON: {response}")
                return {}
                
        except Exception as e:
            logger.error(f"Error parsing query with LLM: {str(e)}")
            return {}

    def interpret(self, query: str) -> Dict[str, Any]:
        """Interpret a natural language query about trading."""
        # Normalize the query first
        normalized_query = self._normalize_query(query)
        
        # Try to parse with LLM first
        llm_parsed = self._parse_with_llm(normalized_query)
        if llm_parsed:
            return llm_parsed
            
        # If LLM parsing fails, use traditional parsing
        result = {
            'symbol': self._extract_symbol(normalized_query),
            'intent': self._determine_intent(normalized_query),
            'timeframe': self._extract_timeframe(normalized_query),
            'parameters': {}
        }
        
        # Check for ambiguity
        if not result['symbol']:
            return {
                'needs_clarification': True,
                'clarification_message': "Which stock or symbol are you interested in?",
                'clarification_options': list(self.common_symbols.keys())[:5]  # Show top 5 common symbols
            }
            
        if result['intent'] == 'unknown':
            return {
                'needs_clarification': True,
                'clarification_message': "What would you like to know about this stock?",
                'clarification_options': [
                    "Current price",
                    "Options data",
                    "Technical indicators",
                    "Historical performance",
                    "News and sentiment"
                ]
            }
            
        # Extract additional parameters based on intent
        if 'options' in result['intent']:
            result['parameters'].update({
                'strike_price': self._extract_strike_price(normalized_query),
                'expiration': self._extract_expiration(normalized_query),
                'greeks': self._extract_greeks(normalized_query)
            })
            
            # Check if we need clarification for options
            if not result['parameters']['strike_price']:
                return {
                    'needs_clarification': True,
                    'clarification_message': "What strike price are you interested in?",
                    'clarification_options': ["150", "200", "250", "300"]
                }
                
        elif 'technical' in result['intent']:
            result['parameters'].update({
                'indicators': self._extract_technical_indicators(normalized_query)
            })
            
            if not result['parameters']['indicators']:
                return {
                    'needs_clarification': True,
                    'clarification_message': "Which technical indicators would you like to see?",
                    'clarification_options': ["RSI", "MACD", "Moving Averages", "Bollinger Bands"]
                }
                
        return result

    def _extract_symbol(self, query: str) -> str:
        """Extract stock symbol from query."""
        query = query.lower()
        
        # First check for exact symbol matches
        for name, symbol in self.common_symbols.items():
            if name in query or symbol in query:
                # Skip options-related terms
                if name in ['call', 'put', 'straddle', 'strangle', 'butterfly', 'iron condor']:
                    continue
                return symbol
                
        # If no exact match, try to find a symbol pattern
        symbol_pattern = r'\b([A-Z]{1,5})\b'
        matches = re.findall(symbol_pattern, query.upper())
        if matches:
            # Filter out common words that might look like symbols
            common_words = {'THE', 'AND', 'FOR', 'WITH', 'CALL', 'PUT', 'IN', 'ON', 'AT', 'SHOW', 'ME', 'THE'}
            valid_symbols = [m for m in matches if m not in common_words]
            if valid_symbols:
                return valid_symbols[0]
                
        return None

    def _determine_intent(self, query: str) -> str:
        """Determine the intent of the query with enhanced context awareness."""
        query = query.lower()
        
        # Check if it's a weekend
        current_time = datetime.now()
        is_weekend = current_time.weekday() >= 5  # 5 is Saturday, 6 is Sunday
        is_market_hours = False
        if not is_weekend:
            market_open = current_time.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = current_time.replace(hour=16, minute=0, second=0, microsecond=0)
            is_market_hours = market_open <= current_time <= market_close
        
        # Check for general market questions
        general_market_terms = [
            'market', 'markets', 'overall', 'general', 'broad', 'sector',
            'sectors', 'industry', 'industries', 'trend', 'trends',
            'outlook', 'sentiment', 'mood', 'feeling', 'vibe'
        ]
        
        if any(term in query for term in general_market_terms):
            if is_weekend:
                return 'market_overview_weekend'
            elif not is_market_hours:
                return 'market_overview_premarket' if current_time < market_open else 'market_overview_postmarket'
            else:
                return 'market_overview'
        
        # Check for specific stock questions
        if any(symbol in query for symbol in self.common_symbols.values()):
            if is_weekend:
                return 'stock_overview_weekend'
            elif not is_market_hours:
                return 'stock_overview_premarket' if current_time < market_open else 'stock_overview_postmarket'
            else:
                return 'stock_overview'
        
        # Check for options questions
        if any(term in query for term in ['option', 'options', 'call', 'calls', 'put', 'puts']):
            if is_weekend:
                return 'options_overview_weekend'
            elif not is_market_hours:
                return 'options_overview_premarket' if current_time < market_open else 'options_overview_postmarket'
            else:
                return 'options_overview'
        
        # Check for technical analysis questions
        if any(indicator in query for indicator in self.technical_indicators.keys()):
            return 'technical_analysis'
        
        # Check for strategy questions
        if any(term in query for term in ['strategy', 'strategies', 'approach', 'method', 'plan']):
            return 'strategy'
        
        # Check for risk management questions
        if any(term in query for term in ['risk', 'risks', 'management', 'manage', 'protect']):
            return 'risk_management'
        
        # Default to general market overview if intent is unclear
        if is_weekend:
            return 'market_overview_weekend'
        elif not is_market_hours:
            return 'market_overview_premarket' if current_time < market_open else 'market_overview_postmarket'
        else:
            return 'market_overview'

    def _extract_timeframe(self, query: str) -> Dict[str, Any]:
        """Extract timeframe information from query with enhanced casual language support."""
        query = query.lower()
        
        # Enhanced timeframe patterns
        timeframe_patterns = {
            # Standard patterns
            r'(last|past|previous|recent)\s*(\d+)\s*(days?|weeks?|months?|years?|hours?|minutes?)': lambda m: (int(m.group(2)), m.group(3)),
            # Casual patterns
            r'(next|upcoming)\s*(month|week|year)': lambda m: (1, m.group(2)),
            r'this\s*(month|week|year)': lambda m: (0, m.group(1)),
            r'last\s*(month|week|year)': lambda m: (1, m.group(1)),
            r'next\s*(\d+)\s*(months|weeks|years)': lambda m: (int(m.group(1)), m.group(2)),
            r'in\s*(\d+)\s*(months|weeks|years)': lambda m: (int(m.group(1)), m.group(2)),
            # Relative patterns
            r'today': lambda m: (0, 'day'),
            r'tomorrow': lambda m: (1, 'day'),
            r'yesterday': lambda m: (1, 'day'),
            r'next\s*friday': lambda m: (1, 'week'),  # Approximate
            r'end\s*of\s*(month|week)': lambda m: (1, m.group(1)),
            r'beginning\s*of\s*(month|week)': lambda m: (0, m.group(1))
        }
        
        for pattern, extractor in timeframe_patterns.items():
            match = re.search(pattern, query)
            if match:
                amount, unit = extractor(match)
                
                # Convert to appropriate timeframe
                if 'minute' in unit:
                    timeframe = Timeframe.MINUTE
                    days = amount / (24 * 60)
                elif 'hour' in unit:
                    timeframe = Timeframe.HOUR
                    days = amount / 24
                elif 'week' in unit:
                    timeframe = Timeframe.WEEK
                    days = amount * 7
                elif 'month' in unit:
                    timeframe = Timeframe.MONTH
                    days = amount * 30
                elif 'year' in unit:
                    timeframe = Timeframe.MONTH
                    days = amount * 365
                else:
                    timeframe = Timeframe.DAY
                    days = amount
                    
                # Calculate dates
                now = datetime.now()
                if 'next' in pattern or 'upcoming' in pattern:
                    start_date = now
                    end_date = now + timedelta(days=days)
                elif 'last' in pattern or 'previous' in pattern:
                    start_date = now - timedelta(days=days)
                    end_date = now
                else:
                    start_date = now - timedelta(days=days/2)
                    end_date = now + timedelta(days=days/2)
                
                return {
                    'timeframe': timeframe.value,
                    'amount': amount,
                    'days': days,
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d')
                }
        
        # Default timeframe (30 days) if no timeframe specified
        now = datetime.now()
        return {
            'timeframe': Timeframe.DAY.value,
            'amount': 30,
            'days': 30,
            'start_date': (now - timedelta(days=30)).strftime('%Y-%m-%d'),
            'end_date': now.strftime('%Y-%m-%d')
        }

    def _extract_comparison(self, query: str) -> Optional[str]:
        """Extract comparison symbol from query."""
        comparison_match = re.search(self.patterns['comparison'], query)
        if comparison_match:
            return comparison_match.group(2)
        return None

    def _extract_parameters(self, query: str) -> Dict[str, Any]:
        """Extract additional parameters from query."""
        params = {}
        
        # Check for specific indicators
        for indicator, config in self.technical_indicators.items():
            if indicator in query:
                params[indicator] = config
                
        # Enhanced options parameters
        if 'strike' in query:
            strike_match = re.search(r'strike\s*(\d+)', query)
            if strike_match:
                params['strike_price'] = float(strike_match.group(1))
                
        if 'expiration' in query:
            exp_match = re.search(r'expiration\s*(\d{1,2}/\d{1,2}/\d{2,4})', query)
            if exp_match:
                params['expiration_date'] = exp_match.group(1)
                
        # Options strategy parameters
        if 'spread' in query:
            spread_types = ['vertical', 'horizontal', 'diagonal', 'butterfly', 'condor', 'iron condor']
            for spread in spread_types:
                if spread in query:
                    params['spread_type'] = spread
                    break
                    
        # Greeks parameters
        greeks = ['delta', 'gamma', 'theta', 'vega', 'rho']
        for greek in greeks:
            if greek in query:
                params[greek] = True
                
        # Moneyness parameters
        moneyness = ['itm', 'otm', 'atm']
        for money in moneyness:
            if money in query:
                params['moneyness'] = money
                
        return params

    def _extract_strategy_components(self, query: str) -> Dict[str, Any]:
        """Extract strategy-related components from query."""
        components = {}
        
        # Check for strategy type
        strategy_types = ['momentum', 'mean reversion', 'breakout', 'trend following', 'swing trading']
        for strategy in strategy_types:
            if strategy in query:
                components['strategy_type'] = strategy
                break
                
        # Check for timeframe
        if 'intraday' in query:
            components['timeframe'] = 'intraday'
        elif 'swing' in query:
            components['timeframe'] = 'swing'
        elif 'position' in query:
            components['timeframe'] = 'position'
            
        return components

    def _extract_risk_parameters(self, query: str) -> Dict[str, Any]:
        """Extract risk management parameters from query."""
        risk_params = {}
        
        # Check for position size
        if 'position size' in query or 'position sizing' in query:
            risk_params['position_size'] = True
            
        # Check for stop loss
        if 'stop loss' in query:
            stop_match = re.search(r'stop loss\s*(\d+\.?\d*)%?', query)
            if stop_match:
                risk_params['stop_loss'] = float(stop_match.group(1))
                
        # Check for take profit
        if 'take profit' in query or 'target' in query:
            target_match = re.search(r'(take profit|target)\s*(\d+\.?\d*)%?', query)
            if target_match:
                risk_params['take_profit'] = float(target_match.group(2))
                
        return risk_params

    def _extract_technical_indicators(self, query: str) -> List[Dict[str, Any]]:
        """Extract technical indicators and their parameters from query."""
        indicators = []
        
        for indicator, config in self.technical_indicators.items():
            if indicator in query:
                # Extract custom periods if specified
                period_match = re.search(f'{indicator}\s*(\d+)', query)
                if period_match:
                    config['period'] = int(period_match.group(1))
                indicators.append(config)
                
        return indicators

    def _format_alpaca_query(self, query: str) -> Dict[str, Any]:
        """Format the query for Alpaca API consumption."""
        symbol = self._extract_symbol(query)
        timeframe = self._extract_timeframe(query)
        indicators = self._extract_technical_indicators(query)
        
        alpaca_query = {
            'symbol': symbol,
            'timeframe': timeframe['timeframe'],
            'start_date': timeframe['start_date'],
            'end_date': timeframe['end_date'],
            'indicators': [ind['name'] for ind in indicators],
            'parameters': self._extract_parameters(query),
            'strategy_components': self._extract_strategy_components(query),
            'risk_parameters': self._extract_risk_parameters(query)
        }
        
        return alpaca_query 

    def _extract_strike_price(self, query: str) -> Optional[float]:
        """Extract strike price from query."""
        # Look for patterns like "150 calls", "strike 150", "at 150"
        patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:strike|level|price|at)?\s*(?:calls?|puts?)',  # "150 calls", "150 strike calls"
            r'strike\s*(\d+(?:\.\d+)?)',          # "strike 150"
            r'at\s*(\d+(?:\.\d+)?)',              # "at 150"
            r'(\d+(?:\.\d+)?)\s*strike',          # "150 strike"
            r'(\d+(?:\.\d+)?)\s*level',           # "150 level"
            r'(\d+(?:\.\d+)?)\s*price'            # "150 price"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                try:
                    # Get the first group that contains the number
                    strike = float(match.group(1))
                    logger.info(f"Extracted strike price: {strike}")
                    return strike
                except (ValueError, IndexError):
                    continue
                    
        logger.warning("No strike price found in query")
        return None

    def _extract_expiration(self, query: str) -> Optional[str]:
        """Extract expiration date from query."""
        # Look for patterns like "expiring next month", "expiration in 2 weeks"
        patterns = [
            r'expir(?:ing|es|ation)?\s*(?:in|on)?\s*(\d+)\s*(weeks?|months?|days?)',
            r'next\s*(month|week|friday|monday|tuesday|wednesday|thursday)',
            r'this\s*(month|week|friday|monday|tuesday|wednesday|thursday)',
            r'end\s*of\s*(month|week)',
            r'(\d+)(?:st|nd|rd|th)\s*(?:of\s*)?(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                try:
                    if 'next' in pattern:
                        day = match.group(1).lower()
                        if day in ['friday', 'monday', 'tuesday', 'wednesday', 'thursday']:
                            return f"next {day}"
                        return f"next {match.group(1)}"
                    elif 'this' in pattern:
                        day = match.group(1).lower()
                        if day in ['friday', 'monday', 'tuesday', 'wednesday', 'thursday']:
                            return f"this {day}"
                        return f"this {match.group(1)}"
                    elif 'end' in pattern:
                        return f"end of {match.group(1)}"
                    else:
                        amount = int(match.group(1))
                        unit = match.group(2)
                        return f"{amount} {unit}"
                except (ValueError, IndexError):
                    continue
                    
        # If no specific expiration found, default to next Friday
        logger.info("No expiration found, defaulting to next Friday")
        return "next friday"

    def _extract_greeks(self, query: str) -> List[str]:
        """Extract requested Greeks from query."""
        greeks = []
        greek_patterns = {
            'delta': r'delta',
            'gamma': r'gamma',
            'theta': r'theta',
            'vega': r'vega',
            'rho': r'rho'
        }
        
        for greek, pattern in greek_patterns.items():
            if re.search(pattern, query):
                greeks.append(greek)
                
        return greeks 
