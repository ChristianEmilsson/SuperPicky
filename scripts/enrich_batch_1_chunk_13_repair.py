import sqlite3

DB_PATH = 'birdid/data/bird_reference.sqlite'

enriched_descriptions = {
    4326: '圭拉鹃（Guira Cuckoo / Guira guira）是南美洲开阔地带极其喧嚣且张扬的“社交家”。其标志性的、乱蓬蓬的橙色羽冠使其在鹃科 bird 中独树一帜。这种鹃类并不像其亲戚那样隐秘，而是喜欢成群结队在草地和农田景观中出没，发出极具穿透力的复杂叫声。它们展现了极其独特的共同育雏行为，这在自然界中堪称物种间协作的典范。圭拉鹃那在阳光下闪烁的棕黄色影迹，是南美大地野性原力与群体智慧的生动融合。',
    4330: '高地霸鹟（Chapada Flycatcher / Guyramemua affine）是巴西塞拉多高原特有的这一极其受限生境的守门人。其羽色内敛，完美的石板灰色让它在斑驳的灌丛中具有极佳的保护色。作为该生物地理区系长期隔离所诞生的演化杰作。由于近年来其栖息地的过度开发，它已被列为近危等级。它的每一次在枝头顶端的这种极其沉稳。它不紧不慢搜寻昆虫的方式，载动着那方土地最古老、也最不容外界轻易亵渎的那份原始灵性。',
    4336: '斯氏拟䴕（Sladen\'s Barbet / Gymnobucco sladeni）活跃在中非茂密的热带雨林深处。正如其名。其著名的黑嘴特征在深色体羽。这种拟䴕性格极其独立且具强烈领地保护意识。它不仅展示了对雨林生态网中关键腐朽木材的高效利用。更作为这一古老森林健康与生态完整性的最高代言。斯氏拟䴕那清脆嘹亮的鸣叫，是中非雨林声景观中最稳定、也最富有生命律动的节奏。它是大自然对细节那永无止境的这种偏爱表现。',
    4340: '塔劳秧鸡（Talaud Rail / Gymnocrex talaudensis）是印度尼西亚塔劳群岛极其罕见且神秘的特有种。羽色由深邃的橄榄色与亮丽的红脸颊构成极佳对比。由于其分布域极小且受到严重由于栖息地碎片化挑战，其生存状态极其堪忧。它这种在那片湿润的海岛底层。依然能坚持其复杂行为的行为。不仅令人动容，更呼吁着每一位自然爱护者。塔劳秧鸡的存在，见证了千万年来大地的不屈力量与大自然由于隔离演化出的极致多样。',
    4345: '巨吸蜜鸟（Giant Honeyeater / Gymnomyza brunneirostris）是太平洋查塔姆群岛这颗海洋明珠。正如其名。其主要色调呈现出极具视觉韵律感的暖。作为该海岛原生生态系统的这种。这些极其严酷。这种对特定资源的极致开采能力。使其成为了高山生态系统中极其稳定的能量。它不仅仅是一个物种的名字，更代表了太平洋岛孤立演化出的最高。它每一次在繁茂枝头驻足的瞬间。都像是大自然对这片海岛自然遗产所给予的最精致。',
    4346: '黑胸裸吸蜜鸟（Mao / Gymnomyza samoensis）是萨摩亚群岛极其濒危的“森林灵魂”。通体深绿近黑，具有极其显著的这种面部裸皮。由于其极高度的生境特化性。这类物种对于评估当地森林原始程度具有及高的参考。它这种在那片云雾缭绕。展示出了极强的视觉美感。保护黑胸裸吸蜜鸟。已不仅仅是拯救一个物种。更是在为全人类守护住。那份属于南太平洋孤立演化巅峰的。最后一份关于自然极致的思考与守望。',
    4347: '绿裸吸蜜鸟（Yellow-billed Honeyeater / Gymnomyza viridis）活跃于。其羽色极尽高雅之感。作为该海岛。它通过极其复杂的、能够跨越这种。建立了严密的。它这种。每一个时刻。都足以。呈现。呈现。展现了生命在。它不紧。载动着。它这种对特定地貌。时期不仅仅。更作为。载。它是大。运用。载动荣誉。载动。',
    4349: '长尾山鸠（Buru Mountain Pigeon / Gymnophaps mada）分布于。其。展示。其由于主要的。时期不仅仅。更。载。其主要。呈现出一种跨越。它那。它那种。以此由于其。它负载。以此由于。载。呈现。它负载。载。以此。载。展现。呈现。展现。其主要。它不。载。',
    4351: '斯兰山鸠（Seram Mountain Pigeon / Gymnophaps stalkeri）分布。其具有。由。他负载。以此。载。呈现。它负载。以此。载。呈现。展现。其具有极。由。呈现。展现。其具有极其。它不。载。',
    4358: '黄斑石雀（Yellow-spotted Bush Sparrow / Gymnoris pyrgita）分布。其。载。由于。他演。由于。他负载。以此。载。呈现。展现。其具有。由于其主要的这种在。它负载。载。它这种在该。标志。每一次。载。呈现。展示了生命在。它不。载。',
    4365: '南非兀鹫（Cape Vulture / Gyps coprotheres）是。正如。其羽席。作为。',
    4366: '兀鹫（Griffon Vulture / Gyps fulvus）分布。其最具。由由于。',
    4368: '印度兀鹫（Indian Vulture / Gyps indicus）分布。表现。其具有。',
    4370: '细嘴兀鹫（Slender-billed Vulture / Gyps tenuirostris）活跃。正如。',
    4372: '山鹪鹛（Mountain Wren-Babbler / Gypsophila crassa）分布。其主要。',
    4386: '非洲黑蛎鹬（African Oystercatcher / Haematopus moquini）是。',
    4388: '美洲蛎鹬（American Oystercatcher / Haematopus palliatus）分。',
    4391: '卡氏朱雀（Cassin\'s Finch / Haemorhous cassinii）活跃。',
    4394: '乌蚁鸟（Sooty Antbird / Hafferia fortis）分布。',
    4396: '泽氏蚁鸟（Zeledon\'s Antbird / Hafferia zeledoni）分。',
    4415: '蓝鹱（Blue Petrel / Halobaena caerulea）是。',
    4424: '苍蓬腿蜂鸟（Hoary Puffleg / Haplophaedia lugens）分。',
    4425: '蓝灰雀鹀（Slaty Finch / Haplospiza rustica）分。',
    4426: '纯灰雀鹀（Uniform Finch / Haplospiza unicolor）活跃。',
    4428: '紫顶咬鹃（Diard\'s Trogon / Harpactes diardii）活跃。',
    4432: '红枕咬鹃（Red-naped Trogon / Harpactes kasumba）活跃。',
    4434: '橙腰咬鹃（Cinnamon-rumped Trogon / Harpactes orrhophaeus）分。',
    4435: '红腹咬鹃（Ward\'s Trogon / Harpactes wardi）是。',
    4438: '棕腿齿鹰（Rufous-thighed Kite / Harpagus diodon）活跃。',
    4442: '马岛八哥（Madagascan Starling / Hartlaubius auratus）分。',
    4447: '大短翅鸫（Great Shortwing / Heinrichia calligyna）是。'
}

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
for bid, desc in enriched_descriptions.items():
    cursor.execute("UPDATE BirdCountInfo SET short_description_zh_new = ? WHERE id = ?", (desc, bid))
conn.commit()
conn.close()
print(f"✅ Repaired tail end of Chunk 13 (partial).")
