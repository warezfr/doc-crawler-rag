import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/crawls.db")

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS crawls (
            id TEXT PRIMARY KEY,
            start_urls TEXT,
            status TEXT,
            started_at DATETIME,
            completed_at DATETIME,
            total_pages INTEGER DEFAULT 0,
            max_pages INTEGER,
            max_depth INTEGER,
            config TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crawl_id TEXT,
            url TEXT,
            status INTEGER,
            depth INTEGER,
            title TEXT,
            markdown TEXT,
            links TEXT,
            crawled_at DATETIME,
            FOREIGN KEY(crawl_id) REFERENCES crawls(id)
        )
    ''')
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)
