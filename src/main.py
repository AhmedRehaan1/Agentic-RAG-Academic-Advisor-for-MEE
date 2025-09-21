# pip install python-telegram-bot langchain langchain-google-genai langchain-openai langchain-chroma tiktoken rapidfuzz langchain-text-splitters
import os, re, json, logging, sys
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveJsonSplitter
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

from config.logging import logger
from rag.rag_intialize import rag_system
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import os, re, json, logging, sys
from config.config import TELEGRAM_TOKEN,OPENAI_API_KEY,GOOGLE_API_KEY
from Telegram.telegram import start,help_command,button_callback,error_handler,examples_command,handle_message
if not OPENAI_API_KEY:
    logger.critical("❌ OPENAI_API_KEY not found in environment variables!")
    sys.exit(1)

if not GOOGLE_API_KEY:
    logger.critical("❌ GOOGLE_API_KEY not found in environment variables!")
    sys.exit(1)
def main():
    logger.info("🤖 Starting  MEE Assistant Bot...")
    
    if not rag_system:
        logger.critical("💥 RAG system failed to initialize!")
        return
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("examples", examples_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    logger.info("🎓  Bot is ready and running!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()