# 🎓 MEE Academic Assistant Bot

An intelligent Telegram bot powered by advanced RAG (Retrieval-Augmented Generation) technology that helps students and faculty access information about the Master of Engineering in Electronics (MEE) program. The bot uses OpenAI's GPT-4 and advanced document retrieval techniques to answer questions about courses, prerequisites, training requirements, and general program information.

## 🚀 Features

### 📚 **Multi-Category Query Handling**
- **Course Prerequisites**: Information about course codes, names, and requirements
- **Program Descriptions**: Detailed course content, syllabi, and learning objectives  
- **Training Rules**: Industrial training and summer training requirements and procedures
- **General Information**: Program mission, vision, admission requirements, and graduation criteria

### 🔍 **Advanced RAG Technology**
- **Hybrid Retrieval**: Combines vector similarity search (Chroma) with keyword-based search (BM25)
- **Intelligent Categorization**: Automatically categorizes queries for optimized responses
- **Context-Aware Responses**: Tailored prompts for different question types
- **Smart Document Filtering**: Category-based document retrieval for precision

### 💬 **Telegram Integration**
- Interactive menu with category buttons
- Real-time typing indicators
- Message length optimization for Telegram
- Error handling and user feedback
- Source page citations

## 📋 Prerequisites

### System Requirements
- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended for optimal performance)
- 2GB free disk space
- Internet connection for API calls

### Required Accounts & Keys
- **Telegram Bot Token**: Get from [@BotFather](https://t.me/botfather)
- **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/mee-academic-assistant-bot.git
cd mee-academic-assistant-bot
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Setup
Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your_openai_api_key_here
TELEGRAM_TOKEN=your_telegram_bot_token_here
```

### 5. Add Your PDF Document
Place your MEE syllabus PDF file in the project directory and name it:
```
MEE_Sylabus_with_metadata.pdf
```

## 📦 Dependencies

```txt
python-telegram-bot>=20.0
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-community>=0.0.10
chromadb>=0.4.0
pypdf>=3.0.0
tiktoken>=0.5.0
rapidfuzz>=3.0.0
python-dotenv>=1.0.0
```

## 🏃‍♂️ Running the Bot

### Local Development
```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run the bot
python your_bot_filename.py
```

### Using Docker
```bash
# Build the image
docker build -t mee-bot .

# Run the container
docker run -d --name mee-bot \
  --env-file .env \
  -v $(pwd)/chroma_mee:/app/chroma_mee \
  -v $(pwd)/MEE_Sylabus_with_metadata.pdf:/app/MEE_Sylabus_with_metadata.pdf \
  mee-bot
```

### Using Docker Compose
```bash
# Start the bot
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

## 🗂️ Project Structure

```
mee-academic-assistant-bot/
├── your_bot_filename.py          # Main bot application
├── MEE_Sylabus_with_metadata.pdf # Source document (you provide this)
├── requirements.txt              # Python dependencies
├── .env                         # Environment variables (create this)
├── .env.example                 # Environment template
├── Dockerfile                   # Docker configuration
├── docker-compose.yml          # Docker Compose setup
├── README.md                    # This file
├── chroma_mee/                  # Vector database storage
│   └── (generated files)
└── logs/                        # Log files (optional)
    └── bot.log
```

## 📖 Usage Guide

### Bot Commands
- `/start` - Show main menu with category buttons
- `/help` - Display help information and usage instructions
- `/examples` - Show example queries for each category

### Query Categories & Examples

#### 📋 **Course Prerequisites**
```
"What are the prerequisites for MDPS476?"
"Which courses require MDPS423 as a prerequisite?"
"List all available course codes"
"What courses do I need before taking Advanced Control Systems?"
```

#### 📚 **Program Descriptions** 
```
"Describe the Mobile Robots and Autonomous Systems course"
"What topics are covered in computer vision courses?"
"Explain MDPS476 learning objectives"
"What is the content of the Machine Learning course?"
```

#### 🏭 **Training Rules**
```
"What are the industrial training requirements?"
"How long is the summer training period?"
"Industrial training procedures and guidelines"
"Summer training evaluation criteria"
"What documents are needed for training registration?"
```

#### ℹ️ **General Information**
```
"What is the program mission and vision?"
"How many credit hours are required for graduation?"
"What are the admission requirements?"
"Program structure and degree requirements"
```

## 🚀 Deployment Options

### 1. **Cloud VPS (Recommended)**
- **DigitalOcean Droplet**: $5/month
- **AWS EC2**: Free tier available
- **Linode**: $5/month
- **Hetzner Cloud**: €3.29/month

### 2. **Serverless Platforms**
- **Heroku**: Free tier for testing
- **Railway**: Simple GitHub integration
- **Render**: Modern platform with auto-deploy
- **Google Cloud Run**: Pay-per-use

### 3. **Container Platforms**
- **AWS ECS**: Managed container service
- **Google Cloud Run**: Serverless containers
- **Azure Container Instances**: Simple container hosting

## 📊 System Architecture

### Document Processing Pipeline
```
PDF Document → Page Extraction → Metadata Extraction → 
Text Chunking → Vector Embeddings → Chroma Database Storage
```

### Query Processing Flow
```
User Query → Category Classification → Document Retrieval → 
Context Assembly → LLM Processing → Response Generation
```

### Page-Based Categorization
- **Pages 1-7**: General Information
- **Pages 8-17**: Course Prerequisites  
- **Pages 18-34**: Program Descriptions
- **Pages 35-41**: Training Rules

## 🔧 Configuration

### Environment Variables
```env
# Required
OPENAI_API_KEY=your_openai_api_key
TELEGRAM_TOKEN=your_telegram_bot_token

# Optional
PDF_PATH=MEE_Sylabus_with_metadata.pdf
COLLECTION_NAME=mee_syllabus_v1
LOG_LEVEL=INFO
MAX_TOKENS=4000
TEMPERATURE=0
```

### Customizable Parameters
- **Chunk Size**: Default 1200 characters
- **Chunk Overlap**: Default 150 characters  
- **Retrieval Count**: Default 8 documents (vector) + 6 (BM25)
- **Temperature**: Default 0 (deterministic responses)

## 🐛 Troubleshooting

### Common Issues

#### Bot Not Responding
```bash
# Check logs
tail -f logs/bot.log

# Verify environment variables
echo $TELEGRAM_TOKEN
echo $OPENAI_API_KEY
```

#### PDF Loading Errors
- Ensure PDF file exists in project directory
- Check file permissions
- Verify PDF is not corrupted or password-protected

#### Memory Issues
- Increase system RAM
- Reduce chunk size in configuration
- Use smaller embedding models

#### API Errors
- Verify OpenAI API key is valid
- Check API usage limits
- Ensure stable internet connection

### Performance Optimization
- Use SSD storage for vector database
- Increase RAM for better caching
- Consider using GPU for faster embeddings

## 📝 Logging

The bot includes comprehensive logging:
- **Info Level**: Normal operations, user queries
- **Error Level**: Exceptions, API failures
- **Debug Level**: Detailed processing information

Log files are stored in `logs/bot.log` with automatic rotation.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This bot is designed for academic purposes. Ensure compliance with:
- OpenAI's usage policies
- Telegram's bot guidelines
- Your institution's data policies
- Applicable privacy regulations

## 📞 Support

- **Issues**: Create an issue on GitHub
- **Documentation**: Check this README and inline code comments
- **Updates**: Watch the repository for new releases

## 🎯 Roadmap

- [ ] Multi-language support
- [ ] Voice message processing
- [ ] Integration with learning management systems
- [ ] Advanced analytics dashboard
- [ ] Mobile app companion
- [ ] Multi-document support
- [ ] Real-time document updates

---

**Made with ❤️ for the MEE community**
