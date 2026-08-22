import os
import streamlit as st
from google import genai
from pypdf import PdfReader

# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Gyan AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 2. GET GEMINI API KEY
# ============================================================

api_key = None

# Streamlit Cloud Secrets
try:
    api_key = st.secrets.get("GEMINI_API_KEY")
except Exception:
    pass

# Local environment variable fallback
if not api_key:
    api_key = os.getenv("GEMINI_API_KEY")

# Remove accidental whitespace
if api_key:
    api_key = str(api_key).strip()

# Stop if API key doesn't exist
if not api_key:
    st.error(
        "❌ GEMINI_API_KEY is missing.\n\n"
        "Add your Gemini API key to Streamlit Secrets."
    )
    st.stop()

# ============================================================
# 3. INITIALIZE GEMINI CLIENT
# ============================================================

try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"❌ Failed to initialize Gemini: {e}")
    st.stop()

# ============================================================
# 4. SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🤖 AI PERSONA")

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

    # --------------------------------------------------------
    # PERSONAS
    # --------------------------------------------------------

    system_instructions = {

        "Senior Tech Lead":
            """
            You are GYAN, an expert Senior Tech Lead.

            Help the user with:
            - Python
            - C/C++
            - Java
            - debugging
            - software architecture
            - Git and GitHub
            - APIs
            - clean code
            - project development

            Give practical and production-quality solutions.
            Explain code clearly.
            When providing code, provide complete working examples.
            """,

        "Data Science Mentor":
            """
            You are GYAN, an expert Data Science Mentor.

            Help the user with:
            - Python
            - NumPy
            - Pandas
            - SQL
            - Matplotlib
            - Plotly
            - Machine Learning
            - Statistics
            - Scikit-learn
            - Data Cleaning
            - EDA
            - NLP
            - ML projects

            Teach concepts step by step.
            Give practical examples and clean code.
            """,

        "Exam Prep Coach":
            """
            You are GYAN, an academic Exam Preparation Coach.

            Help students understand difficult concepts.

            Provide:
            - simple explanations
            - formulas
            - derivations
            - examples
            - revision notes
            - important exam points
            - practice questions

            Prioritize exam-oriented and easy-to-understand explanations.
            """,

        "Creative Director":
            """
            You are GYAN, an expert Creative Director.

            Help with:
            - graphic design
            - Photoshop
            - Canva
            - typography
            - color palettes
            - posters
            - branding
            - social media designs
            - T-shirt designs
            - visual hierarchy

            Give practical and professional design advice.
            """
    }

    active_system_instruction = system_instructions[persona_choice]

    # --------------------------------------------------------
    # DOCUMENT UPLOAD
    # --------------------------------------------------------

    st.markdown("---")

    st.markdown("## 📄 DOCUMENT RAG")

    uploaded_file = st.file_uploader(
        "Upload PDF or TXT",
        type=["pdf", "txt"]
    )

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

                document_text = uploaded_file.read().decode(
                    "utf-8",
                    errors="ignore"
                )

            st.success("✅ Document loaded successfully!")

            # Show document information
            st.caption(
                f"Characters extracted: {len(document_text):,}"
            )

        except Exception as e:

            st.error(
                f"❌ Error reading document: {e}"
            )

    # --------------------------------------------------------
    # NEW CHAT
    # --------------------------------------------------------

    st.markdown("---")

    if st.button(
        "➕ New Chat",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.rerun()

# ============================================================
# 5. MAIN HEADER
# ============================================================

st.markdown(
    """
    <h1 style="
        text-align: center;
        color: #a29bfe;
        font-size: 60px;
        margin-bottom: 0px;
    ">
        GYAN
    </h1>

    <p style="
        text-align: center;
        color: #888888;
        font-size: 18px;
        margin-top: 0px;
    ">
        Your AI-powered learning, coding & productivity assistant
    </p>
    """,
    unsafe_allow_html=True
)

# ============================================================
# 6. SESSION STATE
# ============================================================

if "messages" not in st.session_state:

    st.session_state.messages = []

# ============================================================
# 7. DISPLAY CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

# ============================================================
# 8. CHAT INPUT
# ============================================================

prompt = st.chat_input(
    "Ask GYAN anything..."
)

if prompt:

    # --------------------------------------------------------
    # SAVE USER MESSAGE
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    # --------------------------------------------------------
    # DISPLAY USER MESSAGE
    # --------------------------------------------------------

    with st.chat_message("user"):

        st.markdown(prompt)

    # --------------------------------------------------------
    # BUILD CONTEXT
    # --------------------------------------------------------

    conversation_parts = []

    # System instruction
    conversation_parts.append(
        f"""
SYSTEM INSTRUCTIONS:

{active_system_instruction}
"""
    )

    # Uploaded document
    if document_text:

        conversation_parts.append(
            f"""
UPLOADED DOCUMENT:

{document_text}

IMPORTANT:

Use the uploaded document as context when answering
questions related to it.

If the answer is not available in the document,
say that clearly and then use your general knowledge.
"""
        )

    # Conversation history
    for message in st.session_state.messages:

        role = message["role"].upper()
        content = message["content"]

        conversation_parts.append(
            f"{role}:\n{content}"
        )

    final_prompt = "\n\n".join(conversation_parts)

    # --------------------------------------------------------
    # GENERATE RESPONSE
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        placeholder = st.empty()

        placeholder.markdown("🤔 Thinking...")

        try:

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=final_prompt
            )

            response_text = response.text

            if not response_text:

                response_text = (
                    "⚠️ Gemini returned an empty response."
                )

        except Exception as e:

            response_text = (
                "❌ **Gemini API Error**\n\n"
                f"`{str(e)}`"
            )

        placeholder.markdown(response_text)

    # --------------------------------------------------------
    # SAVE ASSISTANT RESPONSE
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response_text
        }
    )
