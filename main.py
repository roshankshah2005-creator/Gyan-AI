import os
import uuid
import json
import streamlit as st
from groq import Groq

# -------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -------------------------------------------------------------------------
st.set_page_config(
    page_title="Gyan AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# -------------------------------------------------------------------------
# 2. CLIENT INITIALIZATION
# -------------------------------------------------------------------------
api_key = None
try:
    if "GROQ_API_KEY" in st.secrets:
        api_key = str(st.secrets["GROQ_API_KEY"]).strip()
except Exception:
    pass

if not api_key:
    api_key = os.getenv("GROQ_API_KEY", "").strip()

if not api_key:
    st.error("⚠️ GROQ_API_KEY is missing. Please configure it in your Streamlit Secrets.")
    st.stop()

try:
    client = Groq(api_key=api_key)
except Exception as e:
    st.error(f"Failed to initialize Groq client: {e}")
    st.stop()

# -------------------------------------------------------------------------
# 3. PERSISTENT CHAT STORAGE FUNCTIONS
# -------------------------------------------------------------------------
CHATS_FILE = "chats.json"

def load_chats():
    if os.path.exists(CHATS_FILE):
        try:
            with open(CHATS_FILE, "r") as f:
                data = json.load(f)
                if data:
                    return data
        except Exception:
            pass
    initial_id = f"chat_{uuid.uuid4().hex[:6]}"
    return [{"id": initial_id, "title": "New Chat", "messages": []}]

def save_chats(chats_data):
    try:
        with open(CHATS_FILE, "w") as f:
            json.dump(chats_data, f)
    except Exception as e:
        print(f"Error saving chats: {e}")

# -------------------------------------------------------------------------
# 4. STATE MANAGEMENT
# -------------------------------------------------------------------------
if "chats" not in st.session_state:
    st.session_state.chats = load_chats()

if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = st.session_state.chats[0]["id"]

def get_active_chat():
    for chat in st.session_state.chats:
        if chat["id"] == st.session_state.active_chat_id:
            return chat
    return st.session_state.chats[0]

# -------------------------------------------------------------------------
# 5. SIDEBAR: TYPOGRAPHY LOGO, CHAT HISTORY & PERSONAS
# -------------------------------------------------------------------------
with st.sidebar:
    # If logo.png (with transparent background) exists, it renders it; otherwise renders clean text branding
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.markdown(
            "<h1 style='text-align: center; color: #ffffff; font-family: sans-serif; letter-spacing: 2px; margin-bottom: 0px;'>gyan</h1>", 
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown("### 💬 CHAT HISTORY")
    
    if st.button("➕ New Chat", use_container_width=True):
        new_id = f"chat_{uuid.uuid4().hex[:6]}"
        st.session_state.chats.insert(0, {"id": new_id, "title": "New Chat", "messages": []})
        st.session_state.active_chat_id = new_id
        save_chats(st.session_state.chats)
        st.rerun()

    st.markdown("---")
    
    for chat in list(st.session_state.chats):
        is_active = chat["id"] == st.session_state.active_chat_id
        label = f"📌 {chat['title']}" if is_active else chat["title"]
        
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(label, key=f"btn_{chat['id']}", use_container_width=True):
                st.session_state.active_chat_id = chat["id"]
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{chat['id']}", use_container_width=True, help="Delete chat"):
                st.session_state.chats = [c for c in st.session_state.chats if c["id"] != chat["id"]]
                if not st.session_state.chats:
                    new_id = f"chat_{uuid.uuid4().hex[:6]}"
                    st.session_state.chats = [{"id": new_id, "title": "New Chat", "messages": []}]
                if st.session_state.active_chat_id == chat["id"]:
                    st.session_state.active_chat_id = st.session_state.chats[0]["id"]
                save_chats(st.session_state.chats)
                st.rerun()

    st.markdown("---")
    st.markdown("### 🤖 AI PERSONA")
    persona_choice = st.selectbox(
        "Choose Persona",
        [
            "Exam Prep Coach",
            "Strict Professor",
            "Senior Tech Lead", 
            "Data Science Mentor", 
            "Creative Director"
        ],
        label_visibility="collapsed"
    )
    
    system_instructions = {
        "Exam Prep Coach": (
            "You are an elite university Exam Prep Coach specializing in rigorous engineering and technical subjects. "
            "When given a topic, formula, or syllabus item, break it down into clean step-by-step derivations, "
            "key conceptual definitions, and standard numerical problem-solving workflows. "
            "Keep explanations high-yield, structured, and tailored for scoring top semester exam grades."
        ),
        "Strict Professor": (
            "You are a notoriously strict, old-school university professor holding a viva and grading tests. "
            "Do not accept vague answers or sugarcoat feedback. When the student answers a viva question or submits test work, "
            "critique their logic brutally, point out flaws, and assign a strict numeric score out of 10 with detailed remarks. "
            "Never give a 10/10 unless the answer is flawless."
        ),
        "Senior Tech Lead": "You are an expert Senior Tech Lead. Provide clean, efficient code snippets, rigorous code reviews, and robust software architecture guidance.",
        "Data Science Mentor": "You are a Data Science Mentor. Help with machine learning algorithms, pandas dataframes, scikit-learn pipelines, statistics, and data cleaning workflows.",
        "Creative Director": "You are a Creative Director. Offer sharp typography feedback, color palette advice, design layouts, and creative direction for visual projects."
    }
    
    active_system_instruction = system_instructions.get(persona_choice, "You are Gyan, a helpful AI assistant.")

# -------------------------------------------------------------------------
# 6. MAIN CHAT INTERFACE
# -------------------------------------------------------------------------
st.markdown("<h1 style='text-align: center; color: #ffffff; margin-bottom: 0px;'>gyan</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748b; font-size: 14px; margin-bottom: 25px;'>Your Semester Exam & Tech Companion</p>", unsafe_allow_html=True)

active_chat = get_active_chat()

# Render chat message history
for message in active_chat["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Bottom Chat Input
if prompt := st.chat_input("Ask an exam derivation, technical problem, or chat with your coach..."):
    active_chat["messages"].append({"role": "user", "content": prompt})
    
    if active_chat["title"] == "New Chat":
        active_chat["title"] = prompt[:25] + ("..." if len(prompt) > 25 else "")

    save_chats(st.session_state.chats)

    with st.chat_message("user"):
        st.markdown(prompt)

    messages_payload = [{"role": "system", "content": active_system_instruction}]
    
    recent_messages = active_chat["messages"][-10:]
    for msg in recent_messages:
        messages_payload.append({"role": msg["role"], "content": msg["content"]})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        response_text = None
        try:
            chat_completion = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=messages_payload,
                temperature=0.7,
            )
            response_text = chat_completion.choices[0].message.content
        except Exception as e:
            response_text = f"API Error Encountered: {e}"
        
        message_placeholder.markdown(response_text)
        active_chat["messages"].append({"role": "assistant", "content": response_text})
        
        save_chats(st.session_state.chats)
        st.rerun()
