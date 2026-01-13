import threading
import queue
import time
import json
import requests
from datetime import datetime
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import trafilatura
import tldextract
from models import get_connection

class CrawlerEngine(threading.Thread):
    def __init__(self, crawl_id, start_urls, max_pages, max_depth, user_agent, timeout):
        super().__init__()
        self.crawl_id = crawl_id
        self.start_urls = start_urls
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.user_agent = user_agent
        self.timeout = timeout
        self.stop_event = threading.Event()
        self.daemon = True

    def run(self):
        conn = get_connection()
        c = conn.cursor()
        
        try:
            # Update status to running
            c.execute("UPDATE crawls SET status = 'running' WHERE id = ?", (self.crawl_id,))
            conn.commit()

            session = requests.Session()
            visited = set()
            q = queue.Queue()
            
            for url in self.start_urls:
                q.put((url, 0))

            pages_count = 0
            
            while not q.empty() and pages_count < self.max_pages and not self.stop_event.is_set():
                current_url, depth = q.get()
                
                if current_url in visited or depth > self.max_depth:
                    continue
                
                visited.add(current_url)
                
                # Fetch
                try:
                    headers = {"User-Agent": self.user_agent}
                    resp = session.get(current_url, headers=headers, timeout=self.timeout)
                    status_code = resp.status_code
                    html = resp.text
                    soup = BeautifulSoup(html, "html.parser")
                    title = soup.title.string if soup.title else current_url
                    
                    # Enhanced content extraction
                    extracted_text = trafilatura.extract(html, include_links=True, output_format='markdown', include_tables=True)
                    if extracted_text:
                        markdown = extracted_text
                    else:
                        # Fallback to simple markdownify if trafilatura fails to find main content
                        markdown = md(html, strip=["script", "style"])
                    
                    # Extract links
                    links = []
                    if depth < self.max_depth:
                        base_netloc = urlparse(current_url).netloc
                        for tag in soup.find_all("a", href=True):
                            normalized = urljoin(current_url, tag["href"])
                            parsed = urlparse(normalized)
                            # Simple same-domain filter or subdomains
                            # For now strict same netloc or similar logic as original
                            if parsed.netloc == base_netloc: # strict same domain
                                clean_url = parsed._replace(fragment="", query=parsed.query).geturl()
                                if clean_url not in visited:
                                    links.append(clean_url)
                                    q.put((clean_url, depth + 1))
                    
                    # Save page
                    c.execute('''
                        INSERT INTO pages (crawl_id, url, status, depth, title, markdown, links, crawled_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (self.crawl_id, current_url, status_code, depth, title, markdown, json.dumps(links), datetime.utcnow()))
                    conn.commit()
                    
                    pages_count += 1
                    
                    # Update progress
                    c.execute("UPDATE crawls SET total_pages = ? WHERE id = ?", (pages_count, self.crawl_id))
                    conn.commit()
                    
                except Exception as e:
                    print(f"Error crawling {current_url}: {e}")
                    # Log error page
                    c.execute('''
                        INSERT INTO pages (crawl_id, url, status, depth, title, markdown, links, crawled_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (self.crawl_id, current_url, 0, depth, "Error: " + str(e), "", "[]", datetime.utcnow()))
                    conn.commit()

            # Finish
            status = 'completed' if not self.stop_event.is_set() else 'stopped'
            c.execute("UPDATE crawls SET status = ?, completed_at = ? WHERE id = ?", 
                     (status, datetime.utcnow(), self.crawl_id))
            conn.commit()

        except Exception as e:
            c.execute("UPDATE crawls SET status = 'failed' WHERE id = ?", (self.crawl_id,))
            conn.commit()
            raise e
        finally:
            conn.close()

    def stop(self):
        self.stop_event.set()
