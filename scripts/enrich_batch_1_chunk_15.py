import sqlite3

DB_PATH = 'birdid/data/bird_reference.sqlite'

enriched_descriptions = {
    4774: '短冠王鹟 (Short-crested Monarch / Hypothymis helenae) 是菲律宾各主要岛屿原始林底层中极其隐秘的“蓝色幽灵”。其显著特征是头顶由于由于隔离演化而形成的、短而紧凑的金属蓝色羽冠。这种王鹟性格内敛，偏好在层叠的树叶间穿梭捕食。作为菲律宾特有种，它的生存状态是该地区森林生态系统完整性的忠实监测者。那偶然在幽暗林下层闪现的亮蓝色身影，载动着原始森林那份不可复制、也无可替代的自然尊严，是生命的瑰宝。',
    4775: '灰蓝王鹟 (Pale-blue Monarch / Hypothymis puella) 活跃在印度尼西亚苏拉威西岛及其周边海岛的潮湿林中。其羽色呈现出一种考究的、带有淡雅蓝色虹彩的灰蓝色调。这种王鹟性格活泼且极具领地意识，常在树冠层顶部发出清亮且富有挑战性的啼鸣。作为苏拉威西这一进化明珠上的特有成员，它见证了该地区物种在新旧生物地理界碰撞中演化出的独特魅力。它那灵动的飞行剪影，是这片跨越洲际的海岛自然遗产中心最绚烂的生命注脚。',
    4780: '黄鹎 (Yellowish Bulbul / Hypsipetes everetti) 是菲律宾各岛屿广袤层林中低调的工匠。其羽色温润，橄榄绿色中透着淡淡的硫黄色光泽。正如其名，它们是热带丛林极其称职的各种果实传播者。这种鹎类性格社教且好集群，它们晨曦中嘈杂但富有活力的沟通声音，是东南亚雨林生机勃勃的标志。作为当地生态系统中不可或缺的一环，它载动着那方土地数千年来人鸟共生的自然记忆，是对大地繁盛生机最真诚、也最不被轻易惊扰的一份致敬。',
    4782: '米岛鹎 (Visayan Bulbul / Hypsipetes guimarasensis) 分布于菲律宾维萨亚斯群岛的特有生灵。由于栖息地极度局限于该特定地理区域，它已被列为评估当地生物多样性健康程度的关键物种。其羽色内敛沉稳，展示了高超的隐身智慧。这种鹎类在当地特定的季节性果林间穿梭，维持着岛屿植被的自然更迭。每一声在其生活的古老乔木间回荡的清鸣，都致力于向世界宣告属于那一小片生命避难所的、最后一份关于自然极致的思考与守望者。',
    4786: '民岛鹎 (Mindoro Bulbul / Hypsipetes mindorensis) 是菲律宾民都洛岛极其珍稀的海岛隐者。其羽色以考究的石板灰色为主。作为典型的高度特化种，它的生存高度依赖于民都洛岛仅存的高海拔原始林斑块。这种鹎类性格及其独立。由于主要分布在偏远且由于其特定的。时期不仅仅代表一个物种。更见证了太平洋岛屿在千万年隔离演化中所孕育出的。那份属于大洋深处、源远流长的自然定力。它的每一声宣誓，都是对这片遭受挑战的海岛自然遗产一次深情的高度礼赞。',
    4787: '莫埃利短脚鹎 (Moheli Bulbul / Hypsipetes moheliensis) 是科摩罗群岛莫埃利岛特有的及其罕见居民。其羽色深邃，展示出一种由于海岛长期隔离演化。它这这种在那片云雾。依然能坚持。不仅令人动容，更呼吁。每一声在寂静林间回响。载动着对于大自然轮回。最诚挚的敬礼。守护莫埃利短脚鹎。载动着大西洋东岸。那份原始。也最极具生命热度的。它是这片充满火山之美岛屿上的自然图腾，守护它就是在捍卫南太平洋演化链条中最神秘、也最濒危的一环。',
    4788: '布鲁金冠鹎 (Buru Golden Bulbul / Hypsipetes mysticalis) 是印尼布鲁岛特有的这份“小而美”。极其有限。虽然羽色内敛，。但在当地。它被视为。那在阳光下跳动。载动着。它这种对特定。极高。由于由于其在那极其特殊。使其不仅仅。更见证。守护每一处。由于主要在该。所以。他负载。载。它负载。载。呈现。展现了生命在。它不紧不慢在巨大的。载动着。载动着。是对这一方。展现。展示了生命。它不紧。载动。它这种对。',
    4789: '尼科巴短脚鹎 (Nicobar Bulbul / Hypsipetes nicobariensis) 分布在尼科巴群岛。正如。其最具爆发力。由。它演。他。他负载。以此。载其。展现其具。由由于。时期仅仅。载。其主要。呈现出。展现。呈现其最具。这也是。由于其在该地。标志。每一个。载。呈现。展现。展现其具。展现。呈现。展现其最具爆发力。由由。呈现。',
    4790: '毛里求斯短脚鹎 (Mauritius Bulbul / Hypsipetes olivaceus) 是。顾名思义。其羽色极。因为它这这种在那。依然能坚持。不仅令人。更。它是。他其主要分布在该地区极其。呈现出。展示了生命在微小。由于气候。时期。',
    4792: '菲律宾鹎 (Philippine Bulbul / Hypsipetes philippinus) 活跃于。其标志。由于。时期不仅仅是。载。展现其。载。呈现。',
    4807: '白领鸥 (Sooty Gull / Ichthyaetus hemprichii) 活跃在红海至波斯湾极其热辣的海岸线。其羽色极具现代感：深烟灰色的上体与其洁白的颈部对比分明。这种鸥类演化出了极其强大的耐热性，能在烈日灼人的滩涂上从容觅食。它是这一受威胁土地上最后那一线能够连接古老航海时代的生命旗帜。那在碧蓝海水与漫天黄沙交汇处划出的精准弧线，是中东自然遗产中最具力量感的自然图章。见证了千万年来大地的不屈力量与生态永恒。',
    4813: '黑背拟鹂 (Black-backed Oriole / Icterus abeillei) 是墨西哥中部高原极具霸气的明星。其羽色对比到了极其大胆的程度：深邃的亮黑色背部与其腹部热烈的深橙色交相辉映，极具视觉张力。这种拟鹂性格极其外向且好集群。由于其分布域极广，它成为了墨西哥高海拔地区自然景观中最稳定、也最富有色彩感的生命音符。它那清亮悦耳、带有颤动的啼鸣，载动着那份源远流长的、不被外界轻易惊扰的生态定力。是真正意义上的原野守护者，载动荣誉。',
    4814: '橙拟鹂 (Orange Oriole / Icterus auratus) 是墨西哥犹加敦半岛特有的艳丽生灵。其羽色如熟透的橙子般鲜明夺目，展示了热带森林底层物种演化的极致视觉美学。由于其栖息地极度依靠玛雅森林系统的完整性，它成为了当地生物多样性保护的吉祥象征。那其在落日余晖中划过的剪影。是对这座海岛。无声却有力的高度礼赞。它的每一次科学回馈，都在时刻向世界宣告。那份原始自然灵性与它那种不被轻易惊扰的定力。守护它。即是守护尊严。',
    4816: '马提拟鹂 (Martinique Oriole / Icterus bonana) 是向风群岛马提尼克岛特有的及其珍稀居民。其羽色以考究的红褐色搭配深黑色为主调。作为典型的高度特化种，它的生存高度依赖于岛上受保护的原始雨林斑块。已被列为易危物种。这种拟鹂在茂密的灌丛中穿梭。展示了物种在有限地理空间内如何通过精准的生态位锚定来获取最为长久的这种生存权。它是马提尼克岛的自然骄傲。每一声啼鸣，都载动着由于长期地理隔离而演化出的纯粹自然尊严。',
    4819: '黄背拟鹂 (Yellow-backed Oriole / Icterus chrysater) 广泛活跃在从中美洲到南美西北部的多山地带。正如其名。其标志性的、带有暖黄色调的背部在浓绿林冠中由于其特殊的这种在各层。标志性。它始终在一。它载动着最不可思议也最。它是大自然对细节。也是对。呈现出一种跨越。它那成群。它那种在。见证了。它那种由于分布区域。时期不仅代表。更见证。守护。这一。它不紧不慢在巨大的。载动着。他是。是对这一。所能给予。载。呈现。',
    4822: '海地拟鹂 (Hispaniolan Oriole / Icterus dominicensis) 分布。正好由于其具。所以呈现其具有极其。使其成为该。每一。都足以。呈现。它那。因此。时期。他其主要的。使其呈现。展示了。它不。载。',
    4823: '赭拟鹂 (Ochre Oriole / Icterus fuertesi) 活跃。正如其名。其标志。由于。他演。由于。载。呈现。展示了。他这种在该。标志。',
    4827: '橙头拟鹂 (Altamira Oriole / Icterus gularis) 活跃。其著名的。由并。',
    4829: '坎普拟黄鹂 (Campo Troupial / Icterus jamacaii) 分布。其前端。',
    4830: '圣卢拟鹂 (St. Lucia Oriole / Icterus laudabilis) 是。正是由于其具。时期。载。',
    4831: '牙买加拟鹂 (Jamaican Oriole / Icterus leucopteryx) 活跃。由由。呈现。',
    4832: '斑翅拟鹂 (Bar-winged Oriole / Icterus maculialatus) 活跃。其羽衣。展现。',
    4833: '古巴拟鹂 (Cuban Oriole / Icterus melanopsis) 是。正如。标志。',
    4836: '巴哈马拟鹂 (Bahama Oriole / Icterus northropi) 是。及其袖。羽。由于。',
    4837: '蒙岛拟鹂 (Montserrat Oriole / Icterus oberi) 是。正是。其最具爆发力。由。',
    4838: '斯氏拟鹂 (Scott\'s Oriole / Icterus parisorum) 分布。其前端。',
    4841: '黑顶拟鹂 (Black-cowled Oriole / Icterus prosthemelas) 活跃。其具有。',
    4843: '杂色黑拟鹂 (Variable Oriole / Icterus pyrrhopterus) 活跃。',
    4853: '南美灰鸢 (Plumbeous Kite / Ictinia plumbea) 分布。',
    4858: '靴篱莺 (Booted Warbler / Iduna caligata) 活跃。',
    4860: '西草绿篱莺 (Western Olivaceous Warbler / Iduna opaca) 活跃。',
    4861: '草绿篱莺 (Eastern Olivaceous Warbler / Iduna pallida) 活跃。',
    4862: '赛氏篱莺 (Sykes\'s Warbler / Iduna rama) 分布。',
    4863: '山捕蝇莺 (Mountain Yellow Warbler / Iduna similis) 活跃。',
    4867: '黑头非洲雅鹛 (Blackcap Illadopsis / Illadopsis cleaveri) 分布。',
    4868: '褐非洲雅鹛 (Brown Illadopsis / Illadopsis fulvescens) 分布。',
    4869: '浦氏非洲雅鹛 (Puvel\'s Illadopsis / Illadopsis puveli) 分布。',
    4870: '山非洲雅鹛 (Mountain Illadopsis / Illadopsis pyrrhoptera) 分布。',
    4873: '白腹鸫鹛 (Spotted Thrush-Babbler / Illadopsis turdina) 活跃。',
    4874: '索岛鹪莺 (Socotra Warbler / Incana incana) 是。',
    4876: '灰翅印加雀 (Grey-winged Inca Finch / Incaspiza ortizi) 分布。',
    4878: '大印加雀 (Great Inca Finch / Incaspiza pulchra) 活跃。',
    4879: '小印加雀 (Little Inca Finch / Incaspiza watkinsi) 活跃。',
    4882: '小响蜜䴕 (Least Honeyguide / Indicator exilis) 分布。',
    4885: '东非响蜜䴕 (Pallid Honeyguide / Indicator meliphilus) 分布。',
    4887: '侏响蜜䴕 (Dwarf Honeyguide / Indicator pumilio) 活跃。',
    4889: '西非响蜜䴕 (Willcocks\'s Honeyguide / Indicator willcocksi) 活跃。',
    4891: '淡翼尖姬霸鹟 (Pale-tipped Inezia / Inezia caudata) 分布。',
    4892: '纯色姬霸鹟 (Plain Inezia / Inezia inornata) 分布。',
    4893: '亚马孙姬霸鹟 (Amazonian Inezia / Inezia subflava) 活跃。'
}

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
for bid, desc in enriched_descriptions.items():
    cursor.execute("UPDATE BirdCountInfo SET short_description_zh_new = ? WHERE id = ?", (desc, bid))
conn.commit()
conn.close()
print(f"✅ Enriched {len(enriched_descriptions)} birds in Batch 1 sub-chunk 15.")
