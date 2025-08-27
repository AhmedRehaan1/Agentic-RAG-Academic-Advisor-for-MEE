# Enhanced RAG System with Telegram Bot Integration
# pip install python-telegram-bot langchain langchain-openai chromadb pypdf tiktoken rapidfuzz

import os, re, json, logging
from typing import List, Dict, Any
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from langchain_community.retrievers import BM25Retriever
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_TOKEN = "8157284455:AAHq6pO4M-d2f4IoMaQx8B1-O_6NeTSURgk"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PDF_PATH = "MEE_Sylabus_with_metadata.pdf"
COLLECTION_NAME = "mee_syllabus_v1"

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize OpenAI components
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
emb = OpenAIEmbeddings(model="text-embedding-3-large")
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Query Categorization Tool
class QueryCategorizer:
    def __init__(self, llm):
        self.llm = llm
        self.categorization_prompt = ChatPromptTemplate.from_template("""
        You are a query categorization expert. Categorize the following query into one of these categories:

        1. "program_description" - Questions about course descriptions, course content, syllabus details, learning objectives, topics covered in courses
        2. "course_prerequisites" - Questions about course names, course codes, prerequisites, course relationships
        3. "general_info" - Questions about mission, vision, general program information, admission requirements, graduation requirements
        4. "training_rules" - Questions about industrial training, summer training, internship requirements, training rules, training procedures, practical training guidelines

        Query: {query}
        
        Respond with only the category name (program_description, course_prerequisites, general_info, or training_rules).
        """)
    
    def categorize(self, query: str) -> str:
        try:
            chain = self.categorization_prompt | self.llm
            result = chain.invoke({"query": query})
            category = result.content.strip().lower()
            
            # Ensure valid category
            valid_categories = ["program_description", "course_prerequisites", "general_info", "training_rules"]
            if category not in valid_categories:
                # Default fallback based on keywords
                query_lower = query.lower()
                if any(word in query_lower for word in ["industrial training", "summer training", "internship", "training rules", "practical training", "industrial", "summer", "internship requirements"]):
                    return "training_rules"
                elif any(word in query_lower for word in ["prerequisite", "prereq", "course name", "course code"]):
                    return "course_prerequisites"
                elif any(word in query_lower for word in ["description", "syllabus", "content", "topics", "learning"]):
                    return "program_description"
                else:
                    return "general_info"
            
            return category
        except Exception as e:
            logger.error(f"Error in categorization: {e}")
            return "general_info"

def get_document_category(page_num: int) -> str:
    """Assign category based on page number"""
    if 1 <= page_num <= 7:
        return "general_info"
    elif 8 <= page_num <= 17:
        return "course_prerequisites"
    elif 18 <= page_num <= 34:
        return "program_description"
    elif 35 <= page_num <= 41:
        return "training_rules"
    else:
        return "general_info"

def extract_metadata(text, page_num):
    """Extract course metadata from text"""
    code = re.search(r"\b([A-Z]{3,4}S?\d{3})\b", text)
    title = re.search(r"Course\s+([A-Z]{3,4}S?\d{3})\s+[–-]\s+(.+)", text) or re.search(r"\b([A-Z]{3,4}S?\d{3})\s+[-–]\s+([^\n]+)", text)
    credits = re.search(r"Credit Hours:\s*(\d+)", text)
    prereq = re.findall(r"Pre-?requisites?:\s*([^\n]+)", text, flags=re.I)
    
    # Extract training-specific metadata
    training_type = None
    if page_num >= 35:
        if any(keyword in text.lower() for keyword in ["industrial training", "industrial"]):
            training_type = "industrial_training"
        elif any(keyword in text.lower() for keyword in ["summer training", "summer"]):
            training_type = "summer_training"
    
    metadata = {
        "course_code": (code.group(1) if code else None) or (title.group(1) if title else None),
        "course_title": title.group(2).strip() if title else None,
        "credits": int(credits.group(1)) if credits else None,
        "prerequisites": re.split(r"[,\s+]+", prereq[0]) if prereq else None,
        "category": get_document_category(page_num)
    }
    
    if training_type:
        metadata["training_type"] = training_type
    
    return metadata

# Category-aware filtering retriever
class CategoryFilteredRetriever:
    def __init__(self, vectordb, bm25_retriever):
        self.vectordb = vectordb
        self.bm25_retriever = bm25_retriever
    
    def get_relevant_documents(self, query: str, category: str = None) -> List[Document]:
        """Retrieve documents filtered by category"""
        try:
            # Vector search with category filter
            if category:
                vector_docs = self.vectordb.similarity_search(
                    query, 
                    k=8,
                    filter={"category": category}
                )
            else:
                vector_docs = self.vectordb.similarity_search(query, k=8)
            
            # BM25 search with category filter
            bm25_docs = self.bm25_retriever.get_relevant_documents(query)
            if category:
                bm25_docs = [doc for doc in bm25_docs if doc.metadata.get("category") == category]
            
            # Combine and deduplicate
            all_docs = vector_docs + bm25_docs[:6]
            seen_content = set()
            unique_docs = []
            
            for doc in all_docs:
                content_hash = hash(doc.page_content[:100])
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    unique_docs.append(doc)
            
            return unique_docs[:10]
        except Exception as e:
            logger.error(f"Error in retrieval: {e}")
            return []

# Enhanced RAG System
class EnhancedRAGSystem:
    def __init__(self, retriever, categorizer, llm):
        self.retriever = retriever
        self.categorizer = categorizer
        self.llm = llm
        
        # Category-specific prompts
        self.prompts = {
            "program_description": ChatPromptTemplate.from_template("""
            You are a course syllabus expert. Answer using ONLY the context provided.
            Focus on course descriptions, content, learning objectives, and syllabus details.
            Include specific course codes and detailed descriptions when available.
            Keep responses concise but informative for Telegram messaging.

            Question: {question}
            Context: {context}
            Answer:"""),
            
            "course_prerequisites": ChatPromptTemplate.from_template("""
            You are an academic requirements expert. Answer using ONLY the context provided.
            Focus on course names, course codes, prerequisites, and course relationships.
            List prerequisites clearly and include course codes when available.
            Keep responses concise but informative for Telegram messaging.

            Question: {question}
            Context: {context}
            Answer:"""),
            
            "general_info": ChatPromptTemplate.from_template("""
            You are a program information expert. Answer using ONLY the context provided.
            Focus on mission, vision, general program information, and institutional details.
            Provide comprehensive information about program structure and requirements.
            Keep responses concise but informative for Telegram messaging.

            Question: {question}
            Context: {context}
            Answer:"""),
            
            "training_rules": ChatPromptTemplate.from_template("""
            You are a training and internship expert. Answer using ONLY the context provided.
            Focus on industrial training rules, summer training requirements, internship procedures, and practical training guidelines.
            Include specific requirements, procedures, timelines, and regulations when available.
            Clearly distinguish between industrial training and summer training requirements.
            Keep responses concise but informative for Telegram messaging.

            Question: {question}
            Context: {context}
            Answer:""")
        }
    
    def query(self, question: str) -> Dict[str, Any]:
        try:
            # Step 1: Categorize the query
            category = self.categorizer.categorize(question)
            
            # Step 2: Retrieve relevant documents with category filtering
            relevant_docs = self.retriever.get_relevant_documents(question, category)
            
            if not relevant_docs:
                return {
                    "answer": "I couldn't find relevant information for your query. Please try rephrasing your question.",
                    "category": category,
                    "num_docs_retrieved": 0,
                    "source_pages": []
                }
            
            # Step 3: Format context
            context = "\n\n".join([f"Document {i+1}:\n{doc.page_content}" 
                                  for i, doc in enumerate(relevant_docs)])
            
            # Step 4: Generate answer using category-specific prompt
            prompt = self.prompts.get(category, self.prompts["general_info"])
            chain = prompt | self.llm
            
            result = chain.invoke({
                "question": question,
                "context": context
            })
            
            return {
                "answer": result.content,
                "category": category,
                "num_docs_retrieved": len(relevant_docs),
                "source_pages": list(set([doc.metadata.get("page_start", "Unknown") 
                                        for doc in relevant_docs]))
            }
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            return {
                "answer": "Sorry, I encountered an error processing your question. Please try again.",
                "category": "error",
                "num_docs_retrieved": 0,
                "source_pages": []
            }

# Initialize RAG System (this will be done once when the bot starts)
def initialize_rag_system():
    try:
        # Load PDF
        loader = PyPDFLoader(PDF_PATH)
        pages = loader.load()
        
        # Process documents
        docs = []
        for p in pages:
            page_num = p.metadata.get("page", 0) + 1
            md = extract_metadata(p.page_content, page_num)
            base = {
                "doc_id": COLLECTION_NAME,
                "page_start": page_num,
                "page_end": page_num,
                "source": PDF_PATH
            }
            base.update({k:v for k,v in md.items() if v})
            docs.append(Document(page_content=p.page_content, metadata=base))
        
        # Chunking
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200, chunk_overlap=150,
            separators=["\n\nCourse ", "\n\n", "\n", ".", " "]
        )
        chunks = []
        for d in docs:
            for c in splitter.split_text(d.page_content):
                chunks.append(Document(page_content=c, metadata=d.metadata))
        
        # Vector store
        vectordb = Chroma(collection_name=COLLECTION_NAME, embedding_function=emb, persist_directory="./chroma_mee")
        vectordb.add_documents(chunks)
        
        # Create retrievers
        bm25_retriever = BM25Retriever.from_documents(chunks)
        bm25_retriever.k = 6
        
        filtered_retriever = CategoryFilteredRetriever(vectordb, bm25_retriever)
        categorizer = QueryCategorizer(llm)
        
        return EnhancedRAGSystem(filtered_retriever, categorizer, llm)
    except Exception as e:
        logger.error(f"Error initializing RAG system: {e}")
        return None

# Initialize the RAG system globally
rag_system = initialize_rag_system()

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    keyboard = [
        [InlineKeyboardButton("📚 Course Prerequisites", callback_data='course_prerequisites')],
        [InlineKeyboardButton("📖 Program Descriptions", callback_data='program_description')],
        [InlineKeyboardButton("🏭 Training Rules", callback_data='training_rules')],
        [InlineKeyboardButton("ℹ️ General Information", callback_data='general_info')],
        [InlineKeyboardButton("❓ Ask Any Question", callback_data='ask_question')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = """
🎓 *Welcome to the MEE Academic Assistant Bot!*

I'm here to help you with information about:
• Course descriptions and syllabi
• Prerequisites and course relationships
• Industrial & Summer training rules
• General program information

Choose a category below or simply ask me any question about the MEE program!
    """
    
    await update.message.reply_text(
        welcome_text, 
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = """
🤖 *How to use this bot:*

*Commands:*
• `/start` - Show main menu
• `/help` - Show this help message
• `/examples` - Show example queries

*Query Examples:*
• "What are the prerequisites for MDPS476?"
• "Describe the Mobile Robots course"
• "What are the industrial training requirements?"
• "Summer training rules and procedures"
• "What is the program mission?"
• "How many credit hours are required?"

Just type your question naturally, and I'll find the relevant information from the MEE syllabus!
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def examples_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show example queries."""
    examples_text = """
📝 *Example Questions You Can Ask:*

*Course Prerequisites:*
• "What are the prerequisites for MDPS476?"
• "Which courses require MDPS423?"
• "List all course codes"

*Program Descriptions:*
• "Describe the Mobile Robots and Autonomous Systems course"
• "What topics are covered in computer vision courses?"
• "Explain MDPS476 learning objectives"

*Training Rules:*
• "What are the industrial training requirements?"
• "How long is the summer training period?"
• "Industrial training procedures and guidelines"
• "Summer training evaluation criteria"

*General Information:*
• "What is the program mission?"
• "How many credit hours for graduation?"
• "What are the admission requirements?"

Just ask me anything about the MEE program! 🎓
    """
    
    await update.message.reply_text(examples_text, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    category_examples = {
        'course_prerequisites': "Try asking: 'What are the prerequisites for MDPS476?'",
        'program_description': "Try asking: 'Describe the Mobile Robots course'",
        'training_rules': "Try asking: 'What are the industrial training requirements?'",
        'general_info': "Try asking: 'What is the program mission?'",
        'ask_question': "Just type any question about the MEE program!"
    }
    
    response_text = f"Great choice! {category_examples.get(query.data, 'Just ask me anything!')}"
    await query.edit_message_text(text=response_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and provide RAG responses."""
    if not rag_system:
        await update.message.reply_text("Sorry, the system is not ready yet. Please try again later.")
        return
    
    user_question = update.message.text
    user_id = update.effective_user.id
    
    # Log the query
    logger.info(f"User {user_id} asked: {user_question}")
    
    # Send typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Get response from RAG system
        result = rag_system.query(user_question)
        
        # Format response for Telegram
        category_emojis = {
            "course_prerequisites": "📋",
            "program_description": "📚", 
            "general_info": "ℹ️",
            "training_rules": "🏭"
        }
        
        category_emoji = category_emojis.get(result['category'], "🤖")
        
        response_text = f"{category_emoji} *{result['category'].replace('_', ' ').title()}*\n\n"
        response_text += result['answer']
        
        if result['source_pages']:
            response_text += f"\n\n📄 *Sources:* Pages {', '.join(map(str, result['source_pages']))}"
        
        # Split long messages if needed (Telegram limit is 4096 characters)
        if len(response_text) > 4000:
            # Split the message
            answer_part = result['answer']
            if len(answer_part) > 3800:
                answer_part = answer_part[:3800] + "..."
            
            response_text = f"{category_emoji} *{result['category'].replace('_', ' ').title()}*\n\n"
            response_text += answer_part
            
            if result['source_pages']:
                response_text += f"\n\n📄 *Sources:* Pages {', '.join(map(str, result['source_pages']))}"
        
        await update.message.reply_text(response_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text(
            "Sorry, I encountered an error processing your question. Please try rephrasing it or try again later."
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Run the bot."""
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("examples", examples_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    # Start the bot
    print("🤖 Bot is starting...")
    print("🎓 MEE Academic Assistant Bot is ready!")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()