# MEE Academic Assistant – RAG + Telegram Bot:
This project is a Retrieval-Augmented Generation (RAG) system integrated with a Telegram bot designed to provide quick, accurate, and context-aware responses to student queries about courses, prerequisites, schedules, and general information related to the Mechanical Engineering department.

The system combines Chroma vector search, BM25 keyword retrieval, and LLM-powered query understanding to deliver precise and reliable answers.

https://github.com/user-attachments/assets/74fe43cf-622d-491f-8955-05fbf04c46cf

## Features

Telegram Bot Interface
Simple, accessible chat interface for students to ask questions.

Retrieval-Augmented Generation (RAG)
Combines semantic search (via Chroma) and keyword search (BM25) for contextually relevant results.

Query Categorization
Automatic classification of questions into categories (e.g., general info, course details, prerequisites).

Structured Prompts
Different prompt templates tailored for each query type for more accurate LLM responses.

Metadata Filtering
Ensures retrieved documents are relevant by filtering based on course code, semester, or data source.

Extensible Data Pipeline
Supports loading and preprocessing multiple JSON data sources (courses, schedules, training programs).

Logging & Error Handling
Centralized logging for debugging and monitoring.

# Project Structure
<img width="227" height="527" alt="Image" src="https://github.com/user-attachments/assets/6f5c446d-865c-4b0f-8cbf-75ecf7648589" />




# Setup & Installation
## 1. Clone the Repository
git clone https://github.com/your-username/mee-academic-assistant.git
cd mee-academic-assistant

## 2. Create a Virtual Environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

## 3. Install Dependencies
pip install -r requirements.txt

## 4. Configure Environment Variables

Create a .env file in the project root with the following:

TELEGRAM_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_gemini_api_key
CHROMA_DB_PATH=./chroma_db
LOG_FILE=./logs/app.log

# Usage
## 1. Build or Update the Vector Database
python src/rag/initialize.py

## 2. Start the Telegram Bot
python src/main.py


Once running, open Telegram and start chatting with your bot.

Data Sources

The system currently supports:

General_Info.json – Department-wide announcements and general guidance

courses_prereq_description.json – Course descriptions and prerequisites

mee_spring_2025_raw_data.json – Spring 2025 semester data

Fall_2024.json – Fall 2024 semester data

Industrial_training.json – Industrial training requirements

Adding new data sources only requires placing them in data/ and re-running initialize.py.

Development & Testing

Run unit tests:

pytest tests/

# Deployment

This project can be easily containerized for production deployment. A Dockerfile can be added to package the bot with all dependencies and run it on a server or cloud platform.

# Roadmap

Add support for web-based admin panel to upload new JSON data

Integrate Selenium-based scraping for automatic data updates

Expand query categories for more specialized responses

Add support for streaming responses in Telegram for long answers
