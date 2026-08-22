import os
import streamlit as st
from google import genai
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
# 2. GET GEMINI API KEY
# -------------------------------------------------------------------------

api_key = None

# First try Streamlit Secrets
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = str(st.secrets["GEMINI_API_KEY"]).strip()
except Exception:
    pass

# Then try environment variable
if not api_key:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

# Stop if API key is missing
if not api_key:
    st.error(
        "⚠️ GEMINI_API_KEY is missing. "
        "Please add it to Streamlit Secrets or your environment variables."
    )
    st.stop()

# -------------------------------------------------------------------------
# 3. CREATE GEMINI CLIENT
# -------------------------------------------------------------------------

try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"❌ Failed to initialize Gemini client: {e}")
    st.stop()

# -------------------------------------------------------------------------
# 4. SIDEBAR
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

        "Senior Tech Lead":
            """You are an expert Senior Tech Lead.
            Provide clean, efficient code snippets,
            rigorous code reviews, debugging help,
            and robust software architecture guidance.
            Explain technical concepts clearly.""",

        "Data Science Mentor":
            """You are a Data Science Mentor.
            Help with Python, pandas, NumPy, SQL,
            machine learning, statistics,
            scikit-learn, data cleaning,
            visualization, and ML projects.
            Teach concepts step by step.""",

        "Exam Prep Coach":
            """You are an academic Exam Prep Coach.
            Break down difficult engineering concepts,
            create structured study guides,
            provide high-yield revision notes,
            formulas, examples, and exam-oriented explanations.""",

        "Creative Director":
            """You are a Creative Director.
            Provide typography feedback,
            color palette advice, layout suggestions,
            branding ideas, poster design guidance,
            and creative direction for visual projects."""
    }

    active_system_instruction = system_instructions[persona_choice]

    # ---------------------------------------------------------------------
    # DOCUMENT RAG
    # ---------------------------------------------------------------------

    st.markdown("---")
    st.markdown("### 📄 DOCUMENT RAG")

    uploaded_file = st.file_uploader(
        "Upload PDF or TXT",
        type=["pdf", "txt"],
        label_visibility="collapsed"
    )

    st.caption("PDF / TXT")

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

            st.success("✅ Document loaded successfully!")

        except Exception as e:

            st.error(f"❌ Error reading document: {e}")

    # ---------------------------------------------------------------------
    # NEW CHAT
    # ---------------------------------------------------------------------

    st.markdown("---")

    if st.button("➕ New Chat", use_container_width=True):

        st.session_state.messages = []

        st.rerun()

# -------------------------------------------------------------------------
# 5. MAIN UI
# -------------------------------------------------------------------------

st.markdown(
    """
    <h1 style="
        text-align:center;
        color:#a29bfe;
        font-size:60px;
        margin-bottom:0px;
    ">
        GYAN
    </h1>

    <p style="
        text-align:center;
        color:#888;
        font-size:18px;
    ">
        Your AI-powered learning & coding assistant
    </p>
    """,
    unsafe_allow_html=True
)

# -------------------------------------------------------------------------
# 6. INITIALIZE CHAT HISTORY
# -------------------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------------------------------------------------------
# 7. DISPLAY PREVIOUS MESSAGES
# -------------------------------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

# -------------------------------------------------------------------------
# 8. CHAT INPUT
# -------------------------------------------------------------------------

if prompt := st.chat_input(
    "Ask a coding problem, exam query, or upload a document..."
):

    # Save user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # ---------------------------------------------------------------------
    # BUILD PROMPT
    # ---------------------------------------------------------------------

    conversation = []

    # System instructions
    conversation.append(
        f"""
SYSTEM INSTRUCTIONS:

{active_system_instruction}
"""
    )

    # Document context
    if document_text:

        conversation.append(
            f"""
UPLOADED DOCUMENT:

{document_text}

Use the uploaded document as the primary source
when the user's question is related to it.
If the answer cannot be found in the document,
clearly say so and then answer using your general knowledge.
"""
        )

    # Previous conversation
    for msg in st.session_state.messages:

        conversation.append(
            f"{msg['role'].upper()}: {msg['content']}"
        )

    final_prompt = "\n\n".join(conversation)

    # ---------------------------------------------------------------------
    # GEMINI RESPONSE
    # ---------------------------------------------------------------------

    with st.chat_message("assistant"):

        message_placeholder = st.empty()

        message_placeholder.markdown(" Thinking...")

        try:

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=final_prompt
            )

            response_text = response.text

            if not response_text:
                response_text = "⚠️ Gemini returned an empty response."

        except Exception as e:

            response_text = f"""
❌ **Gemini API Error**

`{str(e)}`
"""

        message_placeholder.markdown(response_text)

    # Save assistant response
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response_text
        }
    )
