#!/usr/bin/env python3
"""
Fast & Resilient Source Fetcher & Converter for LLM Wiki Ingestion
Supports:
1. Web URLs:
   - Tier 1: Fast HTTP + BeautifulSoup extraction (<0.5s)
   - Tier 2: Playwright Headless Chromium for Dynamic/SPA websites (React, Vue, SET, JS-rendered)
2. YouTube Videos:
   - Automated transcript extraction with timestamps via youtube-transcript-api / yt-dlp
3. Local Documents:
   - Tier 3: MarkItDown for Documents (PDF, DOCX, PPTX, XLSX)
"""

import sys
import os
import re
import datetime
import urllib.request
import argparse
from pathlib import Path
import tempfile

from raw_capture import write_capture

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

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

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

import subprocess
import shutil

FFMPEG_PATH = shutil.which('ffmpeg')


def clean_slug(text: str) -> str:
    cleaned = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    if not cleaned:
        # For non-Latin scripts (e.g. Thai), keep unicode words/letters
        cleaned = re.sub(r'[^\w\d]+', '-', text, flags=re.UNICODE).strip('-')
    return cleaned[:60] if len(cleaned) > 60 else (cleaned or "source")


def extract_youtube_video_id(url: str) -> str:
    m = re.search(r'(?:v=|\/|youtu\.be\/|embed\/)([a-zA-Z0-9_-]{11})', url)
    return m.group(1) if m else None


def extract_youtube_keyframes(url: str, slug: str, vault_root: Path, timestamps: list = None) -> tuple:
    """Extracts key exhibits from YouTube video using yt-dlp and FFmpeg."""
    if not yt_dlp or not FFMPEG_PATH:
        return 0, ""

    assets_dir = vault_root / "06-Assets" / slug
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Default interval timestamps if none provided (e.g. 20%, 40%, 60% of video)
    if not timestamps:
        timestamps = [
            ("img_01_key_slide.png", 600, 610, "00:00:03"),
            ("img_02_key_slide.png", 1800, 1810, "00:00:03"),
            ("img_03_key_slide.png", 2400, 2410, "00:00:03")
        ]

    count = 0
    for filename, start_s, end_s, offset in timestamps:
        out_img = assets_dir / filename
        temp_clip = assets_dir / f"temp_{start_s}.mp4"
        try:
            ydl_opts = {
                'format': 'bestvideo[height<=720]/best[height<=720]',
                'outtmpl': str(temp_clip),
                'extractor_args': {'youtube': {'player_client': ['android', 'ios', 'web']}},
                'download_ranges': yt_dlp.utils.download_range_func(None, [(start_s, end_s)]),
                'overwrites': True,
                'quiet': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            if temp_clip.exists():
                cmd = [FFMPEG_PATH, '-y', '-ss', offset, '-i', str(temp_clip), '-frames:v', '1', '-q:v', '2', str(out_img)]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                temp_clip.unlink(missing_ok=True)
                if out_img.exists() and out_img.stat().st_size > 0:
                    count += 1
        except Exception as e:
            print(f"Warning extracting video frame {filename}: {e}")
            if temp_clip.exists():
                temp_clip.unlink(missing_ok=True)

    rel_dir = f"06-Assets/{slug}" if count > 0 else ""
    return count, rel_dir


def fetch_youtube_video(url: str, output_dir: Path = None, extract_frames: bool = True, timestamps: list = None) -> Path:
    video_id = extract_youtube_video_id(url)
    if not video_id:
        raise ValueError(f"Could not parse YouTube video ID from URL: {url}")
        
    print(f"Fetching YouTube transcript for Video ID: {video_id}...")
    
    # 1. Fetch metadata
    req = urllib.request.Request(
        f"https://www.youtube.com/watch?v={video_id}",
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        
    title = f"YouTube Video {video_id}"
    m_title = re.search(r'"title":\{"runs":\[\{"text":"([^"]+)"\}', html)
    if m_title:
        title = m_title.group(1)
    else:
        soup = BeautifulSoup(html, 'html.parser') if BeautifulSoup else None
        if soup and soup.title:
            title = soup.title.string.replace(" - YouTube", "").strip()

    author = "YouTube Channel"
    m_author = re.search(r'"ownerChannelName":"([^"]+)"', html) or re.search(r'"author":"([^"]+)"', html)
    if m_author:
        author = m_author.group(1)

    published = datetime.date.today().isoformat()
    m_pub = re.search(r'"publishDate":"([^"]+)"', html) or re.search(r'"uploadDate":"([^"]+)"', html)
    if m_pub:
        match = re.search(r'\d{4}-\d{2}-\d{2}', m_pub.group(1))
        if match:
            published = match.group(0)

    # 2. Fetch Transcript
    transcript_lines = []
    if YouTubeTranscriptApi:
        api = YouTubeTranscriptApi()
        try:
            # Try fetching Thai or English
            t_list = api.list(video_id)
            transcript = None
            try:
                transcript = api.fetch(video_id, languages=['th', 'en'])
            except Exception:
                for t in t_list:
                    transcript = t.fetch()
                    break
            
            if transcript:
                for s in transcript.snippets:
                    mins = int(s.start // 60)
                    secs = int(s.start % 60)
                    transcript_lines.append(f"[{mins:02d}:{secs:02d}] {s.text}")
        except Exception as e:
            print(f"YouTubeTranscriptApi warning ({e}). Trying fallback...")

    body_text = "\n".join(transcript_lines) if transcript_lines else "*(Transcript could not be extracted automatically)*"

    date_prefix = published.replace('-', '')
    slug = f"{date_prefix}_{clean_slug(title)}"
    vault_root = Path(__file__).resolve().parent.parent
    
    # 3. Extract Exhibits / Frames if requested
    img_count, img_dir = 0, ""
    if extract_frames and yt_dlp and FFMPEG_PATH:
        print(f"Extracting key exhibits via yt-dlp & FFmpeg for {slug}...")
        img_count, img_dir = extract_youtube_keyframes(url, slug, vault_root, timestamps=timestamps)

    if output_dir is None:
        output_dir = vault_root / "01-Raw" / "video"
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    content = f"""---
title: "{title}"
type: raw
source_type: video
url: "{url}"
publisher: "YouTube"
author: "{author}"
published: {published}
captured: {datetime.date.today().isoformat()}
conversion_method: youtube-transcript
status: raw
images: {img_count}
img_dir: "{img_dir}"
tags: []
---

# {title}

**Source:** {url}  
**Channel:** {author} | **Published:** {published}

---

## Transcript

{body_text.strip()}
"""
    return write_capture(output_dir, slug, url, (content.strip() + "\n").encode("utf-8"))


def extract_content_from_html(html: str, url: str):
    soup = BeautifulSoup(html, 'html.parser') if BeautifulSoup else None
    
    title = "Untitled"
    if soup:
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            title = og_title['content']
        elif soup.title and soup.title.string:
            title = soup.title.string.strip()
            
    author = "Unknown"
    if soup:
        author_meta = soup.find('meta', attrs={'name': re.compile(r'author', re.I)}) or soup.find('meta', property='article:author')
        if author_meta and author_meta.get('content'):
            author = author_meta['content'].strip()
            
    publisher = "Web"
    if soup:
        og_site = soup.find('meta', property='og:site_name')
        if og_site and og_site.get('content'):
            publisher = og_site['content'].strip()
        else:
            domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
            if domain_match:
                publisher = domain_match.group(1)

    published = datetime.date.today().isoformat()
    if soup:
        pub_meta = soup.find('meta', property=re.compile(r'published_time', re.I)) or soup.find('meta', attrs={'name': re.compile(r'pubdate|date', re.I)})
        if pub_meta and pub_meta.get('content'):
            match = re.search(r'\d{4}-\d{2}-\d{2}', pub_meta['content'])
            if match:
                published = match.group(0)

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


def fetch_document_url(url: str, output_dir: Path = None, media_type: str = "filing") -> Path:
    print(f"Fetching Document / PDF URL: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()

    vault_root = Path(__file__).resolve().parent.parent
    if output_dir is None:
        output_dir = vault_root / "01-Raw" / media_type
    output_dir.mkdir(parents=True, exist_ok=True)

    url_clean = url.split('?')[0]
    filename = url_clean.split('/')[-1] if '/' in url_clean else "document.pdf"
    if not any(filename.endswith(ext) for ext in ['.pdf', '.docx', '.pptx', '.xlsx']):
        filename += ".pdf"

    # Conversion must not stage downloads over files already in 01-Raw.
    with tempfile.TemporaryDirectory(prefix="wiki-document-") as temporary:
        temp_doc_path = Path(temporary) / filename
        temp_doc_path.write_bytes(data)

        body_text = ""
        if MarkItDown:
            try:
                md = MarkItDown()
                res = md.convert(str(temp_doc_path))
                body_text = res.text_content
            except Exception as e:
                print(f"MarkItDown failed ({e}), falling back...")

        if not body_text:
            try:
                import pypdf
                reader = pypdf.PdfReader(str(temp_doc_path))
                body_text = "\n\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
            except Exception as e:
                print(f"PyPDF failed ({e})")

    title = filename.rsplit('.', 1)[0]
    published = datetime.date.today().isoformat()
    publisher = "SET" if "set.or.th" in url else "Company Filing"
    author = "Management"

    lines = [l.strip() for l in body_text.splitlines() if l.strip()]
    if lines:
        first_few = " ".join(lines[:15])
        m_comp = re.search(r'บริษัท\s+([^\(\n]+?)\s*จำกัด\s*\(มหาชน\)', first_few) or re.search(r'บริษัท\s+([^\(\n]+?)\s*จํากัด\s*\(มหาชน\)', first_few)
        m_ticker = re.search(r'\b([A-Z0-9]{2,10})\s+IR\b', first_few)
        
        thai_months = {
            'มกราคม': '01', 'กุมภาพันธ์': '02', 'มีนาคม': '03', 'เมษายน': '04',
            'พฤษภาคม': '05', 'มิถุนายน': '06', 'กรกฎาคม': '07', 'สิงหาคม': '08',
            'กันยายน': '09', 'ตุลาคม': '10', 'พฤศจิกายน': '11', 'ธันวาคม': '12'
        }
        for m_name, m_num in thai_months.items():
            m_date = re.search(rf'(\d{{1,2}})\s+{m_name}\s+(\d{{4}})', first_few)
            if m_date:
                day = int(m_date.group(1))
                year = int(m_date.group(2))
                if year > 2400:
                    year -= 543
                published = f"{year:04d}-{m_num}-{day:02d}"
                break

        comp_name = m_comp.group(1).strip() if m_comp else ""
        ticker = m_ticker.group(1).strip() if m_ticker else ""
        
        if ticker and ("คําอธิบาย" in first_few or "คำอธิบาย" in first_few):
            period = "2Q26" if ("30 มิถุนายน" in first_few or "30 มถิ ุนายน" in first_few or "2569" in first_few) else "MD&A"
            title = f"{ticker} MD&A {period}"
        elif comp_name:
            title = f"{comp_name} - Filing"

    date_prefix = published.replace('-', '')
    slug = f"{date_prefix}_{clean_slug(title)}"
    
    raw_document = write_capture(
        output_dir, slug, url, data, suffix=Path(filename).suffix
    )

    content = f"""---
title: "{title}"
type: raw
source_type: {media_type}
url: "{url}"
publisher: "{publisher}"
author: "{author}"
published: {published}
captured: {datetime.date.today().isoformat()}
conversion_method: markitdown
status: raw
raw_file: "{raw_document.as_posix()}"
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
    return write_capture(output_dir, slug, url, (content.strip() + "\n").encode("utf-8"))


def fetch_url(url: str, output_dir: Path = None, media_type: str = "article", force_playwright: bool = False, timestamps: list = None) -> Path:
    # Check if YouTube URL
    if "youtube.com" in url or "youtu.be" in url:
        return fetch_youtube_video(url, output_dir=output_dir, timestamps=timestamps)

    # Check if Direct Document URL (PDF, DOCX, PPTX, XLSX)
    url_clean = url.lower().split('?')[0]
    if url_clean.endswith(('.pdf', '.docx', '.pptx', '.xlsx')) or (media_type in ['filing', 'book'] and '.pdf' in url_clean):
        return fetch_document_url(url, output_dir=output_dir, media_type=media_type)

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
    
    return write_capture(output_dir, slug, url, (content.strip() + "\n").encode("utf-8"))


def convert_local_file(file_path: str, media_type: str = "book") -> Path:
    src = Path(file_path).resolve()
    if not src.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    vault_root = Path(__file__).resolve().parent.parent
    output_dir = vault_root / "01-Raw" / media_type
    output_dir.mkdir(parents=True, exist_ok=True)
    
    date_prefix = datetime.date.today().strftime('%Y%m%d')
    slug = f"{date_prefix}_{clean_slug(src.stem)}"
    
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
    return write_capture(output_dir, slug, src.as_uri(), (content.strip() + "\n").encode("utf-8"))


def parse_custom_timestamps(ts_str: str) -> list:
    """Parses comma-separated timestamps (e.g. '60,300,1200' or '01:00,05:00,20:00') into list of tuples."""
    results = []
    items = [t.strip() for t in ts_str.split(',') if t.strip()]
    for idx, item in enumerate(items, 1):
        seconds = 0
        if ':' in item:
            parts = item.split(':')
            if len(parts) == 2:
                seconds = int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        else:
            seconds = int(item)
        
        start_s = max(0, seconds - 2)
        end_s = seconds + 8
        results.append((f"img_{idx:02d}_key_slide.png", start_s, end_s, "00:00:02"))
    return results


def main():
    parser = argparse.ArgumentParser(description="Fast & Resilient Fetcher for LLM Wiki")
    parser.add_argument("source", help="URL or local file path")
    parser.add_argument("--type", default="article", choices=["article", "filing", "book", "video", "dataset"])
    parser.add_argument("--playwright", action="store_true", help="Force Playwright headless rendering for SPAs")
    parser.add_argument("--timestamps", default=None, help="Comma-separated timestamps for video keyframe extraction (e.g. '120,600,1800,2400')")
    args = parser.parse_args()
    
    custom_ts = parse_custom_timestamps(args.timestamps) if args.timestamps else None
    
    if args.source.startswith("http://") or args.source.startswith("https://"):
        saved = fetch_url(args.source, media_type=args.type, force_playwright=args.playwright, timestamps=custom_ts)
    else:
        saved = convert_local_file(args.source, media_type=args.type)
        
    print(f"SAVED_RAW: {saved}")


if __name__ == "__main__":
    main()
