from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import os, re, json, logging, sys
from typing import List, Dict, Any, Optional
from datetime import datetime
from Telegram.utils import format_for_telegram
from rag.rag_intialize import rag_system
from config.logging import logger
def create_telegram_message(answer: str, category: str, semester_info: Optional[List[str]] = None, source_files: Optional[List[str]] = None) -> str:
    """Create properly formatted Telegram message"""
    category_emojis = {
        "courses_and_curriculum": "📚",
        "general_info": "ℹ️",
        "training_rules": "🏭",
        "results_statistics": "📊"
    }
    
    category_names = {
        "courses_and_curriculum": "Courses & Curriculum",
        "general_info": "General Information",
        "training_rules": "Training Rules",
        "results_statistics": "Results Statistics"
    }
    
    emoji = category_emojis.get(category, "🤖")
    name = category_names.get(category, category.replace('_', ' ').title())
    
    # Build message parts
    message_parts = [f"{emoji} <b>{name}</b>"]
    
    # Add main content
    if answer and answer.strip():
        formatted_answer = format_for_telegram(answer.strip())
        message_parts.append(formatted_answer)
    
    # Add semester info
    if semester_info:
        semesters = []
        for sem in semester_info:
            if sem == "spring_2025" or sem == "Spring 2025":
                semesters.append("Spring 2025")
            elif sem == "fall_2024" or sem == "Fall 2024":
                semesters.append("Fall 2024")
        if semesters:
            message_parts.append(f"\n🗓️ <i>Semester(s): {', '.join(semesters)}</i>")
    
    # Add sources
    if source_files:
        clean_sources = [f.replace('.json', '') for f in source_files]
        message_parts.append(f"\n📄 <i>Source: {', '.join(clean_sources)}</i>")
    
    final_message = '\n\n'.join(message_parts)
    
    # Ensure within Telegram limits
    if len(final_message) > 4000:
        final_message = final_message[:3900] + "\n\n<i>... (message truncated)</i>"
    
    return final_message

# Bot Handlers (from second document)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📚 Courses & Curriculum", callback_data='courses_and_curriculum')],
        [InlineKeyboardButton("🏭 Training Rules", callback_data='training_rules')],
        [InlineKeyboardButton("📊 Results Statistics", callback_data='results_statistics')],
        [InlineKeyboardButton("ℹ️ General Information", callback_data='general_info')],
        [InlineKeyboardButton("❓ Ask Any Question", callback_data='ask_question')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = """🎓 <b>Welcome to the  MEE Academic Assistant!</b>

I can help you with:
📚 Course information, descriptions, and prerequisites
🏭 Training and internship rules  
📊 Academic results and statistics
ℹ️ General program information

Choose a category or just ask me anything!"""
    
    await update.message.reply_text(welcome_text, parse_mode='HTML', reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """🤖 <b>How to use this  bot:</b>

<b>Commands:</b>
• /start - Main menu
• /help - This help message  
• /examples - Example questions

• Smart course code detection (MDPS423, CMPS402, etc.)
• Better document retrieval with filtering
• Improved categorization

<b>Just ask naturally:</b>
• "What are the prerequisites for MDPS476?"
• "Describe the Control Systems course"
• "What are the training requirements?"
• "Show me Spring 2025 results"

I'll understand your questions and find the right information! 💬"""
    
    await update.message.reply_text(help_text, parse_mode='HTML')

async def examples_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    examples_text = """📝 <b>Example Questions:</b>

<b>📚 Courses:</b>
• "What is MDPS372 about?"
• "Prerequisites for Mobile Robots course"
• "How many credit hours is MDPS476?"
• "Describe the Control Systems course"

<b>🏭 Training:</b>
• "Industrial training requirements"
• "Summer training duration"
• "Training evaluation process"

<b>📊 Results:</b>
• "Spring 2025 grade statistics"
• "Fall 2024 performance data"
• "Course pass rates"

<b>ℹ️ General:</b>
• "Program mission and vision"
• "Graduation requirements"
• "Total credit hours needed"

Just ask in your own words! 💬"""
    
    await update.message.reply_text(examples_text, parse_mode='HTML')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    suggestions = {
        'courses_and_curriculum': "Ask me: 'What are the prerequisites for MDPS476?' or 'Describe the Control Systems course'",
        'training_rules': "Ask me: 'What are the industrial training requirements?' or 'How long is summer training?'",
        'results_statistics': "Ask me: 'Show me Spring 2025 results' or 'What are the grade statistics?'",
        'general_info': "Ask me: 'What is the program mission?' or 'What are graduation requirements?'",
        'ask_question': "Just type any question about the MEE program!"
    }
    
    response = suggestions.get(query.data, "Ask me anything about the MEE program!")
    await query.edit_message_text(text=f"Perfect! {response}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not rag_system:
        await update.message.reply_text(
            "❌ Sorry, the  system is currently initializing. Please try again in a few moments.",
            parse_mode='HTML'
        )
        return
    
    user_question = update.message.text
    user_id = update.effective_user.id
    
    logger.info(f"👤 User {user_id}: {user_question}")
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        start_time = datetime.now()
        result = rag_system.query(user_question)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        
        telegram_message = create_telegram_message(
            answer=result['answer'],
            category=result['category'],
            semester_info=result.get('semester_info'),
            source_files=result.get('source_files')
        )
        
        await update.message.reply_text(telegram_message, parse_mode='HTML')
        
    except Exception as e:
        await update.message.reply_text(
            "⚠️ I encountered an error processing your question. Please try rephrasing it or try again later.",
            parse_mode='HTML'
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"❌ Telegram error: {context.error}")