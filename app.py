import os
import time
import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader

# -------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -------------------------------------------------------------------------
st.set_page_config(
    page_title="Gyan AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------------------
# 2. API KEY VALIDATION & CLIENT INITIALIZATION
# -------------------------------------------------------------------------
api_key = None
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

if not api_key:
    api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("API Key not configured properly on the server.")
    st.stop()

# Configure the classic Google GenAI library directly
genai.configure(api_key=api_key)

# -------------------------------------------------------------------------
# 3. SIDEBAR CONFIGURATION & PERSONAS
# -------------------------------------------------------------------------
with st.sidebar:
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

    st.markdown("---")
    st.markdown("### 💬 RECENT CHATS")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# -------------------------------------------------------------------------
# 4. CHAT INTERFACE & STATE MANAGEMENT
# -------------------------------------------------------------------------
st.markdown("<h1 style='text-align: center; color: #a29bfe;'>GYAN</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a coding problem, exam query, or upload a doc..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Build history context
    history_chat = []
    for msg in st.session_state.messages[:-1]:
        role = "user" if msg["role"] == "user" else "model"
        history_chat.append({"role": role, "parts": [msg["content"]]})

    # Add document RAG context if uploaded
    full_prompt = prompt
    if document_text:
        full_prompt = f"Context from uploaded document:\n{document_text}\n\nUser Question: {prompt}"

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        response_text = None
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Initialize model with system instruction
                model = genai.GenerativeModel(
                    model_name='gemini-3.6-flash',
                    system_instruction=active_system_instruction
                )
                
                chat = model.start_chat(history=history_chat)
                response = chat.send_message(full_prompt)
                response_text = response.text
                break
            except Exception as e:
                if ("503" in str(e) or "429" in str(e)) and attempt < max_retries - 1:
                    time.sleep(1.5)
                    continue
                else:
                    response_text = f"An error occurred. Details: {e}"
        
        message_placeholder.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
