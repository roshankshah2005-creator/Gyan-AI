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

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    visibility: hidden;
}

/* ---------------------------------------------------------
   BRAND TITLE
--------------------------------------------------------- */
.brand-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(
        135deg,
        #00cec9 0%,
        #a29bfe 50%,
        #fd79a8 100%
    );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    letter-spacing: 4px;
    margin-bottom: 0px;
    text-transform: lowercase;
}

/* ---------------------------------------------------------
   SIDEBAR TITLE
--------------------------------------------------------- */
.sidebar-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(
        135deg,
        #00cec9 0%,
        #a29bfe 100%
    );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    letter-spacing: 3px;
    margin-bottom: 5px;
}

/* ---------------------------------------------------------
   HIDE FILE / DOCUMENT UPLOADERS
--------------------------------------------------------- */
[data-testid="stFileUploader"] {
    display: none !important;
}

[data-testid="stFileUploaderDropzone"] {
    display: none !important;
}

/* Hide attachment/document button if present */
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

/* ---------------------------------------------------------
   GENERAL LAYOUT
--------------------------------------------------------- */
.block-container {
    padding-top: 2rem;
    padding-bottom: 5rem;
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
# 3. PERSISTENT CHAT STORAGE FUNCTIONS
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

    return [
        {
            "id": initial_id,
            "title": "New Chat",
            "messages": []
        }
    ]


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
# 4. MATH CLEANER
# -------------------------------------------------------------------------
def clean_math_syntax(text):
    """
    Converts common raw LaTeX formats into
    Streamlit-compatible Markdown/LaTeX.

    Examples:

    [ \\frac{a}{b} ]
        ->
    $$\\frac{a}{b}$$

    \\[ x^2 + y^2 \\]
        ->
    $$x^2 + y^2$$

    \\( x^2 \\)
        ->
    $x^2$

    The function intentionally does NOT modify
    normal square brackets used in ordinary text.
    """

    if not text:
        return text

    cleaned = str(text)

    # ---------------------------------------------------------
    # 1. Convert \[ ... \] into $$ ... $$
    # ---------------------------------------------------------
    cleaned = re.sub(
        r'\\\[\s*(.*?)\s*\\\]',
        r'$$\1$$',
        cleaned,
        flags=re.DOTALL
    )

    # ---------------------------------------------------------
    # 2. Convert \( ... \) into $ ... $
    # ---------------------------------------------------------
    cleaned = re.sub(
        r'\\\(\s*(.*?)\s*\\\)',
        r'$\1$',
        cleaned,
        flags=re.DOTALL
    )

    # ---------------------------------------------------------
    # 3. Convert [ \LaTeX ] into $$ \LaTeX $$
    #
    # This catches formulas such as:
    #
    # [ \frac{d}{dt}\int_{V_m}\rho\,dV = 0 ]
    # ---------------------------------------------------------
    cleaned = re.sub(
        r'\[\s*(\\(?:frac|int|sum|prod|sqrt|partial|nabla|lim|begin|'
        r'mathbf|mathrm|text|alpha|beta|gamma|rho|sigma|Delta|Omega|'
        r'cdot|times|rightarrow|Rightarrow|approx|neq|leq|geq|in|'
        r'notin|infty|dot|hat|bar|vec)[^\]]*?)\s*\]',
        r'$$\1$$',
        cleaned,
        flags=re.DOTALL
    )

    # ---------------------------------------------------------
    # 4. Catch remaining [ \something ] equations
    # ---------------------------------------------------------
    cleaned = re.sub(
        r'\[\s*(\\[^]]+?)\s*\]',
        r'$$\1$$',
        cleaned,
        flags=re.DOTALL
    )

    # ---------------------------------------------------------
    # 5. Prevent accidental $$$ / $$$$
    # ---------------------------------------------------------
    cleaned = re.sub(
        r'\${3,}',
        '$$',
        cleaned
    )

    return cleaned


# -------------------------------------------------------------------------
# 5. STATE MANAGEMENT
# -------------------------------------------------------------------------
if "chats" not in st.session_state:
    st.session_state.chats = load_chats()

if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = (
        st.session_state.chats[0]["id"]
    )


def get_active_chat():

    for chat in st.session_state.chats:

        if chat["id"] == st.session_state.active_chat_id:
            return chat

    return st.session_state.chats[0]


# -------------------------------------------------------------------------
# 6. SIDEBAR
# -------------------------------------------------------------------------
with st.sidebar:

    st.markdown(
        "<div class='sidebar-title'>gyan</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <p style='
            text-align: center;
            color: #a0aec0;
            font-size: 10px;
            letter-spacing: 2px;
            margin-top: -5px;
            margin-bottom: 20px;
        '>
            NEURAL KNOWLEDGE ENGINE
        </p>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.markdown("### 💬 CHAT HISTORY")

    # ---------------------------------------------------------
    # NEW CHAT
    # ---------------------------------------------------------
    if st.button(
        "➕ New Chat",
        use_container_width=True
    ):

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

    # ---------------------------------------------------------
    # CHAT HISTORY
    # ---------------------------------------------------------
    for chat in list(st.session_state.chats):

        is_active = (
            chat["id"] == st.session_state.active_chat_id
        )

        label = (
            f"📌 {chat['title']}"
            if is_active
            else chat["title"]
        )

        col1, col2 = st.columns([4, 1])

        with col1:

            if st.button(
                label,
                key=f"btn_{chat['id']}",
                use_container_width=True
            ):

                st.session_state.active_chat_id = chat["id"]

                st.rerun()

        with col2:

            if st.button(
                "🗑️",
                key=f"del_{chat['id']}",
                use_container_width=True,
                help="Delete chat"
            ):

                st.session_state.chats = [
                    c
                    for c in st.session_state.chats
                    if c["id"] != chat["id"]
                ]

                if not st.session_state.chats:

                    new_id = f"chat_{uuid.uuid4().hex[:6]}"

                    st.session_state.chats = [
                        {
                            "id": new_id,
                            "title": "New Chat",
                            "messages": []
                        }
                    ]

                if (
                    st.session_state.active_chat_id
                    == chat["id"]
                ):

                    st.session_state.active_chat_id = (
                        st.session_state.chats[0]["id"]
                    )

                save_chats(st.session_state.chats)

                st.rerun()

    st.markdown("---")

    # ---------------------------------------------------------
    # AI PERSONA
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # PERSONA INSTRUCTIONS
    # ---------------------------------------------------------
    system_instructions = {

        "Exam Prep Coach": (

            "You are an elite university Exam Prep Coach "
            "specializing in rigorous engineering and technical "
            "subjects. "

            "When given a topic, formula, or syllabus item, "
            "break it down into clean step-by-step derivations, "
            "key conceptual definitions, and standard numerical "
            "problem-solving workflows. "

            "MATHEMATICAL FORMATTING RULES: "

            "Always use standard Markdown LaTeX. "

            "Use $...$ for inline mathematics and "
            "$$...$$ for display mathematics. "

            "NEVER use square brackets [ ... ] as mathematical "
            "delimiters. "

            "NEVER write mathematical equations in the form "
            "[ \\formula ]. "

            "NEVER output raw LaTeX inside square brackets. "

            "For example, write "
            "$$\\frac{d}{dt}\\int_{V_m}\\rho\\,dV = 0$$ "
            "instead of "
            "[ \\frac{d}{dt}\\int_{V_m}\\rho\\,dV = 0 ]. "

            "Keep mathematical notation clean and readable."
        ),

        "Strict Professor": (

            "You are a notoriously strict, old-school university "
            "professor holding a viva and grading tests. "

            "Do not accept vague answers or sugarcoat feedback. "

            "When the student answers a viva question or submits "
            "test work, critique their logic brutally, point out "
            "flaws, and assign a strict numeric score out of 10 "
            "with detailed remarks. "

            "Always format mathematical equations using proper "
            "LaTeX delimiters: $...$ for inline mathematics and "
            "$$...$$ for display mathematics. "

            "Never use [ ... ] as mathematical delimiters."
        ),

        "Senior Tech Lead": (

            "You are an expert Senior Tech Lead. "

            "Provide clean, efficient code snippets, rigorous "
            "code reviews, and robust software architecture "
            "guidance."
        ),

        "Data Science Mentor": (

            "You are a Data Science Mentor. "

            "Help with machine learning algorithms, pandas "
            "dataframes, scikit-learn pipelines, statistics, "
            "and data cleaning workflows."
        ),

        "Creative Director": (

            "You are a Creative Director. "

            "Offer sharp typography feedback, color palette "
            "advice, design layouts, and creative direction "
            "for visual projects."
        )
    }

    active_system_instruction = system_instructions.get(
        persona_choice,
        "You are gyan, a helpful AI assistant."
    )


# -------------------------------------------------------------------------
# 7. MAIN CHAT INTERFACE
# -------------------------------------------------------------------------
st.markdown(
    "<div class='brand-title'>gyan</div>",
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='
        text-align: center;
        color: #a0aec0;
        font-size: 13px;
        letter-spacing: 1px;
        margin-bottom: 25px;
    '>
        Your Ultimate Semester Exam & Technical Companion
    </p>
    """,
    unsafe_allow_html=True
)

active_chat = get_active_chat()


# -------------------------------------------------------------------------
# 8. RENDER CHAT HISTORY
# -------------------------------------------------------------------------
for message in active_chat["messages"]:

    with st.chat_message(message["role"]):

        st.markdown(
            clean_math_syntax(message["content"])
        )


# -------------------------------------------------------------------------
# 9. CHAT INPUT
# -------------------------------------------------------------------------
if prompt := st.chat_input(
    "Ask an exam derivation, technical problem, or chat with your coach..."
):

    # ---------------------------------------------------------
    # SAVE USER MESSAGE
    # ---------------------------------------------------------
    active_chat["messages"].append(
        {
            "role": "user",
            "content": prompt
        }
    )

    # ---------------------------------------------------------
    # GENERATE CHAT TITLE
    # ---------------------------------------------------------
    if active_chat["title"] == "New Chat":

        active_chat["title"] = (
            prompt[:25]
            + ("..." if len(prompt) > 25 else "")
        )

    save_chats(st.session_state.chats)

    # ---------------------------------------------------------
    # DISPLAY USER MESSAGE
    # ---------------------------------------------------------
    with st.chat_message("user"):

        st.markdown(prompt)

    # ---------------------------------------------------------
    # PREPARE GROQ MESSAGES
    # ---------------------------------------------------------
    messages_payload = [
        {
            "role": "system",
            "content": active_system_instruction
        }
    ]

    recent_messages = active_chat["messages"][-10:]

    for msg in recent_messages:

        messages_payload.append(
            {
                "role": msg["role"],
                "content": msg["content"]
            }
        )

    # ---------------------------------------------------------
    # GENERATE AI RESPONSE
    # ---------------------------------------------------------
    with st.chat_message("assistant"):

        message_placeholder = st.empty()

        message_placeholder.markdown("Thinking...")

        response_text = None

        try:

            chat_completion = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=messages_payload,
                temperature=0.7
            )

            response_text = (
                chat_completion
                .choices[0]
                .message
                .content
            )

        except Exception as e:

            response_text = (
                f"API Error Encountered: {e}"
            )

        # -----------------------------------------------------
        # CLEAN MATH BEFORE DISPLAY
        # -----------------------------------------------------
        formatted_response = clean_math_syntax(
            response_text
        )

        message_placeholder.markdown(
            formatted_response
        )

        # -----------------------------------------------------
        # SAVE RAW RESPONSE
        # -----------------------------------------------------
        active_chat["messages"].append(
            {
                "role": "assistant",
                "content": response_text
            }
        )

        save_chats(
            st.session_state.chats
        )

        st.rerun()
