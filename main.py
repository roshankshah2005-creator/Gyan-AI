import streamlit as st
from groq import Groq
import sqlite3
import json
import streamlit.components.v1 as components

# 1. Page Configuration & Custom CSS to Hide GitHub/Streamlit Header Icons
st.set_page_config(
    page_title="Gyan AI - Intelligent Companion",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        /* Hide Streamlit top header, menu, and GitHub share button */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        
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
    c.execute('''CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    email TEXT, 
                    title TEXT, 
                    messages TEXT
                )''')
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

def save_user(email, name):
    conn = sqlite3.connect('gyan_ai.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (email, name) VALUES (?, ?)", (email, name))
    conn.commit()
    conn.close()

def load_chats(email):
    conn = sqlite3.connect('gyan_ai.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT id, title, messages FROM chats WHERE email = ?", (email,))
    rows = c.fetchall()
    conn.close()
    
    chats = []
    for row in rows:
        chats.append({
            "id": row[0],
            "title": row[1],
            "messages": json.loads(row[2])
        })
    return chats

def save_chat_to_db(email, chat_id, title, messages):
    conn = sqlite3.connect('gyan_ai.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT id FROM chats WHERE id = ?", (chat_id,))
    exists = c.fetchone()
    
    messages_json = json.dumps(messages)
    if exists:
        c.execute("UPDATE chats SET title = ?, messages = ? WHERE id = ?", (title, messages_json, chat_id))
    else:
        c.execute("INSERT INTO chats (email, title, messages) VALUES (?, ?, ?)", (email, title, messages_json))
    conn.commit()
    conn.close()

def delete_chat_from_db(chat_id):
    conn = sqlite3.connect('gyan_ai.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
    conn.commit()
    conn.close()

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

# 4. Authentication Screen
if not st.session_state.user_email:
    st.title("Welcome to Gyan AI")
    st.markdown("Please enter your details to sign in or register.")
    
    with st.form("auth_form"):
        name_input = st.text_input("Your Name")
        email_input = st.text_input("Email Address (Used to save your account)")
        submit_auth = st.form_submit_button("Continue to App")
        
        if submit_auth:
            name = name_input.strip()
            email = email_input.strip().lower()
            if name and email:
                save_user(email, name)
                st.session_state.user_email = email
                st.query_params["email"] = email
                
                user_chats = load_chats(email)
                if not user_chats:
                    conn = sqlite3.connect('gyan_ai.db', check_same_thread=False)
                    c = conn.cursor()
                    c.execute("INSERT INTO chats (email, title, messages) VALUES (?, ?, ?)", (email, "New Conversation", json.dumps([])))
                    conn.commit()
                    new_chat_id = c.lastrowid
                    conn.close()
                    user_chats = [{"id": new_id, "title": "New Conversation", "messages": []}]
                
                st.session_state.chats = user_chats
                st.session_state.current_chat_id = user_chats[0]["id"]
                st.rerun()
            else:
                st.error("Please fill in both fields correctly.")
    st.stop()

user_name = get_user(st.session_state.user_email)
groq_api_key = st.secrets.get("GROQ_API_KEY", "")

st.session_state.chats = load_chats(st.session_state.user_email)

# 5. Sidebar: Chat History, Persona Selector & Controls
with st.sidebar:
    st.title("Gyan AI")
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
        conn = sqlite3.connect('gyan_ai.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("INSERT INTO chats (email, title, messages) VALUES (?, ?, ?)", (st.session_state.user_email, "New Conversation", json.dumps([])))
        conn.commit()
        new_id = c.lastrowid
        conn.close()
        
        st.session_state.current_chat_id = new_id
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
            conn = sqlite3.connect('gyan_ai.db', check_same_thread=False)
            c = conn.cursor()
            c.execute("INSERT INTO chats (email, title, messages) VALUES (?, ?, ?)", (st.session_state.user_email, "New Conversation", json.dumps([])))
            conn.commit()
            new_id = c.lastrowid
            conn.close()
            st.session_state.current_chat_id = new_id
        else:
            st.session_state.current_chat_id = refreshed_chats[0]["id"]
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

# Display "Hi, Username" for new empty chats, then switch to chat title once started
if current_chat and (current_chat["title"] == "New Conversation" or len(current_chat["messages"]) == 0):
    st.header(f"Hi, {user_name} 👋")
else:
    st.header(current_chat["title"] if current_chat else "Gyan AI")

system_prompts = {
    "General Companion": "You are Gyan, an intelligent multi-persona AI companion created by Roshan, a student of NIT Durgapur.",
    "Exam Prep Coach": "You are an expert Exam Prep Coach, helping students break down derivations, concepts, and study schedules clearly. You were created by Roshan, a student of NIT Durgapur.",
    "Strict Professor": "You are a strict, academic professor who demands rigorous precision and high standards. You were created by Roshan, a student of NIT Durgapur.",
    "Senior Tech Lead": "You are a pragmatic Senior Tech Lead providing clean code architecture and debugging guidance. You were created by Roshan, a student of NIT Durgapur.",
    "Data Science Mentor": "You are a Data Science Mentor explaining machine learning algorithms, Python, and data pipelines. You were created by Roshan, a student of NIT Durgapur.",
    "Creative Director": "You are a Creative Director focusing on design principles, typography, and visual aesthetics. You were created by Roshan, a student of NIT Durgapur.",
    "Code Helper": "You are an expert Code Helper and debugging assistant, providing clean, well-commented code snippets and solutions. You were created by Roshan, a student of NIT Durgapur."
}

if current_chat:
    for message in current_chat["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("Ask anything or request a structured guide..."):
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
                max_tokens=8
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
            formatted_messages = [{"role": "system", "content": system_prompts.get(persona, system_prompts["General Companion"])}]
            for m in current_chat["messages"]:
                formatted_messages.append({"role": m["role"], "content": m["content"]})

            stream = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=formatted_messages,
                temperature=0.6,
                max_tokens=1024,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            full_response = f"AI Error: {str(e)}"
            message_placeholder.markdown(full_response)

    current_chat["messages"].append({"role": "assistant", "content": full_response})
    save_chat_to_db(st.session_state.user_email, current_chat["id"], current_chat["title"], current_chat["messages"])
    scroll_to_bottom()
