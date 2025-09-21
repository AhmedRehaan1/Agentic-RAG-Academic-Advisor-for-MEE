import re
from typing import List, Dict, Any, Optional
from langchain.schema import Document

#  Retriever 
class Retriever:
    """ retriever with course code extraction and filtering"""
    def __init__(self, vectordb, bm25_retriever):
        self.vectordb = vectordb
        self.bm25_retriever = bm25_retriever

    def _extract_course_code(self, query: str) -> Optional[str]:
        """Extracts a course code from a query string using a flexible regex pattern"""
        match = re.search(r'\b([A-Z]{3,4}[SN]?\d{3})\b', query, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None

    def get_relevant_documents(self, query: str, category: str) -> List[Document]:
        """ document retrieval with course code filtering"""
        course_code = self._extract_course_code(query)
        
        # Construct ChromaDB filter
        if course_code:
            filter_dict = {
                "$and": [
                    {"category": category},
                    {"course_code": course_code}
                ]
            }
            print(f"✅ Found course code. Applying precise filter: category={category}, course_code={course_code}")
        else:
            filter_dict = {"category": category}
            print(f"✅ No course code found. Applying category filter: category={category}")

        try:
            # Vector search with proper filter
            vector_docs = self.vectordb.similarity_search(query, k=5, filter=filter_dict)
            print(f"✅ Vector search returned {len(vector_docs)} documents")
        except Exception as e:
            print(f"❌ Vector search failed: {e}")
            # Fallback to search without course_code filter
            try:
                vector_docs = self.vectordb.similarity_search(query, k=5, filter={"category": category})
                print(f"✅ Fallback vector search returned {len(vector_docs)} documents")
            except Exception as e2:
                print(f"❌ Fallback vector search also failed: {e2}")
                vector_docs = []

        # BM25 search with filtering
        bm25_docs = self.bm25_retriever.get_relevant_documents(query)
        print(f"✅ BM25 search returned {len(bm25_docs)} documents")
        
        filtered_bm25 = []
        for doc in bm25_docs:
            if doc.metadata.get("category") == category:
                if course_code and doc.metadata.get("course_code") == course_code:
                    filtered_bm25.append(doc)
                elif not course_code:
                    filtered_bm25.append(doc)

        print(f"✅ Filtered BM25 results: {len(filtered_bm25)} documents")

        # Combine and deduplicate results
        all_docs = vector_docs + filtered_bm25
        seen_ids = set()
        unique_docs = []
        for doc in all_docs:
            doc_id = doc.metadata.get("course_code", doc.page_content[:100])
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                unique_docs.append(doc)
        
        print(f"✅ Final unique documents: {len(unique_docs[:8])}")
        return unique_docs[:8]
