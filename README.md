# 🧠 Gyan AI

Gyan AI is a high-performance, multi-persona conversational assistant built with **Streamlit** and powered by **Groq's ultra-fast inference engine**. It features dynamic persona switching, document context ingestion (RAG), and lightning-fast text processing, completely bypassing complex cloud configuration overhead.

---

## ✨ Features

* **Multi-Persona Intelligence**: Seamlessly switch between specialized AI modes:
  * **Senior Tech Lead**: For clean code snippets, architecture choices, and rigorous code reviews.
  * **Data Science Mentor**: For machine learning workflows, pandas operations, and statistical logic.
  * **Exam Prep Coach**: For structured academic revision, chapter summaries, and high-yield concepts.
  * **Creative Director**: For typography feedback, design layouts, and color palettes.
* **Document Context Ingestion (RAG)**: Upload PDF or TXT files directly to ground the AI's responses in your custom documents.
* **Blazing Fast Performance**: Powered by Groq's LPU infrastructure, delivering thousands of tokens per second.
* **Clean UI**: Built with Streamlit for a responsive, clean, and modern web interface.

---

## 🛠️ Tech Stack

* **Frontend & UI**: [Streamlit](https://streamlit.io/)
* **AI Inference Provider**: [Groq API](https://groq.com/) (`openai/gpt-oss-20b`)
* **Document Parsing**: `pypdf`
* **Language**: Python 3.10+

---

## 🚀 Quick Setup & Installation

### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/gyan-ai.git](https://github.com/your-username/gyan-ai.git)
cd gyan-ai
