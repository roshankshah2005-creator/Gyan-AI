import os
import uuid
import json
import re
import streamlit as st
from groq import Groq

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

/* Hide file uploaders */
[data-testid="stFileUploader"] {
    display: none !important;
}

[data-testid="stFileUploaderDropzone"] {
    display: none !important;
}

/* Hide Add Document / attachment button */
[data-testid="stChatInput"] [data-testid="stChatInputFileButton"] {
    display: none !important;
}

[data-testid="stChatInput"] button[aria-label*="Attach" i] {
    display: none !important;
}

[data-testid="stChatInput"] button[aria-label*="file" i] {
    display: none !important;
}

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
# 3. GROQ CLIENT
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
    st.error(
        "⚠️ GROQ_API_KEY is missing. "
        "Please configure it in your Streamlit Secrets."
    )
    st.stop()

try:
    client = Groq(api_key=api_key)
except Exception as e:
    st.error(f"Failed to initialize Groq client: {e}")
    st.stop()


# -------------------------------------------------------------------------
# 4. CHAT STORAGE
# -------------------------------------------------------------------------
CHATS_FILE = "chats.json"


def load_chats():
    if os.path.exists(CHATS_FILE):
        try:
            with open(CHATS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data:
                    return data
        except Exception:
            pass

    initial_id = f"chat_{uuid.uuid4().hex[:6]}"
    return [{
        "id": initial_id,
        "title": "New Chat",
        "messages": []
    }]


def save_chats(chats_data):
    try:
        with open(CHATS_FILE, "w", encoding="utf-8") as f:
            json.dump(
                chats_data,
                f,
                ensure_ascii=False,
                indent=2
            )
    except Exception as e:
        print(f"Error saving chats: {e}")


# -------------------------------------------------------------------------
# 5. MATH & TABLE REPAIR CLEANER
# -------------------------------------------------------------------------
def clean_math_syntax(text):
    if not text:
        return ""

    text = str(text)

    # Convert \[ ... \] to $$ ... $$
    text = re.sub(
        r'\\\[\s*(.*?)\s*\\\]',
        lambda m: "\n\n$$\n" + m.group(1).strip() + "\n$$\n\n",
        text,
        flags=re.DOTALL
    )

    # Convert \( ... \) to $ ... $
    text = re.sub(
        r'\\\(\s*(.*?)\s*\\\)',
        lambda m: "$" + m.group(1).strip() + "$",
        text,
        flags=re.DOTALL
    )

    # Fix broken table rows where math equations introduced unescaped line breaks
    def fix_table_row(match):
        row = match.group(0)
        return row.replace('\n', ' ')

    text = re.sub(r'\|.*\|', fix_table_row, text)

    # Ensure display equations are separated from text cleanly
    text = re.sub(r'(?<!\n)\$\$', '\n\n$$', text)
    text = re.sub(r'\$\$(?!\n)', '$$\n\n', text)

    # Remove excessive blank lines
    text = re.sub(r'\n{4,}', '\n\n\n', text)

    return text.strip()


# -------------------------------------------------------------------------
# 6. SESSION STATE & FRESH USER INITIALIZATION
# -------------------------------------------------------------------------
if "chats" not in st.session_state:
    st.session_state.chats = load_chats()

# Ensure a brand new browser session always starts with a fresh empty chat page
if "initialized_session" not in st.session_state:
    st.session_state.initialized_session = True
    new_id = f"chat_{uuid.uuid4().hex[:6]}"
    st.session_state.chats.insert(
        0,
        {
            "id": new_id,
            "title": "New Chat",
            "messages": []
        }
    )
    st.session_state.active_chat_id = new_id
    save_chats(st.session_state.chats)

if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = st.session_state.chats[0]["id"]


def get_active_chat():
    for chat in st.session_state.chats:
        if chat["id"] == st.session_state.active_chat_id:
            return chat
    return st.session_state.chats[0]


# -------------------------------------------------------------------------
# 7. SIDEBAR
# -------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<div class='sidebar-title'>gyan</div>", unsafe_allow_html=True)
    st.markdown(
        """
        <p style='
            text-align:center;
            color:#a0aec0;
            font-size:10px;
            letter-spacing:2px;
            margin-top:-5px;
            margin-bottom:20px;
        '>
            NEURAL KNOWLEDGE ENGINE
        </p>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.markdown("### 💬 CHAT HISTORY")

    if st.button("➕ New Chat", use_container_width=True):
        new_id = f"chat_{uuid.uuid4().hex[:6]}"
        st.session_state.chats.insert(
            0,
            {
                "id": new_id,
                "title": "New Chat",
                "messages": []
            }
        )
        st.session_state.active_chat_id = new_id
        save_chats(st.session_state.chats)
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
                st.session_state.chats = [
                    c for c in st.session_state.chats if c["id"] != chat["id"]
                ]
                if not st.session_state.chats:
                    new_id = f"chat_{uuid.uuid4().hex[:6]}"
                    st.session_state.chats = [{
                        "id": new_id,
                        "title": "New Chat",
                        "messages": []
                    }]
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
# 8. MAIN HEADER
# -------------------------------------------------------------------------
st.markdown("<div class='brand-title'>gyan</div>", unsafe_allow_html=True)
st.markdown(
    """
    <p style='
        text-align:center;
        color:#a0aec0;
        font-size:13px;
        letter-spacing:1px;
        margin-bottom:25px;
    '>
        Your Ultimate Semester Exam & Technical Companion
    </p>
    """,
    unsafe_allow_html=True
)


# -------------------------------------------------------------------------
# 9. ACTIVE CHAT & HISTORY
# -------------------------------------------------------------------------
active_chat = get_active_chat()

for message in active_chat["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(clean_math_syntax(message["content"]))


# -------------------------------------------------------------------------
# 10. CHAT INPUT
# -------------------------------------------------------------------------
if prompt := st.chat_input("Ask an exam derivation, technical problem, or chat with your coach..."):
    active_chat["messages"].append({
        "role": "user",
        "content": prompt
    })

    if active_chat["title"] == "New Chat":
        active_chat["title"] = prompt[:25] + ("..." if len(prompt) > 25 else "")

    save_chats(st.session_state.chats)

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

        save_chats(st.session_state.chats)
        st.rerun()
