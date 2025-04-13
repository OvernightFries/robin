import os
from pathlib import Path
from typing import List
import PyPDF2
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import OllamaEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file."""
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    return "\n".join([page.page_content for page in pages])

def clean_text_pass1(text: str) -> str:
    """First pass: Basic text cleaning and structure normalization."""
    # Remove headers/footers and page numbers
    text = re.sub(r'\n\d+\n', '\n', text)  # Page numbers
    text = re.sub(r'Page \d+ of \d+', '', text)  # Page X of Y
    text = re.sub(r'©.*?\n', '\n', text)  # Copyright notices
    text = re.sub(r'Confidential.*?\n', '\n', text)  # Confidential notices
    
    # Remove URLs and email addresses
    text = re.sub(r'http\S+|www.\S+', '', text)
    text = re.sub(r'\S+@\S+', '', text)
    
    # Clean whitespace and formatting
    text = re.sub(r'\s+', ' ', text)  # Multiple spaces
    text = re.sub(r'\n\s*\n', '\n', text)  # Multiple newlines
    text = text.strip()
    
    # Remove special characters but preserve mathematical symbols
    text = re.sub(r'[^\w\s$%.,()+\-*/=<>]', ' ', text)
    
    return text

def clean_text_pass2(text: str) -> str:
    """Second pass: Domain-specific cleaning for options and trading."""
    # Clean mathematical expressions and preserve explanations
    text = re.sub(r'\$\$.*?\$\$', 'EQUATION', text)  # Block equations
    text = re.sub(r'\$.*?\$', 'EQUATION', text)      # Inline equations
    text = re.sub(r'\\[a-zA-Z]+', 'MATH_SYMBOL', text)  # LaTeX symbols
    
    # Preserve mathematical explanations
    text = re.sub(r'\b(derivative|partial derivative|integral|differentiation|integration)\b', 'CALCULUS_TERM', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(function|variable|constant|parameter|coefficient)\b', 'MATH_TERM', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(limit|convergence|divergence|series|sequence)\b', 'CALCULUS_CONCEPT', text, flags=re.IGNORECASE)
    
    # Clean probability and statistics concepts
    text = re.sub(r'\b(probability|likelihood|chance|odds)\b', 'PROBABILITY_TERM', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(expectation|expected value|mean|variance|standard deviation|std dev)\b', 'STATISTICAL_MEASURE', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(distribution|normal|lognormal|binomial|poisson|geometric)\b', 'DISTRIBUTION_TYPE', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(cumulative|probability density|PDF|CDF|PMF)\b', 'DISTRIBUTION_FUNCTION', text, flags=re.IGNORECASE)
    
    # Clean stochastic processes
    text = re.sub(r'\b(random walk|Brownian motion|Wiener process|martingale)\b', 'STOCHASTIC_PROCESS', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(geometric Brownian motion|GBM|Ito process|diffusion)\b', 'STOCHASTIC_MODEL', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(volatility smile|skew|kurtosis|fat tails)\b', 'DISTRIBUTION_CHARACTERISTIC', text, flags=re.IGNORECASE)
    
    # Clean financial symbols and tickers
    text = re.sub(r'[€£¥$]', 'CURRENCY', text)
    text = re.sub(r'\b[A-Z]{1,5}\b', 'TICKER', text)  # Stock tickers
    
    # Clean options symbols and identifiers
    text = re.sub(r'\b[A-Z]{1,5}\d{6}[CP]\d{8}\b', 'OPTION_SYMBOL', text)  # Full option symbol
    text = re.sub(r'\b[A-Z]{1,5}\d{6}[CP]\b', 'OPTION_SYMBOL', text)  # Shorter option symbol
    text = re.sub(r'\b[A-Z]{1,5}\s+\d{1,2}[A-Z]{3}\d{2}\s+[CP]\s+\d+\.?\d*\b', 'OPTION_SYMBOL', text)  # Spaced format
    
    # Clean prices and monetary values
    text = re.sub(r'\$\d+\.?\d*', 'PRICE', text)  # Dollar amounts
    text = re.sub(r'\d+\.?\d*\s*(bps|points|pips)', 'PRICE_UNIT', text)  # Price units
    text = re.sub(r'(\d{1,3}(,\d{3})+)', 'NUMBER', text)  # Large numbers
    text = re.sub(r'\d+%', 'PERCENTAGE', text)  # Percentages
    
    # Clean dates and time periods
    text = re.sub(r'\d{1,2}/\d{1,2}/\d{2,4}', 'DATE', text)  # MM/DD/YYYY
    text = re.sub(r'\d{4}-\d{2}-\d{2}', 'DATE', text)  # YYYY-MM-DD
    text = re.sub(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', 'DATE', text)
    text = re.sub(r'\b\d{1,2}:\d{2}(:\d{2})?\s*(AM|PM)?\b', 'TIME', text)
    
    # Clean Greeks and risk metrics with mathematical context
    text = re.sub(r'\b(delta|gamma|theta|vega|rho)\b', 'GREEK', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(implied volatility|IV|historical volatility|HV)\b', 'VOLATILITY', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(beta|alpha|sharpe ratio|sortino ratio)\b', 'RISK_METRIC', text, flags=re.IGNORECASE)
    
    # Preserve mathematical explanations of Greeks
    text = re.sub(r'\b(rate of change|sensitivity|acceleration|convexity)\b', 'DERIVATIVE_TERM', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(second derivative|partial derivative with respect to)\b', 'HIGHER_ORDER_DERIVATIVE', text, flags=re.IGNORECASE)
    
    # Clean option strategies
    text = re.sub(r'\b(vertical|horizontal|diagonal|butterfly|condor|straddle|strangle)\b', 'OPTION_STRATEGY', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(iron condor|iron butterfly|jade lizard|broken wing butterfly)\b', 'COMPLEX_STRATEGY', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(calendar spread|ratio spread|backspread|frontspread)\b', 'SPREAD_STRATEGY', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(collar|fence|seagull|risk reversal)\b', 'RISK_MANAGEMENT_STRATEGY', text, flags=re.IGNORECASE)
    
    # Clean option types and status
    text = re.sub(r'\b(call|put)\b', 'OPTION_TYPE', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(ITM|OTM|ATM|in-the-money|out-of-the-money|at-the-money)\b', 'OPTION_STATUS', text, flags=re.IGNORECASE)
    
    # Clean trading terms and market data
    text = re.sub(r'\b(bid|ask|spread|volume|open interest|OI|VWAP|TWAP)\b', 'TRADING_TERM', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(market order|limit order|stop order|stop-limit order)\b', 'ORDER_TYPE', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(long|short|bullish|bearish|neutral)\b', 'POSITION_TYPE', text, flags=re.IGNORECASE)
    
    # Clean technical indicators
    text = re.sub(r'\b(RSI|MACD|Bollinger Bands|Moving Average|MA|EMA|SMA)\b', 'TECHNICAL_INDICATOR', text)
    text = re.sub(r'\b(support|resistance|trend line|channel|breakout|breakdown)\b', 'TECHNICAL_TERM', text, flags=re.IGNORECASE)
    
    # Clean market conditions
    text = re.sub(r'\b(bull market|bear market|sideways|consolidation|trending)\b', 'MARKET_CONDITION', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(overbought|oversold|divergence|convergence)\b', 'MARKET_STATE', text, flags=re.IGNORECASE)
    
    # Clean quantitative strategies
    text = re.sub(r'\b(statistical arbitrage|pairs trading|mean reversion|momentum)\b', 'QUANT_STRATEGY', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(market making|high frequency trading|HFT|algorithmic trading)\b', 'ALGO_STRATEGY', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(factor investing|smart beta|risk parity|trend following)\b', 'FACTOR_STRATEGY', text, flags=re.IGNORECASE)
    
    # Clean strategy parameters
    text = re.sub(r'\b(entry|exit|stop loss|take profit|position sizing)\b', 'STRATEGY_PARAMETER', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(backtest|forward test|walk forward|optimization)\b', 'STRATEGY_TESTING', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(profit factor|win rate|risk reward ratio|max drawdown)\b', 'STRATEGY_METRIC', text, flags=re.IGNORECASE)
    
    # Preserve mathematical relationships
    text = re.sub(r'\b(proportional to|inversely proportional|correlation|covariance)\b', 'MATH_RELATIONSHIP', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(linear|nonlinear|exponential|logarithmic)\b', 'MATH_FUNCTION_TYPE', text, flags=re.IGNORECASE)
    
    # Clean risk and probability measures
    text = re.sub(r'\b(VaR|Value at Risk|expected shortfall|ES|CVaR)\b', 'RISK_MEASURE', text)
    text = re.sub(r'\b(confidence interval|significance level|p-value)\b', 'STATISTICAL_SIGNIFICANCE', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(monte carlo|simulation|random sampling)\b', 'SIMULATION_METHOD', text, flags=re.IGNORECASE)
    
    return text

def clean_text(text: str) -> str:
    """Two-pass text cleaning."""
    text = clean_text_pass1(text)
    text = clean_text_pass2(text)
    return text

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """Split text into chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    return text_splitter.split_text(text)

def process_pdfs_to_pinecone(docs_dir: str = "data/docs"):
    """Process all PDFs in directory and store in Pinecone."""
    # Initialize Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
    embedding = OllamaEmbeddings(model="llama3")
    vectorstore = PineconeVectorStore(index, embedding, "text")
    
    # Process each PDF
    for pdf_file in Path(docs_dir).glob("*.pdf"):
        print(f"Processing {pdf_file.name}...")
        
        # Extract and clean text
        text = extract_text_from_pdf(str(pdf_file))
        text = clean_text(text)
        
        # Split into chunks
        chunks = chunk_text(text)
        
        # Add to Pinecone
        for i, chunk in enumerate(chunks):
            vectorstore.add_texts(
                texts=[chunk],
                metadatas=[{"source": pdf_file.name, "chunk": i}]
            )
        
        print(f"Added {len(chunks)} chunks from {pdf_file.name} to Pinecone")

if __name__ == "__main__":
    process_pdfs_to_pinecone() 
