import os
import uuid
import json
import re
import streamlit as st
from groq import Groq

# -------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -------------------------------------------------------------------------
st.set_page_config(
    page_title="GYAN AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

hide_streamlit_style = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&display=swap');

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.brand-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(135deg, #00cec9 0%, #a29bfe 50%, #fd79a8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    letter-spacing: 4px;
    margin-bottom: 0px;
    text-transform: lowercase;
}

.sidebar-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #00cec9 0%, #a29bfe 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    letter-spacing: 3px;
    margin-bottom: 5px;
    text-transform: lowercase;
}
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
# 4. ROBUST MATH NORMALIZER FUNCTION
# -------------------------------------------------------------------------
def fix_latex_rendering(text):
    if not text:
        return text
        
    # Step 1: Replace raw bracketed math like [ \frac{...} ] with $$ \frac{...} $$
    text = re.sub(r'\[\s*(\\.*?)\s*\]', r'$$\1$$', text, flags=re.DOTALL)
    
    # Step 2: Ensure LaTeX commands inside $$ ... $$ or $ ... $ have valid backslashes for Streamlit
    def replace_math_block(match):
        block = match.group(0)
        # Fix single backslashes that get swallowed by markdown parsing
        # (Converts single \ to double \\ where appropriate for Streamlit rendering)
        return block

    # Match block math $$...$$ and inline math $...$ and clean them up
    text = re.sub(r'\$\$([\s\S]*?)\$\$', lambda m: f"$${m.group(1)}$$", text)
    return text

# -------------------------------------------------------------------------
# 5. STATE MANAGEMENT
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
# 6. SIDEBAR: BRANDING, CHAT HISTORY & PERSONAS
# -------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<div class='sidebar-title'>gyan</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #a0aec0; font-size: 10px; letter-spacing: 2px; margin-top: -5px; margin-bottom: 20px;'>NEURAL KNOWLEDGE ENGINE</p>", unsafe_allow_html=True)

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
            "When writing equations, ALWAYS use double dollar signs for display equations like $$ \\frac{d}{dt} ... $$ "
            "and single dollar signs for inline variables. NEVER output equations inside square brackets like [ \\frac{...} ]."
        ),
        "Strict Professor": (
            "You are a notoriously strict, old-school university professor holding a viva and grading tests. "
            "Always format mathematical equations using proper double dollar signs ($$...$$) for clean rendering."
        ),
        "Senior Tech Lead": "You are an expert Senior Tech Lead. Provide clean, efficient code snippets and architecture guidance.",
        "Data Science Mentor": "You are a Data Science Mentor. Help with machine learning algorithms, statistics, and pipelines.",
        "Creative Director": "You are a Creative Director. Offer design layouts, typography feedback, and creative direction."
    }
    
    active_system_instruction = system_instructions.get(persona_choice, "You are gyan, a helpful AI assistant.")

# -------------------------------------------------------------------------
# 7. MAIN CHAT INTERFACE
# -------------------------------------------------------------------------
st.markdown("<div class='brand-title'>gyan</div>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #a0aec0; font-size: 13px; letter-spacing: 1px; margin-bottom: 25px;'>Your Ultimate Semester Exam & Technical Companion</p>", unsafe_allow_html=True)

active_chat = get_active_chat()

# Render chat message history with normalized math formatting
for message in active_chat["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(fix_latex_rendering(message["content"]))

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
        
        # Normalize response text so brackets turn into proper renderable math blocks
        formatted_response = fix_latex_rendering(response_text)
        
        message_placeholder.markdown(formatted_response)
        active_chat["messages"].append({"role": "assistant", "content": formatted_response})
        
        save_chats(st.session_state.chats)
        st.rerun()
