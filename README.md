# PDF Summarizer - Chat with Your Documents

A web app that lets you upload PDFs and chat with them using AI. Get answers in multiple languages, manage multiple documents, and keep all your conversations saved.

## What it does

Upload any PDF and ask questions about it in plain language. The AI reads through your document and answers based on its content. You can also switch languages mid-conversation - ask in English, get answers in Spanish, or whatever you prefer.

I built this because I needed something to quickly scan through research papers and documentation without reading everything. Works pretty well for that.

## Features

- Upload and chat with multiple PDFs
- Ask questions in 10+ languages
- Get complete document summaries
- Dark/light theme toggle
- All your chats are saved automatically
- Pretty fast thanks to some caching tricks

## Tech stuff

Built with Flask and PostgreSQL. Uses LangChain to handle the AI parts (Groq's Llama model) and FAISS for searching through documents. Frontend is just vanilla JavaScript with Bootstrap.

The embeddings model runs locally (sentence-transformers), so you don't need to make API calls for every search. Makes it way faster.

## Setup

You'll need:
- Python 3.8+
- A PostgreSQL database (I use Railway, it's free)
- A Groq API key (also free from console.groq.com)

### Installation

```bash
# Clone/download the project
cd "your-project-folder"

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file:

```
DATABASE_URL=your_postgresql_url_here
SECRET_KEY=your_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here
FLASK_ENV=development
```

Generate the keys:
```bash
# SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Database setup

```bash
python init_db.py
```

This creates the tables you need: users, api_keys, chat_messages, and pdf_documents.

### Run it

```bash
python app.py
```

Go to http://localhost:5000

## How to use

1. Sign up and log in
2. Add your Groq API key in the API Keys section (activate it with the radio button)
3. Upload a PDF on the dashboard
4. Start asking questions

You can upload multiple PDFs and switch between them. All your chat history stays organized by document.

## Deployment

I deployed mine on Render with the database still on Railway. Works fine on the free tier.

Basic steps:
1. Push to GitHub
2. Connect to Render
3. Set these environment variables:
   - `DATABASE_URL` (your Railway PostgreSQL URL)
   - `SECRET_KEY` (generate a new one for production)
   - `ENCRYPTION_KEY` (generate a new one)
   - `FLASK_ENV=production`

The `build.sh` script handles the rest.

## Project structure

```
├── app.py              # Main Flask app
├── models.py           # Database models
├── config.py           # Config handling
├── templates/          # HTML files
├── static/            # CSS and JS
├── requirements.txt
├── build.sh           # Deployment build script
└── Procfile           # For Render/Heroku
```

## Known issues

- First load after inactivity takes a while (cold starts on free hosting)
- Large PDFs (>10MB) can be slow to process
- Some PDFs with images-as-text won't work well

## Future ideas

Things I might add:
- Export conversations to PDF
- Better summary generation
- Collaborative workspaces
- More customization options

## License

Do whatever you want with it. No restrictions.

## Notes

The app caches the embeddings model in memory, which makes subsequent PDF uploads much faster. First upload might take a few seconds while it loads the model.

API keys are encrypted in the database using Fernet, so they're not stored in plain text. Still, keep your .env file safe and don't commit it to git.

If you're running this locally and want to test with SQLite instead of PostgreSQL, just set `DATABASE_URL=sqlite:///app.db` in your .env file. The app handles both.
