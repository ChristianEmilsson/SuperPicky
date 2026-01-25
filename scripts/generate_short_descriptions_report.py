import sqlite3

DB_PATH = 'birdid/data/bird_reference.sqlite'
OUTPUT_PATH = 'short_descriptions_report.md'

def generate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Query all birds with short descriptions
    cursor.execute("""
        SELECT id, chinese_simplified, english_name, scientific_name, short_description_zh_new, LENGTH(short_description_zh_new) as len 
        FROM BirdCountInfo 
        WHERE len < 80 
        ORDER BY id
    """)
    rows = cursor.fetchall()
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write("# Report: Bird Descriptions Under 80 Characters\n\n")
        f.write(f"**Total Count**: {len(rows)}\n\n")
        f.write("| ID | Chinese Name | English Name | Length | Current Description |\n")
        f.write("|----|--------------|--------------|--------|---------------------|\n")
        for row in rows:
            bid, cname, ename, sname, desc, length = row
            desc = desc.replace('\n', ' ').replace('|', '\\|') if desc else ""
            f.write(f"| {bid} | {cname} | {ename} | {length} | {desc} |\n")
            
    conn.close()
    print(f"✅ Generated report for {len(rows)} birds at {OUTPUT_PATH}")

if __name__ == "__main__":
    generate()
