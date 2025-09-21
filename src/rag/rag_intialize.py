# Initialize RAG System
from data_processing.chunking import process_json_files
from config.config import PERSIST_DIRECTORY,COLLECTION_NAME,llm,ChatGoogleGenerativeAI,embedding_function
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from retrieval.query_categorizer import QueryCategorizer
from retrieval.retrieval import Retriever
from rag.rag_system import RAGSystem
from config.logging import logger
def initialize_rag_system():
    """Initialize the  RAG system with better document processing"""
    try:
        print("🚀 Initializing  RAG system...")
        
        # Process documents with  chunking
        all_chunks = process_json_files()
        if not all_chunks:
            logger.error("❌ No documents created")

            return None
        
        # Load or create vector database
        print(f"Vector database path: {PERSIST_DIRECTORY}")
        
        try:
            # Try to load existing vector database
            vectordb = Chroma(
                embedding_function=embedding_function,
                persist_directory=PERSIST_DIRECTORY,
                collection_name=COLLECTION_NAME
            )
            print(f"✅ Loaded existing vector database with {vectordb._collection.count()} documents")
        except:
            # Create new vector database if loading fails
            print("Creating new vector database...")
            vectordb = Chroma(
                embedding_function=embedding_function,
                persist_directory=PERSIST_DIRECTORY,
                collection_name=COLLECTION_NAME
            )
            # Add documents in batches
            batch_size = 50
            for i in range(0, len(all_chunks), batch_size):
                batch = all_chunks[i:i + batch_size]
                vectordb.add_documents(batch)
                print(f"Added batch {i//batch_size + 1}")
            print(f"✅ Created new vector database with {len(all_chunks)} documents")
        
        # Create BM25 retriever
        bm25_retriever = BM25Retriever.from_documents(all_chunks)
        bm25_retriever.k = 6
        
        # Initialize  components
        retriever = Retriever(vectordb, bm25_retriever)
        query_categorizer = QueryCategorizer(llm)
        
        print("✅  RAG system initialized successfully!")
        return RAGSystem(retriever, query_categorizer, llm)
        
    except Exception as e:
        logger.error(f"❌  RAG initialization failed: {e}")

        return None

# Initialize the  RAG system
rag_system = initialize_rag_system()
