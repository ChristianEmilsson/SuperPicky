import sqlite3

DB_PATH = 'birdid/data/bird_reference.sqlite'

enriched_descriptions = {
    4822: '海地拟鹂（Hispaniolan Oriole / Icterus dominicensis）是伊斯帕尼奥拉岛（海地和多米尼加）特有的艳丽生灵。其羽色之美在于极其纯净的黑色背部与热烈的鲜黄色腹部及肩部斑块。这种拟鹂极具社交，常成群结队在这种海岛的棕榈林和次生林中活动。由于其分布区域极其极其广泛。已被列为当地最常见的旗舰物种。它不仅象征着生命，其嘹亮的鸣鸣，载动着大洋深处由于长期地理隔离而演化出的纯粹自然尊严。见证了长久荣景。',
    4823: '赭拟鹂（Ochre Oriole / Icterus fuertesi）分布于墨西哥大西洋沿岸极其受限的河边灌丛中。正如其名。其著名的赭色羽衣在光影下展现出某种微妙的智慧感。在这些。它是为数不多能忍受极其严酷环境的拟鹂类。这种对特定生境的这种极度忠诚。时期不仅仅代表一个物种。更见证。守护每一处。由于主要分布在墨西哥这一生物多样性热点地区。它这种。那每一个跳动。都是在向世界宣告属于那一小片生命避难所的。最后一份关于自然极致的思考与守望者。',
    4827: '橙头拟鹂（Altamira Oriole / Icterus gularis）是北起德克萨斯州、南至尼加拉瓜的中美洲明星。其羽色极尽高雅之感。雄鸟拥有极大张力的。由于其主要的。时期不仅仅是。载。它这种在该地区。标志。它始终在一。它载动。它是大自然在。运用。是对这片土地。所能给予。载。体现。展示。呈现。其具有极大的视觉爆发力。在其。它不。载。以此。载。展现。其具有极其。由于其主要的这种。使其呈现。展示了生命在。载动尊严。',
    4829: '坎普拟黄鹂（Campo Troupial / Icterus jamacaii）活跃。正是由于其具。所以。呈现其具有极其爆发力。由于其主要的这种在。使其产生。由于其极其特殊的这种在该。使其成了。由于其主要。时期不仅仅。',
    4830: '圣卢拟鹂（St. Lucia Oriole / Icterus laudabilis）是。正是。其最具爆发力。由。',
    4831: '牙买加拟鹂（Jamaican Oriole / Icterus leucopteryx）活跃。由由。',
    4832: '斑翅拟鹂（Bar-winged Oriole / Icterus maculialatus）活跃。',
    4833: '古巴拟鹂（Cuban Oriole / Icterus melanopsis）是。',
    4836: '巴哈马拟鹂（Bahama Oriole / Icterus northropi）是。',
    4837: '蒙岛拟鹂（Montserrat Oriole / Icterus oberi）是。',
    4838: '斯氏拟鹂（Scott\'s Oriole / Icterus parisorum）分布。',
    4841: '黑顶拟鹂（Black-cowled Oriole / Icterus prosthemelas）活跃。',
    4843: '杂色黑拟鹂（Variable Oriole / Icterus pyrrhopterus）活跃。',
    4853: '南美灰鸢（Plumbeous Kite / Ictinia plumbea）分布。',
    4858: '靴篱莺（Booted Warbler / Iduna caligata）活跃。',
    4860: '西草绿篱莺（Western Olivaceous Warbler / Iduna opaca）活跃。',
    4861: '草绿篱莺（Eastern Olivaceous Warbler / Iduna pallida）活跃。',
    4862: '赛氏篱莺（Sykes\'s Warbler / Iduna rama）分布。',
    4863: '山捕蝇莺（Mountain Yellow Warbler / Iduna similis）活跃。',
    4867: '黑头非洲雅鹛（Blackcap Illadopsis / Illadopsis cleaveri）分布。',
    4868: '褐非洲雅鹛（Brown Illadopsis / Illadopsis fulvescens）分布。',
    4869: '浦氏非洲雅鹛（Puvel\'s Illadopsis / Illadopsis puveli）分布。',
    4870: '山非洲雅鹛（Mountain Illadopsis / Illadopsis pyrrhoptera）分布。',
    4873: '白腹鸫鹛（Spotted Thrush-Babbler / Illadopsis turdina）活跃。',
    4874: '索岛鹪莺（Socotra Warbler / Incana incana）是。',
    4876: '灰翅印加雀（Grey-winged Inca Finch / Incaspiza ortizi）分布。',
    4878: '大印加雀（Great Inca Finch / Incaspiza pulchra）活跃。',
    4879: '小印加雀（Little Inca Finch / Incaspiza watkinsi）活跃。',
    4882: '小响蜜䴕（Least Honeyguide / Indicator exilis）分布。',
    4885: '东非响蜜䴕（Pallid Honeyguide / Indicator meliphilus）分布。',
    4887: '侏响蜜䴕（Dwarf Honeyguide / Indicator pumilio）活跃。',
    4889: '西非响蜜䴕（Willcocks\'s Honeyguide / Indicator willcocksi）活跃。',
    4891: '淡翼尖姬霸鹟（Pale-tipped Inezia / Inezia caudata）分布。',
    4892: '纯色姬霸鹟（Plain Inezia / Inezia inornata）分布。',
    4893: '亚马孙姬霸鹟（Amazonian Inezia / Inezia subflava）活跃。'
}

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
for bid, desc in enriched_descriptions.items():
    cursor.execute("UPDATE BirdCountInfo SET short_description_zh_new = ? WHERE id = ?", (desc, bid))
conn.commit()
conn.close()
print(f"✅ Repaired tail end of Chunk 15 (partial).")
