# 🚀 YouTube Creator OS (YCIS)

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://youtube-creator-os.streamlit.app)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Groq Powered](https://img.shields.io/badge/AI-Groq%20Llama%203.1-orange.svg)](https://groq.com/)

> **Live Application:** [Test the live deployment here!](https://youtube-creator-os-c23.streamlit.app)

**YouTube Creator Intelligent System (YCIS)** is a comprehensive, multi-modal AI framework designed to automate market intelligence, competitive analysis, and production storyboarding for digital content creators. Built with a decoupled **Streamlit** architecture and accelerated by the **Groq LPU (Llama 3.1)**, YCIS solves the "Ideation-to-Execution Gap" by providing real-time data and high-authority factual research in a single dashboard.

---

## ✨ Core Features

* **End-to-End Analytics:** Scans live market data using the YouTube Data API to detect algorithmic outliers and trending formats.
* **Video X-Ray & Competitor Deconstruction:** Extracts transcripts of competitor videos, running Natural Language Processing (NLP) to map sentiment arcs and isolate pacing drags or retention hooks.
* **Deep Research Workspace:** Automates academic evidence gathering via Google Dorking and DuckDuckGo, pulling verifiable PDFs and scholarly articles into a structured "Evidence Locker."
* **Production Studio & AI Co-Pilot:** Transforms raw research into a structured storyboard matrix and provides real-time AI critiques of script drafts to maximize viewer retention.

---

## 🛠️ Technology Stack

* **Frontend:** Streamlit
* **LLM Inference:** Groq Cloud API (Llama 3.1 8B)
* **Data APIs:** YouTube Data API v3, YouTube Transcript API
* **Search & Retrieval:** DuckDuckGo Search (DDGS), Wikipedia API
* **Data Processing & NLP:** Pandas, TextBlob
* **Data Visualization:** Altair

---

## ⚙️ Local Installation & Setup

If you wish to run the YouTube Creator OS locally on your own machine, follow these steps:

## 1. Clone the Repository
```bash
git clone https://github.com/suhaschahure/youtube-creator-os.git
cd youtube-creator-os
```

## 2. Install Dependencies
> **Pro-Tip:** It is recommended to use a virtual environment (e.g., `venv` or `conda`) to avoid package conflicts.

```bash
pip install -r requirements.txt
```

## 3. Configure API Keys
Create a `.streamlit` folder in the root directory and add a `secrets.toml` file to securely store your API keys.

```toml
# .streamlit/secrets.toml
GROQ_API_KEY = "gsk_your_groq_api_key_here"
YOUTUBE_API_KEY = "AIza_your_youtube_api_key_here"
```

## 4. Run the Application
```bash
streamlit run app.py
```

---

## 🧠 System Architecture

The system follows a decoupled client-server model optimized for sub-3-second response times:

1. **User Input:** Creators interact via the Streamlit Web GUI.
2. **API Fetching:** Python backend retrieves real-time statistics and transcripts via YouTube and DuckDuckGo.
3. **AI Processing:** Data is sent to the Groq LPU architecture for zero-shot reasoning and semantic breakdown using Llama 3.1.
4. **Structured Output:** Processed intelligence is rendered back to the user via Altair charts and organized storyboard matrices.

---

## 👨‍💻 Development
* **Suhas Chahure** - Developer / Researcher
