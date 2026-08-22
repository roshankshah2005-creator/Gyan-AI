import os
import uuid
import streamlit as st
from groq import Groq
from pypdf import PdfReader

# -------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -------------------------------------------------------------------------
st.set_page_config(
    page_title="Gyan AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide Streamlit default header, footer, and menu
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# -------------------------------------------------------------------------
# 2. CLIENT INITIALIZATION (Using Groq)
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
# 3. CHAT SESSIONS STATE MANAGEMENT
# -------------------------------------------------------------------------
if "chats" not in st.session_state:
    initial_id = f"chat_{uuid.uuid4().hex[:6]}"
    st.session_state.chats = [{"id": initial_id, "title": "New Chat", "messages": []}]

if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = st.session_state.chats[0]["id"]

# Helper function to get current active chat dictionary
def get_active_chat():
    for chat in st.session_state.chats:
        if chat["id"] == st.session_state.active_chat_id:
            return chat
    # Fallback if ID not found
    return st.session_state.chats[0]

# -------------------------------------------------------------------------
# 4. SIDEBAR CONFIGURATION & CHAT HISTORY
# -------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 💬 CHAT HISTORY")
    
    if st.button("➕ New Chat", use_container_width=True):
        new_id = f"chat_{uuid.uuid4().hex[:6]}"
        st.session_state.chats.insert(0, {"id": new_id, "title": "New Chat", "messages": []})
        st.session_state.active_chat_id = new_id
        st.rerun()

    st.markdown("---")
    
    # Display saved chats list
    for chat in st.session_state.chats:
        is_active = chat["id"] == st.session_state.active_chat_id
        label = f"📌 {chat['title']}" if is_active else chat["title"]
        
        if st.button(label, key=f"btn_{chat['id']}", use_container_width=True):
            st.session_state.active_chat_id = chat["id"]
            st.rerun()

    st.markdown("---")
    st.markdown("### 🤖 AI PERSONA")
    persona_choice = st.selectbox(
        "Choose Persona",
        [
            "Senior Tech Lead", 
            "Data Science Mentor", 
            "Exam Prep Coach", 
            "Creative Director"
        ],
        label_visibility="collapsed"
    )
    
    system_instructions = {
        "Senior Tech Lead": "You are an expert Senior Tech Lead. Provide clean, efficient code snippets, rigorous code reviews, and robust software architecture guidance.",
        "Data Science Mentor": "You are a Data Science Mentor. Help with machine learning algorithms, pandas dataframes, scikit-learn pipelines, statistics, and data cleaning workflows.",
        "Exam Prep Coach": "You are an academic Exam Prep Coach. Break down tough engineering concepts, create structured study guides, summarize chapters, and give high-yield revision notes.",
        "Creative Director": "You are a Creative Director. Offer sharp typography feedback, color palette advice, design layouts, and creative direction for visual projects."
    }
    
    active_system_instruction = system_instructions.get(persona_choice, "You are Gyan, a helpful AI assistant.")

    st.markdown("---")
    st.markdown("### 📄 DOCUMENT RAG")
    uploaded_file = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"], label_visibility="collapsed")
    st.caption("200MB per file • PDF, TXT")

    document_text = ""
    if uploaded_file is not None:
        try:
            if uploaded_file.type == "application/pdf":
                reader = PdfReader(uploaded_file)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        document_text += text + "\n"
            else:
                document_text = uploaded_file.read().decode("utf-8")
            st.success("Document loaded successfully!")
        except Exception as e:
            st.error(f"Error reading document: {e}")

# -------------------------------------------------------------------------
# 5. CHAT INTERFACE & MESSAGE HANDLING
# -------------------------------------------------------------------------
st.markdown("<h1 style='text-align: center; color: #a29bfe;'>GYAN</h1>", unsafe_allow_html=True)

active_chat = get_active_chat()

# Render existing messages for the active chat
for message in active_chat["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a coding problem, exam query, or upload a doc..."):
    # Append user prompt to current chat
    active_chat["messages"].append({"role": "user", "content": prompt})
    
    # Auto-update title if it's the first message
    if active_chat["title"] == "New Chat":
        active_chat["title"] = prompt[:25] + ("..." if len(prompt) > 25 else "")

    with st.chat_message("user"):
        st.markdown(prompt)

    # Build messages payload for Groq
    messages_payload = [{"role": "system", "content": active_system_instruction}]
    
    if document_text:
        messages_payload.append({"role": "system", "content": f"Context from uploaded document:\n{document_text}"})
    
    for msg in active_chat["messages"]:
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
        
        # Rerun to refresh sidebar chat list titles smoothly
        st.rerun()
