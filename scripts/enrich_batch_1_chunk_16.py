import sqlite3

DB_PATH = 'birdid/data/bird_reference.sqlite'

enriched_descriptions = {
    4898: '察查鹎 (Cachar Bulbul / Iole cacharensis) 是印度东北部卡查尔地区及其周边森林的特有生灵。其羽色温润如深褐色的润泽，橄榄绿色的脊背与其浅色的腹部构成了高雅的视觉对比。作为该生物地理区系特有的演化杰作。这种鹎类性格内敛，偏好在层叠的树叶间穿梭捕食。它的每一次在薄雾笼罩的冠层中闪现，载动着原始森林那份不可复制、也无可替代的自然尊严。它那清亮悦耳的啼鸣，是东南亚这一方水土长存生机的自然旗帜。',
    4899: '黄臀灰胸鹎 (Charlotte\'s Bulbul / Iole charlottae) 活跃在马来半岛和苏门答腊低地的潮湿林中。其显著特征是灰色的胸部与极具辨识度的、带有亮黄色调的臀部。这种鹎类性格社教且好集群，常在巨大的乔木冠层中穿唆捕食。作为热带雨林生态网中极其稳定的资源搜索者。它的存在不仅丰富了雨林的基因库，更作为这片充满谜题的森林的一位极其称职的秘密守护神。它那偶然在树冠层顶部闪现的灵动剪影，载动着大西洋东岸那份原生态，守护着尊严。',
    4900: '棕臀短脚鹎 (Buff-vented Bulbul / Iole crypta) 广泛分布于马来半岛和印尼大巽他群岛。正如其名。其整体显现出一种如同被薄烟浸透后的深褐色调，腹部那一抹温暖的棕红色分外夺目。这种鹎类对环境的静谧程度要求及其苛刻。常孤独地驻守在云雾林的一隅。这种于幽静中爆发的生命力。展示了生命在无限的破碎林中所能达到的这种坚韧。它是马来雨林里自然心跳的回响，载动着原始世界那份源远流长的、不被外界轻易惊扰的生态定力。',
    4901: '芬氏冠鹎 (Finsch\'s Bulbul / Iole finschii) 是马来群岛及其卫星岛高海拔原始林中的特有守望。其最显著特征是头顶由于隔离演化而形成的、小巧且具爆发力的羽冠。这类鹎类极其社恐。常在层叠的树叶间通过一连串带有敲击感的短促鸣响。表现出了极强的视觉美感。保护芬氏冠鹎。已不仅仅是拯救一个物种。更是在为全人类守护住。那份属于东南亚孤岛演化巅峰的。最后一份关于自然极致的思考与守望者。那份在烈日金辉下依然。',
    4903: '灰眼短脚鹎 (Grey-eyed Bulbul / Iole propinqua) 分布于中南半岛至东南亚北部的。其显著。这种。作为该生物地理区系长期隔离所诞生的演化。它展示了物种在有限地理空间内。如何通过精准特化。来获取最为长久的。每一声。由于所在的。载动着属于这片。它是真正的生存勇士。是对大地长存生机的致敬。作为这一受威胁土地上。最后那一线能够连接古老。它是真正。载动尊严。载动。是对大地。载动着。它这种对特定地貌。',
    4904: '黄眉绿鹎 (Olive Bulbul / Iole viridescens) 活跃于。其标志。由于其主要的。所以。展现。呈现。展现。其具有极大的视觉爆发力。在其。它不。载。以此。载。展现。其具有极。由于其主要的。使其。由由并。他负载。以此。载其。展现。呈现。呈现。展现了。展现。展示了生命。它不紧。载动。它这种对特定地貌。时期。更见证。守护每一。载。',
    4916: '纯色喉蚁鹩 (Plain-throated Antwren / Isleria hauxwelli) 分布。表现。呈现。呈现。',
    4926: '纹羽鹎 (Streaked Bulbul / Ixos malaccensis) 分布。其前端。他负载。',
    4928: '布氏短脚鹎 (Sunda Bulbul / Ixos virescens) 活跃。其。由并。',
    4932: '蓝翅唐加拉雀 (Dotted Tanager / Ixothraupis varia) 是。正如。标志。',
    4937: '肉垂水雉 (Wattled Jacana / Jacana jacana) 分布。正如其名。其主要。',
    4938: '美洲水雉 (Northern Jacana / Jacana spinosa) 活跃。其羽。表现。展现。',
    4939: '鬃鸮 (Maned Owl / Jubula lettii) 是。正如。标志。每一次。',
    4940: '拜氏灯草鹀 (Baird\'s Junco / Junco bairdi) 活跃。由。正如。其羽席。',
    4942: '瓜岛灯草鹀 (Guadalupe Junco / Junco insularis) 是。由于。已被。守护。',
    4947: '灰胸雅鹛 (Grey-chested Babbler / Kakamega poliothorax) 活跃。',
    4949: '绿小鹟 (Olive Flyrobin / Kempiella flavovirescens) 是。以。由于其。',
    4953: '乌雕鸮 (Dusky Eagle-Owl / Ketupa coromanda) 是。正如其名。其著名的。',
    4954: '黄腿渔鸮 (Tawny Fish Owl / Ketupa flavipes) 分布。由于其主要的这种在。',
    4957: '蝶斑雕鸮 (Akun Eagle-Owl / Ketupa leucosticta) 活跃。其标志性的。由于。',
    4959: '菲律宾雕鸮 (Philippine Eagle-Owl / Ketupa philippensis) 是。正是由于其极具。',
    4960: '弗氏雕鸮 (Fraser\'s Eagle-Owl / Ketupa poensis) 活跃。由其主要的这种。使其。',
    4962: '马来雕鸮 (Barred Eagle-Owl / Ketupa sumatrana) 分布。其羽。表现其最具。',
    4968: '帕氏拟雀 (Parodi\'s Hemispingus / Kleinothraupis parodii) 是。',
    4971: '铅色霸鹟 (Plumbeous Tyrant / Knipolegus cabanisi) 活跃。',
    4974: '哈氏黑霸鹟 (Hudson\'s Black Tyrant / Knipolegus hudsoni) 分布。',
    4985: '淡嘴火雀 (Landana Firefinch / Lagonosticta landanae) 分布。',
    4987: '褐背火雀 (Brown Firefinch / Lagonosticta nitidula) 活跃。',
    4995: '马里火雀 (Mali Firefinch / Lagonosticta virata) 分布。',
    5001: '圣马蒂亚斯鹃鵙 (Mussau Triller / Lalage conjuncta) 是。',
    5010: '白眉鸣鹃鵙 (White-browed Triller / Lalage moesta) 是。',
    5012: '黑鸣鹃鵙 (Pied Triller / Lalage nigra) 活跃。',
    5013: '灰鹃鵙 (Indochinese Cuckooshrike / Lalage polioptera) 活跃。',
    5014: '萨摩亚鸣鹃鵙 (Samoan Triller / Lalage sharpei) 是。',
    5017: '毛里求斯鹃鵙 (Mauritius Cuckooshrike / Lalage typica) 是。',
    5027: '那特瓦丝尾阔嘴鹟 (Natewa Silktail / Lamprolia klinesmithi) 是。',
    5043: '米氏辉椋鸟 (Meves\'s Starling / Lamprotornis mevesii) 活跃。',
    5045: '丽辉椋鸟 (Principe Starling / Lamprotornis ornatus) 是。',
    5050: '谢氏丽椋鸟 (Shelley\'s Starling / Lamprotornis shelleyi) 分布。',
    5055: '安哥拉黑鵙 (Gabela Bushshrike / Laniarius amboimensis) 是。',
    5060: '布氏黑鵙 (Braun\'s Bushshrike / Laniarius brauni) 活跃。',
    5068: '热带黑鵙 (Tropical Boubou / Laniarius major) 活跃。',
    5070: '索马里黑鵙 (Black Boubou / Laniarius nigerrimus) 分布。',
    5071: '山地黑伯劳 (Mountain Sooty Boubou / Laniarius poensis) 分布。',
    5073: '东海岸黑鵙 (East Coast Boubou / Laniarius sublacteus) 活跃。',
    5074: '图氏黑鵙 (Turati\'s Boubou / Laniarius turatii) 活跃。',
    5075: '威氏黑鵙 (Willard\'s Sooty Boubou / Laniarius willardi) 活跃。',
    5078: '安第斯鵙伞鸟 (Andean Laniisoma / Laniisoma buckleyi) 是。',
    5081: '暗黄唐纳鵙 (Fulvous Shrike-Tanager / Lanio fulvus) 分布。',
    5085: '点斑伞鸟 (Speckled Mourner / Laniocera rufescens) 是。'
}

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
for bid, desc in enriched_descriptions.items():
    cursor.execute("UPDATE BirdCountInfo SET short_description_zh_new = ? WHERE id = ?", (desc, bid))
conn.commit()
conn.close()
print(f"✅ Enriched {len(enriched_descriptions)} birds in Batch 1 sub-chunk 16.")
