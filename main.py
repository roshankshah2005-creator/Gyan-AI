import streamlit as st
from groq import Groq
from streamlit_cookies_controller import CookieController
import sqlite3
import json

# 1. Page Configuration
st.set_page_config(
    page_title="Gyan AI - Intelligent Companion",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Initialize Cookie Controller for persistent login
controller = CookieController()

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

# 3. Session State & Persistent Cookie Auto-Login
if "user_email" not in st.session_state:
    saved_email = controller.get("gyan_user_email")
    if saved_email:
        st.session_state.user_email = saved_email
        user_chats = load_chats(saved_email)
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
                
                # Save only the small email string in browser cookie for persistence
                controller.set("gyan_user_email", email, max_age=30*24*60*60)
                
                # Load user's chats from SQLite
                user_chats = load_chats(email)
                if not user_chats:
                    conn = sqlite3.connect('gyan_ai.db', check_same_thread=False)
                    c = conn.cursor()
                    c.execute("INSERT INTO chats (email, title, messages) VALUES (?, ?, ?)", (email, "New Conversation", json.dumps([])))
                    conn.commit()
                    new_chat_id = c.lastrowid
                    conn.close()
                    user_chats = [{"id": new_chat_id, "title": "New Conversation", "messages": []}]
                
                st.session_state.chats = user_chats
                st.session_state.current_chat_id = user_chats[0]["id"]
                st.rerun()
            else:
                st.error("Please fill in both fields correctly.")
    st.stop()

# Retrieve user name from database
user_name = get_user(st.session_state.user_email)

# Get API key from Streamlit Secrets
groq_api_key = st.secrets.get("GROQ_API_KEY", "")

# 5. Sidebar: Chat History & Controls
with st.sidebar:
    st.title("Gyan AI")
    st.caption(f"Logged in as: **{user_name}**")
    
    if st.button("➕ New Chat", use_container_width=True):
        conn = sqlite3.connect('gyan_ai.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("INSERT INTO chats (email, title, messages) VALUES (?, ?, ?)", (st.session_state.user_email, "New Conversation", json.dumps([])))
        conn.commit()
        new_id = c.lastrowid
        conn.close()
        
        st.session_state.chats.insert(0, {
            "id": new_id,
            "title": "New Conversation",
            "messages": []
        })
        st.session_state.current_chat_id = new_id
        st.rerun()

    st.markdown("---")
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
        st.session_state.chats = [c for c in st.session_state.chats if c["id"] not in chats_to_delete]
        if not st.session_state.chats:
            conn = sqlite3.connect('gyan_ai.db', check_same_thread=False)
            c = conn.cursor()
            c.execute("INSERT INTO chats (email, title, messages) VALUES (?, ?, ?)", (st.session_state.user_email, "New Conversation", json.dumps([])))
            conn.commit()
            new_id = c.lastrowid
            conn.close()
            st.session_state.chats = [{"id": new_id, "title": "New Conversation", "messages": []}]
            st.session_state.current_chat_id = new_id
        else:
            st.session_state.current_chat_id = st.session_state.chats[0]["id"]
        st.rerun()

    st.markdown("---")
    if st.button("Log Out", use_container_width=True):
        controller.remove("gyan_user_email")
        st.session_state.user_email = None
        st.session_state.chats = []
        st.session_state.current_chat_id = None
        st.rerun()

# 6. Main Chat Interface
current_chat = next((c for c in st.session_state.chats if c["id"] == st.session_state.current_chat_id), None)
if not current_chat and st.session_state.chats:
    current_chat = st.session_state.chats[0]
    st.session_state.current_chat_id = current_chat["id"]

col_title, col_persona = st.columns([2, 2])
with col_title:
    st.header(current_chat["title"])
with col_persona:
    persona = st.selectbox(
        "Persona",
        ["General Companion", "Exam Prep Coach", "Strict Professor", "Senior Tech Lead", "Data Science Mentor", "Creative Director"],
        label_visibility="collapsed"
    )

# System prompts with creator identity hardcoded
system_prompts = {
    "General Companion": "You are Gyan, an intelligent multi-persona AI companion created by Roshan, a student of NIT Durgapur.",
    "Exam Prep Coach": "You are an expert Exam Prep Coach, helping students break down derivations, concepts, and study schedules clearly. You were created by Roshan, a student of NIT Durgapur.",
    "Strict Professor": "You are a strict, academic professor who demands rigorous precision and high standards. You were created by Roshan, a student of NIT Durgapur.",
    "Senior Tech Lead": "You are a pragmatic Senior Tech Lead providing clean code architecture and debugging guidance. You were created by Roshan, a student of NIT Durgapur.",
    "Data Science Mentor": "You are a Data Science Mentor explaining machine learning algorithms, Python, and data pipelines. You were created by Roshan, a student of NIT Durgapur.",
    "Creative Director": "You are a Creative Director focusing on design principles, typography, and visual aesthetics. You were created by Roshan, a student of NIT Durgapur."
}

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

    # Automatically generate a smart title for the chat history
    if current_chat["title"] == "New Conversation":
        try:
            client_temp = Groq(api_key=groq_api_key)
            title_res = client_temp.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": "Generate a short, concise title (max 4 words) summarizing this user query. No quotes, no punctuation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10
            )
            gen_title = title_res.choices[0].message.content.strip()
            current_chat["title"] = gen_title if gen_title else (prompt[:25] + "...")
        except Exception:
            current_chat["title"] = prompt[:25] + "..." if len(prompt) > 25 else prompt

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        try:
            client = Groq(api_key=groq_api_key)
            
            formatted_messages = [{"role": "system", "content": system_prompts.get(persona, system_prompts["General Companion"])}]
            for m in current_chat["messages"]:
                formatted_messages.append({"role": m["role"], "content": m["content"]})

            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=formatted_messages,
                temperature=0.6,
                max_tokens=1500
            )
            
            reply = response.choices[0].message.content
            message_placeholder.markdown(reply)
            current_chat["messages"].append({"role": "assistant", "content": reply})
            
            # Save to SQLite database immediately
            save_chat_to_db(st.session_state.user_email, current_chat["id"], current_chat["title"], current_chat["messages"])
            
        except Exception as e:
            error_msg = f"AI Error: {str(e)}"
            message_placeholder.markdown(error_msg)
            current_chat["messages"].append({"role": "assistant", "content": error_msg})
            save_chat_to_db(st.session_state.user_email, current_chat["id"], current_chat["title"], current_chat["messages"])
