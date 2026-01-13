# 🕷️ Advanced Doc Crawler for RAG - AnythingLLM, NotebookLLM, ... Optimized

**Stop feeding your RAG garbage.**

This is a powerful, self-hosted web crawler designed to ingest documentation into LLM pipelines (like **AnythingLLM**). 

Unlike generic crawlers, it uses `trafilatura` to **strip away navigation bars, ads, and footers**, leaving you with clean, high-quality markdown that LLMs actually understand.

NEW CRAWL

<img width="2460" height="590" alt="image" src="https://github.com/user-attachments/assets/3fc3494f-ef72-4240-81fa-3fc942c4e745" />

CRAWL STATUS

<img width="1319" height="693" alt="image" src="https://github.com/user-attachments/assets/edf79187-fd2c-4a44-ae06-35def4964d31" />

CRAWL HISTORY AND DOWNLOAD 

<img width="2139" height="815" alt="image" src="https://github.com/user-attachments/assets/7d5311cf-b2be-49e9-bf3e-132ded0847cf" />



## ⚡ Why this crawler?

*   **Clean Data = Better Answers**: Most crawlers dump raw HTML. This one extracts the *article* text automatically.
*   **Ready for Vector DBs**: Automatically splits large exports into **20MB chunks** (JSON/Markdown) to fit upload limits.
*   **Self-Hosted & Private**: Runs on your NAS/Server via Docker. Your data stays yours.
*   **Resilient**: Background threading with persistent SQLite history. Resume or stop crawls at any time.

## ✨ Features

*   **Smart Extraction**: Uses `trafilatura` to extract only the main article content, removing navbars, footers, and ads.
*   **RAG-Ready Exports**: Automatically splits large datasets into 20MB chunks (JSON/Markdown) for easy upload to vector databases.
*   **Live Dashboard**: Real-time progress tracking, speed metrics (pages/sec), and recent activity logs.
*   **Resilient**: Background threading with persistent SQLite history. Resume or stop crawls at any time.
*   **Dockerized**: Simple deployment with Docker Compose.

## 🚀 Quick Start

### 1. Clone & Configure
```bash
https://github.com/warezfr/doc-crawler-rag.git
cd doc-crawler-rag
```

### 2. Deploy with Docker
```bash
docker compose up -d
```

Access the dashboard at `http://localhost:18510`.

## 🛠️ Configuration

Edit `docker-compose.yml` to persist data or change ports:

```yaml
volumes:
  - ./data:/app/data  # Persistent storage for crawls
```

## 🏗️ Architecture

*   **Frontend**: Streamlit (UI, File Exports)
*   **Backend**: Python `threading` + `sqlite3`
*   **Engine**: `Trafilatura` (Extraction) + `Requests` (Fetching)

## 📦 Requirements

*   Docker & Docker Compose
*   (Optional) AnythingLLM instance for direct uploads
