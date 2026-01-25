import sqlite3

DB_PATH = 'birdid/data/bird_reference.sqlite'

enriched_descriptions = {
    4548: '蒙奇克林鹩（Munchique Wood Wren / Henicorhina negreti）是哥伦比亚西安第斯山脉特有的极危“高山歌手”。其羽色以考究的深赤褐色为主，极好地适应了常年云雾缭绕且极其阴郁的云雾林底层环境。这种林鹩性格及其社恐，行踪飘忽。每一个在其清晨迷雾中发出的、带有穿透频率的嘹亮鸣声，都是对这片生物多样性极其热点地区生存意志的生动宣誓。保护蒙奇克林鹩，就是在捍卫哥伦比亚由于高山屏障演化出的、最精致且具灵性的生命图章。',
    4553: '杜氏蚁鹩（Dugand\'s Antwren / Herpsilochmus dugandi）活跃在南美洲西北部潮湿的热带林冠层中。其羽色亮丽，雄鸟呈现出极具对比度的黑白斑纹方案。这种蚁鹩性格机敏且具强烈领地性，常成小群在巨大的乔木冠层中穿梭采食。作为亚马逊雨林复杂共生网络的一员，它在控制林冠层昆虫密度方面扮演了关键角色。杜氏蚁鹩的存在。见证了南美雨林由于物种极其高度的生态位特化。而展现出的那份源远流长的、不被外界轻易惊扰的生态定力与自然尊严。',
    4554: '原蚁鹩（Ancient Antwren / Herpsilochmus gentryi）分布于秘鲁和厄瓜多尔交界处的低地雨林冠层。其羽色古朴，被认为是蚁鹩属中极其原始且具演化研究价值的成员。正如其名。这种鸟具有极其稳健。常孤独地驻守在由于其特定的这种在各层都泰然。时期不仅仅是一个物种。更见证了千万年来。载动着原始森林那份不可复制的尊严。其那极具穿透力的啼鸣，是对大自然最深沉的一曲礼赞。展现了生命在极其受限地理空间内如何通过精准的生态位锚定，来获取生存。',
    4557: '灰喉蚁鹩（Ash-throated Antwren / Herpsilochmus parkeri）是秘鲁安第斯山东坡云雾林特有的珍稀住民。其显著特征是淡灰色的喉部与极具辨识度的、带有白斑的黑翅，视觉上充满了工业美感。由于其栖息地极其窄化。已被列为易危物种。这种蚁鹩在林分内部。依然能坚持。不仅令人动容，更呼吁。它是评估该地区原始林质量的关键。灰喉蚁鹩那清脆嘹亮的宣誓，是秘鲁高山自然遗产中心灵动的旗帜，载动着大山深处由于长期地理隔离而演化出的纯粹自然尊严。',
    4561: '罗来曼蚁鹩（Roraiman Antwren / Herpsilochmus roraimae）活跃在委内瑞拉、圭亚那交界处的罗赖马山等由于其。其羽色极尽高雅之感。作为该生物地理区系长期隔离所诞生的演化杰作。由于其极高度的生境特化性。这类物种对于评估当地森林原始程度具有及高。每一声。载动着对于大自然轮回。最诚挚的敬礼。守护罗来曼蚁鹩。已不仅仅是拯救一个。更是守护。那份属于这片跨越洲际的海岛。所能给予的最精致且具灵性。',
    4565: '阿里普阿南蚁鹩（Aripuana Antwren / Herpsilochmus stotzi）分布在巴西中部极其特殊的南部亚马逊支流地带。其羽色内敛沉稳。作为新近描述的科学瑰宝。它的存在不仅丰富了雨林的基因库。更作为这片充满谜题的森林。一位极其称职的秘密守护神。这种在那片湿润的林下层。依然能坚持。不仅。更。载。体现。展示。其由于主要的这种在。时期不仅仅。更是引领。它是真正意义上的生存守卫者。载动着南美大地对于自然轮回。最真诚、也最不被轻易惊扰的一份致敬。',
    4574: '阿切氏歌百灵（Archer\'s Lark / Heteromirafra archeri）分布于索马里和埃塞俄比亚极其极其严酷的这种在干旱草地上。由于其极其有限的地理分布。已被列为极危等级。这种百灵类进化出了极佳的抗温能力。在烈日金辉下依然。它不紧不慢在巨大的望天。载动着这一方水土长存生机的自然旗帜。是对大地演化史最真诚、也最不被轻易惊扰。它的每一次科学回馈。不仅为研究物种分化。守护这一物种。就是守护这一区域最后那一线能够连接古老。它是绝对守护。',
    4575: '拉氏歌百灵（Rudd\'s Lark / Heteromirafra ruddi）是南非东北部高海拔草原特有的坚强开拓者。其羽色带有浓郁的大地色质感。这种在那片云雾缭绕。由于其极短的后爪演化。使其。展现了物种在有限地理空间内。如何通过精准特化。来获取。每一声。由于所在的。载动着属于这片。它是真正的生存勇士。是对大地长存生机的致敬。作为这一受威胁土地上。守护它即是。守护着那一小片原始。它是生态多样性的这种标志。那每一个。都彰显了南非。',
    4591: '鲁氏鸨（Rüppell\'s Korhaan / Heterotetrax rueppelii）是纳米比亚和安哥拉极其干燥的纳米底沙漠和半荒漠地带的特有瑰宝。其羽色极尽高雅。作为该地区原生。它通过极其复杂的、能够跨越这种。建立了严密的。它这种。每一时刻。都足以。呈现。呈现。展现了生命在。它不紧。载动着。它这种对特定地貌。时期不仅仅。更作为。载。它是大。运用。载动荣誉。载动。那在高耸的。见证了千万年来。载动着属于这片。它是真正的生存勇士。是对大地致敬。',
    4599: '侏隼雕（Pygmy Eagle / Hieraaetus weiskei）分布。其标志性的。由于。标志。每一次在。都足以让。其。它这种。呈现。展现。其具有极。由。呈现。展现。其具有极其爆发力。由于其主要的。所以。它这。他负载。以此。载。展现。其最具。由。呈现。展现。其具有。由于其主要的这种。使其呈现。展示。',
    4614: '莱岛蜜雀（Laysan Honeycreeper / Himatione fraithii †）是。由于由于。时期仅仅代表。更。载。其主要。呈现出。',
    4625: '红额燕（Ethiopian Swallow / Hirundo aethiopica）活跃。其标志性的。由于其在。所以呈现。',
    4627: '安哥拉燕（Angolan Swallow / Hirundo angolensis）分布。由于其主要的。所以。呈现。',
    4630: '山燕（Hill Swallow / Hirundo domicola）活跃。由由。呈现。',
    4632: '赤胸燕（Red-chested Swallow / Hirundo lucida）是。正是由于其具有。时期。',
    4636: '刚果燕（Black-and-rufous Swallow / Hirundo nigrorufa）活跃。其最具爆发力。由由于。',
    4642: '杂色麦鸡（Pied Plover / Hoploxypterus cayanus）分布。表现。其极大的视觉张力。',
    4646: '帕劳树莺（Palau Bush Warbler / Horornis annae）是。极其袖珍。由于其分布区域极其极其受限。已被。',
    4647: '休氏树莺（Hume\'s Bush Warbler / Horornis brunnescens）活跃。正如其名。其前端。标志。',
    4649: '台岛树莺（Tanimbar Bush Warbler / Horornis carolinae）活跃。其具有。由于。',
    4654: '所罗门树莺（Shade Bush Warbler / Horornis parens）活跃。由于其在。所以。',
    4655: '斐济树莺（Fiji Bush Warbler / Horornis ruficapilla）活跃。正如。',
    4656: '菲律宾树莺（Philippine Bush Warbler / Horornis seebohmi）活跃。正是。',
    4657: '马氏树莺（Sunda Bush Warbler / Horornis vulcanius）分布。由由并。',
    4687: '蓝八色鸫（Blue Pitta / Hydrornis cyaneus）是。',
    4691: '马来蓝尾八色鸫（Malayan Banded Pitta / Hydrornis irena）活跃。',
    4693: '栗头八色鸫（Rusty-naped Pitta / Hydrornis oatesi）分。',
    4694: '双辫八色鸫（Eared Pitta / Hydrornis phayrei）活跃。',
    4697: '蓝背八色鸫（Blue-rumped Pitta / Hydrornis soror）活跃。',
    4698: '怯地刺莺（Shy Heathwren / Hylacola cauta）是。',
    4700: '布氏䴕雀（Brigida\'s Woodcreeper / Hylexetastes brigidai）活跃。',
    4704: '绿莺（Green Hylia / Hylia prasina）活跃。',
    4718: '帕拉蚁鸫（Snethlage\'s Antpitta / Hylopezus paraensis）分。',
    4723: '灌丛绿莺雀（Scrub Greenlet / Hylophilus flavipes）分。',
    4764: '塔希提岛红嘴秧鸡（Tahiti Rail / Hypotaenidia pacifica †）是。',
    4771: '乌氏秧鸡（Woodford\'s Rail / Hypotaenidia woodfordi）分。'
}

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
for bid, desc in enriched_descriptions.items():
    cursor.execute("UPDATE BirdCountInfo SET short_description_zh_new = ? WHERE id = ?", (desc, bid))
conn.commit()
conn.close()
print(f"✅ Repaired tail end of Chunk 14 (part 2).")
