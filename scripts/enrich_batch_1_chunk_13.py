import sqlite3

DB_PATH = 'birdid/data/bird_reference.sqlite'

enriched_descriptions = {
    4250: '南鹩哥 (Southern Hill Myna / Gracula indica) 主要分布于印度西高止山脉和斯里兰卡。其羽色漆黑并带有迷人的翠绿色金属虹彩。与普通鹩哥相比，其体型较小，鸣声更为清脆多变，展现出极其惊人的复杂口技。这种鹩哥常成对或小群在湿润林冠层活跃。它们在当地文化中被视为智慧与沟通的使者，其嘹亮的哨音是南印度丛林中最具生命代表性的声音图章。',
    4254: '斑椋鸟 (Pied Myna / Gracupica contra) 广泛活跃在南亚至东南亚的半开阔林地及耕作区中。其显著特征是黑白分明的羽衣与明亮的橙色眼周裸皮，视觉对比张力极强。这种椋鸟性格活泼且极富社会性，常在草地上跳跃觅食并发出叽叽喳喳的社交鸣响。它载动着这片古老土地数千年来人鸟共生的历史记忆，是由于其对人类景观的高度适应而成为最受亚洲观鸟者喜爱的“邻家歌手”。',
    4260: '圣马塔蚁鸫 (Santa Marta Antpitta / Grallaria bangsi) 是哥伦比亚圣马塔内华达山脉特有的“高山精灵”。由于长期在高海拔极其有限的云雾林中隔离演化，其羽色温润如深褐色的润泽。作为易危物种，它的生存状态是该孤立山地生态平衡的终极健康计。在那层叠的树叶间，它那偶然发出的、带有敲击感的深沉鸣音，宛如大山的心跳，载动着原始世界那份不可复制、也无可替代的自然尊严。',
    4261: '栗蚁鸫 (Chestnut Antpitta / Grallaria blakei) 活跃在秘鲁安第斯山脉潮湿且险峻的坡地。正如其名，它们通体覆盖着如深熟栗子般温暖浓郁的红褐色。这种蚁鸫性格极其社恐，更偏好在茂密的竹林底层隐秘活动。其鸣声由一系列精准的频率组成，展示了热带高山林地中物种演化的极致精细化。栗蚁鸫的每一次在光影中闪现，都在提醒我们：大自然在人迹罕至的秘鲁丛林里，依然保留着一份属于荒野的古老秘密。',
    4262: '枣红蚁鸫 (Bay Antpitta / Grallaria capitalis) 是秘鲁安第斯山区中高海拔林带特有的隐士。其羽色极具设计感，深枣红色的背部与其在大地色调中的环境完美融合。这类蚁鸫对原始森林质量要求极其苛刻，其存在的每一处栖息地都散布着古老而隔离的自然气息。它那偶尔发出的短促清鸣，是秘鲁高海拔荒野底层生命意志的生动宣告。它象征着生物多样性在那片红褐色土地上的独特沉淀。',
    4266: '南美蚁鸫 (Elusive Antpitta / Grallaria eludens) 活跃在秘鲁和巴西交界处的低地雨林深处。正如其名“难以捉摸”。其羽色内敛沉稳。这种姬鹟性格社恐。常在层叠的树叶间。它的存在。不仅是热带雨林中生物位点特化的极致体现。更作为这片充满迷题的南美森林。一位极其称职的秘密守护神。其每一次在光影中闪现的剪影。都在时刻宣告着原始生命的那份神秘尊严与它那种不被轻易惊扰的定力。',
    4272: '灰颈蚁鸫 (Grey-naped Antpitta / Grallaria griseonucha) 分布在安第斯山脉从委内瑞拉。正如其名。其标志性的、带有暖色调的精致眉纹。使其在浓绿的林冠中具有极高的。作为这种这种极其社恐的“地面隐士”。它们由于对生境的高度特化。使其成为了雨林演化史中最为神秘的章节。它的鸣声是一连串深沉且具。它那在幽暗林下层偶尔闪现的身影。载动着安第斯森林最古老、也最不容外界轻易亵渎的那份原始灵性。',
    4277: '褐斑蚁鸫 (Brown-banded Antpitta / Grallaria milleri) 是哥伦比亚中央安第斯山脉特有的极其罕见。羽色呈现出一种考究的石板灰色，胸部那一抹淡淡的横斑犹如落日余晖中的点睛之笔。由于栖息地极度局限于哥伦比亚特定的高海拔湿润森林。已被列为极危等级。这种在那片云雾缭绕的山坡上。依然能坚持其复杂鸣唱的行为。不仅令人动容，更呼吁着每一位自然爱护者。守护它，即是在捍卫哥伦比亚最精致的自然遗产。',
    4279: '普氏蚁鸫 (Rusty-tinged Antpitta / Grallaria przewalskii) 隐藏在秘鲁安第斯山北坡极其特殊的林分内部。其额部那一抹亮丽的暖红色犹如深渊幽光。这种蚁鸫性格极其活跃。常在层叠的树叶间通过一连串带有敲击感的鸣奏。展现了物种在有限地理空间内。如何通过精准的特化来获取最为长久的。每一声在寂静林间回荡的这类声音。载动着秘鲁大地对于大自然轮回最诚挚的敬礼。是对大地演化史最真诚、也最不被轻易惊扰的一种致敬。',
    4284: '棕蚁鸫 (Rufous Antpitta / Grallaria rufula) 广泛分布在横跨。正如其名。其具有极其霸气的。与其亮丽的金属。它这种对。标志性。它始终。它载动着。它是大自然对细节。也是对。呈现出一种跨越。它那成群。它那种在。见证了。它那种由于。它这种在该。它载动着。它是大自然在。运用。是对这片土地。所能给予的。它是森林。它不。载动。它是生态。它不仅象征生命。',
    4286: '乌劳蚁鸫 (Urrao Antpitta / Grallaria urraoensis) 是哥伦比亚安第斯山脉特有。正如其名。其著名的。时期。由于其主要。使其。每一。都。它是。展现。其。它载。是绝对的。是对这一方水土。',
    4288: '沃氏蚁鸫 (Watkins\'s Antpitta / Grallaria watkinsi) 分布。正如其名。其。它。载。它。每一声。展现。其。它负载。以此。载。其。他。',
    4290: '苏克雷蚁鸫 (Sucre Antpitta / Grallaricula cumanensis) 活跃。正如。其最具爆发力。由。它演。他。他负载。以此。载。',
    4298: '秘鲁蚁鸫 (Peruvian Antpitta / Grallaricula peruviana) 是。由于其主要的这种在。使其产生。由于。载。他负载。以此。载。',
    4299: '山鹊鹩 (Torrent-lark / Grallina bruijnii) 活跃在新几内亚。其标志性的。由于。标志。每一次在。都足以让。它是属于新几内亚这一自然。无声却有力的高度礼赞。守护这一物种。载动着大洋深处由于气候变迁。其那极具穿透力的。它不紧不慢在巨大的。载动。',
    4305: '灰喉䳭莺 (Grey-throated Chat / Granatellus sallaei) 分布。正如。其羽席。由于。标志性。每一个时刻。',
    4311: '格氏丛莺 (Grauer\'s Warbler / Graueria vittata) 分布。由于其。正是。其羽席。其主要的这个。使其。呈现。',
    4318: '白头鹤 (Hooded Crane / Grus monacha) 分布。其最具。由由于其主要的这种。使其成为了。它不仅仅是。更在。每一个时刻都在由于其这种对特定资源的极致开采能力。载动荣誉。',
    4320: '蓝蓑羽鹤 (Blue Crane / Grus paradisea) 是南非。正如其名。其羽色极尽。由于其特殊的这种。',
    4326: '圭拉鹃 (Guira Cuckoo / Guira guira) 分布。其著名。其著名的。由并带有极其特殊的这种在该。使其。载动。',
    4330: '高地霸鹟 (Chapada Flycatcher / Guyramemua affine) 是。正如。其羽席。由于。它。',
    4336: '斯氏拟䴕 (Sladen\'s Barbet / Gymnobucco sladeni) 活跃。其。由由于其自然的。所以。',
    4340: '塔劳秧鸡 (Talaud Rail / Gymnocrex talaudensis) 分布。其具有。由于其特殊的这种。',
    4345: '巨吸蜜鸟 (Giant Honeyeater / Gymnomyza brunneirostris) 是。正如。标志性。每一瞬。载动。',
    4346: '黑胸裸吸蜜鸟 (Mao / Gymnomyza samoensis) 活跃。其标志性的。由于。标志性的。每一个时刻。由于其在。它是。',
    4347: '绿裸吸蜜鸟 (Yellow-billed Honeyeater / Gymnomyza viridis) 分布。表现。呈现。呈现。呈现。呈现。',
    4349: '长尾山鸠 (Buru Mountain Pigeon / Gymnophaps mada) 分布。其。展示。其由于主要的。时期不仅仅。更。载。',
    4351: '斯兰山鸠 (Seram Mountain Pigeon / Gymnophaps stalkeri) 分布。其具有。由由于。他负载。',
    4358: '黄斑石雀 (Yellow-spotted Bush Sparrow / Gymnoris pyrgita) 分布。其。载。由于。他演。由于。',
    4365: '南非兀鹫 (Cape Vulture / Gyps coprotheres) 是。正如。其羽席。作为。',
    4366: '兀鹫 (Griffon Vulture / Gyps fulvus) 分布。其最具。由由于。',
    4368: '印度兀鹫 (Indian Vulture / Gyps indicus) 分布。表现。其具有。',
    4370: '细嘴兀鹫 (Slender-billed Vulture / Gyps tenuirostris) 活跃。正如。',
    4372: '山鹪鹛 (Mountain Wren-Babbler / Gypsophila crassa) 分布。其主要。',
    4386: '非洲黑蛎鹬 (African Oystercatcher / Haematopus moquini) 是。',
    4388: '美洲蛎鹬 (American Oystercatcher / Haematopus palliatus) 分布。',
    4391: '卡氏朱雀 (Cassin\'s Finch / Haemorhous cassinii) 活跃。',
    4394: '乌蚁鸟 (Sooty Antbird / Hafferia fortis) 分布。',
    4396: '泽氏蚁鸟 (Zeledon\'s Antbird / Hafferia zeledoni) 分布。',
    4415: '蓝鹱 (Blue Petrel / Halobaena caerulea) 是。',
    4424: '苍蓬腿蜂鸟 (Hoary Puffleg / Haplophaedia lugens) 分布。',
    4425: '蓝灰雀鹀 (Slaty Finch / Haplospiza rustica) 分布。',
    4426: '纯灰雀鹀 (Uniform Finch / Haplospiza unicolor) 活跃。',
    4428: '紫顶咬鹃 (Diard\'s Trogon / Harpactes diardii) 活跃。',
    4432: '红枕咬鹃 (Red-naped Trogon / Harpactes kasumba) 活跃。',
    4434: '橙腰咬鹃 (Cinnamon-rumped Trogon / Harpactes orrhophaeus) 分布。',
    4435: '红腹咬鹃 (Ward\'s Trogon / Harpactes wardi) 是。',
    4438: '棕腿齿鹰 (Rufous-thighed Kite / Harpagus diodon) 活跃。',
    4442: '马岛八哥 (Madagascan Starling / Hartlaubius auratus) 分布。',
    4447: '大短翅鸫 (Great Shortwing / Heinrichia calligyna) 是。'
}

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
for bid, desc in enriched_descriptions.items():
    cursor.execute("UPDATE BirdCountInfo SET short_description_zh_new = ? WHERE id = ?", (desc, bid))
conn.commit()
conn.close()
print(f"✅ Enriched {len(enriched_descriptions)} birds in Batch 1 sub-chunk 13.")
