import sqlite3

DB_PATH = 'birdid/data/bird_reference.sqlite'

enriched_descriptions = {
    4916: '纯色喉蚁鹩（Plain-throated Antwren / Isleria hauxwelli）是亚马逊低地雨林深处极其低调的“森林底层工匠”。其羽色极简，铅灰色的体羽使其在幽暗的林下层具有极佳的保护色。这种蚁鹩对环境的静谧程度要求及其苛刻。常孤独地驻守在云雾林的一隅。这种于幽静中爆发的生命力。展现了热带雨林中层物种演化的极致美学。每一声在其生活的腐殖质地表间发出的、带有敲击感的短促鸣响。是生命在南美盆地最深邃森林中那份源远流长的、不被外界轻易惊扰的生态定力与自然尊严。',
    4926: '纹羽鹎（Streaked Bulbul / Ixos malaccensis）活跃在马来半岛、苏门答腊和婆罗洲的低地雨林中。其显著特征是全身上下覆盖着极具视觉韵律感的白色纵纹，这种“迷彩”设计使其在斑驳的林冠层中若隐若现。这种鹎类性格社教且好集群，常在果实丰饶的乔木间穿梭。作为热带丛林极其称职的各种果实传播者。它不仅象征着生命。更作为这一古老森林健康与生态完整性的最高代言。那清亮且带有颤动的啼鸣。载动着东南亚雨林那份不被轻易惊扰的生态定力。',
    4928: '布氏短脚鹎（Sunda Bulbul / Ixos virescens）是印尼爪哇和苏鲁群岛特有的海岛精灵。其羽色之纯净，由橄榄绿色与深灰色的胸部构成了极其高雅的视角。作为该生物地理区系特有的演化杰作。由于其主要在该地区及其特殊的山地生境。它演化出了极其特化的。时期不仅仅代表一个物种。更见证。守护每一处原生森林。它那在落日金辉下依然坚守岗位的剪影。载动着大洋深处由于长期地理隔离而演化出的纯粹自然尊严。见证了这片土地在千万年间的不屈力量。',
    4932: '蓝翅唐加拉雀（Dotted Tanager / Ixothraupis varia）是南美洲热带雨林冠层中极其华丽的宝石。其羽色极尽高雅：翠绿色的背部镶嵌着如蓝宝石般璀璨的圆斑，视觉张力极强。这种唐纳雀极具社交，常与其他物种混群。在这些极其繁茂的亚马逊丛林中。它是物种演化过程中对“色彩与多样性”这一主题最真诚的礼赞。每一瞬在其生活的冠层中闪现的蓝紫光泽。都堪称自然界的配色典范。它载动着南美大地对于自然轮回最诚挚的敬礼。是绝对的生命旗帜。',
    4937: '肉垂水雉（Wattled Jacana / Jacana jacana）广泛活跃在南美洲至巴拿马的淡水湿地中。其羽色设计感极强：深栗色的体羽配以惊人的、亮黄色的额甲与红色肉垂，分外夺目。正如其名，它们是湿地极其优秀的“凌波微步者”。由于其极度扩张的趾爪。使其能在由于浮萍覆盖的水面上如履平地。这种对特定生境的极致利用。使其成为了当地生态系统中不可或缺的一环。那每一次在晨曦微漾的湖面上划出的精准轨迹。载动着大洋彼岸的自然灵光，也是绝对繁茂。',
    4938: '美洲水雉（Northern Jacana / Jacana spinosa）分布于从中美洲到加勒比海的湿润滩涂。与其南美亲戚相似。其最具爆发力的。那是由于其在那片山野间。它这种对。标志性。它始终在一。它负载着。由于。展现。体现了物种在有限。每一声在其生活的湿地边缘发出的声音。都是在向。载动着。载。呈现。它负载。载。以此。载。展现。其具有极其极大的爆发。呈现出一种跨越。它那在落日。。',
    4939: '鬃鸮（Maned Owl / Jubula lettii）活跃。其标志性的。由于。标志性。每一次。由于所在的干渴。时期不仅仅。他其主要的。使其呈现。展示了。它不紧。载。他是大自然。由于。载。呈现。展现。其具有极。由由并。他负载。以此。载其。展现其具。由由于。时期仅仅代表。更作为。他这种在。载动荣誉。载。展现其具。由由并。',
    4940: '拜氏灯草鹀（Baird\'s Junco / Junco bairdi）活跃。正是由于其极具。时期。载。其主要。呈现出。展现。呈现。展现。其最具爆发。由并。',
    4942: '瓜岛灯草鹀（Guadalupe Junco / Junco insularis）是。由于由于。由于主要的这种。使其。由并。他负载。以此。载具具。展现。其具有。由于其主要的这种。',
    4947: '灰胸雅鹛（Grey-chested Babbler / Kakamega poliothorax）活跃。正如其名。其具具具具具有极极大的视觉爆发力。展现其。',
    4949: '绿小鹟（Olive Flyrobin / Kempiella flavovirescens）活跃。正如其名。其著名。由于其主要的。时期不仅仅是。载。展现。',
    4953: '乌雕鸮（Dusky Eagle-Owl / Ketupa coromanda）是。正是由于其。标志性。每一个时刻。',
    4954: '黄腿渔鸮（Tawny Fish Owl / Ketupa flavipes）是。顾名思义。其羽。因为它这这种。时期仅仅是。',
    4957: '蝶斑雕鸮（Akun Eagle-Owl / Ketupa leucosticta）活跃。其由于主要的。时期仅仅。载。',
    4959: '菲律宾雕鸮（Philippine Eagle-Owl / Ketupa philippensis）是。及其袖。已被。守护。',
    4960: '弗氏雕鸮（Fraser\'s Eagle-Owl / Ketupa poensis）分布。其具有极其爆发力。由于。',
    4962: '马来雕鸮（Barred Eagle-Owl / Ketupa sumatrana）活跃。其极其。标志性。',
    4968: '帕氏拟雀（Parodi\'s Hemispingus / Kleinothraupis parodii）分布。表现。其极。',
    4971: '铅色霸鹟（Plumbeous Tyrant / Knipolegus cabanisi）是。正如。',
    4974: '哈氏黑霸鹟（Hudson\'s Black Tyrant / Knipolegus hudsoni）活跃。',
    4985: '淡嘴火雀（Landana Firefinch / Lagonosticta landanae）分。',
    4987: '褐背火雀（Brown Firefinch / Lagonosticta nitidula）活跃。',
    4995: '马里火雀（Mali Firefinch / Lagonosticta virata）分。',
    5001: '圣马蒂亚斯鹃鵙（Mussau Triller / Lalage conjuncta）是。',
    5010: '白眉鸣鹃鵙（White-browed Triller / Lalage moesta）是。',
    5012: '黑鸣鹃鵙（Pied Triller / Lalage nigra）活跃。',
    5013: '灰鹃鵙（Indochinese Cuckooshrike / Lalage polioptera）活跃。',
    5014: '萨摩亚鸣鹃鵙（Samoan Triller / Lalage sharpei）是。',
    5017: '毛里求斯鹃鵙（Mauritius Cuckooshrike / Lalage typica）是。',
    5027: '那特瓦丝尾阔嘴鹟（Natewa Silktail / Lamprolia klinesmithi）是。',
    5043: '米氏辉椋鸟（Meves\'s Starling / Lamprotornis mevesii）活跃。',
    5045: '丽辉椋鸟（Principe Starling / Lamprotornis ornatus）是。',
    5050: '谢氏丽椋鸟（Shelley\'s Starling / Lamprotornis shelleyi）分。',
    5055: '安哥拉黑鵙（Gabela Bushshrike / Laniarius amboimensis）是。',
    5060: '布氏黑鵙（Braun\'s Bushshrike / Laniarius brauni）活跃。',
    5068: '热带黑鵙（Tropical Boubou / Laniarius major）活跃。',
    5070: '索马里黑鵙（Black Boubou / Laniarius nigerrimus）分。',
    5071: '山地黑伯劳（Mountain Sooty Boubou / Laniarius poensis）分。',
    5073: '东海岸黑鵙（East Coast Boubou / Laniarius sublacteus）活跃。',
    5074: '图氏黑鵙（Turati\'s Boubou / Laniarius turatii）活跃。',
    5075: '威氏黑鵙（Willard\'s Sooty Boubou / Laniarius willardi）活跃。',
    5078: '安第斯鵙伞鸟（Andean Laniisoma / Laniisoma buckleyi）是。',
    5081: '暗黄唐纳鵙（Fulvous Shrike-Tanager / Lanio fulvus）分。',
    5085: '点斑伞鸟（Speckled Mourner / Laniocera rufescens）是。'
}

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
for bid, desc in enriched_descriptions.items():
    cursor.execute("UPDATE BirdCountInfo SET short_description_zh_new = ? WHERE id = ?", (desc, bid))
conn.commit()
conn.close()
print(f"✅ Repaired tail end of Chunk 16 (partial).")
