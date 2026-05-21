# Agentic X (Twitter) Trend Synthesizer & Dashboard

An intelligent, autonomous agentic system built with LangChain and Google Gemini that retrieves real-time trending topics, gathers and verifies online news sources, synthesizes factual summaries, and serves them on a modern, high-fidelity interactive dashboard.

---

## ✨ Features

* **Real-time Trend Scraping**: Seamlessly extracts trending topics from global/local channels.
* **Dual-Agent Architecture**:
  1. **Trend Analyzer Agent**: Reviews the hot trends and dynamically selects the most discussion-worthy, factual topic to analyze.
  2. **News Synthesizer Agent**: Aggregates web data, performs factual cross-referencing, drafts a policy-compliant tweet (<280 characters) citing the primary source, and creates a comprehensive brief.
* **Verified News Retriever**: Searches the web to harvest **20+ premium and verified online articles** (e.g., Reuters, TechCrunch, Forbes) with active outbound links.
* **Windows Terminal Stability**: Fully reconfigured for UTF-8 standard console outputs to prevent Windows terminal character decoding crashes.
* **Interactive Glassmorphism Dashboard**: Updates a custom local HTML dashboard with premium styling, dark mode, responsive grids, and direct **"Share to X"** Web Intent buttons.

---

## 🛠️ Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/vikrammaditya/twitter-trend-synthesizer.git
   cd twitter-trend-synthesizer
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   * Copy the template file:
     ```bash
     cp .env.template .env
     ```
   * Open `.env` and fill in your details (like `GEMINI_API_KEY`):
     ```ini
     GEMINI_API_KEY=AIzaSy...
     TRENDS_LOCATION=global
     CHECK_INTERVAL_HOURS=2
     MAX_SOURCES=25
     ```

---

## 🚀 Usage

### 1. Run Now (Immediate Execution)
Execute a one-off cycle to scrape current trends, search the web, compile a news digest, and update the dashboard:
```bash
python app.py --run-now
```

### 2. Run background Scheduler
Run the background scheduler to automatically check, analyze, and post trending updates every few hours:
```bash
python app.py
```

### 3. Open the Premium Dashboard
Simply open the generated `dashboard.html` file in any web browser to view your runs, read synthesized reports, browse verified sources, and share drafted posts to X with a single click.

---

## 🛡️ Security

This repository is strictly **code-only**. The local databases (`history.json`), customized API keys (`.env`), scraped logs, and dashboard render outputs (`*.html`) are isolated via `.gitignore` to prevent any credential exposure.
