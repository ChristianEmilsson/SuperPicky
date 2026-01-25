import sqlite3
import time
import random
import requests
import logging

# Configuration
DB_PATH = 'birdid/data/bird_reference.sqlite'
LOG_FILE = 'wiki_fetch_en.log'
BATCH_SIZE = 200
DELAY_MIN = 2.0
DELAY_MAX = 2.2  # Slight jitter around 2 seconds

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
    """
    Fetches the summary of a Wikipedia page.
    Uses English Wikipedia by default as per new strategy.
    """
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
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError:
            logging.error(f"JSON Decode Error for {query}. Response status: {response.status_code}. Response text: {response.text[:200]}")
            return None
            
        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            if page_id == "-1":
                return None  # Not found
            
            summary = page_data.get("extract", "")
            return summary
            
    except Exception as e:
        logging.error(f"Error fetching {query}: {e}")
        return None

def fetch_and_update(limit=BATCH_SIZE):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Select birds that don't have an ENGLISH wiki intro yet
    cursor.execute("""
        SELECT id, scientific_name, english_name 
        FROM BirdCountInfo 
        WHERE wikipedia_intro_en IS NULL OR wikipedia_intro_en = ''
        ORDER BY id ASC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    
    if not rows:
        logging.info("No birds found needing English Wikipedia update.")
        conn.close()
        return

    logging.info(f"Starting batch of {len(rows)} birds (Source: English Wikipedia).")
    
    success_count = 0
    
    for row in rows:
        bid, sc_name, en_name = row
        logging.info(f"Processing ID {bid}: {en_name} ({sc_name})")
        
        # Try Scientific Name first (most accurate on EN Wiki)
        summary = get_wiki_summary(sc_name, lang='en')
        
        # If failed, try English Name
        if not summary:
            logging.info(f"  Scientific name match failed, trying English name: {en_name}")
            summary = get_wiki_summary(en_name, lang='en')
            
        if summary:
            summary = summary.strip()
            # Save to wikipedia_intro_en
            cursor.execute("UPDATE BirdCountInfo SET wikipedia_intro_en = ? WHERE id = ?", (summary, bid))
            conn.commit()
            success_count += 1
            logging.info(f"  ✅ Found English summary ({len(summary)} chars). Saved.")
        else:
            logging.warning(f"  ❌ No English Wikipedia entry found for {sc_name} / {en_name}")
            # Mark NOT_FOUND so we don't retry immediately
            cursor.execute("UPDATE BirdCountInfo SET wikipedia_intro_en = 'NOT_FOUND' WHERE id = ?", (bid,))
            conn.commit()

        # Sleep to be polite to Wikipedia API
        sleep_time = random.uniform(DELAY_MIN, DELAY_MAX)
        logging.info(f"  Sleeping for {sleep_time:.2f}s...")
        time.sleep(sleep_time)

    conn.close()
    logging.info(f"Batch complete. Updated {success_count}/{len(rows)} birds.")

def fetch_random_test(count=20):
    """Fetches a random set of birds for testing purposes."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Select random birds for test
    cursor.execute("""
        SELECT id, scientific_name, english_name 
        FROM BirdCountInfo 
        WHERE wikipedia_intro_en IS NULL OR wikipedia_intro_en = ''
        ORDER BY RANDOM()
        LIMIT ?
    """, (count,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("No birds found for testing.")
        return

    print(f"\n🧪 Starting RANDOM TEST of {len(rows)} birds...")
    print(f"   (Saving to DB: Yes, Delay: {DELAY_MIN}-{DELAY_MAX}s)\n")
    
    for row in rows:
        bid, sc_name, en_name = row
        print(f"Processing ID {bid}: {en_name} ({sc_name})")
        
        summary = get_wiki_summary(sc_name, lang='en')
        if not summary:
            print(f"  Scientific name failed, trying: {en_name}")
            summary = get_wiki_summary(en_name, lang='en')
            
        conn = sqlite3.connect(DB_PATH) 
        cursor = conn.cursor()
            
        if summary:
            summary = summary.strip()
            cursor.execute("UPDATE BirdCountInfo SET wikipedia_intro_en = ? WHERE id = ?", (summary, bid))
            conn.commit()
            # Print first 100 chars
            preview = summary[:100].replace('\n', ' ')
            print(f"  ✅ Found: \"{preview}...\" ({len(summary)} chars)")
        else:
            print(f"  ❌ Not Found")
            cursor.execute("UPDATE BirdCountInfo SET wikipedia_intro_en = 'NOT_FOUND' WHERE id = ?", (bid,))
            conn.commit()
        conn.close()

        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    print("\n✅ Random test complete.")

def print_progress():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM BirdCountInfo")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM BirdCountInfo WHERE wikipedia_intro_en IS NOT NULL AND wikipedia_intro_en != 'NOT_FOUND'")
    fetched = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM BirdCountInfo WHERE wikipedia_intro_en = 'NOT_FOUND'")
    not_found = cursor.fetchone()[0]
    
    remaining = total - fetched - not_found
    
    print(f"\n📊 English Extraction Progress:")
    print(f"  Total Birds: {total}")
    print(f"  ✅ Fetched (EN): {fetched} ({(fetched/total)*100:.1f}%)")
    print(f"  ❌ Not Found:    {not_found} ({(not_found/total)*100:.1f}%)")
    print(f"  ⏳ Remaining:    {remaining} ({(remaining/total)*100:.1f}%)")
    print("-" * 30 + "\n")
    
    conn.close()

if __name__ == "__main__":
    print_progress()
    fetch_and_update(limit=BATCH_SIZE)
    print_progress()
    
    # UNCOMMENT TO RUN RANDOM TEST
    # fetch_random_test(count=20)
