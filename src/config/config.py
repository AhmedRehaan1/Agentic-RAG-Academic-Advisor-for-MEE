import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
load_dotenv()
# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
COLLECTION_NAME = "updated_mee_syllabus_json"
PERSIST_DIRECTORY = "./rehaan_chroma_db"

# JSON file paths
JSON_FILES = {
    "data\General_Info.json": "general_info",
    "data\courses_prereq_description.json": "courses_and_curriculum",
    "data\mee_spring_2025_raw_data.json": "results_statistics",
    "data\Fall_2024.json": "results_statistics",
    "data\Industrial_training.json": "training_rules"
}
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# Initialize OpenAI Embeddings and Gemini LLM
embedding_function = OpenAIEmbeddings(model="text-embedding-3-small")
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0
)
