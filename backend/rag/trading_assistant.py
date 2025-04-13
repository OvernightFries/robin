import os
from typing import List, Dict, Optional
from langchain_community.embeddings import OllamaEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from alpaca_alp.market_data import AlpacaMarketData
from alpaca_alp.options_scanner import OptionsScanner

class TradingAssistant:
    def __init__(self):
        """Initialize both RAG and market data systems."""
        # Initialize Pinecone for RAG
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index = self.pc.Index(os.getenv("PINECONE_INDEX_NAME"))
        self.embedding = OllamaEmbeddings(model="llama3")
        self.vectorstore = PineconeVectorStore(self.index, self.embedding, "text")
        
        # Initialize market data
        self.market_data = AlpacaMarketData()
        self.scanner = OptionsScanner()
    
    def find_relevant_strategies(self, query: str, symbol: str) -> List[Dict]:
        """Find relevant trading strategies using RAG."""
        # Get current market conditions
        market_conditions = self.market_data.get_market_conditions(symbol)
        
        # Enhance query with market context
        enhanced_query = f"""
        Current market conditions for {symbol}:
        - Price: ${market_conditions['price_data']['last_price']}
        - IV: {market_conditions['volatility_data']['historical_volatility']:.2%}
        
        Query: {query}
        """
        
        # Search for relevant strategies
        docs = self.vectorstore.similarity_search(enhanced_query, k=3)
        
        # Format results
        strategies = []
        for doc in docs:
            strategies.append({
                'content': doc.page_content,
                'source': doc.metadata.get('source', 'Unknown'),
                'relevance_score': doc.metadata.get('score', 0)
            })
        
        return strategies
    
    def validate_strategy(self, strategy: Dict, symbol: str) -> Dict:
        """Validate a strategy against current market conditions."""
        # Get current market data
        market_data = self.market_data.get_market_conditions(symbol)
        
        # Check if strategy is feasible
        validation = {
            'strategy': strategy['content'],
            'symbol': symbol,
            'is_feasible': True,
            'reasons': [],
            'suggested_adjustments': []
        }
        
        # Example validation checks
        if 'high volatility' in strategy['content'].lower():
            current_iv = market_data['volatility_data']['historical_volatility']
            if current_iv < 0.3:  # Example threshold
                validation['is_feasible'] = False
                validation['reasons'].append(f"Current IV ({current_iv:.2%}) is too low for this strategy")
                validation['suggested_adjustments'].append("Consider waiting for higher volatility")
        
        if 'credit spread' in strategy['content'].lower():
            # Check if we can find suitable strikes
            spreads = self.scanner.find_credit_spreads(symbol)
            if not spreads:
                validation['is_feasible'] = False
                validation['reasons'].append("No suitable credit spreads found")
                validation['suggested_adjustments'].append("Consider different strike prices or expiration")
        
        return validation
    
    def get_trading_recommendations(self, query: str, symbol: str) -> Dict:
        """Get comprehensive trading recommendations."""
        # Find relevant strategies
        strategies = self.find_relevant_strategies(query, symbol)
        
        # Validate each strategy
        validated_strategies = []
        for strategy in strategies:
            validation = self.validate_strategy(strategy, symbol)
            validated_strategies.append(validation)
        
        # Get current market opportunities
        opportunities = {
            'high_iv': self.scanner.scan_high_iv_options(symbol),
            'credit_spreads': self.scanner.find_credit_spreads(symbol),
            'volume_spikes': self.scanner.scan_volume_spikes(symbol)
        }
        
        return {
            'query': query,
            'symbol': symbol,
            'validated_strategies': validated_strategies,
            'current_opportunities': opportunities
        }

def main():
    assistant = TradingAssistant()
    
    # Example usage
    query = "What's a good options strategy for a sideways market?"
    symbol = "AAPL"
    
    recommendations = assistant.get_trading_recommendations(query, symbol)
    
    print("\n=== Trading Recommendations ===")
    print(f"\nQuery: {query}")
    print(f"Symbol: {symbol}")
    
    print("\nValidated Strategies:")
    for strategy in recommendations['validated_strategies']:
        print(f"\nStrategy: {strategy['strategy'][:100]}...")
        print(f"Feasible: {strategy['is_feasible']}")
        if not strategy['is_feasible']:
            print("Reasons:")
            for reason in strategy['reasons']:
                print(f"  - {reason}")
            print("Suggestions:")
            for suggestion in strategy['suggested_adjustments']:
                print(f"  - {suggestion}")
    
    print("\nCurrent Opportunities:")
    print("\nHigh IV Options:")
    for option in recommendations['current_opportunities']['high_iv'][:3]:
        print(f"  {option['type'].upper()} ${option['strike']} (IV: {option['iv']:.2%})")
    
    print("\nCredit Spreads:")
    for spread in recommendations['current_opportunities']['credit_spreads'][:3]:
        print(f"  {spread['type'].replace('_', ' ').title()}")
        print(f"  Strikes: ${spread['short_strike']} / ${spread['long_strike']}")
        print(f"  Credit: ${spread['credit']:.2f}")

if __name__ == "__main__":
    main() 
