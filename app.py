import os
import uuid
import json
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
# 3. PERSISTENT CHAT STORAGE FUNCTIONS
# -------------------------------------------------------------------------
CHATS_FILE = "chats.json"

def load_chats():
    """Load saved chats from local JSON file if it exists."""
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
    """Save current chats list to local JSON file."""
    try:
        with open(CHATS_FILE, "w") as f:
            json.dump(chats_data, f)
    except Exception as e:
        print(f"Error saving chats: {e}")

# -------------------------------------------------------------------------
# 4. CHAT SESSIONS STATE MANAGEMENT
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
# 5. SIDEBAR CONFIGURATION (History & Personas Only)
# -------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 💬 CHAT HISTORY")
    
    if st.button("➕ New Chat", use_container_width=True):
        new_id = f"chat_{uuid.uuid4().hex[:6]}"
        st.session_state.chats.insert(0, {"id": new_id, "title": "New Chat", "messages": []})
        st.session_state.active_chat_id = new_id
        save_chats(st.session_state.chats)
        st.rerun()

    st.markdown("---")
    
    # Display saved chats list with select and delete buttons side-by-side
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
            "Strict Professor",
            "Senior Tech Lead", 
            "Data Science Mentor", 
            "Exam Prep Coach", 
            "Creative Director"
        ],
        label_visibility="collapsed"
    )
    
    system_instructions = {
        "Strict Professor": (
            "You are a notoriously strict, old-school university professor holding a viva and grading tests. "
            "Do not accept vague answers or sugarcoat feedback. When the student answers a viva question or submits test work, "
            "critique their logic brutally, point out flaws, and assign a strict numeric score out of 10 with detailed remarks. "
            "Never give a 10/10 unless the answer is flawless."
        ),
        "Senior Tech Lead": "You are an expert Senior Tech Lead. Provide clean, efficient code snippets, rigorous code reviews, and robust software architecture guidance.",
        "Data Science Mentor": "You are a Data Science Mentor. Help with machine learning algorithms, pandas dataframes, scikit-learn pipelines, statistics, and data cleaning workflows.",
        "Exam Prep Coach": "You are an academic Exam Prep Coach. Break down tough engineering concepts, create structured study guides, summarize chapters, and give high-yield revision notes.",
        "Creative Director": "You are a Creative Director. Offer sharp typography feedback, color palette advice, design layouts, and creative direction for visual projects."
    }
    
    active_system_instruction = system_instructions.get(persona_choice, "You are Gyan, a helpful AI assistant.")

# -------------------------------------------------------------------------
# 6. CHAT INTERFACE & RESOURCE ATTACHMENT
# -------------------------------------------------------------------------
st.markdown("<h1 style='text-align: center; color: #a29bfe;'>GYAN</h1>", unsafe_allow_html=True)

active_chat = get_active_chat()

# Render existing messages for the active chat
for message in active_chat["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Taskbar attachment option right above the chat input
with st.expander("➕ Attach Photo, PDF, or Text Resource"):
    uploaded_resource = st.file_uploader(
        "Upload resource file", 
        type=["png", "jpg", "jpeg", "pdf", "txt"], 
        label_visibility="collapsed"
    )

# Process uploaded file content if present
resource_context = ""
if uploaded_resource is not None:
    try:
        file_extension = uploaded_resource.name.split(".")[-1].lower()
        if file_extension in ["png", "jpg", "jpeg"]:
            resource_context = f"[Attached Image: {uploaded_resource.name}]"
            st.info(f"📷 Attached image: {uploaded_resource.name}")
        elif file_extension == "pdf":
            reader = PdfReader(uploaded_resource)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    resource_context += text + "\n"
            st.success(f"📄 Loaded PDF: {uploaded_resource.name}")
        elif file_extension == "txt":
            resource_context = uploaded_resource.read().decode("utf-8")
            st.success(f"📝 Loaded Text File: {uploaded_resource.name}")
    except Exception as e:
        st.error(f"Error processing resource: {e}")

if prompt := st.chat_input("Ask a coding problem, exam query, or reference an uploaded file..."):
    full_user_input = prompt
    if resource_context:
        full_user_input = f"{prompt}\n\n[Resource Content / Context Provided]:\n{resource_context}"

    # Append user prompt to current chat
    active_chat["messages"].append({"role": "user", "content": full_user_input})
    
    # Auto-update title if it's the first message
    if active_chat["title"] == "New Chat":
        active_chat["title"] = prompt[:25] + ("..." if len(prompt) > 25 else "")

    save_chats(st.session_state.chats)

    with st.chat_message("user"):
        st.markdown(full_user_input)

    # Build messages payload for Groq
    messages_payload = [{"role": "system", "content": active_system_instruction}]
    
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
        
        save_chats(st.session_state.chats)
        st.rerun()
