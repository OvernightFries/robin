import os
import logging
from typing import List, Dict
from datetime import datetime
import numpy as np
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from pdf_cleaner import PDFCleaner
import json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class DocumentIngestor:
    def __init__(self):
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = "robin-ai"  # Your main RAG index
        
        # Initialize embedding model for 2048 dimensions
        self.model = SentenceTransformer('BAAI/bge-large-en-v1.5')  # This outputs 2048-dim vectors
        
        # Initialize PDF cleaner
        self.cleaner = PDFCleaner()
        
        # Initialize Pinecone client
        self.pc = Pinecone(api_key=self.api_key)
        
        # Create index if it doesn't exist
        if self.index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=self.index_name,
                dimension=2048,  # Dimension for bge-large model
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-west-2'
                )
            )
            
        self.index = self.pc.Index(self.index_name)

    def process_pdf(self, pdf_path: str) -> List[Dict]:
        """Process PDF using 2-pass cleaning and strategy detection."""
        chunks = self.cleaner.process_pdf(pdf_path)
        
        # Enhance chunks with strategy analysis
        enhanced_chunks = []
        for i, chunk in enumerate(chunks):
            # Analyze strategies in the chunk
            strategy_info = self.cleaner.analyze_trading_strategies(chunk['text'])
            
            # Get strategy context if strategies are found
            strategy_context = self.cleaner.get_strategy_context(chunk['text']) if any(strategy_info.values()) else ""
            
            # Add strategy information to chunk
            enhanced_chunk = {
                **chunk,
                'chunk_num': i + 1,
                'strategy_info': strategy_info,
                'strategy_context': strategy_context,
                'has_strategy': any(strategy_info.values()),
                'strategy_types': [k for k, v in strategy_info.items() if v and k != 'detected_patterns'],
                'detected_patterns': list(strategy_info.get('detected_patterns', set())),
                'has_math': self.cleaner.has_mathematical_content(chunk['text'])
            }
            enhanced_chunks.append(enhanced_chunk)
            
        return enhanced_chunks

    def vectorize_and_store(self, chunks: List[Dict], metadata: Dict):
        """Convert cleaned chunks to vectors and store in Pinecone with enhanced metadata."""
        try:
            # Generate embeddings for cleaned text
            texts = [chunk['text'] for chunk in chunks]
            embeddings = self.model.encode(texts)
            
            # Generate IDs
            ids = [f"doc_{metadata['title']}_{chunk['chunk_num']}_{datetime.now().strftime('%Y%m%d')}" 
                   for chunk in chunks]
            
            # Prepare vectors with enhanced metadata
            vectors = []
            for i, (embedding, chunk) in enumerate(zip(embeddings, chunks)):
                # Prepare strategy metadata
                strategy_metadata = {
                    'has_strategy': chunk['has_strategy'],
                    'strategy_types': chunk['strategy_types'],
                    'detected_patterns': chunk['detected_patterns'],
                    'has_math': chunk['has_math']
                }
                
                vectors.append({
                    'id': ids[i],
                    'values': embedding.tolist(),
                    'metadata': {
                        **metadata,
                        **strategy_metadata,
                        'text': chunk['text'],
                        'page': chunk['page'],
                        'chunk_num': chunk['chunk_num'],
                        'strategy_context': chunk.get('strategy_context', ''),
                        'timestamp': datetime.now().isoformat()
                    }
                })
            
            # Store in batches
            batch_size = 50
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
                logger.info(f"Upserted batch {i//batch_size + 1} of {len(vectors)//batch_size + 1}")
                
            # Log strategy statistics
            strategy_stats = self._compute_strategy_stats(chunks)
            logger.info("\nStrategy Statistics:")
            logger.info(f"Total chunks: {len(chunks)}")
            logger.info(f"Chunks with strategies: {strategy_stats['chunks_with_strategies']}")
            logger.info(f"Strategy type distribution: {strategy_stats['strategy_type_counts']}")
            logger.info(f"Pattern distribution: {strategy_stats['pattern_counts']}")
                
        except Exception as e:
            logger.error(f"Error vectorizing and storing: {str(e)}")
            raise

    def _compute_strategy_stats(self, chunks: List[Dict]) -> Dict:
        """Compute statistics about strategies in the processed chunks."""
        stats = {
            'chunks_with_strategies': 0,
            'strategy_type_counts': {},
            'pattern_counts': {}
        }
        
        for chunk in chunks:
            if chunk['has_strategy']:
                stats['chunks_with_strategies'] += 1
                
                # Count strategy types
                for strategy_type in chunk['strategy_types']:
                    stats['strategy_type_counts'][strategy_type] = \
                        stats['strategy_type_counts'].get(strategy_type, 0) + 1
                
                # Count patterns
                for pattern in chunk['detected_patterns']:
                    stats['pattern_counts'][pattern] = \
                        stats['pattern_counts'].get(pattern, 0) + 1
        
        return stats

def main():
    # Create necessary directories
    os.makedirs("data/docs", exist_ok=True)
    
    ingestor = DocumentIngestor()
    
    # Process all PDFs in the docs directory
    docs_dir = "data/docs"
    for filename in os.listdir(docs_dir):
        if filename.endswith(".pdf"):
            logger.info(f"Processing {filename}")
            
            # Extract metadata from filename
            title = filename.replace(".pdf", "")
            
            # Process PDF with enhanced cleaning and strategy detection
            pdf_path = os.path.join(docs_dir, filename)
            chunks = ingestor.process_pdf(pdf_path)
            
            # Store with metadata
            metadata = {
                'title': title,
                'source': filename,
                'type': 'textbook' if 'book' in filename.lower() else 'strategy',
                'processed_date': datetime.now().isoformat()
            }
            
            ingestor.vectorize_and_store(chunks, metadata)
            logger.info(f"Successfully processed {filename}")

if __name__ == "__main__":
    main() 
