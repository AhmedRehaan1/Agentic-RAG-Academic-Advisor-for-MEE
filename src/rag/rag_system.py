from langchain.prompts import ChatPromptTemplate
import os, re, json, logging, sys
from config.logging import logger
from typing import List, Dict, Any, Optional
from langchain_core.output_parsers import StrOutputParser
from langchain.schema import Document
from rag.prompts import prompts

class RAGSystem:
    def __init__(self, retriever, categorizer, llm):
        self.retriever = retriever
        self.categorizer = categorizer
        self.llm = llm
        
        self.prompts = prompts
            

    def _prepare_context(self, docs: List[Document], category: str) -> str:
        """Prepare context based on category"""
        if category == "courses_and_curriculum":
            context_parts = []
            for doc in docs:
                source = doc.metadata.get('source', 'Unknown')
                course_code = doc.metadata.get('course_code', '')
                course_name = doc.metadata.get('course_name', '')
                
                header = f"Source: {source}"
                if course_code or course_name:
                    header += f" - {course_code} {course_name}".strip()
                
                context_parts.append(f"{header}\n{doc.page_content}")
            return "\n\n".join(context_parts)
        else:
            context_parts = []
            for doc in docs:
                source = doc.metadata.get('source', 'Unknown')
                context_parts.append(f"Source: {source}\n{doc.page_content}")
            return "\n\n".join(context_parts)

    def query(self, question: str) -> Dict[str, Any]:
        try:
            print(f"🔍 Processing question: {question}")
            
            # Categorize query
            try:
                category = self.categorizer.categorize(question)
                print(f"📂 Category: {category}")
            except Exception as e:
                print(f"❌ Error in categorization: {str(e)}")
                raise

            # Extract course code from the question
            try:
                course_code = self.retriever._extract_course_code(question)
                print(f"📝 Course code: {course_code}")
            except Exception as e:
                print(f"❌ Error extracting course code: {str(e)}")
                raise

            # Retrieve relevant documents with filtering
            try:
                relevant_docs = self.retriever.get_relevant_documents(question, category)
                print(f"📚 Retrieved {len(relevant_docs)} documents")
            except Exception as e:
                print(f"❌ Error retrieving documents: {str(e)}")
                raise

            if not relevant_docs:
                logger.info(f"[RAGSystem] No relevant documents found for category: {category}")
                return {
                    "answer": f"I couldn't find specific information about your question in the {category.replace('_', ' ')} category. Please try rephrasing your question or asking about a different topic.",
                    "category": category,
                    "num_docs_retrieved": 0,
                    "source_files": [],
                    "semester_info": None,
                    "extracted_course_code": course_code
                }

            # Extract semester info for results
            semester_info = None
            if category == "results_statistics":
                semesters = {doc.metadata.get("semester") for doc in relevant_docs if doc.metadata.get("semester")}
                semester_info = list(semesters) if semesters else None
                logger.debug(f"[RAGSystem] Semester info: {semester_info}")

            context = self._prepare_context(relevant_docs, category)
            logger.debug(f"[RAGSystem] Prepared context (length: {len(context)})")

            # Generate response
            try:
                prompt = self.prompts.get(category, self.prompts["general_info"])
                print(f"🤖 Using prompt template for {category}")
                chain = prompt | self.llm | StrOutputParser()
                print("🔄 Invoking LLM...")
                result = chain.invoke({"question": question, "context": context})
                print("✅ Got LLM response")
            except Exception as e:
                print(f"❌ Error generating response: {str(e)}")
                raise

            return {
                "answer": result,
                "category": category,
                "num_docs_retrieved": len(relevant_docs),
                "source_files": list({doc.metadata.get("source", "Unknown") for doc in relevant_docs}),
                "semester_info": semester_info,
                "extracted_course_code": course_code
            }

        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()
            print(f"❌ ERROR in RAG system: {type(e).__name__}: {str(e)}\n{tb_str}")
            logger.error(f"RAGSystem error for question: '{question}'\nType: {type(e).__name__}\nError: {str(e)}\nTraceback:\n{tb_str}")
            return {
                "answer": f"I encountered an error while processing your question: {str(e)}. Please try rephrasing it or try again later.",
                "category": "error",
                "num_docs_retrieved": 0,
                "source_files": [],
                "semester_info": None,
                "extracted_course_code": None
            }