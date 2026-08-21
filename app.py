import streamlit as st
from google import genai
from google.genai import types
import ml_model
import pypdf
import time

# ---------------------------------------------------------
# 1. LOAD THE MACHINE LEARNING MODEL
# ---------------------------------------------------------
@st.cache_resource
def load_ml_pipeline():
    return ml_model.train_intent_classifier()

classifier = load_ml_pipeline()

# ---------------------------------------------------------
# 2. STREAMLIT UI & ADVANCED DESIGN SYSTEM CSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="Gyan AI Platform", 
    page_icon="🧠", 
    layout="centered"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Global Theme Base */
    .stApp {
        background-color: #0f1117;
        font-family: 'Inter', sans-serif;
        color: #e2e8f0;
    }
    
    /* Gorgeous Gradient Hero Title */
    .hero-title {
        font-size: 5rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #38bdf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-top: 15vh;
        margin-bottom: 1.5rem;
        letter-spacing: -2px;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #14171f;
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }
    
    [data-testid="stSidebar"] h3 {
        color: #94a3b8 !important;
        font-weight: 600;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }

    /* Chat Input Bar */
    .stChatInputContainer {
        border-top: none !important;
        padding-bottom: 1.5rem;
    }
    
    .stChatInput input {
        background-color: #1a1e29 !important;
        color: #f8fafc !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 14px !important;
        padding: 12px 16px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
        font-family: 'Inter', sans-serif;
    }
    
    .stChatInput input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.3) !important;
    }

    /* Sidebar Buttons (Smooth Hover Micro-Elevation) */
    div.stButton > button {
        background-color: #1a1e29;
        color: #cbd5e1;
        border-radius: 10px;
        width: 100%;
        font-weight: 500;
        font-size: 0.9rem;
        border: 1px solid rgba(255, 255, 255, 0.06);
        text-align: left;
        padding: 10px 14px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    div.stButton > button:hover {
        background-color: #262b3a;
        border-color: #6366f1;
        color: #ffffff;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
        transform: translateY(-1px);
    }

    /* Chat Messages Glassmorphism Cards */
    [data-testid="stChatMessage"] {
        background-color: #161922;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
        margin-bottom: 1rem;
    }

    /* Minimalist Badge Labels */
    .chat-label-user {
        font-size: 0.75rem;
        font-weight: 700;
        color: #818cf8;
        margin-bottom: 4px;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    
    .chat-label-assistant {
        font-size: 0.75rem;
        font-weight: 700;
        color: #34d399;
        margin-bottom: 4px;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "sessions" not in st.session_state:
    st.session_state.sessions = {"New Chat": []}

if "current_session" not in st.session_state:
    st.session_state.current_session = "New Chat"

# ---------------------------------------------------------
# 3. SIDEBAR (Recents, Personas & Document Upload RAG)
# ---------------------------------------------------------
with st.sidebar:
    st.subheader("🎭 AI Persona")
    persona_choice = st.selectbox(
        "Choose Gyan's Style",
        ["Senior Tech Lead", "Strict Professor", "Chill Mentor"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.subheader("📄 Document RAG")
    uploaded_file = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"], label_visibility="collapsed")
    
    doc_text = ""
    if uploaded_file is not None:
        try:
            if uploaded_file.type == "application/pdf":
                reader = pypdf.PdfReader(uploaded_file)
                for page in reader.pages:
                    doc_text += page.extract_text() or ""
            else:
                doc_text = uploaded_file.read().decode("utf-8")
            st.success(f"✓ Loaded: {uploaded_file.name}")
        except Exception as e:
            st.error(f"Error reading file: {e}")

    st.markdown("---")
    st.subheader("📁 Recent Chats")
    
    if st.button("➕ New Chat", key="new_chat_btn"):
        new_name = "New Chat"
        counter = 1
        while new_name in st.session_state.sessions:
            new_name = f"New Chat ({counter})"
            counter += 1
        st.session_state.sessions[new_name] = []
        st.session_state.current_session = new_name
        st.rerun()
        
    st.markdown("---")
    
    for session_name in list(st.session_state.sessions.keys()):
        button_label = f"💬 {session_name}"
        if st.button(button_label, key=f"btn_{session_name}"):
            st.session_state.current_session = session_name
            st.rerun()

# Initialize Gemini Client
client = None
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error("API Key not configured properly on the server.")

# ---------------------------------------------------------
# 4. CHAT INTERFACE & LOGIC
# ---------------------------------------------------------
current_messages = st.session_state.sessions[st.session_state.current_session]

if len(current_messages) == 0:
    st.markdown("<div class='hero-title'>GYAN</div>", unsafe_allow_html=True)

for message in current_messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown("<p class='chat-label-user'>QUESTION</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p class='chat-label-assistant'>ANSWER</p>", unsafe_allow_html=True)
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a coding problem, exam query, or upload a doc..."):
    if not client:
        st.error("Chatbot unavailable due to missing API configuration.")
    else:
        # Auto-title session
        current_title = st.session_state.current_session
        if current_title.startswith("New Chat") and len(current_messages) == 0:
            new_title = prompt.strip()[:25] + ("..." if len(prompt) > 25 else "")
            if new_title in st.session_state.sessions:
                new_title = f"{new_title} (1)"
            st.session_state.sessions[new_title] = st.session_state.sessions.pop(current_title)
            st.session_state.current_session = new_title
            current_messages = st.session_state.sessions[new_title]

        # Step A: Predict ML Intent
        predicted_intent = classifier.predict([prompt])[0]
        
        # Step B: Map Persona & Intent to System Instructions
        persona_instructions = {
            "Senior Tech Lead": "You are a pragmatic, elite software engineering manager focused on clean, optimized production code.",
            "Strict Professor": "You are a rigorous, academic university professor. Emphasize deep conceptual clarity, theory, and precise definitions.",
            "Chill Mentor": "You are an easygoing, friendly, and encouraging peer mentor who breaks complex concepts down simply."
        }
        
        intent_instructions = {
            "CODING": "Provide structured code solutions and clean architecture logic.",
            "DATA_SCIENCE": "Provide practical Python/Pandas workflows and statistical explanations.",
            "EXAM_PREP": "Format your answer like high-yield study notes, key flashcard bullets, and core concepts to memorize.",
            "RESUME_ROASTER": "Critique professionally, give actionable bullet point improvements, and check for ATS alignment.",
            "GENERAL": "Be direct, concise, and helpful."
        }
        
        active_system_instruction = f"{persona_instructions[persona_choice]} {intent_instructions.get(predicted_intent, '')}"

        # Inject Document RAG Context if available
        final_prompt = prompt
        if doc_text:
            final_prompt = f"Reference Document Context:\n{doc_text[:4000]}\n\nUser Question: {prompt}"

        current_messages.append({"role": "user", "content": prompt})

        # Step C: Query Gemini with Auto-Retry Protection & High Accuracy
        try:
            contents = []
            for i, msg in enumerate(current_messages):
                role = "user" if msg["role"] == "user" else "model"
                text_content = msg["content"]
                if i == len(current_messages) - 1 and doc_text and msg["role"] == "user":
                    text_content = final_prompt
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=text_content)]))

            response = None
            for attempt in range(3):
                try:
                    response = client.models.generate_content(
                        model='gemini-3.7-flash',
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=active_system_instruction,
                            temperature=0.7,
                            thinking_config=types.ThinkingConfig(thinking_level="HIGH")
                        )
                    )
                    break
                except Exception as retry_err:
                    if "503" in str(retry_err) and attempt < 2:
                        time.sleep(1.5)
                        continue
                    raise retry_err
            
            reply_text = response.text
            current_messages.append({"role": "assistant", "content": reply_text})
            
        except Exception as e:
            st.error(f"Server is busy handling high traffic (503). Gyan automatically tried to reconnect—please send your message again in a moment!")