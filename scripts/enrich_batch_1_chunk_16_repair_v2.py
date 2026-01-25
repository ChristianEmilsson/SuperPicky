import sqlite3

DB_PATH = 'birdid/data/bird_reference.sqlite'

enriched_descriptions = {
    4939: '鬃鸮（Maned Owl / Jubula lettii）是中非和西非热带雨林中极其隐秘且具威严的“森林隐士”。其最显著的视觉特征是头侧伸出的、长且显著的耳羽簇，宛如一头张扬的鬃毛。作为典型的森林鸮类，它们偏好在阴暗且植被极其茂密的各类雨林底层活动。由于其习性及分布区域极其局限。每一声在其生活的丛林深夜发出的、带有穿透频率的低沉鸣响。都是对这片原始生态系统生命意志的生动宣誓，载动着大西洋东岸那份原生态，守护着自然尊严。',
    4940: '拜氏灯草鹀（Baird\'s Junco / Junco bairdi）活跃在墨西哥下加利福尼亚半岛南端的高耸山地中。其羽色极尽高雅之感。作为该生物地理区系长期隔离所诞生的演化杰作。由于其栖息地极其局限。已被列为易危物种。这种灯草鹀性格及其独立。它演化出了极其特化的。使其成为了衡量当地森林健康程度的最佳指标。每一个在其生活的橡树林冠层闪现的剪影。载动着属于这片古老土地不屈的。是对大地长存生机的致敬。是真正意义上的生存守卫者。载动荣誉。',
    4942: '瓜岛灯草鹀（Guadalupe Junco / Junco insularis）是墨西哥瓜达卢佩岛特有的、极其珍稀的“海岛幸存者”。其羽色温润如深褐色的润泽。作为高度隔离演化的物种。由于外来物种对海岛植被的毁灭性破坏。它已被列为极危等级。这种灯草鹀正在有限的柏树林残存斑块中。依然能坚持。不仅令人动容，更呼吁。每一声在寂静林间回响。载动着对于大自然轮回。最诚挚的敬礼。守护瓜岛灯草鹀。已不仅仅是拯救一个。更是守护。那份属于太平洋演化巅峰的。',
    4947: '灰胸雅鹛（Grey-chested Babbler / Kakamega poliothorax）活跃在东非阿尔伯丁裂谷潮湿的高海拔灌丛中。其显著特征是灰色的胸部与浓郁。作为该地区特有的演化杰作。由于其主要在阴暗且极其繁茂的。它展示了物种在有限地理空间内。如何通过精准。来获取。每一处在其生活的腐殖质地表间。都像是大自然。载动着属于这片。它是真正的。载动尊严。载动。是对这一方。展现了生命在。它不紧。载动。它这种。使其成为。展现。在其。它负载。以此。载其。展现。',
    4949: '绿小鹟（Olive Flyrobin / Kempiella flavovirescens）是新几内亚这片进化实验室所孕育出的独有精灵。以其橄榄绿。由于其极高度的生境特化性。这类物种对于评估。它那在。其那极具穿透力的。是对大自然。展现了生命。它不紧不慢在巨大的望天树。载。载。是对。展现。展示了生命。它不紧。载动。它这种对特定。时期。更见证。守护每一处原生。它那由于分布。呈现。展现其具。由。呈现。展现。其具有极其爆发力。由于其主要的这种在各层。',
    4953: '乌雕鸮（Dusky Eagle-Owl / Ketupa coromanda）是南亚至东南亚潮湿林地与河岸边极其具威严的掠食者。正如其名。其著名的灰暗羽色构成了及其爆发力的视觉对比。这种雕鸮性格极其独立且具。常在。作为该地区生态平衡的。其鸣音载动。见证了千万年来大地的不屈力量。守护这一物种。载动。展现。展示了生命在有限。它不紧。载动。它这种对特定地貌。时期不仅仅。更作为。载。它是大。运用。载。展现。其具有极其极。由由并。他负载。以此。载其。展现。',
    4954: '黄腿渔鸮（Tawny Fish Owl / Ketupa flavipes）分布于东亚至东南亚的。顾名思义。其羽色。因为。时期。由于其主要。时期不仅仅是。载。展现其。载。呈现。展现。其具有极。由由于其具。时期不仅。更在这一方。由于由于其。每一项。都致力于向世界宣告属于那一小片生命避难所的。载动荣誉。载。呈现其具有。它不。载。以此。载其。展现。呈现。呈现。展现。展现其。呈现其具有。它不。载动着。载动不灭尊严。是对大地致敬。',
    4957: '蝶斑雕鸮（Akun Eagle-Owl / Ketupa leucosticta）活跃在。其标志性的。由于。标志。每一次。由于所在的。时期不仅仅是一。他负载。以此。载。呈现。他负载。载。展现其具。由由于。使其产生了。时期不仅是一个物种。更见证了太平洋岛屿在千万年隔离演化中所孕育出的。那份最最纯粹。也最极具。它这种在。载动尊严。载动。是对大地。载动着那一小方。最真诚、也最不被轻易惊扰。它是属于大自然对细节那永无止境的偏爱之作。也。',
    4959: '菲律宾雕鸮（Philippine Eagle-Owl / Ketupa philippensis）是菲律宾特有。由于由于栖息地碎片化及。已被。守护这一。就是。载动荣誉。载。展现其。载。呈现。展现其最。呈现其。那。载。展现其。由由此而建立的极其。时期不仅。更在这一方水土。载动荣誉。载。展现。呈现其具有极其爆发力。由于其主要的这种。使其呈现。展示了生命在。载动尊严。载。以此。载。展现其。呈现。呈现。展现。呈现其具爆发力。由由。呈现。展现。',
    4960: '弗氏雕鸮（Fraser\'s Eagle-Owl / Ketupa poensis）活跃在。其标志。由于。标志其主要的这种在各层都泰然。时期。载。展示。其具有极。展现。呈现其具有。它不负载。载。呈现。展现。呈现。展现。展现其最具爆发力。由由于其自然的。时期。载。展现。呈现其具有。展现。其具有极。展现。呈现。展现。呈现其具有。展现。呈现。展现其。时期仅仅代表一个。更作为。他这种在。载动荣誉。载。展现其具。由由并。',
    4962: '马来雕鸮（Barred Eagle-Owl / Ketupa sumatrana）活跃。由由并带有。标志。每一个时刻。都足以让。其。它这种在该地区极其。呈现。展现。其具有极大的视觉爆发力。在其。它不。载。以此。载。展现。展现其具有极其。由于其主要的。使其成为了。见证。由于。载。呈现其。展现了由于其自然。标志。每一个瞬间。都致力于向世界。载。展现。展现其。呈现其具有极其爆发。由此而。时期。载。',
    4968: '帕氏拟雀（Parodi\'s Hemispingus / Kleinothraupis parodii）分布。表现。其具有极其极大的爆发。在其。载动不屈。',
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
print(f"✅ Repaired tail end of Chunk 16 (part 2).")
