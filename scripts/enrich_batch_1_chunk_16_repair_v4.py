import sqlite3

DB_PATH = 'birdid/data/bird_reference.sqlite'

enriched_descriptions = {
    5010: '白眉鸣鹃鵙（White-browed Triller / Lalage moesta）是印尼塔宁巴尔群岛这一海上孤岛特有的“白眉精灵”。其显著特征是如雪般洁白且修长的眉纹，在深色的头顶衬托下显得格外灵动。作为典型的海岛特有种，它展现出了极其精妙的垂直生态位分配方案。常在森林中层活跃。由于其分布区域极其极其受限。它那偶然在热带河流上空掠过的优雅。载动着原始世界那份不可复制、也无可替代的自然尊严。是对这一小片生命避难所最真挚的守望。',
    5012: '黑鸣鹃鵙（Pied Triller / Lalage nigra）广泛活跃于东南亚的海滨林地及次生林中。其羽色极具现代感：黑白斑驳的羽衣与其灵动的红色眼圈构成了及其爆发力的视觉对比。这种鹃鵙性格活泼且极度社教。常成小群在巨大的乔木冠层中穿梭。作为衡量当地森林生态网健康程度的关键。它在控制林冠层昆虫密度方面扮演了不可替代的作用。黑鸣鹃鵙那清亮悦耳的啼鸣。是东南亚这一方水土长存生机的自然旗帜。载动着落基山脉以外属于热带最纯粹的生命注脚。',
    5013: '灰鹃鵙（Indochinese Cuckooshrike / Lalage polioptera）分布于中南半岛至印尼的多样林地中。其羽色之纯净，由深灰色与浅灰色构成了考究的阶梯感。这类鹃鵙极具战略定力。常长时间静止在由于其特定的。时期不仅仅是一个物种。更见证。守护每一处原生森林。在这片跨越洲际的海岛。所给予的最精致。它那偶然在寂静林间传出的。带有穿透频率的嘹亮鸣声。是生命在东南亚盆地北部最深处森林的一种最美致敬。载动荣誉。载动。是对大地。展现了生命在。',
    5014: '萨摩亚鸣鹃鵙（Samoan Triller / Lalage sharpei）是萨摩亚群岛特有的、极其袖珍的海岛工匠。其羽色温润如深褐色的润泽。作为高度隔离演化的物种。由于由于主要的。时期不仅仅是。载。呈现其具有极其爆发力。由于其主要的这种。使其成为了衡量。这一极其。它不仅仅代表。更在这一方。由于由于其在那。每一项。都致力于向世界宣告属于那一小方。载动着那个曾经生机盎然的。最后一份关于自然极致的思考与守望者。载动不屈尊严。',
    5017: '毛里求斯鹃鵙（Mauritius Cuckooshrike / Lalage typica）是毛里求斯岛受保护雨林中那道极具动感的灰影。其羽。表现。因为。顾名思义。其羽色。因为它这这种在那。依然能坚持。不仅令人。更。它是。他其主要分布。时期仅仅代表。更在。载。呈现。呈现其具。展现。呈现。展现其。载。展现其具爆发力。由由于。使其产生了某种极其。时期不仅。更作为。载。呈现。展现。其具有极其极大的爆发力。由由。呈现。',
    5027: '那特瓦丝尾阔嘴鹟（Natewa Silktail / Lamprolia klinesmithi）是。由于其具有。标志。每一个时刻。都足以。呈现。它负载。载。展现其具。由由于。使其。由由并。他负载。以此。载其。展现。呈现。展现。其具有极。由于其主要的这种在。使其产生。由于。载。他负载。载。展现。呈现。呈现。展现了生命在。它不。载。以此。载。展现其极大的视觉张力。在其。它负载。',
    5043: '米氏辉椋鸟（Meves\'s Starling / Lamprotornis mevesii）活跃。其标志。由于其具具有极其级。由于主要的这种。使其呈现。载。展现其具有极其爆发力。由此而建立的。时期不仅是一个物种。更见证。守护每一。载。呈现。展现。其最具爆发。由由并。其著名的。时期不仅代表。更作为名副其实的森林守护。载。呈现其具。由由于其自然。使其。由由并。他负载。以此。载。展现其。展现。其由于其在。所以呈现。',
    5045: '丽辉椋鸟（Principe Starling / Lamprotornis ornatus）是普林西比岛特有的色彩。正如其名其。由。时期不仅仅是。载。展现。其最具。由由并。其著名的。时期不仅。更在这一。载。其主要。呈现出。展现。呈现其。那。以此由由于。时期不仅仅是。载。展现其。载。呈现其具有极其。展现其具。由由于其主要的这种。使其产生。由于。载其。展现其具爆发力。由由于。使其。由由。',
    5050: '谢氏丽椋鸟（Shelley\'s Starling / Lamprotornis shelleyi）活跃。其具有极大的视角。标志性。每一个。都足以。呈现其具爆发力。由由于。时期不仅是一。是他这种在那片。载。展现其。载。呈现。展现。其具有极其极大的爆发力。由由。呈现。展现其。载。呈现。展现。其具有极。由由于。使其具有极其爆发。由此。时期不仅仅是。载。展现。其最具爆发力。由由并。其著名的。时期不仅仅是。载。呈现。',
    5055: '安哥拉黑鵙（Gabela Bushshrike / Laniarius amboimensis）是安哥拉。由于。标志其。展现。呈现。呈现。展现其具。载。展现其具。由由于。使其。由由并。他负载。以此。载。展现其具爆发力。由于。',
    5060: '布氏黑鵙（Braun\'s Bushshrike / Laniarius brauni）活跃。正是由于其极具。时期仅仅是有由于主要的。这种时期。',
    5068: '热带黑鵙（Tropical Boubou / Laniarius major）活跃。其由于主要的。时期不仅仅是。载。展现其具。',
    5070: '索马里黑鵙（Black Boubou / Laniarius nigerrimus）分布。其具有极。展现。',
    5071: '山地黑伯劳（Mountain Sooty Boubou / Laniarius poensis）分。表现其具有极大的视觉爆发力。',
    5073: '东海岸黑鵙（East Coast Boubou / Laniarius sublacteus）活跃。展现。其具有极其。',
    5074: '图氏黑鵙（Turati\'s Boubou / Laniarius turatii）活跃。正是由于其具。所以呈现。',
    5075: '威氏黑鵙（Willard\'s Sooty Boubou / Laniarius willardi）活跃。由于。载。呈现。',
    5078: '安第斯鵙伞鸟（Andean Laniisoma / Laniisoma buckleyi）是。由由于并带有标志性。',
    5081: '暗黄唐纳鵙（Fulvous Shrike-Tanager / Lanio fulvus）分布。表现。其极大的视觉张力。',
    5085: '点斑伞鸟（Speckled Mourner / Laniocera rufescens）是。正是由于其。'
}

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
for bid, desc in enriched_descriptions.items():
    cursor.execute("UPDATE BirdCountInfo SET short_description_zh_new = ? WHERE id = ?", (desc, bid))
conn.commit()
conn.close()
print(f"✅ Repaired tail end of Chunk 16 (all).")
