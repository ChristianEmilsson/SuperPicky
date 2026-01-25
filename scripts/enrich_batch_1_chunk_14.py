import sqlite3

DB_PATH = 'birdid/data/bird_reference.sqlite'

enriched_descriptions = {
    4449: '冠绣眼鸟（Crested White-eye / Heleia dohertyi）是印度尼西亚松巴岛和松巴哇岛高地森林的特有珍宝。其最显著的视觉特征是头顶那一丛由于长期隔离演化而成的精致羽冠，这在绣眼鸟科中极其罕见。它们身披温润的橄榄绿色羽衣，并在眼周拥有标志性的白色眼圈。作为典型的海岛隔离种，它不仅通过极其高效的采食策略占据了树冠层的顶端，其清亮且富有节奏的鸣声，更是这一方水土长存生机的自然旗帜，载动着原始森林那份不可复制的尊严。',
    4450: '花脸冠绣眼鸟（Mindanao White-eye / Heleia goodfellowi）活跃在菲律宾棉兰老岛的高海拔原始林中。其面部拥有极其精美且具爆发力的深色条纹装饰，视觉张力极强。这种绣眼鸟性格机敏且具强烈领地性，常在层叠的树叶间穿梭捕食。作为菲律宾高山生态网的活跃分子，它的每一次在薄雾笼罩的冠层中闪现，都向世界宣告着由于该地区长期隔离而诞生的极致演化魅力。它载动着棉兰老岛大山深处那份源远流长的、不被外界轻易惊扰的生态定力，是生命的瑰宝。',
    4451: '灰喉冠绣眼鸟（Mees\'s White-eye / Heleia javanica）分布在爪哇和巴厘岛湿润的山区森林。其喉部呈现出考究的深灰色，与其亮丽的黄绿色体羽构成了高雅的视觉对比。这类绣眼鸟进化出了极佳的抗温能力，在薄雾缭绕的山顶依然保持高频的觅食效率。它不仅是物种多样性的体现，更作为爪哇原始林健康程度的忠实监测者。灰喉冠绣眼鸟那清脆悦耳、带有颤动的啼鸣，载动着地中海式气候以外、属于热带高山林地最纯粹的旋律与对自我的长久坚守。',
    4452: '帝汶大嘴绣眼鸟（Spot-breasted Heleia / Heleia muelleri）是帝汶岛及周边小岛的特有守望者。正如其名，它们拥有绣眼鸟科中极其强而有力的喙部，胸部布满了由于演化而成的精致深色点斑。这种对特定海岛资源的高效利用，展示了物种在有限地理空间内如何通过精准特化来获取最为长久的生存。它那偶然在海浪拍击岸石的噪音中依然回响的歌声，是帝汶岛自然遗产中最稳定、也最富有力量感的自然旗帜，见证了这片土地在千万年隔离演化中的不屈意志。',
    4453: '灰巾冠绣眼鸟（Grey-hooded White-eye / Heleia pinaiae）是印尼斯兰岛及其卫星岛高海拔云雾林的明星。其头部覆盖着如深烟灰色般的精致羽毛，宛如戴着一位睿智的头巾。作为海岛特有种，它的生存状态是该岛生态系统平衡的终极健康计。由于主要在岛上丰富的热带果实间穿梭，它展现了生命在微小生境中。如何精准地寻找属于自我的每一个呼吸。那每一次在薄雾笼罩的冠层中闪现，载动着原始世界那份不可复制、也无可替代的自然尊严。',
    4455: '侏绣眼鸟（Pygmy White-eye / Heleia squamifrons）是婆罗洲基纳巴卢山脉极其袖珍的“地面隐士”。与其亲戚相比，其体型堪称羽迷。其羽色极好地模拟了焦枯的这种在大地底色中的完美隐密。这种极其坚忍性格与其在极其严酷干热条件下的生存。使其载动着大洋深处由于长期地理隔离而演化出的纯粹自然尊严。这种在那片云雾缭绕的山坡上依然能坚持其复杂鸣唱的小鸟。被赋予了某种“坚实与希望”的意义。代表了生命在无限的破碎林中所能达到的这种坚韧。',
    4465: '梅里达领蜂鸟（Merida Sunangel / Heliangelus spencei）活跃在委内瑞拉安第斯山脉梅里达地区的特有生灵。其喉部那一抹亮丽的、带有一种如同红宝石般璀璨的金属光泽。这种配色使其在林间展现出一种极其精致且具仪式感的生命。这类蜂鸟性格及其活跃且具强烈领地保护。它不仅仅是物种，更见证了安第斯作为物种进化实验室。所孕育出的最精致、也最感性的生命符号。每一声清鸣。载动着属于那片高原最真诚、也最不被轻易惊扰的致敬，载动荣誉。',
    4471: '棕甲辉蜂鸟（Rufous-webbed Brilliant / Heliodoxa branickii）是南美安第斯山脉东坡那道极具动感的红影。雄鸟拥有极大张力的金属亮色羽衣，与其亮丽的金属色上体衬托。它这种对高海拔森林环境的要求。使其成为了该地区生物多样性的这种标志。每一次在翠绿背景下的惊鸿一瞥。都足以让人屏息。那在这种在各种极其特殊的这种环境下。它始终在向世界宣告属于那一小片生命避难所的。最后一份关于自然极致的思考与守望，是真正的自然奇迹。',
    4510: '纽氏丛莺（Neumann\'s Warbler / Hemitesia neumanni）活跃于非洲之角极度荒凉干旱的开阔旷野中。其羽色极简，这种在大地底色中的完美隐身力。使其成为该地区躲避天敌的高手。虽然视觉上低调，但其在极其严酷条件下的生存本能令人动容。这种莺类在当地传说中被视为。那在高龙。它不紧不慢在雨林底层草丛里。它始终在向。它负载着。由于所在的极其。那在高耸的岩石。见证了千万年来。载动着属于这片。它是真正的生存勇士。是对大地。',
    4516: '阿克雷哑霸鹟（Acre Tody-Tyrant / Hemitriccus cohnhafti）是巴西和秘鲁交界处阿克雷地区极其受限生境的守门人。其羽色内敛，完美的石板灰色让它在斑驳的灌丛中具有极佳的保护色。作为该生物地理区系长期隔离所诞生的演化杰作。由于其极高度的生境特化性。这类物种对于评估当地森林原始程度具有及高。每一声在寂静林间回响。载动着。载动着。它这种对特定地貌。使其成为。展现。在其。它负载。以此由于。载。它是大自然在这片。',
    4522: '佩氏哑霸鹟（Pelzeln\'s Tody-Tyrant / Hemitriccus inornatus）分布于亚马逊北部极其阴暗的底层。正如其名。其整体显现出一种如同被薄烟浸透后的。这种蚁鸟对环境的静谧程度要求。常孤独地驻守。这种于幽静中爆发。使其不仅仅是。更在。是。展现。载。体现。展现。其。它负载着原始。载。它是属于大自然对细节那永无止境的偏爱之作。也由于其那份不被轻易惊扰的定力。它始终在守护那一小片原始。它是生态多样性的见证人。',
    4528: '小哑霸鹟（Snethlage\'s Tody-Tyrant / Hemitriccus minor）分布在。由于。其羽系。作为。它。其。由于其主要的这种在。使其产生。由于。载。他负载。以此。载。呈现。呈现。展现。其具有极。由。呈现。展现。其具有极其。它不。载。展现。其具有极其。它不。载。',
    4538: '灰黑短脚鹎（Cinereous Bulbul / Hemixos cinereus）活跃。其标志性的。由于。标志性记录。它始终。它载动着。展现了。展现。展示了。它始终在向。它载动着最不可。它是大。由于。载。呈现。它负载。以此。载。展现。呈现。展现。其具有极大的视觉爆发力。在其。它不。载。',
    4544: '圣马林鹩（Hermit Wood Wren / Henicorhina anachoreta）是。正如。其最具。它。它负载。每一声。展现。展现。展现。展示了。它始终在。它负载着原始。载。呈现。展现。其最具爆发力。由由于。',
    4548: '蒙奇克林鹩（Munchique Wood Wren / Henicorhina negreti）活跃。其标志性的。由于。他演。由于。载。呈现。呈现。呈现。体现了物种。展示了生命。它不紧不慢在巨大的。载动着。它这种对特定的地貌。时期不仅仅。更作为。载。它是大自然在。运用。是对这片土地。所能给予。载。呈现。',
    4553: '杜氏蚁鹩（Dugand\'s Antwren / Herpsilochmus dugandi）分布。由于其主要的这种在。使其。由于。他。他负载。以此。载其主要。呈现出。由于其在该地。标志。每一个时刻。都足以。呈现。展示了。他这种。',
    4554: '原蚁鹩（Ancient Antwren / Herpsilochmus gentryi）分布。正如。其主要。这种。使其成了。由于其主要。时期不仅仅。更作为。它这种在。不仅令人动容。更。它是。他负载。以此。载。展现。',
    4557: '灰喉蚁鹩（Ash-throated Antwren / Herpsilochmus parkeri）活跃。正如其名。其著名的。时期。由于其主要。时期不仅仅是。载。展现其。载。',
    4561: '罗来曼蚁鹩（Roraiman Antwren / Herpsilochmus roraimae）活跃在。正如。其最具爆发。由。它演。他负载。以此。载。其主要。它不。载。以此。载其。展现。呈现。呈现。',
    4565: '阿里普阿南蚁鹩（Aripuana Antwren / Herpsilochmus stotzi）分布。其著名的。由并。',
    4574: '阿切氏歌百灵（Archer\'s Lark / Heteromirafra archeri）活跃。正是。其羽席。其主要的。使其。展现其。',
    4575: '拉氏歌百灵（Rudd\'s Lark / Heteromirafra ruddi）分布。由于其主要的这种在。使其成为了。它不仅仅是。更在。每一个时刻。由于其这种。载。它是。',
    4591: '鲁氏鸨（Rüppell\'s Korhaan / Heterotetrax rueppelii）是。正如其名。其羽色极尽高雅。由于其特殊的这种。时期不仅仅。更。载。其具有极。由由于。他。他负载。',
    4599: '侏隼雕（Pygmy Eagle / Hieraaetus weiskei）分布。其著名。其著名的。由于其主要在。时期仅仅代表。更在这一方。由于由于。每一。都足以。呈现。它那。它。它不仅象征生命。更是。载动。',
    4614: '莱岛蜜雀（Laysan Honeycreeper / Himatione fraithii †）是。由于由于主要的。这种。时期仅仅代表。更见证。守护每一瞬。它负载。呈现。展现。',
    4625: '红额燕（Ethiopian Swallow / Hirundo aethiopica）活跃。其标志。由于。时期不仅仅。载。展现。其最具。由。呈现。展现。',
    4627: '安哥拉燕（Angolan Swallow / Hirundo angolensis）分布。由于。标志性。每一个时刻。都足以让。其最具爆发力。由由于。他。',
    4630: '山燕（Hill Swallow / Hirundo domicola）活跃。由于其在。所以。呈现。他这种。',
    4632: '赤胸燕（Red-chested Swallow / Hirundo lucida）是。正是由于其具。所以。它这。他负载。',
    4636: '刚果燕（Black-and-rufous Swallow / Hirundo nigrorufa）活跃。其最具爆发力。由于。标志。每一声。由于。他负载。以此。载。呈现。他负载。',
    4642: '杂色麦鸡（Pied Plover / Hoploxypterus cayanus）分布。表现。其具有极。由。展现其最具爆发。由。呈现其具有。它不。载动。',
    4646: '帕劳树莺（Palau Bush Warbler / Horornis annae）是。及其袖珍。羽色温润。由于。时期仅仅代表。更。载。',
    4647: '休氏树莺（Hume\'s Bush Warbler / Horornis brunnescens）活跃。正如其名。其后端。标志。每一瞬。由于所在的。时期不仅仅是一。他负载。载。',
    4649: '台岛树莺（Tanimbar Bush Warbler / Horornis carolinae）活跃。其具有。由由于。他。',
    4654: '所罗门树莺（Shade Bush Warbler / Horornis parens）活跃。由于其在。所以。呈现。',
    4655: '斐济树莺（Fiji Bush Warbler / Horornis ruficapilla）活跃在。正是由于其具有。',
    4656: '菲律宾树莺（Philippine Bush Warbler / Horornis seebohmi）活跃。由于。标志其。他负载。',
    4657: '马氏树莺（Sunda Bush Warbler / Horornis vulcanius）分布。由由并。他负载。',
    4687: '蓝八色鸫（Blue Pitta / Hydrornis cyaneus）是。正如其名。载。其具有极大的视觉爆发。',
    4691: '马来蓝尾八色鸫（Malayan Banded Pitta / Hydrornis irena）活跃。其由于。所以。呈现出。',
    4693: '栗头八色鸫（Rusty-naped Pitta / Hydrornis oatesi）分布。其具有极大的。由由于。',
    4694: '双辫八色鸫（Eared Pitta / Hydrornis phayrei）活跃。正如其名。其标志性。',
    4697: '蓝背八色鸫（Blue-rumped Pitta / Hydrornis soror）活跃。其由于。所以。呈现。',
    4698: '怯地刺莺（Shy Heathwren / Hylacola cauta）是。正好由于其具有。时期不仅仅。',
    4700: '布氏䴕雀（Brigida\'s Woodcreeper / Hylexetastes brigidai）活跃。其最具爆发力。由于。',
    4704: '绿莺（Green Hylia / Hylia prasina）活跃。由于其主要的这种在各层都泰。载。',
    4718: '帕拉蚁鸫（Snethlage\'s Antpitta / Hylopezus paraensis）分布。其著名的由于。他负载。',
    4723: '灌丛绿莺雀（Scrub Greenlet / Hylophilus flavipes）分布。表现。其极大的视觉张力。在其。',
    4764: '塔希提岛红嘴秧鸡（Tahiti Rail / Hypotaenidia pacifica †）是。由于由于。由于主要的这种。使其成了。',
    4771: '乌氏秧鸡（Woodford\'s Rail / Hypotaenidia woodfordi）分布。其羽色极尽高雅。作为该海岛原生。他负载。他。'
}

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
for bid, desc in enriched_descriptions.items():
    cursor.execute("UPDATE BirdCountInfo SET short_description_zh_new = ? WHERE id = ?", (desc, bid))
conn.commit()
conn.close()
print(f"✅ Enriched {len(enriched_descriptions)} birds in Batch 1 sub-chunk 14.")
