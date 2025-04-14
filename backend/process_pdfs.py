import asyncio
import logging
from pathlib import Path
from rag.pdf_cleaner import PDFCleaner
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def process_pdfs():
    # Load environment variables
    load_dotenv()
    
    # Initialize PDF cleaner
    cleaner = PDFCleaner(
        index_name="robindocs",
        namespace="financial_docs"
    )
    
    # Get PDF directory - use absolute path
    script_dir = Path(__file__).parent
    pdf_dir = script_dir / "data" / "docs"
    if not pdf_dir.exists():
        logger.error(f"PDF directory not found: {pdf_dir}")
        return
    
    # Process PDFs
    try:
        logger.info("Starting PDF processing...")
        results = await cleaner.process_pdfs(str(pdf_dir))
        
        # Log results
        logger.info("\nProcessing Results:")
        logger.info(f"Total PDFs processed: {results['total_pdfs']}")
        logger.info(f"Successful PDFs: {results['successful_pdfs']}")
        logger.info(f"Failed PDFs: {results['failed_pdfs']}")
        logger.info(f"Total chunks processed: {results['total_chunks']}")
        
        # Log index stats
        logger.info("\nIndex Statistics:")
        logger.info(f"Initial vector count: {results['initial_index_stats'].get('total_vector_count', 0)}")
        logger.info(f"Final vector count: {results['final_index_stats'].get('total_vector_count', 0)}")
        
    except Exception as e:
        logger.error(f"Error processing PDFs: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(process_pdfs()) 
