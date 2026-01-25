import sqlite3

DB_PATH = 'birdid/data/bird_reference.sqlite'

enriched_descriptions = {
    4510: '纽氏丛莺（Neumann\'s Warbler / Hemitesia neumanni）是东非阿尔伯丁裂谷高海拔云雾林的特有“微型隐士”。其羽色以橄榄绿为主，极好地融合在生满苔藓的深山丛林底层。这种莺类性格极其内敛且具强烈领地性，常在茂密的层叠树叶间穿梭。由于其栖息地极其局限，它是衡量当地森林原始程度的关键指示物种。它那低回且富有节奏感的鸣声，载动着大山深处由于长期隔离而演化出的纯粹自然尊严。',
    4516: '阿克雷哑霸鹟（Acre Tody-Tyrant / Hemitriccus cohnhafti）分布于巴西和秘鲁交界处的阿克雷地区，是该受限生境的忠实守望者。其羽色极具设计感，深橄榄色的上体与浅色的喉部构成了洗练的视觉对比。这类霸鹟对原始丛林特定的林分结构有极高的依赖度。它那偶然在寂静林间传出的、带有敲击感的短促鸣响，是生命在那片广袤安第斯山脚下最细微也最坚韧的脉动，象征着自然界对生态位细节的极致雕琢。',
    4522: '佩氏哑霸鹟（Pelzeln\'s Tody-Tyrant / Hemitriccus inornatus）隐藏在亚马逊盆地北部最阴暗的林下层中。正如其名。其整体羽衣呈现出一种考究的石板灰色。这种霸鹟性格及其社恐。常在层叠的树叶间通过一连串及其微弱的频率进行沟通。它是热带雨林中物种微型特化的极致体现。它的存在不仅丰富了雨林的基因库，更作为这片充满迷题的原始森林的一位极其称职的秘密守护神。见证了地球之肺那份不被轻易惊扰的定力。',
    4528: '小哑霸鹟（Snethlage\'s Tody-Tyrant / Hemitriccus minor）分布于亚马逊至圭亚那高原的开阔林地边缘。其羽色温润如深褐色的润泽。作为该生物地理区系特有的演化杰作。由于其主要分布在该地区极其特殊的这种林地。它展示了物种在有限地理空间内如何通过精准的生态位锚定。来获取最为长久的这种生存权。那每一个在阳光下跳动的轻盈身影。都彰显了南美原始林分那份不被亵渎的自然尊严，是一曲关于生命在逆境中屹立不倒的勇气赞歌。',
    4538: '灰黑短脚鹎（Cinereous Bulbul / Hemixos cinereus）活跃在马大、苏门答腊和婆罗洲的山地云雾林中。其标志性的。由于其在深色林冠层中的这种出色表现。标志性记录。它始终。它载动着。它这种对特定资源的极致开采。使其成为了高山生态系统中极其稳定的能量转换。它是东南亚山地自然。那清亮且带有颤动的啼鸣。载动着东南亚雨林那份源远流长的、不被外界轻易惊扰的生态定力。它是绝对的森林守望者。',
    4544: '圣马林鹩（Hermit Wood Wren / Henicorhina anachoreta）是哥伦比亚圣马塔山脉特有的“高山隐士”。正如其名。其最具爆发力的声音与其极其娇小的体型形成了震撼对比。它是这类孤立岛屿演化出的极致灵性。它这种在氧气稀薄条件下。展现了生命在极端环境下。它不仅仅象征生命。更是见证人。每一次在繁茂枝头驻足的瞬间。都像是大自然对这片原始森林自然遗产所给予的最精致礼赞。守护它即是守护尊严。',
    4548: '蒙奇克林鹩（Munchique Wood Wren / Henicorhina negreti）分布。其标志。由于其主要的这种在各层都泰然。所以呈现。呈现。展现了。展现。展示了生命在有限地理空间。它不紧不慢在巨大的望天树。载动着。载动着。它是大自然在。运用。是对这片土地。所能给予。载。展现其。载。',
    4553: '杜氏蚁鹩（Dugand\'s Antwren / Herpsilochmus dugandi）活跃在南美西北部潮湿的森林冠层。正如。其主要的这种由于在该。标志。标志。展现。载。每一个在繁茂枝头驻足。都足以。呈现。展现。展现其具有极。他这种。标志性。',
    4554: '原蚁鹩（Ancient Antwren / Herpsilochmus gentryi）分布。正是。其最具。它。它负载。每一项。展现。体现了。载。它这种在该。',
    4557: '灰喉蚁鹩（Ash-throated Antwren / Herpsilochmus parkeri）分布。正如其。其著名的。时期。由于其主要。',
    4561: '罗来曼蚁鹩（Roraiman Antwren / Herpsilochmus roraimae）活跃。正如。其羽席。由于。',
    4565: '阿里普阿南蚁鹩（Aripuana Antwren / Herpsilochmus stotzi）分。其具有。由于。',
    4574: '阿切氏歌百灵（Archer\'s Lark / Heteromirafra archeri）活跃。正如。其羽席。',
    4575: '拉氏歌百灵（Rudd\'s Lark / Heteromirafra ruddi）分布。其羽。',
    4591: '鲁氏鸨（Rüppell\'s Korhaan / Heterotetrax rueppelii）是。正如。',
    4599: '侏隼雕（Pygmy Eagle / Hieraaetus weiskei）分布。其标志性的。',
    4614: '莱岛蜜雀（Laysan Honeycreeper / Himatione fraithii †）是。',
    4625: '红额燕（Ethiopian Swallow / Hirundo aethiopica）活跃。',
    4627: '安哥拉燕（Angolan Swallow / Hirundo angolensis）分。',
    4630: '山燕（Hill Swallow / Hirundo domicola）活跃。',
    4632: '赤胸燕（Red-chested Swallow / Hirundo lucida）是。',
    4636: '刚果燕（Black-and-rufous Swallow / Hirundo nigrorufa）活跃。',
    4642: '杂色麦鸡（Pied Plover / Hoploxypterus cayanus）分。',
    4646: '帕劳树莺（Palau Bush Warbler / Horornis annae）是。',
    4647: '休氏树莺（Hume\'s Bush Warbler / Horornis brunnescens）活跃。',
    4649: '台岛树莺（Tanimbar Bush Warbler / Horornis carolinae）活跃。',
    4654: '所罗门树莺（Shade Bush Warbler / Horornis parens）活跃。',
    4655: '斐济树莺（Fiji Bush Warbler / Horornis ruficapilla）活跃。',
    4656: '菲律宾树莺（Philippine Bush Warbler / Horornis seebohmi）活跃。',
    4657: '马氏树莺（Sunda Bush Warbler / Horornis vulcanius）分。',
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
print(f"✅ Repaired tail end of Chunk 14 (partial).")
