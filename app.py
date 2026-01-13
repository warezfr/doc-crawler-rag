import streamlit as st
import sqlite3
import pandas as pd
import json
import time
import uuid
import os
from datetime import datetime
from pathlib import Path
from models import init_db, get_connection
from crawler_engine import CrawlerEngine

# Init DB
init_db()

st.set_page_config(page_title="Advanced Doc Crawler", layout="wide", page_icon="🕷️")

# Custom CSS for layout
st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

if 'active_crawlers' not in st.session_state:
    st.session_state.active_crawlers = {}

def get_crawls():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM crawls ORDER BY started_at DESC", conn)
    conn.close()
    return df

def get_pages(crawl_id):
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM pages WHERE crawl_id = ?", conn, params=(crawl_id,))
    conn.close()
    return df

def get_recent_pages(crawl_id, limit=20):
    conn = get_connection()
    query = """
        SELECT url, status, depth, title, crawled_at 
        FROM pages 
        WHERE crawl_id = ? 
        ORDER BY crawled_at DESC 
        LIMIT ?
    """
    df = pd.read_sql(query, conn, params=(crawl_id, limit))
    conn.close()
    return df

# Sidebar Navigation
st.sidebar.title("🕷️ Crawler Pro")
page = st.sidebar.radio("Navigation", ["New Crawl", "Dashboard", "History"])

if page == "New Crawl":
    st.header("🚀 Start New Crawl")
    
    with st.form("crawl_config"):
        col1, col2 = st.columns(2)
        with col1:
            start_urls_text = st.text_area("Start URLs (one per line)", height=150, help="Enter the URLs to start crawling from.")
        with col2:
            max_pages = st.number_input("Max Pages", min_value=1, max_value=10000, value=100, step=100)
            max_depth = st.number_input("Max Depth", min_value=1, max_value=10, value=2)
            timeout = st.slider("Request Timeout (s)", 5, 120, 30)
            user_agent = st.text_input("User Agent", "DocCrawlerBot/1.0")

        submitted = st.form_submit_button("Start Crawling", type="primary", use_container_width=True)

        if submitted and start_urls_text:
            start_urls = [u.strip() for u in start_urls_text.splitlines() if u.strip()]
            crawl_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(uuid.uuid4())[:8]
            
            # Create DB entry
            conn = get_connection()
            c = conn.cursor()
            c.execute('''
                INSERT INTO crawls (id, start_urls, status, started_at, max_pages, max_depth, config)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (crawl_id, json.dumps(start_urls), 'pending', datetime.utcnow(), max_pages, max_depth, "{}"))
            conn.commit()
            conn.close()
            
            # Start Thread
            engine = CrawlerEngine(crawl_id, start_urls, max_pages, max_depth, user_agent, timeout)
            st.session_state.active_crawlers[crawl_id] = engine
            engine.start()
            
            st.success(f"Crawl {crawl_id} started!")
            time.sleep(1)
            st.rerun()

elif page == "Dashboard":
    st.header("📊 Live Dashboard")
    
    # Auto-refresh logic
    refresh_interval = 2  # seconds
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = True
        
    col_h1, col_h2 = st.columns([3, 1])
    with col_h2:
        st.session_state.auto_refresh = st.checkbox("Auto-refresh (2s)", value=st.session_state.auto_refresh)

    # Get active/running crawls from DB
    crawls = get_crawls()
    active_crawls = crawls[crawls['status'].isin(['pending', 'running'])]
    
    if active_crawls.empty:
        st.info("No active crawls at the moment. Go to 'New Crawl' to start one.")
    else:
        for idx, row in active_crawls.iterrows():
            with st.container():
                st.subheader(f"Crawl: {row['id']}")
                
                # Calculate speed
                started_at = pd.to_datetime(row['started_at'])
                elapsed = (datetime.utcnow() - started_at).total_seconds()
                speed = row['total_pages'] / elapsed if elapsed > 0 else 0.0
                
                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("Status", row['status'])
                col2.metric("Pages Crawled", row['total_pages'])
                col3.metric("Max Pages", row['max_pages'])
                col4.metric("Depth Limit", row['max_depth'])
                col5.metric("Speed", f"{speed:.1f} p/s")
                
                progress = min(row['total_pages'] / row['max_pages'], 1.0)
                st.progress(progress)
                
                # Show live log
                st.caption("⚡ Recent Activity (Last 20 pages)")
                recent = get_recent_pages(row['id'])
                if not recent.empty:
                    st.dataframe(
                        recent[['crawled_at', 'status', 'depth', 'url']], 
                        use_container_width=True,
                        column_config={
                            "crawled_at": st.column_config.DatetimeColumn("Time", format="HH:mm:ss"),
                            "status": st.column_config.NumberColumn("Code", format="%d"),
                            "depth": st.column_config.NumberColumn("Depth", format="%d"),
                            "url": st.column_config.TextColumn("URL"),
                        },
                        hide_index=True,
                        height=300
                    )
                
                if st.button(f"Stop {row['id']}", key=f"stop_{row['id']}"):
                    if row['id'] in st.session_state.active_crawlers:
                        st.session_state.active_crawlers[row['id']].stop()
                        st.warning("Stopping initiated...")
                    else:
                        # Handle "Zombie" crawls (process lost/restarted) immediately
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("UPDATE crawls SET status = ?, completed_at = ? WHERE id = ?", 
                                 ('stopped', datetime.utcnow(), row['id']))
                        conn.commit()
                        conn.close()
                        st.success("Crawl marked as stopped.")
                        time.sleep(1)
                        st.rerun()
                
                st.divider()
        
        # Trigger refresh
        if st.session_state.auto_refresh:
            time.sleep(refresh_interval)
            st.rerun()

    if st.button("Manual Refresh"):
        st.rerun()

elif page == "History":
    st.header("📜 Crawl History")
    crawls = get_crawls()
    
    if crawls.empty:
        st.write("No history found.")
    else:
        st.dataframe(
            crawls[['id', 'status', 'started_at', 'completed_at', 'total_pages', 'start_urls']],
            use_container_width=True,
            column_config={
                "started_at": st.column_config.DatetimeColumn("Started"),
                "completed_at": st.column_config.DatetimeColumn("Completed"),
            }
        )
        
        st.subheader("Export & Details")
        selected_crawl = st.selectbox("Select Crawl to View", crawls['id'].tolist())
        
        if selected_crawl:
            pages = get_pages(selected_crawl)
            st.write(f"Pages in {selected_crawl}: {len(pages)}")
            st.dataframe(pages[['url', 'status', 'depth', 'title']], use_container_width=True)
            
            # Export logic
            if not pages.empty:
                MAX_CHUNK_BYTES = 20 * 1024 * 1024 # 20MB
                
                # Helper to chunk data
                def get_chunks(data_iterator, extension):
                    chunks = []
                    current_buffer = []
                    current_size = 0
                    chunk_idx = 1
                    
                    for item in data_iterator:
                        item_bytes = item.encode('utf-8')
                        if current_size + len(item_bytes) > MAX_CHUNK_BYTES and current_buffer:
                            chunks.append({
                                "name": f"crawl_{selected_crawl}_{chunk_idx}.{extension}",
                                "data": "".join(current_buffer)
                            })
                            chunk_idx += 1
                            current_buffer = []
                            current_size = 0
                        
                        current_buffer.append(item)
                        current_size += len(item_bytes)
                    
                    if current_buffer:
                         chunks.append({
                                "name": f"crawl_{selected_crawl}_{chunk_idx}.{extension}",
                                "data": "".join(current_buffer)
                            })
                    return chunks

                # 1. JSON Export
                json_lines = [json.dumps(record, ensure_ascii=False) + "\n" for record in pages.to_dict(orient="records")]
                json_chunks = get_chunks(json_lines, "json")
                
                st.subheader("JSON Exports")
                for chunk in json_chunks:
                    st.download_button(
                        label=f"Download {chunk['name']}",
                        data=chunk['data'],
                        file_name=chunk['name'],
                        mime="application/json",
                        key=chunk['name']
                    )
                
                # 2. Markdown Export
                md_items = []
                for _, p in pages.iterrows():
                    md_items.append(f"# {p['title']}\nURL: {p['url']}\n\n{p['markdown']}\n\n---\n\n")
                
                md_chunks = get_chunks(md_items, "md")
                
                st.subheader("Markdown Exports")
                for chunk in md_chunks:
                    st.download_button(
                        label=f"Download {chunk['name']}",
                        data=chunk['data'],
                        file_name=chunk['name'],
                        mime="text/markdown",
                        key=chunk['name']
                    )

                # AnythingLLM Upload (Simplified for this view)
                st.subheader("Upload to AnythingLLM")
                base_url = st.text_input("AnythingLLM URL", "http://anythingllm:3001/api/v1/document/upload")
                api_key = st.text_input("API Key", type="password")
                workspace = st.text_input("Workspace", "default")
                
                if st.button("Upload to Workspace"):
                    # This would ideally be a background task too, but for now we do it synchronously
                    import requests
                    success_count = 0
                    with st.status("Uploading documents...") as status:
                        for idx, p in pages.iterrows():
                            # Create a temp file
                            fname = f"{p['id']}.md"
                            content = f"# {p['title']}\nURL: {p['url']}\n\n{p['markdown']}".encode('utf-8')
                            try:
                                resp = requests.post(
                                    base_url,
                                    headers={"Authorization": f"Bearer {api_key}"},
                                    params={"workspace": workspace},
                                    files={"file": (fname, content, "application/octet-stream")},
                                    timeout=10
                                )
                                if resp.status_code == 200:
                                    success_count += 1
                            except Exception as e:
                                pass
                        status.update(label=f"Uploaded {success_count}/{len(pages)} docs", state="complete")


