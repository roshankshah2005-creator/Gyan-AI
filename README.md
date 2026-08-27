# 🧠 GYAN AI

Hey there! Welcome to **GYAN AI**—a sleek, multi-persona AI companion web app built using Python, Streamlit, and the Groq API. It comes packed with features like persistent SQLite chat storage, user authentication with a password reset flow, built-in math verification to keep out bots, and a custom UI design.

---

## ✨ What's Inside?

* **Multiple AI Personas:** Easily switch between different AI modes depending on what you're working on—whether you need a general companion, an exam prep coach, a strict academic professor, a senior tech lead, a data science mentor, a creative director, or a code helper.
* **Real-Time Streaming:** Responses stream smoothly token-by-token so you don't have to wait around.
* **Saved Chats:** Your conversation history and custom chat titles are automatically saved in a local SQLite database.
* **Auth & Security:** Simple and secure Sign Up, Log In, and Forgot Password flows backed up by quick math CAPTCHA checks to block spam bots.
* **Custom Branding:** Styled with custom Google Fonts (Orbitron) and a clean gradient logo.

---

## 🛠️ Built With

* **Frontend:** [Streamlit](https://streamlit.io/)
* **AI Engine:** [Groq API](https://groq.com/)
* **Database:** SQLite & JSON
* **Styling:** Custom CSS & Google Fonts

---

## 📂 Project Layout

```text
📦 gyan-ai
┣ 📂 .streamlit
┃ ┗ 📜 secrets.toml
┣ 📜 README.md
┣ 📜 main.py
┣ 📜 ml_model.py
┗ 📜 requirements.txt
