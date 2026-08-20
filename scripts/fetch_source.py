#!/usr/bin/env python3
"""
Fast & Resilient Source Fetcher & Converter for LLM Wiki Ingestion
Supports:
1. Tier 1: Fast HTTP + BeautifulSoup extraction (<1s)
2. Tier 2: Playwright Headless Chromium for Dynamic/SPA websites (React, Vue, SET, JS-rendered)
3. Tier 3: MarkItDown for Documents (PDF, DOCX, PPTX, XLSX)
"""

import sys
import os
import re
import datetime
import urllib.request
import argparse
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    from markitdown import MarkItDown
except ImportError:
    MarkItDown = None

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


def clean_slug(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text[:60] if len(text) > 60 else text


def extract_content_from_html(html: str, url: str):
    soup = BeautifulSoup(html, 'html.parser') if BeautifulSoup else None
    
    # Title
    title = "Untitled"
    if soup:
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            title = og_title['content']
        elif soup.title and soup.title.string:
            title = soup.title.string.strip()
            
    # Author
    author = "Unknown"
    if soup:
        author_meta = soup.find('meta', attrs={'name': re.compile(r'author', re.I)}) or soup.find('meta', property='article:author')
        if author_meta and author_meta.get('content'):
            author = author_meta['content'].strip()
            
    # Publisher / Site
    publisher = "Web"
    if soup:
        og_site = soup.find('meta', property='og:site_name')
        if og_site and og_site.get('content'):
            publisher = og_site['content'].strip()
        else:
            domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
            if domain_match:
                publisher = domain_match.group(1)

    # Published date
    published = datetime.date.today().isoformat()
    if soup:
        pub_meta = soup.find('meta', property=re.compile(r'published_time', re.I)) or soup.find('meta', attrs={'name': re.compile(r'pubdate|date', re.I)})
        if pub_meta and pub_meta.get('content'):
            match = re.search(r'\d{4}-\d{2}-\d{2}', pub_meta['content'])
            if match:
                published = match.group(0)

    # Clean body extraction
    body_text = ""
    if soup:
        body = soup.find('article') or soup.find('div', class_=re.compile(r'article[-_]?body|story[-_]?content|entry[-_]?content|post[-_]?content', re.I)) or soup.find('body')
        if body:
            paragraphs = []
            for tag in body.find_all(['p', 'h2', 'h3', 'h4', 'blockquote', 'li']):
                txt = tag.get_text(strip=True)
                if len(txt) > 20 and not any(bp in txt.lower() for bp in ['cookie', 'subscribe', 'sign up', 'all rights reserved', 'follow us', 'privacy policy']):
                    paragraphs.append(txt)
            body_text = '\n\n'.join(paragraphs)
            
    if not body_text and MarkItDown:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as f:
            f.write(html)
            tmp_path = f.name
        try:
            md = MarkItDown()
            res = md.convert(tmp_path)
            body_text = res.text_content
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    return title, author, publisher, published, body_text


def fetch_url_http(url: str):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode('utf-8', errors='ignore')


def fetch_url_playwright(url: str):
    if not sync_playwright:
        raise RuntimeError("Playwright is not installed.")
        
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        page.goto(url, wait_until='domcontentloaded', timeout=20000)
        page.wait_for_timeout(2000)
        html = page.content()
        browser.close()
    return html


def fetch_url(url: str, output_dir: Path = None, media_type: str = "article", force_playwright: bool = False) -> Path:
    html = ""
    used_method = "html-scrape"
    
    if force_playwright:
        print(f"Fetching via Playwright (SPA/Dynamic Mode): {url}")
        html = fetch_url_playwright(url)
        used_method = "playwright-render"
    else:
        try:
            print(f"Attempting Fast HTTP fetch: {url}")
            html = fetch_url_http(url)
        except Exception as e:
            print(f"Fast HTTP failed ({e}). Falling back to Playwright...")
            if sync_playwright:
                html = fetch_url_playwright(url)
                used_method = "playwright-render"
            else:
                raise

    title, author, publisher, published, body_text = extract_content_from_html(html, url)
    
    if len(body_text) < 200 and not force_playwright and used_method != "playwright-render" and sync_playwright:
        print("Static HTML yielded sparse content. Falling back to Playwright for dynamic rendering...")
        html = fetch_url_playwright(url)
        used_method = "playwright-render"
        title, author, publisher, published, body_text = extract_content_from_html(html, url)

    date_prefix = published.replace('-', '')
    slug = f"{date_prefix}_{clean_slug(title)}"
    
    if output_dir is None:
        vault_root = Path(__file__).resolve().parent.parent
        output_dir = vault_root / "01-Raw" / media_type
        
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / f"{slug}.md"
    
    content = f"""---
title: "{title}"
type: raw
source_type: {media_type}
url: "{url}"
publisher: "{publisher}"
author: "{author}"
published: {published}
captured: {datetime.date.today().isoformat()}
conversion_method: {used_method}
status: raw
images: 0
img_dir: ""
tags: []
---

# {title}

**Source:** {url}  
**Publisher:** {publisher} | **Author:** {author} | **Published:** {published}

---

{body_text.strip()}
"""
    
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
        
    return out_file


def convert_local_file(file_path: str, media_type: str = "book") -> Path:
    src = Path(file_path).resolve()
    if not src.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    vault_root = Path(__file__).resolve().parent.parent
    output_dir = vault_root / "01-Raw" / media_type
    output_dir.mkdir(parents=True, exist_ok=True)
    
    date_prefix = datetime.date.today().strftime('%Y%m%d')
    slug = f"{date_prefix}_{clean_slug(src.stem)}"
    out_file = output_dir / f"{slug}.md"
    
    body_text = ""
    if MarkItDown:
        md = MarkItDown()
        res = md.convert(str(src))
        body_text = res.text_content
    else:
        with open(src, 'r', encoding='utf-8', errors='ignore') as f:
            body_text = f.read()

    content = f"""---
title: "{src.stem}"
type: raw
source_type: {media_type}
url: "file:///{src.as_posix()}"
publisher: "Local File"
author: "Unknown"
published: {datetime.date.today().isoformat()}
captured: {datetime.date.today().isoformat()}
conversion_method: markitdown
status: raw
raw_file: "{src.as_posix()}"
tags: []
---

# {src.stem}

---

{body_text.strip()}
"""
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
        
    return out_file


def main():
    parser = argparse.ArgumentParser(description="Fast & Resilient Fetcher for LLM Wiki")
    parser.add_argument("source", help="URL or local file path")
    parser.add_argument("--type", default="article", choices=["article", "filing", "book", "video", "dataset"])
    parser.add_argument("--playwright", action="store_true", help="Force Playwright headless rendering for SPAs")
    args = parser.parse_args()
    
    if args.source.startswith("http://") or args.source.startswith("https://"):
        saved = fetch_url(args.source, media_type=args.type, force_playwright=args.playwright)
    else:
        saved = convert_local_file(args.source, media_type=args.type)
        
    print(f"SAVED_RAW: {saved}")


if __name__ == "__main__":
    main()
