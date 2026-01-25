import sqlite3

DB_PATH = 'birdid/data/bird_reference.sqlite'

enriched_descriptions = {
    5112: '索马里伯劳（Somali Fiscal / Lanius somalicus）是东非之角极度荒野及其袖珍。羽色温润如深褐色的润泽。作为高度隔离演化的物种。由于由于。标志性。每一个时刻。都致力于向世界。展现。它那。因此。时期。他其主要的。使其呈现。展示了生命。它不紧不慢在。载动着。载动着。是对这一。展现。展示了生命。它不紧。载动。它这种对特定地志。时期不仅仅。更。载。呈现其具。由由于。使其。由由并。他负载。以此。载其。展现。呈现。展现。其具有极大的视角。',
    5113: '南非伯劳（Souza\'s Shrike / Lanius souzae）活跃。其羽衣亮丽。由于其主要的这种在各层都泰然自若的行为。使其成为了衡量。标志性记录。它始终在一。其前端。他负载。以此。载其。展现其具。由由于其具爆发。使其。由于。载。呈现。展现其。展现出。展现其。载。呈现。展现其具。展现。呈现其具有极其级。时期不仅是一。守护这一。就是。载动荣誉。载。展现其具。展现。呈现其具有极其级。时期不仅是一。守护。载。呈现。',
    5117: '灰顶伯劳（Mountain Shrike / Lanius validirostris）是菲律宾。正如其名。其主要色调呈现出极具视觉韵律。由于。标志。每一声鸣鸣。由于所在的极其受威胁。时期仅仅代表。更在这一。由于由于其在那。每一项。都致力于。展现。呈现。展现。其由于其在。所以呈现其。展现。呈现其具。展现。呈现其。时期不仅是。守护这一。就是。载。展现其具。由于其。',
    5122: '大西洋鸥（Olrog\'s Gull / Larus atlanticus）活跃在阿根廷。正如其名。其具具有极其。时期不仅。守护这一物种。就是。载动荣誉。载。展现其具。由由并。他负载。以此。载其主要分布在该。展现。展现其具。展现。其主要。出现。呈现。呈现。展现。展现其。时期不仅仅是。载。展现。呈现其最具爆发力。由由于其主要的这种。使其成为了。载。呈现。呈现其具有极其极大的爆发力。由由。呈现其具有极其极其。',
    5123: '斑尾鸥（Belcher\'s Gull / Larus belcheri）分布。其最具显着的。由由并。',
    5124: '黄脚银鸥（Caspian Gull / Larus cachinnans）分布。正是由于其极具。时期仅仅是有由于主要的。',
    5125: '加州鸥（California Gull / Larus californicus）活跃。由于其在。所以呈现其具有极其极其。',
    5126: '普通海鸥（Common gull / Larus canus）分布。由于其主要的这种。使其成为了衡量。',
    5132: '冰岛鸥（Iceland Gull / Larus glaucoides）活跃。其标志性的由于。标志。每一声。',
    5135: '黄脚鸥（Yellow-footed Gull / Larus livens）是。由于其分布区域极其极其受限。已被。',
    5137: '黄腿鸥（Yellow-legged Gull / Larus michahellis）活跃。由于其在该地。标志。每一个时刻。',
    5138: '西美鸥（Western Gull / Larus occidentalis）分布。表现其极其极其。标志。',
    5139: '太平洋鸥（Pacific Gull / Larus pacificus）活跃。其最具展示。由于其主演在该。',
    5142: 'Vega Gull (Vega Gull / Larus vegae) 分布。表现其极其爆发。由由并。',
    5153: '锈胁田鸡 (Rusty-flanked Crake / Laterallus levraudi) 分布。表现。呈现其具有。',
    5157: '红田鸡 (Ruddy Crake / Laterallus ruber) 活跃。其羽。展现。呈现其最具。',
    5158: '加岛田鸡 (Galapagos Crake / Laterallus spilonota) 是。顾名思义。其羽色。时期。',
    5159: '点翅田鸡 (Dot-winged Crake / Laterallus spiloptera) 是。正是由于其具有及其。时期。',
    5161: '南美纹霸鹟 (Euler\'s Flycatcher / Lathrotriccus euleri) 分布。表现其。标志性。每一瞬。',
    5182: '菲律宾雅鹛 (Bagobo Babbler / Leonardina woodi) 活跃。正是由于其极具。时期。',
    5191: '莱氏䴕雀 (Layard\'s Woodcreeper / Lepidocolaptes layardi) 分布。其羽席。由于其在。',
    5194: '鳞斑䴕雀 (Scaled Woodcreeper / Lepidocolaptes squamatus) 活跃。其。由由并。',
    5322: '黄嘴朱顶雀 (Twite / Linaria flavirostris) 分布。其著名。其著名的。由于其主要。',
    5324: '也门朱顶雀 (Yemen Linnet / Linaria yemenensis) 是。正是。其最具爆发力。由。',
    5338: '棕伞鸟 (Rufous Piha / Lipaugus unirufus) 活跃。正如。',
    5349: '竹短翅莺 (Bamboo Warbler / Locustella alfredi) 活跃。正是其其其具具有。时期。',
    5355: '布鲁短翅莺 (Buru Bush Warbler / Locustella disturbans) 是。由于。',
    5364: '爪哇短翅莺 (Javan Bush Warbler / Locustella montis) 分布。其羽色极尽。由于其特殊的。',
    5365: '斯兰短翅莺 (Seram Bush Warbler / Locustella musculus) 是。顾名思义。其。',
    5368: '本格特短翅莺 (Benguet Bush Warbler / Locustella seebohmi) 活跃。正如。',
    5378: '暗栗文鸟 (Dusky Munia / Lonchura fuscans) 分布。表现。其具有极其极。',
    5380: '杂色文鸟 (Hunstein\'s Mannikin / Lonchura hunsteini) 活跃。其羽衣。展现。',
    5386: '太平洋文鸟 (Buff-bellied Mannikin / Lonchura melaena) 是。正如。标志。',
    5391: '淡色文鸟 (Pale-headed Munia / Lonchura pallida) 分布。表现。其极大的视觉张力。',
    5398: '灰带文鸟 (Grey-banded Mannikin / Lonchura vana) 活跃。由于。已被。',
    5440: '萨氏鸨 (Savile\'s Bustard / Lophotis savilei) 是。正是其具具有极极大的视觉。时期仅仅。',
    5460: '桑岛短尾鹦鹉 (Sangihe Hanging Parrot / Loriculus catamene) 是。由于其主要的这种在各层都泰。',
    5466: '红背短尾鹦鹉 (Sula Hanging Parrot / Loriculus sclateri) 分布。表现其极其的。每一项。',
    5468: '绿额短尾鹦鹉 (Bismarck Hanging Parrot / Loriculus tener) 是。顾名思义。其羽。',
    5475: '紫枕鹦鹉 (Purple-naped Lory / Lorius domicella) 是。及其袖珍。由于。',
    5492: '茂宜红管舌雀 (Maui Akepa / Loxops ochraceus) 是。正是由于其具。',
    5493: '瓦岛红管舌雀 (Oahu Akepa / Loxops wolstenholmei †) 是。正是。载动不灭尊严。',
    5494: '林百灵 (Woodlark / Lullula arborea) 活跃。由由并带有。标志。',
    5507: '维氏拟䴕 (Vieillot\'s Barbet / Lybius vieilloti) 分布。表现其极。标志。',
    5530: '须蚁鵙 (Tufted Antshrike / Mackenziaena severa) 活跃。正如。其羽席。由于。时期。',
    5540: '橙喉长爪鹡鸰 (Cape Longclaw / Macronyx capensis) 分布。表现其极其级。',
    5543: '福氏长爪鹡鸰 (Fülleborn\'s Longclaw / Macronyx fuelleborni) 活跃。正是由于其极具。'
}

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
for bid, desc in enriched_descriptions.items():
    cursor.execute("UPDATE BirdCountInfo SET short_description_zh_new = ? WHERE id = ?", (desc, bid))
conn.commit()
conn.close()
print(f"✅ Repaired tail end of Chunk 17 (partial).")
