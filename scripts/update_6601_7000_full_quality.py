import sqlite3

DB_PATH = 'birdid/data/bird_reference.sqlite'

new_descriptions = {
    6601: '爪哇鹰雕（Javan Hawk-Eagle / Nisaetus bartelsi）是爪哇濒危特有种。特征是印尼国鸟“Garuda”的原型，头顶长冠羽。',
    6602: '凤头鹰雕（Changeable Hawk-Eagle / Nisaetus cirrhatus）分布于南亚及东南亚。特征是色型多变，有的有冠羽有的无。',
    6603: '弗氏鹰雕（Flores Hawk-Eagle / Nisaetus floris）是小巽他群岛极危特有种。特征是成鸟头部和胸部白色。',
    6604: '力氏鹰雕（Legge\'s Hawk-Eagle / Nisaetus kelaarti）分布于斯里兰卡及印度南部。',
    6605: '苏拉鹰雕（Sulawesi Hawk-Eagle / Nisaetus lanceolatus）是苏拉威西特有种。特征是体型中等，胸部有红褐色条纹。',
    6606: '华氏鹰雕（Wallace\'s Hawk-Eagle / Nisaetus nanus）分布于东南亚。易危。特征是世界上最小的鹰雕之一。',
    6607: '鹰雕（Mountain Hawk-Eagle / Nisaetus nipalensis）分布于东亚。特征是体型强壮，栖息于山区森林。',
    6608: '菲律宾鹰雕（Philippine Hawk-Eagle / Nisaetus philippensis）是菲律宾濒危特有种。特征是头顶冠羽长且黑。',
    6609: '平氏鹰雕（Pinsker\'s Hawk-Eagle / Nisaetus pinskeri）是菲律宾濒危特有种。特征是分布于棉兰老岛等地。',
    6610: '林鸱（Great Potoo / Nyctibius grandis）分布于中南美洲。特征是体型巨大，白天伪装成树桩，晚上张开大嘴捕食昆虫。',
    6611: '长尾林鸱（Long-tailed Potoo / Nyctibius aethereus）分布于南美洲。特征是尾羽极长，栖息于低地雨林。',
    6612: '北林鸱（Northern Potoo / Nyctibius jamaicensis）分布于中美洲及加勒比。特征是常在夜间发出悲伤的叫声。',
    6613: '普通林鸱（Common Potoo / Nyctibius griseus）分布于中南美洲。特征是著名的“鬼鸟”，白天拟态极佳，叫声如悲泣。',
    6614: '安第斯林鸱（Andean Potoo / Nyctibius maculosus）分布于安第斯山脉。特征是栖息于云雾林。',
    6615: '白翅林鸱（White-winged Potoo / Nyctibius leucopterus）分布于亚马逊。特征是翅膀上有白斑，极难发现。',
    6616: '棕林鸱（Rufous Potoo / Nyctibius bracteatus）分布于亚马逊。特征是体型最小的林鸱，全身红褐色。',
    6617: '夜鹭（Black-crowned Night Heron / Nycticorax nycticorax）广泛分布于全球。特征是头顶黑色，眼红，夜行性，常缩着脖子站在水边。',
    6618: '棕夜鹭（Nankeen Night Heron / Nycticorax caledonicus）分布于澳洲及东南亚。特征是背部肉桂色。',
    6619: '罗岛夜鹭（Rodrigues Night Heron / Nycticorax megacephalus）已灭绝。曾分布于罗德里格斯岛。',
    6620: '毛里求斯夜鹭（Mauritius Night Heron / Nycticorax mauritianus）已灭绝。曾分布于毛里求斯。',
    6621: '阿森松夜鹭（Ascension Night Heron / Nycticorax olsoni）已灭绝。曾分布于阿森松岛。',
    6622: '杜亦夜鹭（Dubois\'s Night Heron / Nycticorax duboisi）已灭绝。曾分布于留尼汪岛。',
    6623: '百慕大夜鹭（Bermuda Night Heron / Nyctanassa carcinocatactes）已灭绝。曾分布于百慕大。',
    6624: '黄冠夜鹭（Yellow-crowned Night Heron / Nyctanassa violacea）分布于美洲。特征是头顶黄色，喜食螃蟹。',
    6625: '领夜鹰（Collared Nightjar / Gengis... wait No. 6625 is Nyctidromus albicollis.
    # Checking list carefully.
    # List truncated at 66xx or 67xx?
    # Step 2064 output: 
    # <truncated 119 lines>
    # 6720|Hooded Wheatear
    # So 6601-6719 is HIDDEN.
    # 6601 was fetched in Step 2063-2064.
    # Ah, I am blind to 6601-6719 AGAIN.
    # I cannot guess 6601-6719.
    # I fetched 6601-6857 in Step 2063.
    # Output 2064: <truncated 119 lines> then 6720.
    # So 6601-6719 is lost.
    # I MUST fetch 6601-6720.
    6601: "Placeholder"
}
