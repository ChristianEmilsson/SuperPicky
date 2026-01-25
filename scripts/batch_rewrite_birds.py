import sqlite3
import os
import time
import requests
import json
from datetime import datetime

# 配置
DB_PATH = "birdid/data/bird_reference.sqlite"
API_KEY = os.getenv("GOOGLE_API_KEY", "")
MODEL = "gemini-2.0-flash"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
BATCH_SIZE = 50

def get_pending_birds(limit: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, chinese_simplified, english_name, scientific_name 
        FROM BirdCountInfo 
        WHERE short_description_zh_new IS NULL 
        ORDER BY id
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def generate_description(bird):
    bid, cn, en, sn = bird
    prompt = f"""你是一个鸟类学专家。请为以下鸟类撰写一段100-150字的中文简介：

鸟类信息：
- 中文名：{cn}
- 英文名：{en}  
- 学名：{sn}

要求：
1. **重点包含精确的分布区域信息**（必须说明原产地、迁徙范围或主要栖息国家/大陆）
2. 包含分类信息（目、科）
3. 描述外观特征（体型、羽色）
4. 提及栖息环境或习性
5. 使用原创表述，不要复制任何现有文本
6. 语言简洁专业，适合鸟类摄影爱好者阅读

直接输出描述内容，不要有其他文字。"""

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if 'candidates' in data and data['candidates']:
                return data['candidates'][0]['content']['parts'][0]['text'].strip()
        print(f"Error {response.status_code} for {cn}: {response.text}")
        return None
    except Exception as e:
        print(f"Request failed for {cn}: {e}")
        return None

def update_db(bird_id, new_desc):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE BirdCountInfo SET short_description_zh_new = ? WHERE id = ?", (new_desc, bird_id))
    conn.commit()
    conn.close()

def run_batch():
    birds = get_pending_birds(BATCH_SIZE)
    if not birds:
        print("所有数据已处理完毕。")
        return False
    
    print(f"开始处理批次：预计 {len(birds)} 条记录...")
    success_count = 0
    for bird in birds:
        new_desc = generate_description(bird)
        if new_desc:
            update_db(bird[0], new_desc)
            success_count += 1
            if success_count % 10 == 0:
                print(f"  已完成 {success_count}/{len(birds)}")
        else:
            print(f"  跳过 {bird[1]} (API错误)")
        
        # 避免触发频率限制
        time.sleep(1) 
        
    print(f"批次完成: 成功 {success_count} 条。时间: {datetime.now().strftime('%H:%M:%S')}")
    return True

if __name__ == "__main__":
    if not API_KEY:
        print("错误: 请设置环境变量 GOOGLE_API_KEY")
        exit(1)
        
    # 一次只运行一个批次，由外部控制循环或手动执行
    run_batch()
