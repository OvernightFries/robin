from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from pinecone import Pinecone
import os

router = APIRouter()

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = os.getenv("PINECONE_INDEX_NAME", "robin-ai")
index = pc.Index(index_name)

@router.get("/search/strategies")
async def search_strategies(
    query: str,
    strategy_type: Optional[str] = None,
    require_math: bool = False,
    top_k: int = 5
) -> List[Dict]:
    """Search for trading strategies."""
    try:
        # Build filter conditions
        filter_conditions = {}
        if strategy_type:
            filter_conditions['strategy_type'] = strategy_type
        if require_math:
            filter_conditions['has_math'] = True
        
        # Search in Pinecone
        results = index.query(
            vector=query,  # Pinecone will automatically embed this
            top_k=top_k,
            filter=filter_conditions,
            include_metadata=True
        )
        
        # Process results
        processed_results = []
        for match in results['matches']:
            metadata = match['metadata']
            processed_results.append({
                'text': metadata['text'],
                'source': metadata['source'],
                'page': metadata['page'],
                'has_math': metadata.get('has_math', False),
                'strategy_types': metadata.get('strategy_types', []),
                'detected_patterns': metadata.get('detected_patterns', []),
                'strategy_context': metadata.get('strategy_context', ''),
                'similarity': match['score']
            })
        
        return processed_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/patterns")
async def search_patterns(
    pattern: str,
    include_context: bool = True,
    top_k: int = 5
) -> List[Dict]:
    """Search for specific trading patterns."""
    try:
        results = index.query(
            vector=pattern,  # Pinecone will automatically embed this
            top_k=top_k,
            filter={'detected_patterns': {'$in': [pattern]}},
            include_metadata=True
        )
        
        # Process results
        processed_results = []
        for match in results['matches']:
            metadata = match['metadata']
            result = {
                'pattern': metadata['detected_patterns'][0],
                'similarity': match['score']
            }
            if include_context:
                result['context'] = metadata['text']
            processed_results.append(result)
        
        return processed_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_statistics() -> Dict:
    """Get statistics about stored strategies."""
    try:
        stats = index.describe_index_stats()
        return {
            'total_vectors': stats['total_vector_count'],
            'dimension': stats['dimension'],
            'index_fullness': stats['index_fullness']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
