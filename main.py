import os
import uuid
import re
import streamlit as st
from groq import Groq
from supabase import create_client, Client

# -------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -------------------------------------------------------------------------
st.set_page_config(
    page_title="GYAN AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------------------
# 2. STYLING
# -------------------------------------------------------------------------
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
}

/* Hide file uploaders & attachments */
[data-testid="stFileUploader"], [data-testid="stFileUploaderDropzone"],
[data-testid="stChatInput"] [data-testid="stChatInputFileButton"],
[data-testid="stChatInput"] button[aria-label*="Attach" i],
[data-testid="stChatInput"] button[aria-label*="file" i],
[data-testid="stChatInput"] button[aria-label*="document" i] {
    display: none !important;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 5rem;
}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


# -------------------------------------------------------------------------
# 3. API & SUPABASE CLIENT INITIALIZATION
# -------------------------------------------------------------------------
def get_secret(key):
    try:
        if key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return os.getenv(key, "").strip()

groq_api_key = get_secret("GROQ_API_KEY")
supabase_url = get_secret("SUPABASE_URL")
supabase_key = get_secret("SUPABASE_KEY")

if not groq_api_key:
    st.error("⚠️ GROQ_API_KEY is missing in secrets.")
    st.stop()

if not supabase_url or not supabase_key:
    st.error("⚠️ SUPABASE_URL or SUPABASE_KEY is missing in secrets.")
    st.stop()

try:
    client = Groq(api_key=groq_api_key)
    supabase: Client = create_client(supabase_url, supabase_key)
except Exception as e:
    st.error(f"Failed to initialize clients: {e}")
    st.stop()


# -------------------------------------------------------------------------
# 4. CAPTURE USER IP ADDRESS
# -------------------------------------------------------------------------
def get_user_ip():
    try:
        ip = st.context.ip_address
        return ip if ip else "Localhost / Unknown"
    except Exception:
        return "Unknown"


# -------------------------------------------------------------------------
# 5. SESSION STATE & EARLY URL RECOVERY (FIXES REFRESH WIPE)
# -------------------------------------------------------------------------
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "display_name" not in st.session_state:
    st.session_state.display_name = None

# Grab parameters instantly from URL query string on startup/refresh
qp_user_id = st.query_params.get("user_id")
qp_name = st.query_params.get("name")

if qp_user_id and qp_name:
    st.session_state.user_id = qp_user_id
    st.session_state.display_name = qp_name


# -------------------------------------------------------------------------
# 6. DATABASE HELPER FUNCTIONS (SUPABASE)
# -------------------------------------------------------------------------
def load_chats_from_db(user_id):
    try:
        res = supabase.table("chats").select("*").eq("user_id", user_id).execute()
        if res.data:
            chats = []
            for row in res.data:
                chats.append({
                    "id": row["id"],
                    "title": row["title"],
                    "messages": row["messages"] or []
                })
            return chats
    except Exception:
        pass

    initial_id = f"chat_{uuid.uuid4().hex[:6]}"
    default_chat = [{
        "id": initial_id,
        "title": "New Chat",
        "messages": []
    }]
    save_chats_to_db(user_id, default_chat)
    return default_chat

def save_chats_to_db(user_id, chats_data):
    try:
        user_ip = get_user_ip()
        for chat in chats_data:
            supabase.table("chats").upsert({
                "id": chat["id"],
                "user_id": user_id,
                "title": chat["title"],
                "messages": chat["messages"],
                "ip_address": user_ip
            }).execute()
    except Exception as e:
        print(f"Error saving chats: {e}")

def delete_chat_from_db(chat_id):
    try:
        supabase.table("chats").delete().eq("id", chat_id).execute()
    except Exception as e:
        print(f"Error deleting chat: {e}")


# -------------------------------------------------------------------------
# 7. "WHAT SHOULD I CALL YOU?" WELCOME SCREEN
# -------------------------------------------------------------------------
if not st.session_state.display_name:
    st.markdown("<div class='brand-title' style='margin-top: 50px;'>gyan</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #00cec9; margin-top: 30px;'>Welcome! What should I call you?</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #a0aec0; margin-bottom: 30px;'>Please enter your preferred name or nickname to begin chatting.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        preferred_name = st.text_input("Your Name / Nickname", key="name_input")
        if st.button("Continue to Gyan", use_container_width=True):
            clean_name = preferred_name.strip()
            if clean_name:
                st.session_state.display_name = clean_name.capitalize()
                st.session_state.user_id = uuid.uuid4().hex[:8]
                
                # Save identity in URL query params
                st.query_params["user_id"] = st.session_state.user_id
                st.query_params["name"] = st.session_state.display_name
                st.rerun()
            else:
                st.warning("Please enter a valid name.")
    st.stop()


# -------------------------------------------------------------------------
# 8. MATH & TABLE REPAIR CLEANER
# -------------------------------------------------------------------------
def clean_math_syntax(text):
    if not text:
        return ""
    text = str(text)
    text = re.sub(r'\\\[\s*(.*?)\s*\\\]', lambda m: "\n\n$$\n" + m.group(1).strip() + "\n$$\n\n", text, flags=re.DOTALL)
    text = re.sub(r'\\\(\s*(.*?)\s*\\\)', lambda m: "$" + m.group(1).strip() + "$", text, flags=re.DOTALL)
    text = re.sub(r'\|.*\|', lambda m: m.group(0).replace('\n', ' '), text)
    text = re.sub(r'(?<!\n)\$\$', '\n\n$$', text)
    text = re.sub(r'\$\$(?!\n)', '$$\n\n', text)
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    return text.strip()


# -------------------------------------------------------------------------
# 9. SESSION STATE INITIALIZATION FOR CHATS
# -------------------------------------------------------------------------
if "chats" not in st.session_state:
    st.session_state.chats = load_chats_from_db(st.session_state.user_id)

if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = st.session_state.chats[0]["id"]

def get_active_chat():
    for chat in st.session_state.chats:
        if chat["id"] == st.session_state.active_chat_id:
            return chat
    return st.session_state.chats[0]


# -------------------------------------------------------------------------
# 10. SIDEBAR
# -------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<div class='sidebar-title'>gyan</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <p style='
            text-align:center;
            color:#00cec9;
            font-size:12px;
            font-weight:600;
            letter-spacing:1px;
            margin-top:-5px;
            margin-bottom:15px;
        '>
            CHATTING AS: {st.session_state.display_name.upper()}
        </p>
        """,
        unsafe_allow_html=True
    )

    if st.button("🔄 Switch Name", use_container_width=True):
        st.session_state.display_name = None
        st.session_state.user_id = None
        st.query_params.clear()
        if "chats" in st.session_state:
            del st.session_state.chats
        if "active_chat_id" in st.session_state:
            del st.session_state.active_chat_id
        st.rerun()

    st.markdown("---")
    st.markdown("### 💬 CHAT HISTORY")

    if st.button("➕ New Chat", use_container_width=True):
        new_id = f"chat_{uuid.uuid4().hex[:6]}"
        st.session_state.chats.insert(0, {
            "id": new_id,
            "title": "New Chat",
            "messages": []
        })
        st.session_state.active_chat_id = new_id
        save_chats_to_db(st.session_state.user_id, st.session_state.chats)
        st.rerun()

    st.markdown("---")

    for chat in list(st.session_state.chats):
        is_active = (chat["id"] == st.session_state.active_chat_id)
        label = f"📌 {chat['title']}" if is_active else chat["title"]

        col1, col2 = st.columns([4, 1])

        with col1:
            if st.button(label, key=f"btn_{chat['id']}", use_container_width=True):
                st.session_state.active_chat_id = chat["id"]
                st.rerun()

        with col2:
            if st.button("🗑️", key=f"del_{chat['id']}", use_container_width=True, help="Delete chat"):
                delete_chat_from_db(chat["id"])
                st.session_state.chats = [c for c in st.session_state.chats if c["id"] != chat["id"]]
                if not st.session_state.chats:
                    new_id = f"chat_{uuid.uuid4().hex[:6]}"
                    st.session_state.chats = [{
                        "id": new_id,
                        "title": "New Chat",
                        "messages": []
                    }]
                if st.session_state.active_chat_id == chat["id"]:
                    st.session_state.active_chat_id = st.session_state.chats[0]["id"]
                save_chats_to_db(st.session_state.user_id, st.session_state.chats)
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
            "Creative Director",
            "Research (Quick Mode)",
            "Research (Deep Mode)"
        ],
        label_visibility="collapsed"
    )

    system_instructions = {
        "Exam Prep Coach": (
            "You are an elite university Exam Prep Coach specializing in rigorous engineering and technical subjects.\n\n"
            "Explain concepts clearly and step-by-step. Provide definitions, derivations, formulas, examples, and exam-focused explanations.\n\n"
            "MATHEMATICAL & TABLE FORMATTING RULES:\n"
            "1. Use $...$ for inline mathematics.\n"
            "2. Use $$...$$ for standalone display equations.\n"
            "3. NEVER put complex LaTeX equations or line breaks inside Markdown tables (pipes `|`), because it breaks the table structure. Instead, list them using bullet points or numbered lists.\n"
            "4. Every display equation must be on its own separate line with blank lines before and after."
        ),
        "Strict Professor": (
            "You are a notoriously strict, old-school university professor holding a viva and grading tests.\n\n"
            "Critique logic, point out flaws, and assign a strict numeric score out of 10 when grading answers.\n\n"
            "For mathematics, use $...$ for inline equations and $$...$$ for display equations. NEVER put equations inside Markdown tables."
        ),
        "Senior Tech Lead": (
            "You are an expert Senior Tech Lead. Provide clean, efficient code snippets, rigorous code reviews, debugging help, and robust software architecture guidance."
        ),
        "Data Science Mentor": (
            "You are a Data Science Mentor. Help with machine learning algorithms, pandas, NumPy, scikit-learn, statistics, data cleaning, visualization, and practical data science projects."
        ),
        "Creative Director": (
            "You are a Creative Director. Offer sharp typography feedback, color palette advice, design layouts, branding guidance, and creative direction for visual projects."
        ),
        "Research (Quick Mode)": (
            "You are an agile Research Assistant operating in Quick Mode. "
            "Provide rapid, concise summaries of academic papers, core methodologies, high-level findings, and abstract-level overviews. "
            "Keep answers punchy, structured, and easy to skim without overly dense proofs unless requested."
        ),
        "Research (Deep Mode)": (
            "You are an Advanced Senior Researcher operating in Deep Mode. "
            "Provide exhaustive academic analyses, rigorous theoretical breakdowns, critical methodology evaluations, mathematical formulations, and structured literature synthesis. "
            "Use proper LaTeX formatting ($...$ and $$...$$) and avoid placing complex equations inside tables."
        )
    }

    active_system_instruction = system_instructions.get(
        persona_choice,
        "You are gyan, a helpful AI assistant."
    )


# -------------------------------------------------------------------------
# 11. MAIN HEADER & CHAT INTERFACE
# -------------------------------------------------------------------------
st.markdown("<div class='brand-title'>gyan</div>", unsafe_allow_html=True)

active_chat = get_active_chat()

if not active_chat["messages"]:
    st.markdown(
        f"""
        <p style='
            text-align:center;
            color:#a0aec0;
            font-size:13px;
            letter-spacing:1px;
            margin-top: 5px;
            margin-bottom: 8px;
        '>
            Your Intelligent Multi-Persona AI Companion
        </p>
        <p style='
            text-align:center;
            color:#00cec9;
            font-size:1.8rem;
            font-weight:700;
            margin-bottom:25px;
        '>
            Hello, {st.session_state.display_name}!
        </p>
        """,
        unsafe_allow_html=True
    )

for message in active_chat["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(clean_math_syntax(message["content"]))


# -------------------------------------------------------------------------
# 12. CHAT INPUT
# -------------------------------------------------------------------------
if prompt := st.chat_input("Ask an exam derivation, technical problem, or chat with your coach..."):
    active_chat["messages"].append({
        "role": "user",
        "content": prompt
    })

    if active_chat["title"] == "New Chat":
        active_chat["title"] = prompt[:25] + ("..." if len(prompt) > 25 else "")

    save_chats_to_db(st.session_state.user_id, st.session_state.chats)

    with st.chat_message("user"):
        st.markdown(prompt)

    messages_payload = [
        {
            "role": "system",
            "content": active_system_instruction
        }
    ]

    recent_messages = active_chat["messages"][-10:]
    for msg in recent_messages:
        messages_payload.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")

        response_text = None
        try:
            chat_completion = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=messages_payload,
                temperature=0.4
            )
            response_text = chat_completion.choices[0].message.content
        except Exception as e:
            response_text = f"API Error Encountered: {e}"

        formatted_response = clean_math_syntax(response_text)
        message_placeholder.markdown(formatted_response)

        active_chat["messages"].append({
            "role": "assistant",
            "content": response_text
        })

        save_chats_to_db(st.session_state.user_id, st.session_state.chats)
        st.rerun()
