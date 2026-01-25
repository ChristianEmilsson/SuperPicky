#!/usr/bin/env python3
"""
Wikipedia English Data Fetcher - Autonomous Mode
Usage: python3 scripts/fetch_wiki_all.py
Runs until all birds are processed (no monitoring required).
"""

import sqlite3
import time
import random
import requests
import logging
from datetime import datetime

# Configuration
DB_PATH = 'birdid/data/bird_reference.sqlite'
LOG_FILE = 'wiki_fetch_en_full.log'
DELAY = 0.5  # Reduced to 0.5 seconds
CHECKPOINT_INTERVAL = 50  # Print progress every 50 birds

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def get_wiki_summary(query, lang='en'):
    """Fetches the summary of a Wikipedia page with retry logic."""
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "exintro": True,
        "explaintext": True,
        "redirects": 1,
        "titles": query
    }
    headers = {
        "User-Agent": "SuperPickyBirdBot/1.0 (https://github.com/jamesphotography/superbirdid; contact@jameszhenyu.com)"
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                pages = data.get("query", {}).get("pages", {})
                for page_id, page_data in pages.items():
                    if page_id == "-1":
                        return None  # Not found
                    summary = page_data.get("extract", "")
                    return summary
            elif response.status_code == 429:  # Rate limited
                logging.warning(f"Rate limited, waiting 30s before retry...")
                time.sleep(30)
            else:
                logging.warning(f"HTTP {response.status_code} for {query}")
                return None
        except requests.exceptions.Timeout:
            logging.warning(f"Timeout for {query}, attempt {attempt+1}/{max_retries}")
            time.sleep(5)
        except Exception as e:
            logging.error(f"Error for {query}: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                return None  # Give up after all retries
    return None

def fetch_all():
    """Autonomously fetch all remaining birds."""
    start_time = datetime.now()
    logging.info("=" * 60)
    logging.info(f"Starting FULL AUTONOMOUS FETCH at {start_time}")
    logging.info("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get total count
    cursor.execute("SELECT COUNT(*) FROM BirdCountInfo")
    total = cursor.fetchone()[0]
    
    # Get remaining count
    cursor.execute("""
        SELECT COUNT(*) FROM BirdCountInfo 
        WHERE wikipedia_intro_en IS NULL OR wikipedia_intro_en = ''
    """)
    remaining = cursor.fetchone()[0]
    
    logging.info(f"Total birds: {total}")
    logging.info(f"Already processed: {total - remaining}")
    logging.info(f"Remaining to fetch: {remaining}")
    logging.info("-" * 60)
    
    # Fetch all remaining birds (ordered by ID for predictability)
    cursor.execute("""
        SELECT id, scientific_name, english_name 
        FROM BirdCountInfo 
        WHERE wikipedia_intro_en IS NULL OR wikipedia_intro_en = ''
        ORDER BY id ASC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        logging.info("All birds already processed!")
        return

    success_count = 0
    not_found_count = 0
    
    for idx, row in enumerate(rows, 1):
        bid, sc_name, en_name = row
        
        # Try Scientific Name first
        summary = get_wiki_summary(sc_name, lang='en')
        
        # If failed, try English Name
        if not summary:
            summary = get_wiki_summary(en_name, lang='en')
        
        # Save to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if summary:
            summary = summary.strip()
            cursor.execute("UPDATE BirdCountInfo SET wikipedia_intro_en = ? WHERE id = ?", (summary, bid))
            success_count += 1
            status = "✅"
        else:
            cursor.execute("UPDATE BirdCountInfo SET wikipedia_intro_en = 'NOT_FOUND' WHERE id = ?", (bid,))
            not_found_count += 1
            status = "❌"
        
        conn.commit()
        conn.close()
        
        # Periodic progress report
        if idx % CHECKPOINT_INTERVAL == 0 or idx == len(rows):
            elapsed = datetime.now() - start_time
            rate = idx / elapsed.total_seconds() * 60 if elapsed.total_seconds() > 0 else 0
            eta_minutes = (len(rows) - idx) / rate if rate > 0 else 0
            logging.info(f"[{idx}/{len(rows)}] {status} ID {bid}: {en_name[:30]}... | Rate: {rate:.1f}/min | ETA: {eta_minutes:.0f}min")
        
        # Delay between requests
        time.sleep(DELAY)
    
    # Final report
    end_time = datetime.now()
    duration = end_time - start_time
    logging.info("=" * 60)
    logging.info(f"COMPLETED at {end_time}")
    logging.info(f"Duration: {duration}")
    logging.info(f"Success: {success_count}")
    logging.info(f"Not Found: {not_found_count}")
    logging.info("=" * 60)

if __name__ == "__main__":
    fetch_all()
