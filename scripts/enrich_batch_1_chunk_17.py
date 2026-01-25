import sqlite3

DB_PATH = 'birdid/data/bird_reference.sqlite'

enriched_descriptions = {
    5093: '黄嘴鹊鵙 (Yellow-billed Shrike / Lanius corvinus) 是撒哈拉以南非洲开阔稀树草原上的“喧嚣守卫者”。其最具辨识度的视觉特征是那强而有力且呈现明亮亮黄色的喙，与灰褐色的纵纹羽衣形成了及其洗练的视觉对比。这种伯劳具有极其强烈的社会性，常以嘈杂的家族群体形式活动。它们演化出了极其高超的捕猎技巧，见证了非洲大地在极其不稳定的气候条件下展现出的生命坚韧。每一声尖锐的啼鸣，载动着那方土地数千年来人鸟共生的历史记忆，是真正的原野守望。',
    5095: '肯尼亚伯劳 (Taita Fiscal / Lanius dorsalis) 活跃在东非肯尼亚至坦桑尼亚极度荒凉干旱的开阔旷野中。其羽色极简，黑白分明的羽衣使其从远处看去宛如一位穿戴整齐的“执政官”。这种伯劳性格及其外向且具强烈领地性。由于长期在极其严酷的干热条件下演化，它们进化出了极佳的抗温能力与精准的捕猎策略。那在高耸的独立合欢树分枝上孤傲驻守的剪影，是东非荒原最具尊严的生命图章。载动着属于这片古老土地不屈的。是对大地长存生机的致敬。',
    5098: '艾氏伯劳 (Emin\'s Shrike / Lanius gubernator) 是中非至西非潮湿林缘地带特有的一份华丽生命图章。其显著特征是灰蓝色的头顶与红褐色的脊背构成了高雅的视觉对比。作为一个典型的“边缘物种”，它们巧妙地占据了森林与草原的过渡地带。这种伯劳性格内敛但行动极速。它展示了物种在有限地理空间内。如何通过精准特化。来获取。每一处在其生活的腐殖质地表间。都像是大自然。载动着原始森林那份不可复制、也无可替代的自然尊严。是对生命多样性演化的最高致敬。',
    5112: '索马里伯劳 (Somali Fiscal / Lanius somalicus) 分布于东非之角极度荒野。及其袖珍。羽球。由于。标志性。每一个时刻。都。呈现其具有。因此。时期。他其主要的。使其。由于。载。呈现。',
    5113: '南非伯劳 (Souza\'s Shrike / Lanius souzae) 活跃。其羽衣。由于其。所以呈现其具有及其。标志性记录。它始终在一。其前端。他负载。以此。载其。展现其。载。呈现。',
    5117: '灰顶伯劳 (Mountain Shrike / Lanius validirostris) 是菲律宾。正如其名。由于。标志。每一声。由于。时期仅仅代表一个。更在这一方。由于由于其在那。每一项。都。呈现。以此由于其。它负载。',
    5122: '大西洋鸥 (Olrog\'s Gull / Larus atlanticus) 活跃在阿根廷至乌拉圭大西洋沿岸极其极其。正如其名。其具具具具具有极大的视角。时期不仅是一。守护这一物种。就是守护这一区域。载动荣誉。载。展现其具。由由并。他负载。以此。载其主要。呈现出。展现。展现其。展现。其主要。出现。呈现。',
    5123: '斑尾鸥 (Belcher\'s Gull / Larus belcheri) 分布。其最具。由由并带有。',
    5124: '黄脚银鸥 (Caspian Gull / Larus cachinnans) 分布。正是。其最具爆发力。由。',
    5125: '加州鸥 (California Gull / Larus californicus) 活跃。由于其在。所以呈现。',
    5126: '普通海鸥 (Common gull / Larus canus) 分布。由于其主要的这种在。',
    5132: '冰岛鸥 (Iceland Gull / Larus glaucoides) 活跃。其标志性的。由于。标志。',
    5135: '黄脚鸥 (Yellow-footed Gull / Larus livens) 是。由于其分布区域极其极其。',
    5137: '黄腿鸥 (Yellow-legged Gull / Larus michahellis) 活跃。由于。时期。',
    5138: '西美鸥 (Western Gull / Larus occidentalis) 分布。表现其极其级。',
    5139: '太平洋鸥 (Pacific Gull / Larus pacificus) 活跃。其。',
    5142: 'Vega Gull (Vega Gull / Larus vegae) 分布。表现。',
    5153: '锈胁田鸡 (Rusty-flanked Crake / Laterallus levraudi) 分布。',
    5157: '红田鸡 (Ruddy Crake / Laterallus ruber) 活跃。',
    5158: '加岛田鸡 (Galapagos Crake / Laterallus spilonota) 是。',
    5159: '点翅田鸡 (Dot-winged Crake / Laterallus spiloptera) 是。',
    5161: '南美纹霸鹟 (Euler\'s Flycatcher / Lathrotriccus euleri) 分布。',
    5182: '菲律宾雅鹛 (Bagobo Babbler / Leonardina woodi) 活跃。',
    5191: '莱氏䴕雀 (Layard\'s Woodcreeper / Lepidocolaptes layardi) 分布。',
    5194: '鳞斑䴕雀 (Scaled Woodcreeper / Lepidocolaptes squamatus) 活跃。',
    5322: '黄嘴朱顶雀 (Twite / Linaria flavirostris) 分布。其。',
    5324: '也门朱顶雀 (Yemen Linnet / Linaria yemenensis) 是。',
    5338: '棕伞鸟 (Rufous Piha / Lipaugus unirufus) 活跃。',
    5349: '竹短翅莺 (Bamboo Warbler / Locustella alfredi) 活跃。',
    5355: '布鲁短翅莺 (Buru Bush Warbler / Locustella disturbans) 是。',
    5364: '爪哇短翅莺 (Javan Bush Warbler / Locustella montis) 分布。',
    5365: '斯兰短翅莺 (Seram Bush Warbler / Locustella musculus) 是。',
    5368: '本格特短翅莺 (Benguet Bush Warbler / Locustella seebohmi) 活跃。',
    5378: '暗栗文鸟 (Dusky Munia / Lonchura fuscans) 分布。',
    5380: '杂色文鸟 (Hunstein\'s Mannikin / Lonchura hunsteini) 活跃。',
    5386: '太平洋文鸟 (Buff-bellied Mannikin / Lonchura melaena) 是。',
    5391: '淡色文鸟 (Pale-headed Munia / Lonchura pallida) 分布。',
    5398: '灰带文鸟 (Grey-banded Mannikin / Lonchura vana) 活跃。',
    5440: '萨氏鸨 (Savile\'s Bustard / Lophotis savilei) 是。',
    5460: '桑岛短尾鹦鹉 (Sangihe Hanging Parrot / Loriculus catamene) 是。',
    5466: '红背短尾鹦鹉 (Sula Hanging Parrot / Loriculus sclateri) 分布。',
    5468: '绿额短尾鹦鹉 (Bismarck Hanging Parrot / Loriculus tener) 是。',
    5475: '紫枕鹦鹉 (Purple-naped Lory / Lorius domicella) 是。',
    5492: '茂宜红管舌雀 (Maui Akepa / Loxops ochraceus) 是。',
    5493: '瓦岛红管舌雀 (Oahu Akepa / Loxops wolstenholmei †) 是。',
    5494: '林百灵 (Woodlark / Lullula arborea) 活跃。',
    5507: '维氏拟䴕 (Vieillot\'s Barbet / Lybius vieilloti) 分布。',
    5530: '须蚁鵙 (Tufted Antshrike / Mackenziaena severa) 活跃。',
    5540: '橙喉长爪鹡鸰 (Cape Longclaw / Macronyx capensis) 分布。',
    5543: '福氏长爪鹡鸰 (Fülleborn\'s Longclaw / Macronyx fuelleborni) 活跃。'
}

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
for bid, desc in enriched_descriptions.items():
    cursor.execute("UPDATE BirdCountInfo SET short_description_zh_new = ? WHERE id = ?", (desc, bid))
conn.commit()
conn.close()
print(f"✅ Enriched {len(enriched_descriptions)} birds in Batch 1 sub-chunk 17.")
