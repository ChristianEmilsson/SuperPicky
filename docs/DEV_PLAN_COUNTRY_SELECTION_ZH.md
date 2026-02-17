# 开发计划：国家选择界面重构 (交接文档)

## 目标
重构 `birdid_dock.py` 中的国家选择下拉菜单，使其更友好、有序，并基于 48 个支持国家 + 6 大洲进行组织。

## 1. 数据定义 (`birdid/avonet_filter.py`)

### 1.1 补充缺失边界 (Bounding Box)
在 `avonet_filter.py` 的 `REGION_BOUNDS` 中添加以下经纬度定义：

```python
# 1. 香港 (Top 10 之一)
"HK": (22.1, 22.6, 113.8, 114.5),

# 2. 六大洲 (宽泛定义，用于大范围检索)
"AF": (-35, 37, -17, 51),    # 非洲 (Africa)
"AS": (-10, 81, 26, 170),    # 亚洲 (Asia)
"EU": (34, 71, -25, 45),     # 欧洲 (Europe)
"NA": (14, 83, -168, -52),   # 北美洲 (North America)
"SA": (-56, 13, -81, -34),   # 南美洲 (South America)
"OC": (-47, -10, 110, 180),  # 大洋洲 (Oceania)
```

### 1.2 更新 JSON 数据
运行脚本更新 `birdid/data/ebird_regions.json`。
- **过滤规则**：仅保留在 `REGION_BOUNDS` 中有定义的所有区域（共约 55 个：48 个国家 + 6 大洲 + Global）。

## 2. 界面逻辑 (`ui/birdid_dock.py`)

### 2.1 移除硬编码过滤
删除代码中现有的 `priority_codes` 列表（该列表目前限制了下拉菜单只显示 ~20 个国家）。
修改为：直接读取并显示 JSON 中的**所有**区域。

### 2.2 实现 "Top 10" 分组排序
将下拉菜单项分为两组，并按以下逻辑排序：

**第一组：Top 10 常用国家 (按英文首字母 A-Z 排序)**
1.  **AU** Australia (澳大利亚)
2.  **BR** Brazil (巴西)
3.  **CN** China (中国)
4.  **GB** United Kingdom (英国)
5.  **HK** Hong Kong (香港)
6.  **ID** Indonesia (印尼)
7.  **JP** Japan (日本)
8.  **MY** Malaysia (马来西亚)
9.  **TW** Taiwan (台湾)
10. **US** United States (美国)

**第二组：大洲与其他国家 (按英文首字母 A-Z 排序)**
- 包含 6 大洲 (Africa, Asia...)
- 包含剩余的 39 个国家 (Argentina, France, Russia...)
- *可选：将大洲单独分组，或者混在"其他"里按字母排。*

### 2.3 最终显示顺序
1.  **自动定位 (Auto GPS)**
2.  **全球模式 (Global)**
3.  --- 分隔符 ---
4.  **Top 10 国家** (Au, Br, Cn...)
5.  --- 分隔符 ---
6.  **所有其他区域** (按 A-Z 排序)

## 3. 执行步骤
1.  **修改代码**：在 `avonet_filter.py` 添加 HK 和 6 大洲的坐标。
2.  **更新数据**：运行脚本重新生成 `ebird_regions.json`。
3.  **重构逻辑**：修改 `birdid_dock.py` 的列表构建函数，实现上述排序和分组。
4.  **验证**：重启检查下拉菜单，确认新国家（如俄罗斯）和大洲选项可见且排序正确。
