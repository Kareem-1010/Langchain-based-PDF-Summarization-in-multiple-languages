# 📄 Multilingual PDF Summarizer & QA SaaS

A professional, full-stack web application that allows users to upload PDF documents, ask questions, and receive intelligent responses in multiple languages using AI.

## ✨ Features

- **🔐 User Authentication**: Secure signup/login with password hashing
- **📤 PDF Upload & Processing**: Extract and analyze PDF content using LangChain
- **📚 Multiple PDF Management**: Upload, view, select, and chat with multiple PDFs
- **🤖 AI-Powered Q&A**: Chat with your PDFs or use general knowledge mode
- **📊 Complete Document Summaries**: Ask for "summary" to get comprehensive overviews
- **🌍 Multilingual Support**: Get responses in 10+ languages (English, Spanish, French, German, Hindi, Arabic, Chinese, Japanese, Portuguese, Russian)
- **🔄 Dynamic Language Switching**: Change language anytime during conversation
- **🔑 API Key Management**: Add, manage, and switch between multiple Groq API keys
- **💬 Chat History**: All conversations are saved and searchable by PDF
- **🌓 Dark/Light Theme**: Beautiful UI with theme persistence
- **⚡ Fast Performance**: Cached embeddings model for 3-5x faster processing
- **📱 Responsive Design**: Works seamlessly on desktop and mobile

## 🛠️ Tech Stack

### Backend
- **Flask**: Python web framework
- **PostgreSQL**: Database (Railway)
- **SQLAlchemy**: ORM for database management
- **LangChain**: LLM orchestration framework
- **ChatGroq**: AI model provider (Llama 3.3 70B)
- **HuggingFace Embeddings**: Local vectorization (sentence-transformers 5.2.2)
- **FAISS**: Vector store for document search
- **Gunicorn**: Production WSGI server

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with CSS variables
- **JavaScript (Vanilla)**: Client-side interactivity
- **Bootstrap 5**: Responsive layout framework

## 📋 Prerequisites

- Python 3.8 or higher
- PostgreSQL database (Railway account recommended)
- Groq API key (get one free at https://console.groq.com)

## 🚀 Installation & Setup

### 1. Clone or Download the Project

```bash
cd "c:\Users\Kareem\Desktop\PDF Summarizer"
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=your_railway_postgres_url_here
SECRET_KEY=your_random_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here
FLASK_ENV=development
```

**Important Notes:**
- Get your Railway PostgreSQL URL from your Railway dashboard (use PUBLIC URL)
- If the URL starts with `postgres://`, the app will automatically convert it to `postgresql://` for Flask compatibility
- Generate SECRET_KEY: `python -c "import secrets; print(secrets.token_hex(32))"`
- Generate ENCRYPTION_KEY: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

### 5. Initialize the Database

Run the database initialization script:

```bash
python init_db.py
```

This will create all necessary tables:
- `users` - User accounts
- `api_keys` - Encrypted Groq API keys
- `chat_messages` - Chat history
- `pdf_documents` - Uploaded PDFs and metadata

### 6. Create Uploads Folder

```bash
mkdir uploads
```

## 🏃 Running the Application

### Development Mode

```bash
python app.py
```

The application will be available at: http://localhost:5000

### Production Mode

For production deployment, use a WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📖 Usage Guide

### First Time Setup

1. **Visit the Landing Page**: Navigate to http://localhost:5000
2. **Create an Account**: Click "Sign Up" and create your account
3. **Login**: Use your credentials to log in
4. **Add API Key**: 
   - Go to the "API Keys" section
   - Click "Add New Key"
   - Enter a label (e.g., "My Personal Key")
   - Paste your Groq API key
   - Click "Add Key"

### Using the Application

#### PDF Mode (Document-Based Q&A)
1. Go to the Dashboard
2. Upload a PDF document (drag & drop or browse)
3. Wait for processing (you'll see a success message)
4. Select your preferred response language
5. Ask questions about the document
6. The AI will answer based on the PDF content

#### General Chat Mode
1. Without uploading a PDF, you can still chat
2. The AI will use general knowledge to answer
3. Responses will be in your selected language

#### Managing API Keys
- View all your API keys in the "API Keys" section
- Use radio buttons to select which key is active
- Delete keys you no longer need
- Only the active key is used for requests

#### Viewing History
- Go to "History" to see all past conversations
- Filter by language or role (user/assistant)
- Search through messages
- Clear all history if needed

## 🗂️ Project Structure

```
PDF Summarizer/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── config.py              # Configuration settings
├── init_db.py            # Database initialization script
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore           # Git ignore rules
│
├── templates/            # HTML templates
│   ├── base.html        # Base layout with theme toggle
│   ├── index.html       # Landing page
│   ├── login.html       # Login page
│   ├── signup.html      # Signup page
│   ├── dashboard.html   # Main dashboard with chat
│   ├── api_keys.html    # API key management
│   └── history.html     # Chat history
│
├── static/              # Static files
│   ├── css/
│   │   └── style.css    # Main stylesheet
│   └── js/
│       ├── theme.js     # Theme management
│       └── main.js      # Common functions
│
└── uploads/             # Temporary PDF storage
```

## 🔒 Security Features

- **Password Hashing**: Bcrypt for secure password storage
- **API Key Encryption**: Keys are encrypted using Fernet (cryptography)
- **Session Management**: Secure session cookies
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **CSRF Protection**: Built into Flask forms

## 🎨 Customization

### Changing Colors

Edit `static/css/style.css` and modify the CSS variables in the `:root` section:

```css
:root {
    --primary: #3b82f6;  /* Change primary color */
    --gradient-primary: linear-gradient(...);  /* Change gradients */
}
```

### Adding More Languages

1. Edit `templates/dashboard.html` and add options to the language dropdown
2. The AI will automatically respond in the specified language

### Changing AI Model

In `app.py`, modify the `create_conversation_chain` function:

```python
llm = ChatGroq(
    temperature=0.7,
    model_name="mixtral-8x7b-32768",  # Change model here
    groq_api_key=api_key
)
```

Available Groq models:
- `mixtral-8x7b-32768`
- `llama2-70b-4096`
- `gemma-7b-it`

## 🐛 Troubleshooting

### Database Connection Issues

**Problem**: `connection to server ... failed`

**Solution**: 
- Verify your Railway DATABASE_URL is correct
- Ensure Railway PostgreSQL instance is running
- Check if URL needs `postgresql://` instead of `postgres://`

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'X'`

**Solution**:
```bash
pip install -r requirements.txt
```

### PDF Processing Errors

**Problem**: "Could not extract text from PDF"

**Solution**:
- Ensure PDF is not password-protected
- Try a different PDF (some PDFs have text as images)
- File must be under 16MB

### API Key Errors

**Problem**: "Please add and activate a Groq API key"

**Solution**:
- Go to API Keys section
- Add at least one API key
- Ensure one key has the radio button selected (active)

### Theme Not Persisting

**Problem**: Theme resets after refresh

**Solution**:
- Check browser localStorage is enabled
- Clear browser cache and try again

## 📝 Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | Flask secret key for sessions | `your-secret-key-here` |
| `FLASK_ENV` | Environment mode | `development` or `production` |
| `ENCRYPTION_KEY` | (Optional) Key encryption key | Auto-generated if not set |

## 🚢 Deployment

### 🎯 **Recommended: Render + Railway**

**Deploy your app to Render (free web hosting) with Railway PostgreSQL database.**

📚 **[Complete Deployment Guide →](DEPLOYMENT.md)**

**Quick Overview:**

1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/pdf-summarizer.git
   git push -u origin main
   ```

2. **Set up Railway Database**:
   - Already done! ✅
   - Copy your PUBLIC PostgreSQL URL

3. **Deploy on Render**:
   - Connect GitHub repository
   - Add environment variables (DATABASE_URL, SECRET_KEY, ENCRYPTION_KEY)
   - Deploy! 🚀

4. **Your app goes live**:
   ```
   https://your-app-name.onrender.com
   ```

**Files for Deployment** (already included):
- `render.yaml` - Render service configuration
- `build.sh` - Build script
- `Procfile` - Process file
- `requirements.txt` - Dependencies
- `DEPLOYMENT.md` - Full deployment guide

### Alternative: Heroku

1. Create `Procfile` (already included)
2. Deploy:
```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
```

### Alternative: Railway (Full Stack)

Deploy both app and database on Railway:
```bash
# Add both services to Railway project
railway up
```

## 📄 License

This project is for educational and personal use.

## 🤝 Support

For issues or questions:
1. Check the Troubleshooting section
2. Review the Railway PostgreSQL documentation
3. Check Groq API documentation

## 🎯 Recent Updates

- [x] Multiple PDF support - Upload and switch between PDFs
- [x] PDF management - View, select, and delete PDFs
- [x] Complete document summaries - Enhanced chunk retrieval
- [x] Dynamic language switching - Change language mid-conversation
- [x] Performance optimizations - 3-5x faster with cached embeddings
- [x] Dark/Light theme toggle
- [x] Persistent PDF storage in database

## 🎯 Future Enhancements

- [ ] PDF summarization button (one-click summary)
- [ ] Export chat history to PDF/JSON
- [ ] Collaborative workspaces (share PDFs with teams)
- [ ] Voice input/output
- [ ] Mobile app (React Native)
- [ ] Custom embeddings models selection
- [ ] Advanced search across all PDFs
- [ ] PDF annotations and highlights
- [ ] Scheduled PDF processing
- [ ] Integration with cloud storage (Google Drive, Dropbox)

## 🌟 Credits

Built with:
- Flask
- LangChain
- Groq
- Bootstrap
- Inter Font
- Bootstrap Icons

---

**Made with ❤️ for intelligent document interaction**
