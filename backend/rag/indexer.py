import os
import uuid
from dotenv import load_dotenv
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pinecone

# Load env vars
load_dotenv()

# Pinecone init
pinecone.init(
    api_key=os.getenv("PINECONE_API_KEY"),
    environment=os.getenv("PINECONE_ENVIRONMENT")
)
index = pinecone.Index(os.getenv("PINECONE_INDEX_NAME"))

# Load your doc
loader = TextLoader("data/docs/sample.txt")
docs = loader.load()

# Split it
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
chunks = splitter.split_documents(docs)

# Upload chunks (Pinecone will embed them using its built-in model)
vectors = [
    {
        "id": str(uuid.uuid4()),
        "values": chunk.page_content,
        "metadata": {"source": "sample.txt"}
    }
    for chunk in chunks
]

index.upsert(vectors=vectors, namespace="default")

print(f"✅ Uploaded {len(vectors)} chunks to Pinecone (native embedding)")
