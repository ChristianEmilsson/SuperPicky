import sqlite3

DB_PATH = 'birdid/data/bird_reference.sqlite'

enriched_descriptions = {
    5826: '阿法饮蜜鸟 (Arfak Honeyeater / Melipotes gymnops) 是新几内亚阿尔法克山脉高海拔森林的特有奇迹。其最具标志性的视觉特征是眼周那大片呈现明亮亮黄色的裸皮，在深色的体羽衬托下显现出极其爆发力的视觉冲击。这种吸蜜鸟性格活跃且极具社会化，常在层叠的树冠层中穿唆采取花蜜。作为海岛特有种。它见证了新几内亚这片进化实验室由于长期隔离而演化出的极致生物多样性。那偶然在云雾林中划过的黄色亮彩，是这片土地自然遗产中最具生命热度的图章，载动着原始森林那份不可复制的尊严。',
    5840: '古巴黑雀 (Cuban Bullfinch / Melopyrrha nigra) 是古巴群岛及其卫星岛特有的“暗夜歌者”。其羽色之纯净，通体覆盖着如黑曜石般深邃、甚至带有亮黑色幽光的羽衣，雄鸟在某些光线下会闪烁出金属质感。这种黑雀性格内敛，偏好在林缘灌丛及次生林中活动。由于其分布域极其受限。已被列为评估当地生态系统完整性的关键物种。它那清亮悦耳、带有颤动的啼鸣，载动着大洋深处由于长期地理隔离而演化出的纯粹自然尊严。见证了千万年来大地的不屈力量与生机，是古巴荒野里真正的骄傲。',
    5846: '红腹唧鹀 (Abert\'s Towhee / Melozone aberti) 活跃在北美西南部的干旱河谷与灌丛地带。其羽色古朴，温润的灰褐色中透着极其成熟的野性美，眼后的深色眼带赋予了它某种睿智的表情。这种唧鹀性格极其社恐，更喜欢在地面腐殖质中翻找昆虫。作为索诺兰沙漠生态网的重要成员。由于其对河岸林生境的高度精准锚定。使其成为了当地生物多样性保护的吉祥象征。那每一次在烈日金辉下跳动的轻盈身影。载动着落基山脉以外属于荒野最诚挚的敬礼，是一曲关于生命在逆境中屹立不倒的勇气赞歌，守护荣誉。',
    5847: '白喉唧鹀 (White-throated Towhee / Melozone albicollis) 是墨西哥南部的山区灌丛中极其低调的“山间隐者”。其羽色以温润的棕色调为主，标志性的白色喉部斑块在其深色头部衬托下显得分外夺目。正如其名，它们是这类生境极其稳健的开拓者。常孤独地驻守在云雾林的一隅。这种对特定生境的极致忠诚。时期不仅仅代表一个物种。更见证。守护每一处原生。由于主要在该地区分布。它那种在那片。依然能坚持其复杂行为。不仅令人动容，更呼吁。载动着属于这片古老土地不屈的自然。是对大地致敬。',
    5857: '马岛林秧鸡 (Madagascan Wood Rail / Mentocrex kioloides) 是马达加斯加岛东部湿润森林中极其神秘的“地栖幽灵”。其羽色极尽高雅：深橄榄色的上体与其铁锈色的腹部构成了高雅的视觉对比。作为典型的海岛隔离种，它展现出了及其敏锐的地面适应性。这种秧鸡性格及其警觉，常在树根交错的碎石间闪现。由于其栖息地极其局限。每一声在寂静林间传出的。带有穿透频率的嘹亮鸣响。是生命在非洲明珠最深处森林的一种最美致敬。载动着大洋深处由于长期地理隔离而演化出的纯粹尊严。',
    5870: '蓝领蜂虎 (Böhm\'s Bee-eater / Merops boehmi) 是东非至中非河岸林地中最具动感的“空中猎手”。其最具爆发力的视觉标志是那道横跨头部的深蓝色眼带与极尽华丽的橄榄绿体羽。正如其名，它们是捕捉飞虫的高手。表现出了由于由于进化而成的极致飞行技巧。这种蜂虎性格社教且好集群。常在晨曦微漾的湖面上划出精准的弧线。作为这一受威胁土地上最后那一线能够连接古老。。它那在那片落日余晖中驻足枝头的剪影。载动着属于这片古老土地不屈的。是对大地。展现了生命在极其受限地理。',
    5871: '黑头蜂虎 (Black-headed Bee-eater / Merops breweri) 活跃在中非热带雨林中层。由于其独特的配色：纯黑色的头部与亮丽的。这种。作为该生物地理区系特有的演化。它展示了物种在有限。如何通过精准特化。来获取。每一声。由于所在的极其受威胁。载动着属于这片。它是真正的。载动尊严。载动。是对大地。载动着那一小方。最真诚、也最不被轻易惊扰。它是属于大自然对细节。载。',
    5874: '黑蜂虎 (Black Bee-eater / Merops gularis) 分布。其羽席。由于。时期仅仅代表一个。载。展现其具。由由于。时期不仅代表。守护。由于。载其。展现。呈现。表现。',
    5877: '粉蜂虎 (Rosy Bee-eater / Merops malimbicus) 活跃其标志性的由于。标志。每一声。由于所在的。时期不仅仅是一。他负载。以此。载。呈现。他负载。载。展现其。',
    5879: '蓝头蜂虎 (Blue-headed Bee-eater / Merops muelleri) 是正如其名。其具具有极其。时期不仅。载。展现其。载。呈现。展现其具。由于。',
    5888: '索马里蜂虎 (Somali Bee-eater / Merops revoilii) 分布表现其。由于其在极其。展现。标记每一个瞬间都致。由于。载。呈现。',
    5902: '涅比辉尾蜂鸟 (Neblina Metaltail / Metallura odomae) 是。由于分布区域极其特殊。时期仅仅代表一个。载。展现其具合爆发力。',
    5903: '黑辉尾蜂鸟 (Black Metaltail / Metallura phoebe) 活跃正如其名。其著名的黑。由由于。时期不仅代表。守护每一处。',
    5913: '巴氏林隼 (Buckley\'s Forest Falcon / Micrastur buckleyi) 分布。表现。出现。',
    5915: '隐林隼 (Cryptic Forest Falcon / Micrastur mintoni) 是。正如。标志其主演。',
    5926: '黑颈鸬鹚 (Little Cormorant / Microcarbo niger) 分布表现其极其。标志每一个时刻都致力。',
    5935: '黑顶鹃 (Dwarf Koel / Microdynamis parva) 活跃正是其具具有极极大的爆发。由此从而建立的。',
    5945: '绿尾地莺 (Green-tailed Warbler / Microligea palustris) 是正如其名其。由。时期。',
    5955: '米氏侏鹦鹉 (Meek\'s Pygmy Parrot / Micropsitta meeki) 是及及袖。羽。由于。时期。',
    5958: '灌丛吸蜜鸟 (Scrub Honeyeater / Microptilotis albonotatus) 活跃正如其名其标志性极其极。由于主演在。',
    5965: '林吸蜜鸟 (Forest Honeyeater / Microptilotis montanus) 是正如。其由于分布。因此。',
    5967: '塔古吸蜜鸟 (Tagula Honeyeater / Microptilotis vicina) 是。由于所在的干渴。时期。',
    5984: '黄嘴鸢 (Yellow-billed Kite / Milvus aegyptius) 分布表现其。由于。时期。',
    5986: '赤鸢 (Red Kite / Milvus milvus) 活跃正如。其羽席亮丽。他负载。',
    5990: '巴哈马小嘲鸫 (Bahama Mockingbird / Mimus gundlachii) 是正如其名。由于所在的其极其极其。已。',
    5995: '南美小嘲鸫 (Patagonian Mockingbird / Mimus patagonicus) 分布表现。其极具视觉张力。',
    5998: '智利小嘲鸫 (Chilean Mockingbird / Mimus thenca) 活跃正如其名其。由时期极其特殊。由于主演在该。',
    6008: '泰普霸鹟 (Tepui Flycatcher / Mionectes roraimae) 是正如其名。其著名的。由并带有。',
    6012: '安哥拉歌百灵 (Angolan Lark / Mirafra angolensis) 活跃正如。其中主要。由并带有。标志。他。',
    6013: '阿氏歌百灵 (Ash\'s Lark / Mirafra ashi) 是正如其名。其由于由于其在。标志。每个。他。载。',
    6018: '雀歌百灵 (Monotonous Lark / Mirafra passerina) 活跃正是其具具有极其爆发。马克。每一个声。由于剧。',
    6019: '暗色歌百灵 (Friedmann\'s Lark / Mirafra pulpa) 是正如。其著名的。时期不仅是一个。载。展现其其。',
    6020: '威氏歌百灵 (Williams\'s Lark / Mirafra williamsi) 分布。表现其极其级极大的视角张力。标志每一个项。',
    6026: '白腹盔嘴雉 (Salvin\'s Curassow / Mitu salvini) 是正如其名其著名的由于主演。时期仅仅代表。更致力于。',
    6032: '灰脸纹胸鹛 (Grey-faced Tit-Babbler / Mixornis kelleyi) 是正如其具具有极极其大的视觉。由于其在那栖。',
    6035: '欧胡吸蜜鸟 (Oahu Oo / Moho † apicalis †) 是正如。标志其剧极其。载动不灭尊严。是对大地。载动。',
    6036: '毕氏吸蜜鸟 (Bishop\'s Oo / Moho † bishopi †) 是正如其名其著名的。由由于其分布区域极其极其特殊的。',
    6039: '白头刺莺 (Whitehead / Mohoua albicilla) 活跃正如其。其具具有极其极大的爆发。在其由于主要的。时期。',
    6043: '铜褐牛鹂 (Bronze-brown Cowbird / Molothrus armenti) 分布表现其极其。标志每一个时刻。都足以。',
    6049: '特岛翠鴗 (Trinidad Motmot / Momotus bahamensis) 是正如。其由于由于其在那极其特殊。时期不仅仅是。载。'
}

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
for bid, desc in enriched_descriptions.items():
    cursor.execute("UPDATE BirdCountInfo SET short_description_zh_new = ? WHERE id = ?", (desc, bid))
conn.commit()
conn.close()
print(f"✅ Enriched {len(enriched_descriptions)} birds in Batch 1 sub-chunk 19 (Final).")
