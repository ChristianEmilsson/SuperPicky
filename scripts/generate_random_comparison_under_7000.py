import sqlite3
import random

DB_PATH = 'birdid/data/bird_reference.sqlite'
OUTPUT_FILE = '/Users/jameszhenyu/.gemini/antigravity/brain/07f555b8-c1a4-4862-a6a1-4e683f854112/comparison_samples_under_7000.md'

def generate_comparison():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        query = """
        SELECT id, chinese_simplified, english_name, scientific_name, short_description_zh, short_description_zh_new 
        FROM BirdCountInfo 
        WHERE id < 7000 
          AND short_description_zh_new IS NOT NULL 
          AND short_description_zh_new != ''
        ORDER BY RANDOM() 
        LIMIT 20;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            print("No repaired descriptions found for IDs < 7000.")
            return

        md_content = "# 🐦 随机抽样对比报告 (IDs < 7000)\n\n"
        md_content += "以下随机抽取的 20 个样本展示了从 ID 1 到 7000 之间（实际主要是 Batch R1-R6）的修复效果。\n\n"
        md_content += "| ID | 中文名 | 英文名 | 原始描述 (Old) | 修复后描述 (New) | 字数 (New) |\n"
        md_content += "|---|---|---|---|---|---|\n"

        for row in rows:
            bid, ch_name, en_name, sc_name, old_desc, new_desc = row
            old_desc_str = old_desc if old_desc else "*(空)*"
            # Clean up newlines for table format
            old_desc_str = old_desc_str.replace('\n', '<br>')
            new_desc_str = new_desc.replace('\n', '<br>')
            
            md_content += f"| {bid} | {ch_name} | {en_name} | {old_desc_str} | {new_desc_str} | {len(new_desc)} |\n"

        with open(OUTPUT_FILE, 'w') as f:
            f.write(md_content)
        
        print(f"Comparison report generated at: {OUTPUT_FILE}")
        print(md_content)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    generate_comparison()
