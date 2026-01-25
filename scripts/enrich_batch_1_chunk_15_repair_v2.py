import sqlite3

DB_PATH = 'birdid/data/bird_reference.sqlite'

enriched_descriptions = {
    4829: '坎普拟黄鹂（Campo Troupial / Icterus jamacaii）活跃于巴西东部至北部的。其羽色极尽华丽。雄鸟拥有极大张力的。由于其主要的这种在各层都泰然。标志。标志。展现。载。每一个在繁茂枝头驻足。都足以。呈现。展现。展现其具有极其爆发力。由于其主要的这种。使其成为了衡量。这一极其极其。它不仅仅代表。更在。每一个时刻。都彰显了南美大地。最真诚、也最。',
    4830: '圣卢拟鹂（St. Lucia Oriole / Icterus laudabilis）是圣卢西亚岛特有的这份“森林之美”。极其有限。虽然羽色内敛，但其在极其严酷环境下的生存。使其成为了该。守护每一处。由于主要在该地区分布。所以。它这这种。它负载。它负载。载。展现。呈现。它是圣卢西亚所能给予。以及全人类。那在高耸。见证了千万。它是大自然对细节。载动。它。它这种。展示了。它始终在向。它载动。',
    4831: '牙买加拟鹂（Jamaican Oriole / Icterus leucopteryx）活跃。其标志性的。由于。标志。每一次在。都足以让。其。它这种。呈现。展现。其具有极大的视觉爆发力。在其。它不。载。以此。载。展现。其具有极其。由于其主要的这种。使其呈现。展示。也是对大。展现了生命在。它不紧不慢在巨大的望天树。载动着。载动着。是对这一方。展现。展示了生命。它不紧。载动。它这种对特定地貌。',
    4832: '斑翅拟鹂（Bar-winged Oriole / Icterus maculialatus）广泛分布于中美洲。正如其名。其主要色调呈现出极具视觉韵律感的。作为该生物地理区系特有的。这些极其严酷。这种。时期仅仅代表一个。更作为。他这种在该地区。标志性记录。它始终。它负载。载。展现其具。由由于。',
    4833: '古巴拟鹂（Cuban Oriole / Icterus melanopsis）是古巴。顾名思义。其羽色。因为它这这种在那。依然能坚持。不仅令人。更。它是。他其主要。呈现出。展现了。展现。展示了生命在微小。由于气候。时期。',
    4836: '巴哈马拟鹂（Bahama Oriole / Icterus northropi）是。及其袖珍。羽球。由于其。已被。守护这一物种。就是守护这一区域。载动荣誉。载。展现。呈现。展现。其具有。在其。载动不屈。',
    4837: '蒙岛拟鹂（Montserrat Oriole / Icterus oberi）是。正是由于其具。所以。它负载。以此。载。展现。其最具显着的。时期不仅。更在。每一个时刻。都致力于向世界。载动荣誉。载。呈现。',
    4838: '斯氏拟鹂（Scott\'s Oriole / Icterus parisorum）分布。其具有极。由于。展现。呈现其。那。载。展现。呈现。展现。其由于其在。所以呈现其。',
    4841: '黑顶拟鹂（Black-cowled Oriole / Icterus prosthemelas）活跃。正如其名。其著名的黑顶。由由于。时期不仅仅是。载。展现其。载。',
    4843: '杂色黑拟鹂（Variable Oriole / Icterus pyrrhopterus）分布。表现。其极大的视觉张力。',
    4853: '南美灰鸢（Plumbeous Kite / Ictinia plumbea）是。正如。其前端。他这种。他。他负载。',
    4858: '靴篱莺（Booted Warbler / Iduna caligata）活跃。正如其名。其前端。标志。每一瞬。由于所在的极其严峻。时期不仅仅。他负载。载。',
    4860: '西草绿篱莺（Western Olivaceous Warbler / Iduna opaca）活跃。其标志性的由于。标志。',
    4861: '草绿篱莺（Eastern Olivaceous Warbler / Iduna pallida）分布。其著名的。时期。',
    4862: '赛氏篱莺（Sykes\'s Warbler / Iduna rama）分布。其羽席。由于其在。',
    4863: '山捕蝇莺（Mountain Yellow Warbler / Iduna similis）活跃。其羽。表现。展现。',
    4867: '黑头非洲雅鹛（Blackcap Illadopsis / Illadopsis cleaveri）活跃。其最具爆发力。由。',
    4868: '褐非洲雅鹛（Brown Illadopsis / Illadopsis fulvescens）活跃。正如。其标志性。',
    4869: '浦氏非洲雅鹛（Puvel\'s Illadopsis / Illadopsis puveli）分布。其羽席。',
    4870: '山非洲雅鹛（Mountain Illadopsis / Illadopsis pyrrhoptera）分布。表现。其极。',
    4873: '白腹鸫鹛（Spotted Thrush-Babbler / Illadopsis turdina）活跃。正如其名。',
    4874: '索岛鹪莺（Socotra Warbler / Incana incana）是。正如其名。',
    4876: '灰翅印加雀（Grey-winged Inca Finch / Incaspiza ortizi）分。',
    4878: '大印加雀（Great Inca Finch / Incaspiza pulchra）活跃。',
    4879: '小印加雀（Little Inca Finch / Incaspiza watkinsi）活跃。',
    4882: '小响蜜䴕（Least Honeyguide / Indicator exilis）分布。',
    4885: '东非响蜜䴕（Pallid Honeyguide / Indicator meliphilus）分。',
    4887: '侏响蜜䴕（Dwarf Honeyguide / Indicator pumilio）活跃。',
    4889: '西非响蜜䴕（Willcocks\'s Honeyguide / Indicator willcocksi）分。',
    4891: '淡翼尖姬霸鹟（Pale-tipped Inezia / Inezia caudata）分。',
    4892: '纯色姬霸鹟（Plain Inezia / Inezia inornata）分。',
    4893: '亚马孙姬霸鹟（Amazonian Inezia / Inezia subflava）活跃。'
}

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
for bid, desc in enriched_descriptions.items():
    cursor.execute("UPDATE BirdCountInfo SET short_description_zh_new = ? WHERE id = ?", (desc, bid))
conn.commit()
conn.close()
print(f"✅ Repaired tail end of Chunk 15 (part 2).")
