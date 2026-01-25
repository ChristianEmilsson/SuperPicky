import sqlite3

DB_PATH = 'birdid/data/bird_reference.sqlite'
OUTPUT_PATH = 'comparison_50_random.md'

def generate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Select 50 random birds that have both descriptions
    cursor.execute("""
        SELECT id, chinese_simplified, short_description_zh, short_description_zh_new 
        FROM BirdCountInfo 
        WHERE short_description_zh IS NOT NULL AND short_description_zh_new IS NOT NULL
        ORDER BY RANDOM() 
        LIMIT 50
    """)
    rows = cursor.fetchall()
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write("# 50 Random Bird Description Comparisons\n\n")
        f.write("| ID | Name | Original Description (short_description_zh) | Enriched Description (short_description_zh_new) |\n")
        f.write("|----|------|------------------------------------------|-----------------------------------------------|\n")
        for row in rows:
            bid, name, old_desc, new_desc = row
            # Clean up descriptions for markdown table (escape newlines or pipes if any)
            old_desc = old_desc.replace('\n', ' ').replace('|', '\\|') if old_desc else ""
            new_desc = new_desc.replace('\n', ' ').replace('|', '\\|') if new_desc else ""
            f.write(f"| {bid} | {name} | {old_desc} | {new_desc} |\n")
            
    conn.close()
    print(f"✅ Generated comparison table for 50 random birds at {OUTPUT_PATH}")

if __name__ == "__main__":
    generate()
