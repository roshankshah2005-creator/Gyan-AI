# Gyan-AI
# 🧠 Gyan AI Platform

**Gyan** is an advanced, high-performance AI assistant web application built with **Streamlit**, **Scikit-Learn**, and Google's **Gemini Flash** API. Unlike standard API wrappers, Gyan features a unique hybrid architecture that classifies user intent locally before routing context-aware instructions to the LLM.

---

## ✨ Key Features

* **Hybrid ML Intent Routing:** Uses a custom trained Naive Bayes classifier (`ml_model.py`) to categorize queries into Coding, Data Science, Exam Prep, Resume Roasting, or General chat.
* **Document RAG (Chat with Files):** Seamlessly upload PDF or TXT files in the sidebar and chat directly with your documents.
* **Dynamic AI Personas:** Instantly switch between expert styles (*Senior Tech Lead*, *Strict Professor*, or *Chill Mentor*).
* **Gemini-Style Sidebar History:** Fully functional multi-session chat history with auto-generated dynamic titles.
* **High-Precision Reasoning:** Configured with deep thinking levels (`thinking_level="HIGH"`) for maximum technical accuracy.
* **Resilient Architecture:** Includes built-in auto-retry protection to handle 503 high-demand traffic spikes gracefully.
* **Modern UI Design:** Sleek glassmorphism cards, glowing gradient typography, and a custom semi-dark developer theme.

---

## 📁 Project Structure

```text
gemini-ml-bot/
├── .github
├── .streamlit
├── __pycache__
├── app.py             # Main Streamlit web application & UI logic
├── ml_model.py        # Scikit-Learn Naive Bayes intent classification pipeline
└── README.md          # Project documentation
