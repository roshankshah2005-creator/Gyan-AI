import streamlit as st
from groq import Groq
import sqlite3
import json
import random
import io
import pypdf
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import streamlit.components.v1 as components

# 1. Page Configuration 
st.set_page_config(
    page_title="GYAN - Intelligent Companion",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        /* Import a sleek modern tech font for the logo */
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&display=swap');

        /* Custom Gradient Logo Styling */
        .brand-logo {
            font-family: 'Orbitron', sans-serif;
            font-size: 28px;
            font-weight: 700;
            background: linear-gradient(45deg, #3b82f6, #10b981);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 2px;
            margin-bottom: 5px;
        }

        /* Completely hide Streamlit's top header, menu, deploy button, and share elements */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden !important; display: none !important;}
        footer {visibility: hidden;}
        .stDeployButton {display: none;}
        div.viewerBadge_container__1QSob, .viewerBadge_link__1S137, footer ~ div {
            display: none !important;
        }
        
        /* Ensure mobile sidebar toggle button is still accessible if needed */
        [data-testid="collapsedControl"] {
            display: block !important;
            color: #3b82f6 !important;
        }
        
        /* Distinct styling for User Questions */
        div.stChatMessage[data-testid="stChatMessage-user"] {
            background-color: #1e293b !important;
            border-left: 5px solid #3b82f6 !important;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 10px;
        }
        /* Distinct styling for AI Answers */
        div.stChatMessage[data-testid="stChatMessage-assistant"] {
            background-color: #0f172a !important;
            border-left: 5px solid #10b981 !important;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# Function to auto-scroll
def scroll_to_bottom():
    js = """
    <script>
        setTimeout(function() {
            const mainContainer = window.parent.document.querySelector('.main');
            if (mainContainer) {
                mainContainer.scrollTop = mainContainer.scrollHeight;
            }
        }, 100);
    </script>
    """
    components.html(js, height=0, width=0)

# 2. Initialize SQLite Database
def init_db():
    conn = sqlite3.connect('gyan_ai.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, name TEXT)''')
    
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]
    if "password" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN password TEXT")

    c.execute('''CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    email TEXT, 
                    title TEXT, 
                    messages TEXT,
                    documents TEXT
                )''')
    
    c.execute("PRAGMA table_info(chats)")
    chat_columns = [col[1] for col in c.fetchall()]
    if "documents" not in chat_columns:
        c.execute("ALTER TABLE chats ADD COLUMN documents TEXT")

    conn.commit()
    conn.close()

init_db()

# Database Helper Functions
def get_user(email):
    conn = sqlite3.connect('gyan_ai.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT name FROM users WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def register_user(email, name, password):
    conn = sqlite3.connect('gyan_ai.db', check_same_thread=False)
    c = conn.cursor()
    
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]
    if "password" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN password TEXT")
        conn.commit()

    c.execute("SELECT email FROM users WHERE email = ?", (email,))
    if c.fetchone():
        conn.close()
        return False
    c.execute("INSERT INTO users (email, name, password) VALUES (?, ?, ?)", (email, name, password))
    conn.commit()
    conn.close()
    return True

def verify_user(email, password):
    conn = sqlite3.connect('gyan_ai.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT name, password FROM users WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    if row and row[1] == password:
        return row[0]
    return None

def update_password(email, new_password):
    conn = sqlite3.connect('gyan_ai.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("UPDATE users SET password = ? WHERE email = ?", (new_password, email))
    conn.commit()
    conn.close()

def load_chats(email):
    conn = sqlite3.connect('gyan_ai.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT id, title, messages, documents FROM chats WHERE email = ?", (email,))
    rows = c.fetchall()
    conn.close()
    
    chats = []
    for row in rows:
        doc_data = None
        if row[3]:
            try:
                parsed = json.loads(row[3])
                if isinstance(parsed, list) and len(parsed) > 0:
                    doc_data = parsed[-1]
                elif isinstance(parsed, dict):
                    doc_data = parsed
            except:
                doc_data = None
                
        chats.append({
            "id": row[0],
            "title": row[1],
            "messages": json.loads(row[2]) if row[2] else [],
            "document": doc_data
        })
    return chats

def create_new_chat(email):
    conn = sqlite3.connect('gyan_ai.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT INTO chats (email, title, messages, documents) VALUES (?, ?, ?, ?)", 
              (email, "New Conversation", json.dumps([]), json.dumps(None)))
    conn.commit()
    chat_id = c.lastrowid
    conn.close()
    return chat_id

def save_chat_to_db(email, chat_id, title, messages, document):
    conn = sqlite3.connect('gyan_ai.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT id FROM chats WHERE id = ?", (chat_id,))
    exists = c.fetchone()
    
    messages_json = json.dumps(messages)
    doc_json = json.dumps(document)
    if exists:
        c.execute("UPDATE chats SET title = ?, messages = ?, documents = ? WHERE id = ?", (title, messages_json, doc_json, chat_id))
    else:
        c.execute("INSERT INTO chats (email, title, messages, documents) VALUES (?, ?, ?, ?)", (email, title, messages_json, doc_json))
    conn.commit()
    conn.close()

def delete_chat_from_db(chat_id):
    conn = sqlite3.connect('gyan_ai.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
    conn.commit()
    conn.close()

# RAG Document Processing Utilities
def extract_text_from_file(uploaded_file):
    text = ""
    if uploaded_file.type == "application/pdf":
        try:
            reader = pypdf.PdfReader(uploaded_file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
    elif uploaded_file.type == "text/plain":
        try:
            text = uploaded_file.getvalue().decode("utf-8")
        except Exception as e:
            st.error(f"Error reading text file: {e}")
    return text

def chunk_text(text, chunk_size=400, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks

def retrieve_relevant_chunks(query, document, top_k=5):
    if not document or not document.get("chunks"):
        return ""
    all_chunks = document["chunks"]
    
    try:
        vectorizer = TfidfVectorizer().fit(all_chunks + [query])
        chunk_vectors = vectorizer.transform(all_chunks)
        query_vector = vectorizer.transform([query])
        
        similarities = cosine_similarity(query_vector, chunk_vectors).flatten()
        top_indices = similarities.argsort()[::-1][:top_k]
        
        relevant_text = "\n\n---\n\n".join([all_chunks[idx] for idx in top_indices])
        return relevant_text
    except Exception:
        return "\n\n---\n\n".join(all_chunks[:top_k])

# 3. Session State & URL Parameter Auto-Login
if "user_email" not in st.session_state:
    url_email = st.query_params.get("email", None)
    if url_email:
        st.session_state.user_email = url_email
        user_chats = load_chats(url_email)
        st.session_state.chats = user_chats if user_chats else []
        if user_chats:
            st.session_state.current_chat_id = user_chats[0]["id"]
    else:
        st.session_state.user_email = None

if "chats" not in st.session_state:
    st.session_state.chats = []
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "forgot_password_mode" not in st.session_state:
    st.session_state.forgot_password_mode = False

# Captcha numbers setup
if "captcha_num1" not in st.session_state:
    st.session_state.captcha_num1 = random.randint(1, 10)
    st.session_state.captcha_num2 = random.randint(1, 10)

if "reset_captcha_num1" not in st.session_state:
    st.session_state.reset_captcha_num1 = random.randint(1, 10)
    st.session_state.reset_captcha_num2 = random.randint(1, 10)

# 4. Authentication & Forgot Password Screen
if not st.session_state.user_email:
    st.title("Welcome to GYAN")
    
    if st.session_state.forgot_password_mode:
        st.subheader("Reset Password & Verify Identity")
        with st.form("forgot_password_form"):
            reset_email = st.text_input("Enter your registered Email Address").strip().lower()
            new_pass = st.text_input("Enter New Password", type="password").strip()
            
            rn1 = st.session_state.reset_captcha_num1
            rn2 = st.session_state.reset_captcha_num2
            reset_captcha_input = st.text_input(f"Human Verification: What is {rn1} + {rn2}?")
            
            submit_reset = st.form_submit_button("Update Password")
            back_to_login = st.form_submit_button("Back to Log In")
            
            if submit_reset:
                try:
                    reset_user_answer = int(reset_captcha_input.strip())
                except ValueError:
                    reset_user_answer = -999

                if not reset_email or not new_pass:
                    st.error("Please fill in both email and new password.")
                elif reset_user_answer != (rn1 + rn2):
                    st.error("Incorrect verification answer! Please try again.")
                    st.session_state.reset_captcha_num1 = random.randint(1, 10)
                    st.session_state.reset_captcha_num2 = random.randint(1, 10)
                else:
                    user_exists = get_user(reset_email)
                    if user_exists:
                        update_password(reset_email, new_pass)
                        st.success("Password updated successfully! Please log in.")
                        st.session_state.forgot_password_mode = False
                        st.rerun()
                    else:
                        st.error("No account found with this email address.")
            
            if back_to_login:
                st.session_state.forgot_password_mode = False
                st.rerun()
        st.stop()

    auth_mode = st.radio("Choose Action", ["Log In", "Sign Up"], horizontal=True)
    
    if auth_mode == "Log In":
        with st.form("login_form"):
            email_input = st.text_input("Email Address")
            password_input = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Log In")
            
            if submit_login:
                email = email_input.strip().lower()
                password = password_input.strip()
                name = verify_user(email, password)
                if name:
                    st.session_state.user_email = email
                    st.query_params["email"] = email
                    
                    user_chats = load_chats(email)
                    if not user_chats:
                        create_new_chat(email)
                        user_chats = load_chats(email)
                    
                    st.session_state.chats = user_chats
                    st.session_state.current_chat_id = user_chats[0]["id"]
                    st.rerun()
                else:
                    st.error("Invalid email or password.")
        
        if st.button("Forgot Password?"):
            st.session_state.forgot_password_mode = True
            st.rerun()

    else:
        with st.form("signup_form"):
            name_input = st.text_input("Your Name")
            email_input = st.text_input("Email Address")
            password_input = st.text_input("Password", type="password")
            
            n1 = st.session_state.captcha_num1
            n2 = st.session_state.captcha_num2
            captcha_input = st.text_input(f"Human Verification: What is {n1} + {n2}?")
            
            submit_signup = st.form_submit_button("Sign Up")
            
            if submit_signup:
                name = name_input.strip()
                email = email_input.strip().lower()
                password = password_input.strip()
                
                try:
                    user_answer = int(captcha_input.strip())
                except ValueError:
                    user_answer = -999

                if not name or not email or not password:
                    st.error("Please fill in all fields correctly.")
                elif user_answer != (n1 + n2):
                    st.error("Incorrect verification answer! Please try again.")
                    st.session_state.captcha_num1 = random.randint(1, 10)
                    st.session_state.captcha_num2 = random.randint(1, 10)
                else:
                    success = register_user(email, name, password)
                    if success:
                        st.session_state.user_email = email
                        st.query_params["email"] = email
                        
                        new_chat_id = create_new_chat(email)
                        st.session_state.chats = load_chats(email)
                        st.session_state.current_chat_id = new_chat_id
                        st.rerun()
                    else:
                        st.error("Email is already registered! Please switch to Log In.")
    st.stop()

user_name = get_user(st.session_state.user_email)
groq_api_key = st.secrets.get("GROQ_API_KEY", "")

st.session_state.chats = load_chats(st.session_state.user_email)

# 5. Sidebar - Chat History, Persona Selector, Single Document Uploader & Controls
with st.sidebar:
    st.markdown('<div class="brand-logo">GYAN</div>', unsafe_allow_html=True)
    st.caption(f"Logged in as: **{user_name}**")
    
    st.markdown("---")
    st.subheader("AI Persona")
    persona = st.selectbox(
        "Persona",
        ["General Companion", "Exam Prep Coach", "Strict Professor", "Senior Tech Lead", "Data Science Mentor", "Creative Director", "Code Helper"],
        key="persona_select",
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    if st.button("➕ New Chat", use_container_width=True):
        new_id = create_new_chat(st.session_state.user_email)
        st.session_state.current_chat_id = new_id
        st.rerun()

    # Document Section wrapped in form with clear_on_submit to instantly clear widget box after click
    st.subheader("📚 Knowledge Base Document")
    current_chat = next((c for c in st.session_state.chats if c["id"] == st.session_state.current_chat_id), None)
    
    with st.form("upload_form", clear_on_submit=True):
        uploaded_file = st.file_uploader("Upload single PDF or TXT", type=["pdf", "txt"])
        submit_upload = st.form_submit_button("Upload Document")
        
        if submit_upload and uploaded_file and current_chat:
            with st.spinner("Processing & chunking document..."):
                raw_text = extract_text_from_file(uploaded_file)
                if raw_text and len(raw_text.strip()) > 0:
                    chunks = chunk_text(raw_text)
                    current_chat["document"] = {
                        "filename": uploaded_file.name,
                        "chunks": chunks
                    }
                    save_chat_to_db(st.session_state.user_email, current_chat["id"], current_chat["title"], current_chat["messages"], current_chat["document"])
                    st.success(f"Loaded {uploaded_file.name} successfully!")
                    st.rerun()
                else:
                    st.error("Could not extract text. Make sure your PDF has selectable text.")

    if current_chat and current_chat.get("document"):
        st.caption("Active Document:")
        col_d1, col_d2 = st.columns([4, 1])
        with col_d1:
            st.text(f"• {current_chat['document']['filename']}")
        with col_d2:
            if st.button("🗑️", key="del_doc", help="Remove document"):
                current_chat["document"] = None
                save_chat_to_db(st.session_state.user_email, current_chat["id"], current_chat["title"], current_chat["messages"], current_chat["document"])
                st.rerun()

    st.subheader("Chat History")

    chats_to_delete = []
    for chat in st.session_state.chats:
        col1, col2 = st.sidebar.columns([4, 1])
        with col1:
            is_active = chat["id"] == st.session_state.current_chat_id
            btn_type = "primary" if is_active else "secondary"
            if st.button(chat["title"], key=f"chat_{chat['id']}", type=btn_type, use_container_width=True):
                st.session_state.current_chat_id = chat["id"]
                st.rerun()
        with col2:
            if st.button("❌", key=f"del_{chat['id']}", help="Delete chat"):
                chats_to_delete.append(chat["id"])

    if chats_to_delete:
        for cid in chats_to_delete:
            delete_chat_from_db(cid)
        
        refreshed_chats = load_chats(st.session_state.user_email)
        if not refreshed_chats:
            fallback_id = create_new_chat(st.session_state.user_email)
            st.session_state.current_chat_id = fallback_id
        else:
            st.session_state.current_chat_id = refreshed_chats[0]["id"]
        
        st.session_state.chats = load_chats(st.session_state.user_email)
        st.rerun()

    st.markdown("---")
    if st.button("Log Out", use_container_width=True):
        st.query_params.clear()
        st.session_state.user_email = None
        st.session_state.chats = []
        st.session_state.current_chat_id = None
        st.rerun()

# 6. Main Chat Interface
current_chat = next((c for c in st.session_state.chats if c["id"] == st.session_state.current_chat_id), None)
if not current_chat and st.session_state.chats:
    current_chat = st.session_state.chats[0]
    st.session_state.current_chat_id = current_chat["id"]

if current_chat and len(current_chat["messages"]) == 0:
    st.markdown(f"<h1 style='text-align: center; margin-top: 20vh;'>How can I help you, {user_name}!!</h1>", unsafe_allow_html=True)

system_prompts = {
    "General Companion": "You are Gyan, an intelligent multi-persona AI companion created by Roshan, a student of NIT Durgapur. IMPORTANT: Always format mathematical equations or scientific formulas using double dollar signs ($$...$$) for block equations and single dollar signs ($...$) for inline equations. Never use square brackets [...] for math.",
    "Exam Prep Coach": "You are an expert Exam Prep Coach, helping students break down derivations, concepts, and study schedules clearly. You were created by Roshan, a student of NIT Durgapur. IMPORTANT: Always format mathematical equations or scientific formulas using double dollar signs ($$...$$) for block equations and single dollar signs ($...$) for inline equations. Never use square brackets [...] for math.",
    "Strict Professor": "You are a strict, academic professor who demands rigorous precision and high standards. You were created by Roshan, a student of NIT Durgapur. IMPORTANT: Always format mathematical equations or scientific formulas using double dollar signs ($$...$$) for block equations and single dollar signs ($...$) for inline equations. Never use square brackets [...] for math.",
    "Senior Tech Lead": "You are a pragmatic Senior Tech Lead providing clean code architecture and debugging guidance. You were created by Roshan, a student of NIT Durgapur.",
    "Data Science Mentor": "You are a Data Science Mentor explaining machine learning algorithms, Python, and data pipelines. You were created by Roshan, a student of NIT Durgapur.",
    "Creative Director": "You are a Creative Director focusing on design principles, typography, and visual aesthetics. You were created by Roshan, a student of NIT Durgapur.",
    "Code Helper": "You are an expert Code Helper and debugging assistant, providing clean, well-commented code snippets and solutions. You were created by Roshan, a student of NIT Durgapur."
}

if current_chat:
    for message in current_chat["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("Ask anything or query your uploaded document..."):
    if not groq_api_key:
        st.error("Groq API key is missing! Check your secrets.toml file.")
        st.stop()

    current_chat["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    scroll_to_bottom()

    if current_chat["title"] == "New Conversation":
        try:
            client_temp = Groq(api_key=groq_api_key)
            title_res = client_temp.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": "Generate a short title (max 4 words) summarizing this query. No quotes, no punctuation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=15
            )
            gen_title = title_res.choices[0].message.content.strip()
            current_chat["title"] = gen_title if gen_title else (prompt[:25] + "...")
        except Exception:
            current_chat["title"] = prompt[:25] + "..." if len(prompt) > 25 else prompt

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            client = Groq(api_key=groq_api_key)
            base_system_prompt = system_prompts.get(persona, system_prompts["General Companion"])
            
            rag_context = ""
            if current_chat.get("document"):
                rag_context = retrieve_relevant_chunks(prompt, current_chat["document"], top_k=6)
            
            if rag_context:
                final_system_content = f"{base_system_prompt}\n\n[CONTEXT KNOWLEDGE BASE]\nUse the following extracted document text to answer the user's question accurately and thoroughly:\n{rag_context}"
            else:
                final_system_content = base_system_prompt

            formatted_messages = [{"role": "system", "content": final_system_content}]
            for m in current_chat["messages"]:
                formatted_messages.append({"role": m["role"], "content": m["content"]})

            stream = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=formatted_messages,
                temperature=0.5,
                max_tokens=2048,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    display_text = full_response.lstrip(" .<br>•\n")
                    message_placeholder.markdown(display_text + "▌")
            
            full_response = full_response.lstrip(" .<br>•\n")
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            full_response = f"AI Error: {str(e)}"
            message_placeholder.markdown(full_response)

    current_chat["messages"].append({"role": "assistant", "content": full_response})
    save_chat_to_db(st.session_state.user_email, current_chat["id"], current_chat["title"], current_chat["messages"], current_chat["document"])
    scroll_to_bottom()
