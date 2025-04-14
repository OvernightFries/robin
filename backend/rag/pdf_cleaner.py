import re
import logging
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF
from pathlib import Path
import hashlib
import json
import requests
import aiohttp
import os
from pinecone import Pinecone
import uuid
from dotenv import load_dotenv
import asyncio
from langchain.text_splitter import RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFCleaner:
    def __init__(self, index_name: str = "robindocs", namespace: str = ""):
        # Load environment variables
        load_dotenv()
        
        # Initialize Pinecone
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable is not set")
            
        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name
        self.namespace = namespace
        self.index = self.pc.Index(self.index_name)
        
        # Set embedding dimension for nomic-embed-text (768 dimensions)
        self.embedding_dim = 768
        
        # Ollama configuration
        self.ollama_host = "http://localhost:11434"  # Fixed port number
        self.embedding_model = "nomic-embed-text"
        
        # Mathematical Symbols and Operators
        self.math_symbols = {
            'calculus': [
                '∂', '∫', '∮', '∇', 'Δ', '∑', '∏', '∞', 'lim', '→', '←', '↔',
                'd/dx', '∂/∂x', '∂²/∂x²', '∫_a^b', '∮_C', '∇·', '∇×', '∇²'
            ],
            'algebra': [
                '∈', '∉', '⊂', '⊃', '∪', '∩', '∅', '∀', '∃', '¬', '∧', '∨',
                '⇒', '⇔', '≡', '≠', '≈', '≅', '∼', '∝', '±', '×', '÷', '√',
                '∑', '∏', '∩', '∪', '⊂', '⊃', '∈', '∉', '∅', '∞'
            ],
            'greek_letters': [
                'α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ', 'ι', 'κ', 'λ', 'μ',
                'ν', 'ξ', 'ο', 'π', 'ρ', 'σ', 'τ', 'υ', 'φ', 'χ', 'ψ', 'ω',
                'Γ', 'Δ', 'Θ', 'Λ', 'Ξ', 'Π', 'Σ', 'Φ', 'Ψ', 'Ω'
            ]
        }

        # Regular expression patterns for cleaning
        self.patterns = {
            'noise_patterns': {
                'urls': r'https?://\S+|www\.\S+',
                'emails': r'\S+@\S+',
                'page_numbers': r'^\s*\d+\s*$',
                'headers_footers': r'^(?:Page|Chapter|Section)\s+\d+.*$',
                'bullet_points': r'^[\s•\-*]\s*',
                'excessive_whitespace': r'\s+',
                'table_of_contents': r'^(?:Table of Contents|Contents).*$',
                'copyright': r'©.*$',
                'isbn': r'ISBN.*$',
                'references': r'^(?:References|Bibliography).*$',
                'footnotes': r'^\d+\.\s*'
            },
            'math_symbols': r'[∂∫∮∇Δ∑∏∞→←↔∈∉⊂⊃∪∩∅∀∃¬∧∨⇒⇔≡≠≈≅∼∝±×÷√αβγδεζηθικλμνξοπρστυφχψωΓΔΘΛΞΠΣΦΨΩ]',
            'equations': r'\$[^$]+\$|\\\([^)]+\\\)|\\\[[^\]]+\\\]',
            'black_scholes': r'C\s*=\s*S[_0]N\(d[_1]\)\s*-\s*Ke\^{-rT}N\(d[_2]\)',
            'd1_d2': r'd[_1]\s*=\s*\([ln|log]\(S[_0]/K\)\s*[+]\s*\(r\s*[+]\s*[σσ]\^2/2\)T\)/\([σσ]\s*sqrt\{T\}\)',
            'ito_lemma': r'dX[_t]\s*=\s*[μμ]\(X[_t],t\)dt\s*[+]\s*[σσ]\(X[_t],t\)dW[_t]'
        }

        # Mathematical Terms and Concepts
        self.math_terms = {
            'calculus': [
                'derivative', 'integral', 'differential', 'gradient', 'partial derivative',
                'limit', 'continuity', 'convergence', 'taylor series', 'fourier series',
                'laplace transform', 'complex analysis', 'contour integral', 'residue',
                'cauchy-riemann', 'analytic function', 'harmonic function', 'conformal mapping',
                'vector calculus', 'divergence', 'curl', 'line integral', 'surface integral',
                'volume integral', 'green theorem', 'stokes theorem', 'divergence theorem',
                'jacobian', 'hessian', 'tensor', 'manifold', 'differential form'
            ],
            'algebra': [
                'group', 'ring', 'field', 'vector space', 'linear transformation',
                'matrix', 'determinant', 'eigenvalue', 'eigenvector', 'basis',
                'dimension', 'rank', 'nullity', 'orthogonal', 'orthonormal',
                'inner product', 'outer product', 'tensor product', 'direct sum',
                'quotient space', 'isomorphism', 'homomorphism', 'kernel', 'image',
                'polynomial', 'root', 'factor', 'gcd', 'lcm', 'modulo', 'congruence'
            ],
            'probability': [
                'probability', 'distribution', 'random variable', 'expected value',
                'variance', 'standard deviation', 'correlation', 'covariance',
                'normal distribution', 'poisson', 'binomial', 'monte carlo',
                'markov chain', 'stochastic process', 'brownian motion', 'martingale',
                'ito process', 'stochastic differential equation', 'fokker-planck',
                'kolmogorov equation', 'ergodic', 'stationary', 'autocorrelation',
                'spectral density', 'power spectrum', 'fourier transform'
            ]
        }

        # Financial Terms and Greeks
        self.financial_terms = {
            'greeks': [
                'delta', 'gamma', 'theta', 'vega', 'rho', 'vanna', 'volga',
                'charm', 'speed', 'color', 'zomma', 'ultima', 'vomma',
                'delta-gamma', 'delta-vega', 'gamma-vega', 'cross-gamma'
            ],
            'risk_metrics': [
                'alpha', 'beta', 'sharpe ratio', 'sortino ratio', 'information ratio',
                'maximum drawdown', 'value at risk', 'volatility', 'correlation',
                'r-squared', 'tracking error', 'jensen alpha', 'treynor ratio',
                'calmar ratio', 'omega ratio', 'ulcer index', 'kurtosis', 'skewness'
            ],
            'valuation_metrics': [
                'present value', 'future value', 'npv', 'irr', 'yield',
                'duration', 'convexity', 'forward rate', 'spot rate', 'yield curve',
                'term structure', 'discount factor', 'annuity', 'perpetuity',
                'modified duration', 'key rate duration', 'option adjusted spread',
                'zero coupon', 'par yield', 'bootstrapping'
            ]
        }

        # Trading Strategies by Category with Mathematical Components
        self.strategy_patterns = {
            # Stock Trading Core Strategies
            'fundamental': r'(?:value\s+investing|growth\s+investing|dividend\s+growth|quality\s+factor|momentum\s+factor|low\s+volatility|high\s+yield|defensive|cyclical|sector\s+rotation)',
            'technical': r'(?:trend\s+following|mean\s+reversion|breakout\s+trading|swing\s+trading|scalping|day\s+trading|position\s+trading|range\s+trading)',
            'quantitative': r'(?:factor\s+investing|statistical\s+arbitrage|pairs\s+trading|market\s+neutral|long\s+short|smart\s+beta|risk\s+premia|alpha\s+generation)',
            
            # Options Strategies with Greeks
            'options_basic': r'(?:covered\s+call|protective\s+put|buy\s+write|married\s+put|collar|synthetic\s+stock|protective\s+collar|delta\s+neutral)',
            'options_spread': r'(?:vertical\s+spread|calendar\s+spread|diagonal\s+spread|iron\s+condor|iron\s+butterfly|jade\s+lizard|broken\s+wing\s+butterfly|theta\s+positive)',
            'options_volatility': r'(?:straddle|strangle|ratio\s+spread|backspreads|calendar\s+ratio|double\s+calendar|volatility\s+arbitrage|vega\s+trading)',
            
            # Advanced Trading Concepts with Math
            'portfolio_management': r'(?:asset\s+allocation|portfolio\s+optimization|risk\s+parity|tactical\s+allocation|strategic\s+allocation|rebalancing|factor\s+allocation|correlation\s+matrix)',
            'risk_management': r'(?:position\s+sizing|stop\s+loss|take\s+profit|trailing\s+stop|risk\s+reward\s+ratio|portfolio\s+hedging|delta\s+hedging|gamma\s+hedging|beta\s+hedging)',
            'market_microstructure': r'(?:order\s+flow|market\s+making|liquidity\s+analysis|tick\s+data|bid\s+ask\s+spread|order\s+book|depth\s+analysis|market\s+impact)',
            
            # Mathematical Trading
            'quant_methods': r'(?:time\s+series\s+analysis|stochastic\s+calculus|brownian\s+motion|monte\s+carlo\s+simulation|numerical\s+methods|optimization|machine\s+learning|kalman\s+filter)',
            'derivatives_math': r'(?:black\s+scholes|binomial\s+model|trinomial\s+tree|finite\s+difference|partial\s+differential\s+equation|ito\s+calculus|martingale|wiener\s+process)',
            
            # Market Analysis with Statistics
            'intermarket': r'(?:correlation\s+analysis|cross\s+asset|relative\s+strength|intermarket\s+analysis|asset\s+class\s+correlation|rotation\s+analysis|cointegration)',
            'sentiment': r'(?:market\s+sentiment|fear\s+greed|put\s+call\s+ratio|vix\s+analysis|market\s+breadth|advance\s+decline|tick\s+index|standard\s+deviation)'
        }

        # Technical Indicators with Mathematical Components
        self.technical_indicators = {
            'trend': [
                'Moving Average', 'MACD', 'Directional Movement', 'Parabolic SAR',
                'Trend Lines', 'Channels', 'Fibonacci', 'Ichimoku Cloud',
                'Linear Regression', 'Exponential Moving Average'
            ],
            'momentum': [
                'RSI', 'Stochastic', 'CCI', 'Williams %R', 'Rate of Change',
                'Momentum', 'Relative Vigor Index', 'Ultimate Oscillator',
                'Stochastic RSI', 'Fisher Transform'
            ],
            'volume': [
                'On-Balance Volume', 'Volume Profile', 'Money Flow Index',
                'Accumulation/Distribution', 'Volume RSI', 'Chaikin Money Flow',
                'Volume Weighted Average Price', 'Negative Volume Index'
            ],
            'volatility': [
                'Bollinger Bands', 'ATR', 'Keltner Channels', 'Standard Deviation',
                'Volatility Index', 'Historical Volatility', 'Normalized ATR',
                'Chaikin Volatility', 'Volatility Ratio', 'Volatility Stop'
            ],
            'oscillators': [
                'Detrended Price Oscillator', 'Percentage Price Oscillator',
                'Chande Momentum Oscillator', 'Aroon Oscillator', 'True Strength Index'
            ]
        }

        # Chart Patterns
        self.chart_patterns = {
            'reversal': [
                'Head and Shoulders', 'Double Top', 'Double Bottom', 'Triple Top',
                'Triple Bottom', 'Rounding Bottom', 'Cup and Handle'
            ],
            'continuation': [
                'Triangle', 'Flag', 'Pennant', 'Rectangle', 'Wedge',
                'Channel', 'Measured Move'
            ],
            'candlestick': [
                'Doji', 'Hammer', 'Shooting Star', 'Engulfing', 'Harami',
                'Morning Star', 'Evening Star', 'Three White Soldiers'
            ]
        }

        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=50
        )

    def first_pass_clean(self, text: str) -> str:
        """First pass cleaning: basic text normalization and noise removal."""
        try:
            # Remove URLs and emails
            text = re.sub(self.patterns['noise_patterns']['urls'], '', text)
            text = re.sub(self.patterns['noise_patterns']['emails'], '', text)
            
            # Remove page numbers, headers, and footers
            text = re.sub(self.patterns['noise_patterns']['page_numbers'], '', text, flags=re.MULTILINE)
            text = re.sub(self.patterns['noise_patterns']['headers_footers'], '', text, flags=re.MULTILINE)
            
            # Remove bullet points and excessive whitespace
            text = re.sub(self.patterns['noise_patterns']['bullet_points'], '', text, flags=re.MULTILINE)
            text = re.sub(self.patterns['noise_patterns']['excessive_whitespace'], ' ', text)
            
            # Remove table of contents, copyright notices, ISBNs
            text = re.sub(self.patterns['noise_patterns']['table_of_contents'], '', text, flags=re.MULTILINE)
            text = re.sub(self.patterns['noise_patterns']['copyright'], '', text)
            text = re.sub(self.patterns['noise_patterns']['isbn'], '', text)
            
            # Remove references and footnotes sections
            text = re.sub(self.patterns['noise_patterns']['references'], '', text, flags=re.MULTILINE)
            text = re.sub(self.patterns['noise_patterns']['footnotes'], '', text, flags=re.MULTILINE)
            
            return text.strip()
        except Exception as e:
            logger.error(f"Error in first pass cleaning: {str(e)}")
            return text

    def second_pass_clean(self, text: str) -> str:
        """Second pass cleaning: enhance formatting and preserve important content."""
        try:
            # Preserve mathematical content
            math_matches = re.finditer(self.patterns['math_symbols'], text)
            for match in math_matches:
                # Ensure proper spacing around mathematical symbols
                start, end = match.span()
                if start > 0 and text[start-1] != ' ':
                    text = text[:start] + ' ' + text[start:]
                if end < len(text) and text[end] != ' ':
                    text = text[:end] + ' ' + text[end:]
            
            # Preserve equations
            equation_matches = re.finditer(r'\$[^$]+\$', text)
            for match in equation_matches:
                # Ensure proper spacing around equations
                start, end = match.span()
                if start > 0 and text[start-1] != ' ':
                    text = text[:start] + ' ' + text[start:]
                if end < len(text) and text[end] != ' ':
                    text = text[:end] + ' ' + text[end:]
            
            # Preserve LaTeX-style equations
            latex_matches = re.finditer(r'\\begin\{[^}]+\}.*?\\end\{[^}]+\}', text, re.DOTALL)
            for match in latex_matches:
                start, end = match.span()
                if start > 0 and text[start-1] != ' ':
                    text = text[:start] + ' ' + text[start:]
                if end < len(text) and text[end] != ' ':
                    text = text[:end] + ' ' + text[end:]
            
            # Preserve financial formulas with proper spacing
            formula_patterns = {
                'black_scholes': r'C\s*=\s*S[_0]N\(d[_1]\)\s*-\s*Ke\^{-rT}N\(d[_2]\)',
                'd1_d2': r'd[_1]\s*=\s*\([ln|log]\(S[_0]/K\)\s*[+]\s*\(r\s*[+]\s*[σσ]\^2/2\)T\)/\([σσ]\s*sqrt\{T\}\)',
                'ito_lemma': r'dX[_t]\s*=\s*[μμ]\(X[_t],t\)dt\s*[+]\s*[σσ]\(X[_t],t\)dW[_t]'
            }
            
            for formula_name, pattern in formula_patterns.items():
                formula_matches = re.finditer(pattern, text)
                for match in formula_matches:
                    start, end = match.span()
                    if start > 0 and text[start-1] != ' ':
                        text = text[:start] + ' ' + text[start:]
                    if end < len(text) and text[end] != ' ':
                        text = text[:end] + ' ' + text[end:]
            
            # Normalize whitespace
            text = re.sub(r'\s+', ' ', text)
            
            return text.strip()
        except Exception as e:
            logger.error(f"Error in second pass cleaning: {str(e)}")
            return text

    async def get_ollama_embedding(self, text: str) -> List[float]:
        """Get embedding for text using Ollama's nomic-embed-text model."""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.ollama_host}/api/embeddings",
                        json={
                            "model": "nomic-embed-text",
                            "prompt": text
                        },
                        timeout=aiohttp.ClientTimeout(total=30)  # 30 second timeout
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            embedding = result.get("embedding", [])
                            if embedding and len(embedding) == self.embedding_dim:
                                return embedding
                            else:
                                logging.error(f"Invalid embedding dimension: {len(embedding) if embedding else 0}")
                                return []
                        else:
                            error_text = await response.text()
                            logging.error(f"Ollama API error: {response.status} - {error_text}")
                            
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay * (attempt + 1))
                                continue
                            return []
            except Exception as e:
                logging.error(f"Error getting embedding (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                return []
        return []

    def extract_text_by_page(self, pdf_path: str) -> List[str]:
        """Extract text from each page individually."""
        doc = fitz.open(pdf_path)
        return [page.get_text() for page in doc]

    async def process_pdf(self, pdf_path: str) -> bool:
        """Process a PDF file and store its embeddings in Pinecone."""
        try:
            # Extract text from PDF by page
            logging.info(f"Extracting text from {pdf_path}...")
            pages = self.extract_text_by_page(pdf_path)
            if not pages:
                logging.error(f"Failed to extract text from {pdf_path}")
                return False
                
            total_chunks = 0
            processed_chunks = 0
            all_chunks = []
            
            # Process each page
            for page_num, page_text in enumerate(pages):
                # Clean the text
                logging.info(f"Cleaning page {page_num + 1}...")
                cleaned = self.clean_text(page_text)
                if not cleaned:
                    logging.error(f"Failed to clean page {page_num + 1}")
                    continue
                    
                # Split into chunks
                logging.info(f"Splitting page {page_num + 1} into chunks...")
                chunks = self.split_into_chunks(cleaned)
                if not chunks:
                    logging.error(f"Failed to split page {page_num + 1} into chunks")
                    continue
                    
                # Add chunks to all_chunks with page and chunk indices
                for i, chunk in enumerate(chunks):
                    all_chunks.append((page_num, i, chunk))
                total_chunks += len(chunks)
            
            # Process chunks in batches
            MAX_BATCH_SIZE = 20
            for i in range(0, len(all_chunks), MAX_BATCH_SIZE):
                batch = all_chunks[i:i + MAX_BATCH_SIZE]
                vectors = []
                
                # Generate embeddings for batch
                for page_num, chunk_index, chunk in batch:
                    embedding = await self.get_ollama_embedding(chunk)
                    if embedding:
                        vectors.append({
                            "id": f"{os.path.basename(pdf_path)}_p{page_num}_c{chunk_index}",
                            "values": embedding,
                            "metadata": {
                                "text": chunk,
                                "source": pdf_path,
                                "page": page_num + 1,
                                "chunk_index": chunk_index
                            }
                        })
                        processed_chunks += 1
                
                # Upsert batch to Pinecone
                if vectors:
                    try:
                        self.index.upsert(vectors=vectors, namespace=self.namespace)
                        logging.info(f"Successfully upserted batch of {len(vectors)} vectors to Pinecone ({processed_chunks}/{total_chunks} chunks processed)")
                    except Exception as e:
                        logging.error(f"Error upserting batch to Pinecone: {str(e)}")
                        continue
                
                # Clean up processed chunks
                del batch
                del vectors
            
            logging.info(f"Successfully processed {processed_chunks}/{total_chunks} chunks from {pdf_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error processing PDF {pdf_path}: {str(e)}")
            return False

    def clean_text(self, text: str) -> str:
        """Clean the extracted text using both first and second pass cleaning."""
        try:
            text = self.first_pass_clean(text)
            text = self.second_pass_clean(text)
            return text
        except Exception as e:
            logging.error(f"Error in text cleaning: {str(e)}")
            return ""

    def split_into_chunks(self, text: str) -> List[str]:
        """Split text into chunks using LangChain's RecursiveCharacterTextSplitter."""
        try:
            chunks = self.text_splitter.split_text(text)
            logging.info(f"Split text into {len(chunks)} chunks")
            return chunks
        except Exception as e:
            logging.error(f"Error splitting text into chunks: {str(e)}")
            return []

    def has_trading_strategy(self, text: str) -> bool:
        """Check if text contains trading strategy content with enhanced pattern matching."""
        try:
            strategy_info = self.analyze_trading_strategies(text)
            return any(strategy_info.values())
        except Exception as e:
            logger.error(f"Error checking trading strategy: {str(e)}")
            return False

    def analyze_trading_strategies(self, text: str) -> dict:
        """Analyze text for different types of trading strategies and return detailed information."""
        results = {
            'fundamental_analysis': False,
            'technical_analysis': False,
            'quantitative_methods': False,
            'options_strategies': False,
            'portfolio_management': False,
            'risk_management': False,
            'mathematical_trading': False,
            'market_analysis': False,
            'detected_patterns': set(),
            'detected_indicators': set(),
            'mathematical_concepts': set()
        }
        
        try:
            # Check strategy patterns
            for category, pattern in self.strategy_patterns.items():
                if re.search(pattern, text, re.IGNORECASE):
                    results['detected_patterns'].add(category)
                    
                    # Categorize the strategy
                    if category.startswith('fundamental'):
                        results['fundamental_analysis'] = True
                    elif category.startswith('technical'):
                        results['technical_analysis'] = True
                    elif category.startswith('quant'):
                        results['quantitative_methods'] = True
                    elif category.startswith('options'):
                        results['options_strategies'] = True
                    elif category.startswith('portfolio'):
                        results['portfolio_management'] = True
                    elif category.startswith('risk'):
                        results['risk_management'] = True
                    elif category in ['quant_methods', 'derivatives_math']:
                        results['mathematical_trading'] = True
                    elif category in ['intermarket', 'sentiment']:
                        results['market_analysis'] = True

            # Check technical indicators
            for category, indicators in self.technical_indicators.items():
                for indicator in indicators:
                    if indicator.lower() in text.lower():
                        results['technical_analysis'] = True
                        results['detected_indicators'].add(f"{category}:{indicator}")

            # Check mathematical concepts
            for domain, terms in self.math_terms.items():
                for term in terms:
                    if term.lower() in text.lower():
                        results['mathematical_concepts'].add(f"{domain}:{term}")

            # Check financial terms
            for category, terms in self.financial_terms.items():
                for term in terms:
                    if term.lower() in text.lower():
                        results['mathematical_concepts'].add(f"finance:{term}")

            # Convert sets to lists for JSON serialization
            results['detected_patterns'] = list(results['detected_patterns'])
            results['detected_indicators'] = list(results['detected_indicators'])
            results['mathematical_concepts'] = list(results['mathematical_concepts'])
            
            return results
        except Exception as e:
            logger.error(f"Error analyzing trading strategies: {str(e)}")
            return results

    def get_strategy_context(self, text: str, window_size: int = 100) -> str:
        """Extract context around detected trading strategies."""
        try:
            strategy_info = self.analyze_trading_strategies(text)
            if not any(strategy_info.values()):
                return ""
            
            # Find all strategy mentions
            all_patterns = '|'.join(f"(?:{pattern})" for pattern in self.strategy_patterns.values())
            matches = list(re.finditer(all_patterns, text, re.IGNORECASE))
            
            if not matches:
                return ""
            
            # Extract context around each match
            contexts = []
            for match in matches:
                start = max(0, match.start() - window_size)
                end = min(len(text), match.end() + window_size)
                context = text[start:end].strip()
                contexts.append(context)
            
            return "\n---\n".join(contexts)
        except Exception as e:
            logger.error(f"Error getting strategy context: {str(e)}")
            return ""

    def has_mathematical_content(self, text: str) -> bool:
        """Check if text contains mathematical content."""
        try:
            # Check for mathematical symbols
            for category, symbols in self.math_symbols.items():
                for symbol in symbols:
                    if symbol in text:
                        return True

            # Check for mathematical terms
            for domain, terms in self.math_terms.items():
                for term in terms:
                    if term.lower() in text.lower():
                        return True

            # Check for financial terms with mathematical significance
            for category, terms in self.financial_terms.items():
                for term in terms:
                    if term.lower() in text.lower():
                        return True

            # Check for mathematical expressions
            math_patterns = [
                r'\d+\s*[+\-*/^]\s*\d+',  # Basic arithmetic
                r'[a-zA-Z]+\s*=\s*\d+',    # Variable assignment
                r'[a-zA-Z]+\s*[+\-*/^]\s*[a-zA-Z]+',  # Variable operations
                r'[a-zA-Z]+\s*\([^)]*\)',  # Function calls
                r'[a-zA-Z]+\s*\[[^\]]*\]', # Array/matrix notation
                r'[a-zA-Z]+\s*\{[^}]*\}',  # Set notation
                r'[a-zA-Z]+\s*<[^>]*>',    # Generic notation
                r'[a-zA-Z]+\s*\|[^|]*\|',  # Norm notation
            ]

            for pattern in math_patterns:
                if re.search(pattern, text):
                    return True

            return False
        except Exception as e:
            logger.error(f"Error checking mathematical content: {str(e)}")
            return False

    async def process_pdfs(self, pdf_dir: str = None) -> Dict:
        """Process all PDFs in the specified directory."""
        try:
            # Set default PDF directory
            if pdf_dir is None:
                pdf_dir = os.path.join(os.getcwd(), "backend", "data", "docs")
            
            # Ensure the path exists
            if not os.path.exists(pdf_dir):
                raise ValueError(f"Directory not found: {pdf_dir}")
                
            logging.info(f"Processing PDFs from: {pdf_dir}")
            
            # Get initial index stats
            initial_stats = self.index.describe_index_stats()
            
            # Get list of PDF files
            pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
            logging.info(f"Found {len(pdf_files)} PDF files")
            
            total_chunks = 0
            successful_pdfs = 0
            failed_pdfs = []
            
            for pdf_file in pdf_files:
                pdf_path = os.path.join(pdf_dir, pdf_file)
                try:
                    logging.info(f"Processing {pdf_file}...")
                    # Extract text and get chunk count
                    pages = self.extract_text_by_page(pdf_path)
                    if pages:
                        all_chunks = []
                        for page_num, page_text in enumerate(pages):
                            cleaned = self.clean_text(page_text)
                            if cleaned:
                                chunks = self.split_into_chunks(cleaned)
                                if chunks:
                                    for i, chunk in enumerate(chunks):
                                        all_chunks.append((page_num, i, chunk))
                        if all_chunks:
                            total_chunks += len(all_chunks)
                            if await self.process_pdf(pdf_path):
                                successful_pdfs += 1
                                logging.info(f"Successfully processed {pdf_file} with {len(all_chunks)} chunks")
                            else:
                                failed_pdfs.append(pdf_file)
                        else:
                            failed_pdfs.append(pdf_file)
                    else:
                        failed_pdfs.append(pdf_file)
                except Exception as e:
                    failed_pdfs.append(pdf_file)
                    logging.error(f"Failed to process {pdf_file}: {str(e)}")
            
            # Get final index stats
            final_stats = self.index.describe_index_stats()
            
            return {
                "total_pdfs": len(pdf_files),
                "successful_pdfs": successful_pdfs,
                "failed_pdfs": len(failed_pdfs),
                "total_chunks": total_chunks,
                "initial_index_stats": initial_stats,
                "final_index_stats": final_stats
            }
            
        except Exception as e:
            logging.error(f"Error processing PDFs: {str(e)}")
            raise

def test_cleaner(pdf_path: str = None):
    """Test the PDF cleaner with a sample file or provided PDF."""
    cleaner = PDFCleaner()
    
    if pdf_path is None:
        # Test with a sample string containing various mathematical and financial concepts
        sample_text = """
        Chapter 1: Introduction to Financial Mathematics

        The Black-Scholes formula for option pricing is:
        $C = S_0N(d_1) - Ke^{-rT}N(d_2)$
        
        Let's consider the partial differential equation ∂V/∂t + (1/2)σ²S²(∂²V/∂S²) + rS(∂V/∂S) - rV = 0
        
        For a portfolio with correlation ρ and volatility σ, the expected return μ is:
        μ = α + β(rm - rf) where β represents the market sensitivity.
        
        Technical Analysis Indicators:
        - RSI showing overbought conditions at 70
        - MACD(12,26,9) crossover signals
        - Bollinger Bands (20,2) squeeze
        
        Options Strategy: Iron Condor
        - Sell 1 OTM Call Spread
        - Sell 1 OTM Put Spread
        - Delta neutral position
        - Positive theta decay
        """
        
        # Test cleaning
        cleaned_text = cleaner.clean_chunk(sample_text)
        logger.info("\n=== Cleaning Test ===")
        logger.info("Cleaned text sample:")
        logger.info(cleaned_text[:200] + "...")
        
        # Test mathematical content detection
        logger.info("\n=== Mathematical Content Detection ===")
        has_math = cleaner.has_mathematical_content(cleaned_text)
        logger.info(f"Contains mathematical content: {has_math}")
        
        # Test trading strategy analysis
        logger.info("\n=== Trading Strategy Analysis ===")
        strategy_info = cleaner.analyze_trading_strategies(cleaned_text)
        
        logger.info("\nDetected Strategy Types:")
        for strategy_type, present in {k: v for k, v in strategy_info.items() if isinstance(v, bool)}.items():
            if present:
                logger.info(f"- {strategy_type.replace('_', ' ').title()}")
        
        logger.info("\nDetected Patterns:")
        for pattern in strategy_info['detected_patterns']:
            logger.info(f"- {pattern.replace('_', ' ').title()}")
            
        logger.info("\nDetected Technical Indicators:")
        for indicator in strategy_info['detected_indicators']:
            logger.info(f"- {indicator}")
            
        logger.info("\nMathematical Concepts:")
        for concept in strategy_info['mathematical_concepts']:
            logger.info(f"- {concept}")
            
    else:
        try:
            chunks = cleaner.process_pdf(pdf_path)
            logger.info(f"\nProcessed {len(chunks)} chunks from {pdf_path}")
            
            if chunks:
                # Analyze first chunk in detail
                first_chunk = chunks[0]
                logger.info("\n=== First Chunk Analysis ===")
                logger.info("Text sample:")
                logger.info(first_chunk['text'][:200] + "...")
                
                has_math = cleaner.has_mathematical_content(first_chunk['text'])
                logger.info(f"\nContains mathematical content: {has_math}")
                
                strategy_info = cleaner.analyze_trading_strategies(first_chunk['text'])
                logger.info("\nTrading Strategy Analysis:")
                for key, value in strategy_info.items():
                    if isinstance(value, bool) and value:
                        logger.info(f"- {key.replace('_', ' ').title()}")
                
        except Exception as e:
            logger.error(f"Error testing with PDF {pdf_path}: {str(e)}")

if __name__ == "__main__":
    # Configure logging for better readability
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'  # Simplified format for cleaner output
    )
    
    # Test with sample text
    test_cleaner()
    
    # Test with actual PDF if path provided
    pdf_dir = Path("data/docs")
    if pdf_dir.exists():
        for pdf_file in pdf_dir.glob("*.pdf"):
            logger.info(f"\nTesting with {pdf_file}:")
            test_cleaner(str(pdf_file)) 
