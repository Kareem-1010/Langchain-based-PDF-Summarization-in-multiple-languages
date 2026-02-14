from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
import pickle
import io
from datetime import datetime
from config import Config
from models import db, bcrypt, User, APIKey, ChatMessage, PDFDocument

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from PyPDF2 import PdfReader

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global storage for vector stores (in production, use Redis or similar)
vector_stores = {}
conversation_chains = {}

# Cache embeddings model globally for performance (load once)
_embeddings_cache = None

def get_embeddings_model():
    """Get cached embeddings model or create new one"""
    global _embeddings_cache
    if _embeddings_cache is None:
        print("Loading embeddings model (one-time initialization)...")
        import gc
        _embeddings_cache = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True, 'batch_size': 32}
        )
        # Force garbage collection to free memory
        gc.collect()
        print("✓ Embeddings model loaded")
    return _embeddings_cache

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def get_active_api_key(user_id):
    """Get the active Groq API key for the user"""
    api_key = APIKey.query.filter_by(user_id=user_id, is_active=True).first()
    return api_key.get_key_value() if api_key else None


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    text = ""
    try:
        pdf_reader = PdfReader(pdf_path)
        for page in pdf_reader.pages:
            text += page.extract_text()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
    return text


def create_vector_store(text, user_id):
    """Create FAISS vector store from text quickly using cached embeddings"""
    try:
        # Split text into optimized chunks for speed and quality
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_text(text)
        
        # Use cached embeddings model for speed
        embeddings = get_embeddings_model()
        
        # Create vector store (fast operation with cached model)
        vector_store = FAISS.from_texts(chunks, embeddings)
        vector_stores[user_id] = vector_store
        
        return True
    except Exception as e:
        print(f"Error creating vector store: {e}")
        return False


def get_language_instruction(language):
    """Get language-specific instruction for the prompt"""
    language_map = {
        'English': 'English',
        'Spanish': 'Spanish (Español)',
        'French': 'French (Français)',
        'German': 'German (Deutsch)',
        'Hindi': 'Hindi (हिन्दी)',
        'Arabic': 'Arabic (العربية)',
        'Chinese': 'Chinese (中文)',
        'Japanese': 'Japanese (日本語)',
        'Portuguese': 'Portuguese (Português)',
        'Russian': 'Russian (Русский)'
    }
    lang = language_map.get(language, 'English')
    return f"You must respond in {lang}. Ensure your entire response is in {lang}."


def create_conversation_chain(user_id, language='English'):
    """Create a conversation chain with or without PDF context"""
    api_key = get_active_api_key(user_id)
    if not api_key:
        return None
    
    try:
        llm = ChatGroq(
            temperature=0.7,
            model_name="llama-3.3-70b-versatile",
            groq_api_key=api_key
        )
        
        language_instruction = get_language_instruction(language)
        
        # Check if user has uploaded a PDF
        if user_id in vector_stores:
            # PDF-based QA with comprehensive retrieval
            template = f"""You are a helpful AI assistant. {language_instruction}
            Use the following context from the uploaded PDF document to answer the question comprehensively.
            Provide detailed, complete answers based on all the relevant information in the context.
            If the answer is not in the context, say "I don't have that information in the uploaded document."
            
            Context: {{context}}
            
            Chat History: {{chat_history}}
            
            Human: {{question}}
            
            Assistant:"""
            
            prompt = PromptTemplate(
                template=template,
                input_variables=["context", "chat_history", "question"]
            )
            
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"
            )
            
            # Use more chunks for better coverage (15 chunks)
            chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=vector_stores[user_id].as_retriever(search_kwargs={"k": 8}),
                memory=memory,
                combine_docs_chain_kwargs={"prompt": prompt},
                return_source_documents=False
            )
        else:
            # General knowledge QA
            from langchain.chains import LLMChain
            
            template = f"""You are a helpful AI assistant. {language_instruction}
            Answer the following question to the best of your ability.
            
            Chat History: {{chat_history}}
            
            Human: {{question}}
            
            Assistant:"""
            
            prompt = PromptTemplate(
                template=template,
                input_variables=["chat_history", "question"]
            )
            
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            
            chain = LLMChain(
                llm=llm,
                prompt=prompt,
                memory=memory
            )
        
        conversation_chains[user_id] = chain
        return chain
    
    except Exception as e:
        print(f"Error creating conversation chain: {e}")
        return None


# ============= ROUTES =============

@app.route('/')
def index():
    """Landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # Validation
        if not username or not email or not password:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': 'Username already exists'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email already exists'}), 400
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Account created successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Error creating account'}), 500
    
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    # Clean up user's vector store and conversation chain
    if current_user.id in vector_stores:
        del vector_stores[current_user.id]
    if current_user.id in conversation_chains:
        del conversation_chains[current_user.id]
    
    logout_user()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html', user=current_user)


@app.route('/api-keys')
@login_required
def api_keys():
    """API key management page"""
    return render_template('api_keys.html', user=current_user)


@app.route('/history')
@login_required
def history():
    """Chat history page"""
    return render_template('history.html', user=current_user)


# ============= API ENDPOINTS =============

@app.route('/api/keys', methods=['GET'])
@login_required
def get_api_keys():
    """Get all API keys for the current user"""
    keys = APIKey.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        'keys': [{
            'id': key.id,
            'label': key.label,
            'masked_key': key.get_masked_key(),
            'is_active': key.is_active,
            'created_at': key.created_at.isoformat()
        } for key in keys]
    })


@app.route('/api/keys', methods=['POST'])
@login_required
def add_api_key():
    """Add a new API key"""
    data = request.get_json()
    label = data.get('label')
    key_value = data.get('key_value')
    
    if not label or not key_value:
        return jsonify({'success': False, 'message': 'Label and key are required'}), 400
    
    try:
        api_key = APIKey(user_id=current_user.id, label=label)
        api_key.set_key_value(key_value)
        
        # If this is the first key, make it active
        if not APIKey.query.filter_by(user_id=current_user.id).first():
            api_key.is_active = True
        
        db.session.add(api_key)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'API key added successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error adding API key'}), 500


@app.route('/api/keys/<int:key_id>/activate', methods=['POST'])
@login_required
def activate_api_key(key_id):
    """Set an API key as active"""
    try:
        # Deactivate all keys
        APIKey.query.filter_by(user_id=current_user.id).update({'is_active': False})
        
        # Activate the selected key
        api_key = APIKey.query.filter_by(id=key_id, user_id=current_user.id).first()
        if api_key:
            api_key.is_active = True
            db.session.commit()
            
            # Reset conversation chain to use new key
            if current_user.id in conversation_chains:
                del conversation_chains[current_user.id]
            
            return jsonify({'success': True, 'message': 'API key activated'})
        else:
            return jsonify({'success': False, 'message': 'API key not found'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error activating API key'}), 500


@app.route('/api/keys/<int:key_id>', methods=['DELETE'])
@login_required
def delete_api_key(key_id):
    """Delete an API key"""
    try:
        api_key = APIKey.query.filter_by(id=key_id, user_id=current_user.id).first()
        if api_key:
            was_active = api_key.is_active
            db.session.delete(api_key)
            db.session.commit()
            
            # If deleted key was active, activate another one if available
            if was_active:
                first_key = APIKey.query.filter_by(user_id=current_user.id).first()
                if first_key:
                    first_key.is_active = True
                    db.session.commit()
            
            return jsonify({'success': True, 'message': 'API key deleted'})
        else:
            return jsonify({'success': False, 'message': 'API key not found'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error deleting API key'}), 500


@app.route('/api/upload-pdf', methods=['POST'])
@login_required
def upload_pdf():
    """Upload and process PDF"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Only PDF files are allowed'}), 400
    
    try:
        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{current_user.id}_{filename}")
        file.save(filepath)
        
        # Extract text and count pages
        text = extract_text_from_pdf(filepath)
        
        if not text or len(text.strip()) < 100:
            os.remove(filepath)
            return jsonify({'success': False, 'message': 'Could not extract text from PDF'}), 400
        
        # Get page count
        pdf_reader = PdfReader(filepath)
        page_count = len(pdf_reader.pages)
        file_size = os.path.getsize(filepath)
        
        # Deactivate all other PDFs for this user
        PDFDocument.query.filter_by(user_id=current_user.id).update({'is_active': False})
        
        # Save PDF to database
        pdf_doc = PDFDocument(
            user_id=current_user.id,
            filename=filename,
            original_filename=file.filename,
            file_size=file_size,
            page_count=page_count,
            text_content=text,
            is_active=True
        )
        db.session.add(pdf_doc)
        db.session.commit()
        
        # Create vector store (fast - text stays in DB for later recreation)
        success = create_vector_store(text, current_user.id)
        
        if success:
            # Reset conversation chain
            if current_user.id in conversation_chains:
                del conversation_chains[current_user.id]
            
            # Store PDF info in session
            session['current_pdf'] = filename
            session['current_pdf_id'] = pdf_doc.id
            
            # Clean up temporary file
            os.remove(filepath)
            
            return jsonify({
                'success': True,
                'message': 'PDF processed successfully',
                'filename': filename,
                'pdf_id': pdf_doc.id
            })
        else:
            db.session.delete(pdf_doc)
            db.session.commit()
            os.remove(filepath)
            return jsonify({'success': False, 'message': 'Error processing PDF'}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    """Handle chat messages"""
    data = request.get_json()
    message = data.get('message')
    language = data.get('language', 'English')
    
    if not message:
        return jsonify({'success': False, 'message': 'Message is required'}), 400
    
    # Check if user has an active API key
    api_key = get_active_api_key(current_user.id)
    if not api_key:
        return jsonify({
            'success': False,
            'message': 'Please add and activate a Groq API key in the API Keys section'
        }), 400
    
    try:
        print(f"[CHAT] User {current_user.id} sent message: {message[:50]}...")
        print(f"[CHAT] Language: {language}")
        print(f"[CHAT] Has vector store: {current_user.id in vector_stores}")
        print(f"[CHAT] Has conversation chain: {current_user.id in conversation_chains}")
        # Recreate chain if language changed or doesn't exist
        # This ensures language changes are respected mid-conversation
        chain = conversation_chains.get(current_user.id)
        if not chain or session.get('last_language') != language:
            chain = create_conversation_chain(current_user.id, language)
            session['last_language'] = language
            if not chain:
                return jsonify({'success': False, 'message': 'Error initializing chat'}), 500
        
        # Detect if user is asking for a summary
        is_summary_request = any(keyword in message.lower() for keyword in 
                                ['summary', 'summarize', 'summarise', 'overview', 'main points', 
                                 'key points', 'what is the document about', 'what does the pdf say',
                                 'résumé', 'resumen', 'zusammenfassung', 'riepilogo', 'خلاصة'])
        
        # Get response
        if current_user.id in vector_stores:
            # PDF-based QA
            if is_summary_request:
                # For summaries, use more chunks for comprehensive coverage (balanced for speed)
                retriever = vector_stores[current_user.id].as_retriever(search_kwargs={"k": 20})
                chain.retriever = retriever
            
            response = chain({"question": message})
            answer = response.get('answer', 'Sorry, I could not generate a response.')
        else:
            # General QA
            response = chain.run(question=message, chat_history="")
            answer = response
        
        # Save messages to database
        pdf_name = session.get('current_pdf')
        
        user_message = ChatMessage(
            user_id=current_user.id,
            role='user',
            message=message,
            language=language,
            pdf_name=pdf_name
        )
        
        assistant_message = ChatMessage(
            user_id=current_user.id,
            role='assistant',
            message=answer,
            language=language,
            pdf_name=pdf_name
        )
        
        db.session.add(user_message)
        db.session.add(assistant_message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'response': answer,
            'has_pdf_context': current_user.id in vector_stores
        })
    
    except Exception as e:
        print(f"[ERROR] Chat error for user {current_user.id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/clear-pdf', methods=['POST'])
@login_required
def clear_pdf():
    """Clear the current PDF context"""
    if current_user.id in vector_stores:
        del vector_stores[current_user.id]
    if current_user.id in conversation_chains:
        del conversation_chains[current_user.id]
    if 'current_pdf' in session:
        del session['current_pdf']
    if 'current_pdf_id' in session:
        del session['current_pdf_id']
    
    # Deactivate all PDFs for this user
    PDFDocument.query.filter_by(user_id=current_user.id).update({'is_active': False})
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'PDF context cleared'})


@app.route('/api/pdfs', methods=['GET'])
@login_required
def list_pdfs():
    """Get list of all uploaded PDFs for current user"""
    pdfs = PDFDocument.query.filter_by(user_id=current_user.id)\
        .order_by(PDFDocument.uploaded_at.desc()).all()
    
    return jsonify({
        'success': True,
        'pdfs': [pdf.to_dict() for pdf in pdfs]
    })


@app.route('/api/pdfs/<int:pdf_id>/select', methods=['POST'])
@login_required
def select_pdf(pdf_id):
    """Select a PDF to chat with"""
    pdf_doc = db.session.get(PDFDocument, pdf_id)
    
    if not pdf_doc or pdf_doc.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'PDF not found'}), 404
    
    try:
        # Deactivate all other PDFs
        PDFDocument.query.filter_by(user_id=current_user.id).update({'is_active': False})
        
        # Activate selected PDF
        pdf_doc.is_active = True
        pdf_doc.last_accessed = datetime.utcnow()
        db.session.commit()
        
        # Recreate vector store from text (fast with cached embeddings)
        create_vector_store(pdf_doc.text_content, current_user.id)
        
        # Reset conversation chain
        if current_user.id in conversation_chains:
            del conversation_chains[current_user.id]
        
        # Update session
        session['current_pdf'] = pdf_doc.filename
        session['current_pdf_id'] = pdf_doc.id
        
        return jsonify({
            'success': True,
            'message': f'Now chatting with {pdf_doc.filename}',
            'pdf': pdf_doc.to_dict()
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/pdfs/<int:pdf_id>', methods=['DELETE'])
@login_required
def delete_pdf(pdf_id):
    """Delete a PDF"""
    pdf_doc = db.session.get(PDFDocument, pdf_id)
    
    if not pdf_doc or pdf_doc.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'PDF not found'}), 404
    
    try:
        # Clear from memory if it's the active one
        if pdf_doc.is_active and current_user.id in vector_stores:
            del vector_stores[current_user.id]
            if current_user.id in conversation_chains:
                del conversation_chains[current_user.id]
            if 'current_pdf' in session:
                del session['current_pdf']
            if 'current_pdf_id' in session:
                del session['current_pdf_id']
        
        # Delete from database
        db.session.delete(pdf_doc)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'PDF deleted successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/history', methods=['GET'])
@login_required
def get_history():
    """Get chat history"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    messages = ChatMessage.query.filter_by(user_id=current_user.id)\
        .order_by(ChatMessage.timestamp.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'messages': [msg.to_dict() for msg in messages.items],
        'total': messages.total,
        'pages': messages.pages,
        'current_page': page
    })


@app.route('/api/history/clear', methods=['DELETE'])
@login_required
def clear_history():
    """Clear all chat history"""
    try:
        ChatMessage.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({'success': True, 'message': 'History cleared'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error clearing history'}), 500


# ============= DATABASE INITIALIZATION =============

def init_db():
    """Initialize the database"""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")


if __name__ == '__main__':
    # Get port from environment variable (Render provides this)
    port = int(os.getenv('PORT', 5000))
    # Uncomment the line below to initialize database on first run
    # init_db()
    app.run(debug=True, host='0.0.0.0', port=port)
