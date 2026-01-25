import sqlite3

DB_PATH = 'birdid/data/bird_reference.sqlite'
ids = [46, 617, 742, 1336, 3153, 3740, 4219, 4299, 5059, 6062, 6181, 6187, 6784, 8143, 8612, 8684, 9862, 10171, 10465, 10472]

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

query = f"SELECT id, chinese_simplified, english_name, scientific_name, short_description_zh, short_description_zh_new FROM BirdCountInfo WHERE id IN ({','.join(map(str, ids))})"
cursor.execute(query)
rows = cursor.fetchall()

md_content = "# 鸟类描述随机抽样对比 (20例)\n\n"
md_content += "| ID | 鸟种名称 (中/英/学) | 修改前 (旧描述) | 修改后 (新描述 - 高质量原创) |\n"
md_content += "| :--- | :--- | :--- | :--- |\n"

for row in rows:
    bid, cn, en, sn, old_desc, new_desc = row
    names = f"**{cn}**<br>*{en}*<br>`{sn}`"
    # Clean up descriptions for table display
    old_desc = old_desc.replace('\n', ' ').strip() if old_desc else "无"
    new_desc = new_desc.replace('\n', ' ').strip() if new_desc else "待处理"
    md_content += f"| {bid} | {names} | {old_desc} | {new_desc} |\n"

with open('comparison_20_random.md', 'w') as f:
    f.write(md_content)

conn.close()
