import streamlit as st
from groq import Groq
from streamlit_cookies_controller import CookieController

# 1. Page Configuration
st.set_page_config(
    page_title="Gyan AI - Intelligent Companion",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Initialize Cookie Controller for persistent sessions
controller = CookieController()

# 2. Initialize Session State & Check Cookies
if "user" not in st.session_state:
    # Attempt to restore user session from browser cookies on refresh
    saved_user = controller.get("gyan_logged_in_user")
    st.session_state.user = saved_user if saved_user else None

if "chats" not in st.session_state:
    st.session_state.chats = []
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

# 3. Authentication Screen (Skipped automatically if cookie exists)
if not st.session_state.user:
    st.title("Welcome to Gyan AI")
    st.markdown("Please enter your details to get started.")
    
    with st.form("auth_form"):
        name_input = st.text_input("Your Name")
        email_input = st.text_input("Email Address")
        submit_auth = st.form_submit_button("Continue to App")
        
        if submit_auth:
            if name_input.strip() and email_input.strip():
                user_data = {"name": name_input, "email": email_input}
                st.session_state.user = user_data
                
                # Save session in browser cookie (persists on page refresh)
                controller.set("gyan_logged_in_user", user_data, max_age=30*24*60*60)
                
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
        # Clear cookie and session state on logout
        controller.remove("gyan_logged_in_user")
        st.session_state.user = None
        st.session_state.chats = []
        st.rerun()

# 5. Main Chat Interface
current_chat = next((c for c in st.session_state.chats if c["id"] == st.session_state.current_chat_id), None)
if not current_chat:
    if st.session_state.chats:
        current_chat = st.session_state.chats[0]
        st.session_state.current_chat_id = current_chat["id"]
    else:
        initial_chat_id = 1
        st.session_state.chats = [{"id": initial_chat_id, "title": "New Conversation", "messages": []}]
        st.session_state.current_chat_id = initial_chat_id
        current_chat = st.session_state.chats[0]

col_title, col_persona = st.columns([2, 2])
with col_title:
    st.header(current_chat["title"])
with col_persona:
    persona = st.selectbox(
        "Persona",
        ["General Companion", "Exam Prep Coach", "Strict Professor", "Senior Tech Lead", "Data Science Mentor", "Creative Director"],
        label_visibility="collapsed"
    )

# System prompts with creator identity hardcoded
system_prompts = {
    "General Companion": "You are Gyan, an intelligent multi-persona AI companion created by Roshan, a student of NIT Durgapur.",
    "Exam Prep Coach": "You are an expert Exam Prep Coach, helping students break down derivations, concepts, and study schedules clearly. You were created by Roshan, a student of NIT Durgapur.",
    "Strict Professor": "You are a strict, academic professor who demands rigorous precision and high standards. You were created by Roshan, a student of NIT Durgapur.",
    "Senior Tech Lead": "You are a pragmatic Senior Tech Lead providing clean code architecture and debugging guidance. You were created by Roshan, a student of NIT Durgapur.",
    "Data Science Mentor": "You are a Data Science Mentor explaining machine learning algorithms, Python, and data pipelines. You were created by Roshan, a student of NIT Durgapur.",
    "Creative Director": "You are a Creative Director focusing on design principles, typography, and visual aesthetics. You were created by Roshan, a student of NIT Durgapur."
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

    # Automatically generate a smart title for the chat history
    if current_chat["title"] == "New Conversation":
        try:
            client_temp = Groq(api_key=groq_api_key)
            title_res = client_temp.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": "Generate a short, concise title (max 4 words) summarizing this user query. No quotes, no punctuation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10
            )
            gen_title = title_res.choices[0].message.content.strip()
            current_chat["title"] = gen_title if gen_title else (prompt[:25] + "...")
        except Exception:
            current_chat["title"] = prompt[:25] + "..." if len(prompt) > 25 else prompt

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        try:
            client = Groq(api_key=groq_api_key)
            
            formatted_messages = [{"role": "system", "content": system_prompts.get(persona, system_prompts["General Companion"])}]
            for m in current_chat["messages"]:
                formatted_messages.append({"role": m["role"], "content": m["content"]})

            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
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
