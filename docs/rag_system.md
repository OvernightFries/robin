# RAG System Documentation

## Overview
The Retrieval-Augmented Generation (RAG) system combines document processing, vector embeddings, and semantic search to provide context-aware responses for stock analysis queries.

## Architecture

### Core Components
1. **Document Processing**
   - PDF text extraction
   - Text cleaning
   - Chunking
   - Metadata extraction

2. **Vector Store**
   - Embedding generation
   - Index management
   - Similarity search
   - Context retrieval

3. **Query Processing**
   - Query embedding
   - Context retrieval
   - Response generation
   - Context injection

## Document Processing

### PDF Cleaner (`backend/rag/pdf_cleaner.py`)
```python
class PDFCleaner:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )

    def extract_text_from_pdf(self, file_path: str) -> List[str]:
        """Extract text from PDF file."""
        # Implementation details

    def clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Implementation details

    def split_into_chunks(self, text: str) -> List[str]:
        """Split text into chunks."""
        # Implementation details

    def get_ollama_embedding(self, text: str) -> List[float]:
        """Generate embeddings using Ollama."""
        # Implementation details
```

### Process PDFs (`backend/rag/process_pdfs.py`)
```python
def process_pdfs():
    """Process all PDFs in the data directory."""
    # Implementation details
```

## Vector Store

### Pinecone Integration
1. **Index Management**
   - Index creation
   - Vector upsert
   - Index cleanup
   - Metadata management

2. **Embedding Generation**
   - Text preprocessing
   - Embedding model
   - Dimension validation
   - Batch processing

3. **Similarity Search**
   - Query embedding
   - K-nearest neighbors
   - Score thresholding
   - Context retrieval

## Query Processing

### Context Retrieval
1. **Query Embedding**
   ```python
   def get_query_embedding(query: str) -> List[float]:
       """Generate embedding for query."""
       # Implementation details
   ```

2. **Semantic Search**
   ```python
   def search_context(query_embedding: List[float], k: int = 5) -> List[Dict]:
       """Search for relevant context."""
       # Implementation details
   ```

3. **Context Injection**
   ```python
   def inject_context(query: str, context: List[Dict]) -> str:
       """Inject context into query."""
       # Implementation details
   ```

## Data Flow

### Document Processing Flow
1. PDF upload → Text extraction → Cleaning → Chunking → Embeddings → Pinecone
2. Each step includes:
   - Progress tracking
   - Error handling
   - Logging
   - Validation

### Query Processing Flow
1. User query → Query embedding → Semantic search → Context retrieval → Response generation
2. Each step includes:
   - Error handling
   - Fallback mechanisms
   - Performance monitoring
   - Cache management

## Performance Optimization

### Batch Processing
1. **Document Processing**
   - Parallel processing
   - Batch size optimization
   - Memory management
   - Progress tracking

2. **Vector Operations**
   - Batch embeddings
   - Bulk upserts
   - Cache utilization
   - Index optimization

### Caching Strategy
1. **Embedding Cache**
   - Text to embedding mapping
   - Cache invalidation
   - Memory limits
   - Persistence

2. **Context Cache**
   - Query to context mapping
   - Time-based invalidation
   - Size limits
   - Relevance scoring

## Error Handling

### Common Errors
1. **Document Processing**
   - Invalid PDF format
   - Text extraction failures
   - Cleaning errors
   - Chunking issues

2. **Vector Operations**
   - Embedding failures
   - Index errors
   - Search timeouts
   - Dimension mismatches

3. **Query Processing**
   - Invalid queries
   - Context retrieval failures
   - Response generation errors
   - Timeout handling

## Monitoring

### Performance Metrics
1. **Processing Metrics**
   - Document processing time
   - Embedding generation time
   - Search latency
   - Cache hit rate

2. **Quality Metrics**
   - Chunk quality
   - Embedding quality
   - Search relevance
   - Response quality

### Logging
1. **Application Logs**
   - Processing steps
   - Error details
   - Performance metrics
   - System events

2. **Audit Logs**
   - Document processing
   - Vector operations
   - Query processing
   - System changes

## Deployment

### Container Configuration
1. **Docker Setup**
   - Base image
   - Dependencies
   - Environment
   - Volumes

2. **Service Configuration**
   - Resource limits
   - Scaling parameters
   - Health checks
   - Monitoring setup

### Scaling Strategy
1. **Horizontal Scaling**
   - Multiple instances
   - Load balancing
   - Data partitioning
   - Cache distribution

2. **Vertical Scaling**
   - Resource allocation
   - Performance tuning
   - Cache optimization
   - Index optimization 
