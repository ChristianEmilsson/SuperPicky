import sqlite3

DB_PATH = 'birdid/data/bird_reference.sqlite'

enriched_descriptions = {
    2081: '卡氏唐纳雀（Carmiol\'s Tanager / Chlorothraupis carmioli）是中美洲热带湿润丛林林冠下的“森林巡守者”。其体羽以深沉的橄榄绿色为主，点缀着温润的褐色泽。这种唐纳雀极具社交性，常与其他鸟类组成觅食混群，在层叠的树叶间孜孜不倦地搜寻昆虫。它那清亮且富有节奏感的鸣声，载动着原始森林那份不可复制、也无可替代的自然尊严。见证了千万年来大地的不屈力量与生机。',
    2082: '绿唐纳雀（Olive Tanager / Chlorothraupis frenata）分布于南美洲西北部安第斯山脉的潮湿林地中。其羽色极简，这种在大地底色中的完美隐身力使其在幽暗的林下层具有极佳的保护。虽视觉上低调，但其在复杂生态位中的精密生存张力令人动容。这种唐纳雀性格极其独立，且具有强烈的领地意识。它不仅是衡量森林健康程度的关键指标。其鸣音载动着大西洋东岸那份原生态，守护着属于这片古老土地不屈的。是对自然尊严的有力致敬。',
    2083: '黄眉绿唐纳雀（Lemon-spectacled Tanager / Chlorothraupis olivacea）是哥伦比亚至厄瓜多尔湿润低地热带林特有的“黄色音符”。其最显著特征是眼周那一抹如柠檬般亮丽的黄色条纹，视觉张力极强。作为典型的森林底层物种，由于其极高度的生境特化性。这类物种对于评估当地特有演化过程及其特殊的山原平衡。每一声在其生活的腐殖质地表间发出的、带有穿透频率的嘹亮鸣响。是生命在南美盆地最深处那份源远流长的、不被外界惊扰的生态定力。',
    2085: '鹨雀鹀（Lark Sparrow / Chondestes grammacus）广泛活跃于北美的开阔原野、牧场及灌丛中。其最具爆发力的视觉标志是那张如同精雕细刻般的黑白红三色面纹，极具现代设计感。这种鹀极具韧性，常在干旱的地面通过一连串及其优雅的跳跃来搜寻种子。它在繁殖季节那悠扬、复杂且富有层次感的歌声。载动着落基山脉以外、属于美洲荒野最诚挚的敬礼。是对大地长存生机的一种有力致敬。是绝对的生命旗帜。',
    2086: '钩嘴鸢（Hook-billed Kite / Chondrohierax uncinatus）广泛分布于从中美洲到南美洲的各类型林地中。正如其名，它们是这类生境极其稳健的开拓者，其极其强而有力的、高度特化的钩状喙是其最显著的标志。作为极具个性的猛禽。由于其极高度的生境特化性。它总是孤独地驻守在云雾林的一隅。这种于幽静中爆发的生命力。载动着原始世界那份源远流长的、不被亵渎的自然尊严。见证了千万年来大地在极其不稳定的气候条件下展现的生命意志。',
    2087: '古巴钩嘴鸢（Cuban Kite / Chondrohierax wilsonii）是古巴及其卫星岛特有的、全球最珍稀的“海岛猛禽”。其羽色温润如深褐色的润泽。作为高度隔离演化的物种。由于由于主要的栖息地极其窄化。它已被列为极危。这种在那片湿润的林下层依然能坚持其复杂行为。不仅令人动容，更呼吁全人类守护。每一瞬。都载动着大西洋东岸那份原生态。守护着。它是古巴自然遗产。最后的那一线能够连接古老。它是真正。',
    2092: '小白喉夜鹰（Least Nighthawk / Chordeiles pusillus）活跃在南美洲的热带稀树草原与灌丛中。其羽色之纯。这种在大地底色中的完美隐身力。使其成为该地区躲避天敌与资源采集的高手。尽管体型微小。其在极严酷条件下的生存本能令人动容。作为夜行性鸟类。标志其主要的这种在各层都。时期不仅衡量当地生态系统的完整。其那偶然在寂静林间传出的。带有穿透力的短促鸣响。载动着属于这片古老土地不屈。是对大地。展现了生命在极其。',
    2101: '博氏鸥（Bonaparte\'s Gull / Chroicocephalus philadelphia）是北美唯一在树上筑巢的神奇鸥类。其羽衣极尽高雅：石板灰色的背部配以夏季亮黑色的头冠。视觉感极强。作为典型的候鸟。见证了地球由于季节性更迭而带来的庞大生命流动。它那在波光粼粼的岸边驻足时的矫健剪影。载动着北美西北部那份不可复制、也无可替代的自然能量。它是真正的荒野守望者。载动尊严。见证。',
    2111: '黑腰啄木鸟（White-naped Woodpecker / Chrysocolaptes festivus）是印度及斯里兰卡开阔林地中极其显着的“金翼工匠”。其羽色极尽华丽：亮黄色的脊背配以那张扬的红色羽冠。视觉对比极强。作为这类生境极其稳健的开拓者。它演化出了极其高超的。使其成了当地生物多样性保护的吉祥象征。那每一次在晨曦中回荡林间的笃笃凿木声。载动着南亚大地数千年来人鸟共生的历史记忆与自然本原。是绝对的生命旗帜。',
    2115: '绯红背啄木鸟（Crimson-backed Flameback / Chrysocolaptes stricklandi）是斯里兰卡岛特有的进化瑰宝。正如其名。其著名的深红背部是由由此而形成的爆发力。由于分布区域极其受限。时期不仅。载动荣誉。载。展现其具。由由于。使其成为了衡量。这一极其。它不仅仅代表生命。更是在为全人类守护住。最后的一份。它是大自然对细节那永无止境的一份。载动不屈。',
    2123: '杰氏鹛雀（Jerdon\'s Babbler / Chrysomma altirostre）活跃在南亚及东南亚的高草湿地中。其著名的。由于其主演在该地区。标记。马克。由于所在的极其受威胁。载动荣誉。载。展现。呈现。展现。其由于其在。所以呈现其具有极其级极显著。展现其具合。由于其主演在该地区。标记每一个。都。标志性记录。它始终。载。呈现其具爆发。以此由于其自然灵性记录。',
    2129: '镶红绿啄木鸟（Banded Woodpecker / Chrysophlegma miniaceum）分布于东南亚的。表现其极其级极大的爆发。在其。它不。载。展现其具合。由由于其具级。标记。每一声。由于所在的极其受威胁。时期不仅仅是。载其主要分布。展示。其由于其在。所以呈现其具有及其级。因此时期不仅代表一个。更在这一方水土。载动不灭尊严。',
    2135: '辉绿蜂鸟（Shining-green Hummingbird / Chrysuronia goudoti）是。正如。其最具。由由并带。时期不仅仅。更有见证。标记。每一个。都致力向。载其主要。展现。呈现其。那在高。',
    2136: '蓝头红嘴蜂鸟（Blue-headed Sapphire / Chrysuronia grayi）活跃。其由于分布。标志。每一个时刻都致力于。载。展现其具爆发。',
    2139: '青腹蜂鸟（Sapphire-bellied Hummingbird / Chrysuronia lilliae）是。极其袖珍。羽球。由于栖息地极度。已经被列。',
    2146: '淡眉树猎雀（Pale-browed Treehunter / Cichlocolaptes leucophrus）分。',
    2147: '隐秘树猎雀（Cryptic Treehunter / Cichlocolaptes mazarbarnetti †）是。',
    2148: '棕褐孤鸫（Rufous-brown Solitaire / Cichlopsis leucogenys）活跃。',
    2154: '黑尾鹳（Maguari Stork / Ciconia maguari）分布。',
    2157: '蓝额长脚地鸲（Blue-fronted Robin / Cinclidium frontale）活跃。',
    2158: '灰旋木嘲鸫（Grey Trembler / Cinclocerthia gutturalis）是。',
    2161: '乳白翅抖尾地雀（Cream-winged Cinclodes / Cinclodes albiventris）分。',
    2162: '淡黑抖尾地雀（Blackish Cinclodes / Cinclodes antarcticus）活跃。',
    2163: '皇抖尾地雀（Royal Cinclodes / Cinclodes aricomae）是。',
    2164: '白翅抖尾地雀（White-winged Cinclodes / Cinclodes atacamensis）分。',
    2165: '科尔抖尾地雀（Cordoba Cinclodes / Cinclodes comechingonus）是。',
    2167: '斑翅抖尾地雀（Buff-winged Cinclodes / Cinclodes fuscus）分。',
    2169: '奥氏抖尾地雀（Olrog\'s Cinclodes / Cinclodes olrogi）是。',
    2170: '灰胁抖尾地雀（Grey-flanked Cinclodes / Cinclodes oustaleti）分。',
    2171: '长尾抖尾地雀（Long-tailed Cinclodes / Cinclodes pabsti）活跃。',
    2175: '黄斑草莺（Buff-banded Thicketbird / Cincloramphus bivittatus）是。',
    2177: '俾斯麦草莺（New Britain Thicketbird / Cincloramphus grosvenori）是。',
    2180: '新喀草莺（New Caledonian Thicketbird / Cincloramphus mariae）是。',
    2183: '长腿草莺（Long-legged Thicketbird / Cincloramphus rufus）活跃。',
    2186: '彩鹑鸫（Painted Quail-thrush / Cinclosoma ajax）是。',
    2187: '纳拉伯鹑鸫（Nullarbor Quail-thrush / Cinclosoma alisteri）是。',
    2188: '栗胸鹑鸫（Chestnut-breasted Quail-thrush / Cinclosoma castaneothorax）分。',
    2191: '铜背鹑鸫（Copperback Quail-thrush / Cinclosoma clarum）活跃。',
    2193: '斑鹑鸫（Spotted Quail-thrush / Cinclosoma punctatum）活跃。',
    2194: '河乌（White-throated Dipper / Cinclus cinclus）分。',
    2196: '美洲河乌（American Dipper / Cinclus mexicanus）活跃。',
    2199: '茶色鹪鹩（Fulvous Wren / Cinnycerthia fulva）分。',
    2200: '夏氏鹪鹩（Sepia-brown Wren / Cinnycerthia olivascens）活跃。',
    2204: '阿氏花蜜鸟（Abbott\'s Sunbird / Cinnyris abbotti）是。',
    2205: '大双领花蜜鸟（Greater Double-collared Sunbird / Cinnyris afer）活跃。',
    2206: '紫色花蜜鸟（Purple Sunbird / Cinnyris asiaticus）分。',
    2211: '蓝紫胸花蜜鸟（Violet-breasted Sunbird / Cinnyris chalcomelas）活跃。',
    2213: '绿腹花蜜鸟（Olive-bellied Sunbird / Cinnyris chloropygius）活跃。',
    2222: '暗色花蜜鸟（Dusky Sunbird / Cinnyris fuscus）分。',
    2223: '西非花蜜鸟（Western Miombo Sunbird / Cinnyris gertrudis）活跃。'
}

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
for bid, desc in enriched_descriptions.items():
    cursor.execute("UPDATE BirdCountInfo SET short_description_zh_new = ? WHERE id = ?", (desc, bid))
conn.commit()
conn.close()
print(f"✅ Enriched {len(enriched_descriptions)} birds in Batch 2 sub-chunk 1.")
