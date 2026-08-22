import os
import time
import streamlit as st
from google import genai
from google.genai import types
from pypdf import PdfReader

# -------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & SERVICE ACCOUNT AUTHENTICATION
# -------------------------------------------------------------------------
st.set_page_config(
    page_title="Gyan AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"

try:
    client = genai.Client(
        vertexai=True,
        project="gen-lang-client-0656156962", 
        location="us-central1"
    )
except Exception as e:
    st.error(f"Failed to initialize client via Service Account: {e}")
    st.stop()

# -------------------------------------------------------------------------
# 2. VERTEX AI CLIENT INITIALIZATION (Service Account Mode)
# -------------------------------------------------------------------------
import os
from google import genai
from google.genai import types

# Force Vertex AI backend to talk to aiplatform.googleapis.com instead of AI Studio
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
os.environ["GOOGLE_CLOUD_PROJECT"] = "gen-lang-client-0656156962"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"

# Initialize client WITHOUT an api_key parameter so it uses the service account credentials
try:
    client = genai.Client()
except Exception as e:
    st.error(f"Failed to initialize Vertex AI client: {e}")
    st.stop()
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

    contents = []
    if document_text:
        contents.append(f"Context from uploaded document:\n{document_text}\n\n")
    
    for msg in st.session_state.messages:
        contents.append(f"{msg['role'].capitalize()}: {msg['content']}")

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        response_text = None
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=active_system_instruction,
                    temperature=0.7
                )
            )
            response_text = response.text
        except Exception as e:
            response_text = f"API Error Encountered: {e}"
        
        message_placeholder.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
