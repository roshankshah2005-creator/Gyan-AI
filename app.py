import streamlit as st
from groq import Groq
# pypdf, supabase, and streamlit-cookies-controller are ready for your advanced features here

# 1. Page Configuration
st.set_page_config(
    page_title="Gyan AI - Intelligent Companion",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 2. Initialize Session State
if "user" not in st.session_state:
    st.session_state.user = None
if "chats" not in st.session_state:
    st.session_state.chats = []
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

# 3. Authentication Screen
if not st.session_state.user:
    st.title("Welcome to Gyan AI")
    st.markdown("Please enter your details to get started.")
    
    with st.form("auth_form"):
        name_input = st.text_input("Your Name")
        email_input = st.text_input("Email Address")
        submit_auth = st.form_submit_button("Continue to App")
        
        if submit_auth:
            if name_input.strip() and email_input.strip():
                st.session_state.user = {"name": name_input, "email": email_input}
                initial_chat_id = 1
                st.session_state.chats = [{
                    "id": initial_chat_id,
                    "title": "New Conversation",
                    "messages": []
                }]
                st.session_state.current_chat_id = initial_chat_id
                st.rerun()
            else:
                st.error("Please fill in both fields.")
    st.stop()

# Get API key from Streamlit Secrets
groq_api_key = st.secrets.get("GROQ_API_KEY", "")

# 4. Sidebar: Chat History & Controls
with st.sidebar:
    st.title("Gyan AI")
    st.caption(f"Logged in as: **{st.session_state.user['name']}**")
    
    if st.button("➕ New Chat", use_container_width=True):
        new_id = int(st.session_state.chats[0]["id"] + 1) if st.session_state.chats else 1
        st.session_state.chats.insert(0, {
            "id": new_id,
            "title": "New Conversation",
            "messages": []
        })
        st.session_state.current_chat_id = new_id
        st.rerun()

    st.markdown("---")
    st.subheader("Chat History")

    chats_to_delete = []
    for chat in st.session_state.chats:
        col1, col2 = st.sidebar.columns([4, 1])
        with col1:
            is_active = chat["id"] == st.session_state.current_chat_id
            btn_type = "primary" if is_active else "secondary"
            if st.button(chat["title"], key=f"chat_{chat['id']}", type=btn_type, use_container_width=True):
                st.session_state.current_chat_id = chat["id"]
                st.rerun()
        with col2:
            if st.button("❌", key=f"del_{chat['id']}", help="Delete chat"):
                chats_to_delete.append(chat["id"])

    if chats_to_delete:
        st.session_state.chats = [c for c in st.session_state.chats if c["id"] not in chats_to_delete]
        if not st.session_state.chats:
            new_id = 1
            st.session_state.chats = [{"id": new_id, "title": "New Conversation", "messages": []}]
            st.session_state.current_chat_id = new_id
        else:
            st.session_state.current_chat_id = st.session_state.chats[0]["id"]
        st.rerun()

    st.markdown("---")
    if st.button("Log Out", use_container_width=True):
        st.session_state.user = None
        st.session_state.chats = []
        st.rerun()

# 5. Main Chat Interface
current_chat = next((c for c in st.session_state.chats if c["id"] == st.session_state.current_chat_id), None)
if not current_chat:
    current_chat = st.session_state.chats[0]
    st.session_state.current_chat_id = current_chat["id"]

col_title, col_persona = st.columns([2, 2])
with col_title:
    st.header(current_chat["title"])
with col_persona:
    persona = st.selectbox(
        "Persona",
        ["General Companion", "Exam Prep Coach", "Strict Professor", "Senior Tech Lead", "Data Science Mentor", "Creative Director"],
        label_visibility="collapsed"
    )

system_prompts = {
    "General Companion": "You are Gyan, an intelligent multi-persona AI companion.",
    "Exam Prep Coach": "You are an expert Exam Prep Coach, helping students break down derivations, concepts, and study schedules clearly.",
    "Strict Professor": "You are a strict, academic professor who demands rigorous precision and high standards.",
    "Senior Tech Lead": "You are a pragmatic Senior Tech Lead providing clean code architecture and debugging guidance.",
    "Data Science Mentor": "You are a Data Science Mentor explaining machine learning algorithms, Python, and data pipelines.",
    "Creative Director": "You are a Creative Director focusing on design principles, typography, and visual aesthetics."
}

for message in current_chat["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask anything or request a structured guide..."):
    if not groq_api_key:
        st.error("Groq API key is missing! Check your secrets.toml file.")
        st.stop()

    current_chat["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if current_chat["title"] == "New Conversation":
        current_chat["title"] = prompt[:25] + "..." if len(prompt) > 25 else prompt

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        try:
            # Using the official Groq Python SDK matching your requirements.txt
            client = Groq(api_key=groq_api_key)
            
            formatted_messages = [{"role": "system", "content": system_prompts.get(persona, system_prompts["General Companion"])}]
            for m in current_chat["messages"]:
                formatted_messages.append({"role": m["role"], "content": m["content"]})

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=formatted_messages,
                temperature=0.6,
                max_tokens=1500
            )
            
            reply = response.choices[0].message.content
            message_placeholder.markdown(reply)
            current_chat["messages"].append({"role": "assistant", "content": reply})
            
        except Exception as e:
            error_msg = f"AI Error: {str(e)}"
            message_placeholder.markdown(error_msg)
            current_chat["messages"].append({"role": "assistant", "content": error_msg})
