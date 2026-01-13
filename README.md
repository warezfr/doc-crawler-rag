# 🕷️ Advanced Doc Crawler for RAG - AnythingLLM Optimized

A powerful, self-hosted web crawler designed to ingest documentation into LLM pipelines (like AnythingLLM). Built with Python, Streamlit, and Trafilatura.

NEW CRAWL

<img width="2460" height="590" alt="image" src="https://github.com/user-attachments/assets/3fc3494f-ef72-4240-81fa-3fc942c4e745" />

CRAWL STATUS

<img width="1319" height="693" alt="image" src="https://github.com/user-attachments/assets/edf79187-fd2c-4a44-ae06-35def4964d31" />

CRAWL HISTORY AND DOWNLOAD 

<img width="2139" height="815" alt="image" src="https://github.com/user-attachments/assets/7d5311cf-b2be-49e9-bf3e-132ded0847cf" />



## ✨ Features

*   **Smart Extraction**: Uses `trafilatura` to extract only the main article content, removing navbars, footers, and ads.
*   **RAG-Ready Exports**: Automatically splits large datasets into 20MB chunks (JSON/Markdown) for easy upload to vector databases.
*   **Live Dashboard**: Real-time progress tracking, speed metrics (pages/sec), and recent activity logs.
*   **Resilient**: Background threading with persistent SQLite history. Resume or stop crawls at any time.
*   **Dockerized**: Simple deployment with Docker Compose.

## 🚀 Quick Start

### 1. Clone & Configure
```bash
git clone https://github.com/your-username/doc-crawler-rag.git
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
