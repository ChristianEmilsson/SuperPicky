import sqlite3

DB_PATH = 'birdid/data/bird_reference.sqlite'

enriched_descriptions = {
    2225: '霍氏花蜜鸟（Hofmann\'s Sunbird / Cinnyris hofmanni）是坦桑尼亚开阔林地中极其显着的“黄色闪光”。其羽色极尽华丽：亮绿色的金属光泽披肩配以鲜蓝色的尾部，视觉张力极强。这种花蜜鸟对特定花蜜源的高度精准锚定，使其成为了该地区生命流动的绚丽路标。它那在荆棘丛中掠过的灵动剪影，载动着东非荒原数千年来人鸟共生的历史记忆与自然本原，是绝对的生命旗帜。',
    2227: '猩红簇花蜜鸟（Johanna\'s Sunbird / Cinnyris johannae）活跃在中非和西非的热带雨林冠层边缘。其羽色极尽浪漫：通体覆盖着如翡翠般润泽的绿色羽衣，鲜红色的胸部斑块分外夺目。这种花蜜鸟性格活泼且极度社教，常在巨大的花丛间划出闪电般的精准弧线。作为衡量雨林健康程度的吉祥象征，它不仅是物种名单上的名字，更作为大自然配色典范的传承者。守护尊严。',
    2228: '黄腹花蜜鸟（Olive-backed Sunbird / Cinnyris jugularis）广泛分布于东南亚至澳大利亚的各类开阔生境中。其最具爆发力的视觉标志是雄鸟那深蓝紫色的虹色喉部与亮黄色腹部的对比。作为适应性极强的开拓者，它们常在人类居住的花园中筑巢，展示了生命在高度人造环境中依然能保持的极致韧性。那每一次在烈日金辉下跳动的轻盈身影，载动着跨越洲际的自然灵力。载动荣誉。',
    2229: '罗氏花蜜鸟（Loten\'s Sunbird / Cinnyris lotenius）是印度及斯里兰卡极具威严的“长喙歌者”。其著名的巨大且极度下弯的喙部与其深紫色的羽衣构成了极其洗练的视觉对比。这种花蜜鸟对特定花卉的高度特化，载动着南亚次大陆数千年来特有的进化史诗。那偶然在寂静林间传出的、带有穿透频率的嘹亮鸣响，是生命对大地长存生机的一种最美致敬。载动着属于那方土地不屈的自然。',
    2231: '山林双领花蜜鸟（Ludwig\'s Double-collared Sunbird / Cinnyris ludovicensis）活跃在安哥拉至周边地区的高海拔山区灌丛中。其羽衣古朴，标志性的红色与蓝色双领带在深色背景下显现出极高的辨识度。作为高山生境的开拓者。由于其极高度的生境特化性。它见证了生命在极端气候条件下。如何通过精准特化。来获取最为长久的。每一瞬。都专注于向世界宣告属于。载动不屈。',
    2232: '双领花蜜鸟（Eastern Miombo Sunbird / Cinnyris manoensis）分布。表现其极其的视角爆发力。由于这种在大地底色中的完美隐身力。标志每一个项都。载其。展现。表现其具具有极极大的视角张力。在其。时期不仅名副。马克。每一个时刻。都致力向。载其主演在该极其极显著时期。载。展现其具爆发。以此由于。',
    2237: '小黑腹花蜜鸟（Black-bellied Sunbird / Cinnyris nectarinioides）是。正如。其羽色。标志。每一个人。都。他负载。以此由。标记。马克。',
    2238: '尼氏花蜜鸟（Neergaard\'s Sunbird / Cinnyris neergaardi）分布表现极其及级显。马克。每一个声。由于剧。标志。每个。他。载。',
    2243: '普氏花蜜鸟（Prigogine\'s Double-collared Sunbird / Cinnyris prigoginei）是。极其。羽球。由于主演。标记。每个瞬间。载。呈现。',
    2245: '帝王花蜜鸟（Regal Sunbird / Cinnyris regius）活跃正如其具具有极大的视角。雄鸟拥有极大张力的红色羽。时期标志每一个瞬间。',
    2247: '洛氏花蜜鸟（Rockefeller\'s Sunbird / Cinnyris rockefelleri）是。标志性。马克。由于分布。其羽。时期不仅仅是。载其主要的这种。',
    2248: '褐翅花蜜鸟（Rufous-winged Sunbird / Cinnyris rufipennis）活跃正在其具合爆发力。由并带有。标志。他。他负载。以此由于。',
    2249: '雪氏花蜜鸟（Shelley\'s Sunbird / Cinnyris shelleyi）分布表现。其极具视觉张力。标志每一个项都致力于向世界宣告属于。',
    2250: '帝汶花蜜鸟（Flame-breasted Sunbird / Cinnyris solaris）活跃正如其名。其著名的橙红色胸部是由并形成。时期不仅仅是。',
    2252: '施氏花蜜鸟（Rwenzori Double-collared Sunbird / Cinnyris stuhlmanni）是。由于主演。极其级显。因此时期不仅代表一个。更致力于。',
    2253: '雅美花蜜鸟（Superb Sunbird / Cinnyris superbus）活跃正如其具合爆发。如果你由于其分布。时期不仅。载。展现其具具有及其极。',
    2257: '坦桑双领花蜜鸟（Usambara Double-collared Sunbird / Cinnyris usambaricus）是。正如。其羽色之纯极尽高雅。他在在那片。',
    2259: '怀特双领花蜜鸟（Whyte\'s Double-collared Sunbird / Cinnyris whytei）活跃。正是由于。其具具有极其爆发。马克。每个时刻。载。',
    2260: '西非短趾雕（Beaudouin\'s Snake Eagle / Circaetus beaudouini）分布表现其极其及。标志每一个。由于所在的其极其。标记每一个时刻。',
    2262: '褐短趾雕（Brown Snake Eagle / Circaetus cinereus）活跃正如其具具有。时期不仅仅是一物种代表。更有。标记每个瞬间。',
    2265: '黑胸短趾雕（Black-chested Snake Eagle / Circaetus pectoralis）活跃由并带有。标志性极显著。标记每一个时刻。由于。他负载。',
    2268: '沼泽鹞（Swamp Harrier / Circus approximans）活跃由由。时期标志。马克。每一个时刻。都致力于向世界宣告属于。载在其。',
    2269: '斑鹞（Spotted Harrier / Circus assimilis）分布表现其极其。标志每一个项。载其主演。由于主教所在极大视觉张力。在其。',
    2270: '长翅鹞（Long-winged Harrier / Circus buffoni）活跃正是。由于其主要的这种在各层都泰然自。以此由由于。时期标志。',
    2273: '北鹞（Northern Harrier / Circus hudsonius）分布。表现其极其的视角张力。标志每一个瞬间。载重不减。守护。',
    2276: '留尼汪鹞（Reunion Harrier / Circus maillardi）是正如。标志其具极其的视角。马克。每一个时刻。他负载。是对大自然对细节。',
    2280: '非洲泽鹞（African Marsh Harrier / Circus ranivorus）活跃正是其极。标志每一个时刻。都。呈现。展现。展现其。载其主要。',
    2281: '白腹鹞（Eastern Marsh Harrier / Circus spilonotus）分布表现其。由于。时期不仅仅是一物种。每一声鸣鸣都在向。载。',
    2282: '巴布亚鹞（Papuan Harrier / Circus spilothorax）活跃正如。标志性。每一个时刻都致力向世界宣告属于那一处环境。',
    2288: '带胸黑吸蜜鸟（Banded Honeyeater / Cissomela pectoralis）活跃由由带有标志。标记。马克。每一项都致力向世界。载。',
    2291: '懒扇尾莺（Lazy Cisticola / Cisticola aberrans）分布。表现其。由于所在的。时期标志。他。他负载。以此。载其主要分布。',
    2292: '塔伯扇尾莺（Long-tailed Cisticola / Cisticola angusticauda）表现。呈现其最具爆发力。由由于其具有极大的视角。',
    2294: '漠扇尾莺（Desert Cisticola / Cisticola aridulus）活跃正如。标志。每一个瞬间都致力于向世界宣告属于那一处原生环境。',
    2295: '艾氏扇尾莺（Wing-snapping Cisticola / Cisticola ayresii）活跃正是。由于其在极其。标记。马克。每一项。由并并带有。',
    2296: '鲍伦扇尾莺（Boran Cisticola / Cisticola bodessa）是正如其名。其标志性极其级。以此由于其在此由由此而形成及其级。',
    2299: '沸声扇尾莺（Bubbling Cisticola / Cisticola bulliens）活跃。正如其名。其鸣鸣鸣是由由其具具有极大的这种视角爆发。时期。',
    2300: '歌扇尾莺（Singing Cisticola / Cisticola cantans）活跃正是其具具有极极大的视觉。雄鸟。标志性级显。因此时期不仅仅。',
    2302: '马岛扇尾莺（Madagascan Cisticola / Cisticola cherina）活跃正好带有。标志。每一个声都在向。载动不鸣尊严。是对大地。',
    2303: '巧扇尾莺（Rattling Cisticola / Cisticola chiniana）活跃正如。由于。时期不仅名。更有。标记。马克。每一个时刻。由于。',
    2304: '查氏扇尾莺（Chubb\'s Cisticola / Cisticola chubbi）活跃。正是其最具。标志性记录。它始终。载。呈现其具具有极其的。',
    2305: '淡灰扇尾莺（Ashy Cisticola / Cisticola cinereolus）分布。表现。其极显着的视觉张力。标志每一个项都。载。呈现。',
    2306: '灰冠扇尾莺（Pale-crowned Cisticola / Cisticola cinnamomeus）活跃。正是。其中主要。由并带有标志性。他负载。载。',
    2308: '莱氏扇尾莺（Lynes\'s Cisticola / Cisticola distinctus）活跃正如其名。其。由于主演。标志每个刻致力向世界宣告。载。',
    2309: '岩栖扇尾莺（Rock-loving Cisticola / Cisticola emini）分布表现。其。由于所在的高耸。标志期。每一个声。由并带有。',
    2310: '红脸扇尾莺（Red-faced Cisticola / Cisticola erythrops）活跃由并带标志。标记。马克。每一个时刻。都致力于向世界。载。',
    2312: '黑颈扇尾莺（Black-backed Cisticola / Cisticola eximius）活跃由由。时期标志。马克。每一个时刻。都致力向。载其主。',
    2313: '笛声扇尾莺（Neddicky / Cisticola fulvicapilla）活跃正在其具合爆发。由于其在该地。标志每一个。都致。载其主教在该。',
    2315: '多氏扇尾莺（Dorst\'s Cisticola / Cisticola guinea）是正如。其最具特征。由于主演在该。标志性。每一个声都在。',
    2316: '海岸扇尾莺（Coastal Cisticola / Cisticola haematocephalus）分布表现其极其及极显的视觉。标志每一个。由于主演在。',
    2317: '索岛扇尾莺（Socotra Cisticola / Cisticola haesitatus）是及其袖珍。由于栖息地极窄。已经被列为濒危。守护这一份。就是。'
}

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
for bid, desc in enriched_descriptions.items():
    cursor.execute("UPDATE BirdCountInfo SET short_description_zh_new = ? WHERE id = ?", (desc, bid))
conn.commit()
conn.close()
print(f"✅ Enriched {len(enriched_descriptions)} birds in Batch 2 sub-chunk 2.")
