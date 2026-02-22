# 全屏查看器 v2 设计文档

**日期：** 2026-02-22
**状态：** 已确认，待实现

---

## 背景

全屏查看器 v1 已实现双击进入、焦点叠加、基础滚轮缩放。
v2 目标：Lightroom 式交互体验 + 焦点可开关图层 + 前后 10 张预加载。

**保留现有机制（不破坏）：**
- 缩略图 LRU 缓存（500 张，`_thumb_cache`）
- `show_photo()` 的"先显示缩略图缓存 → 再异步加载高清图"流程
- 高清图 `_ImageLoader`（QThread）

---

## 交互模型（方案 A，Lightroom 风格）

| 状态 | 操作 | 效果 | 光标 |
|------|------|------|------|
| 适配模式（默认）| 单击图片 | 以点击位置为中心，缩放到 100% | Qt.SizeVerCursor（放大镜）|
| 100% 模式 | 单击图片 | 回到适配全屏 | Qt.OpenHandCursor |
| 100% 模式 | 按住拖拽 | 平移图片 | Qt.ClosedHandCursor |
| 任意模式 | 滚轮 | 连续缩放 0.1x–8x，以鼠标为缩放中心 | 不变 |
| 任意模式 | Escape / 返回按钮 | 回到 grid | — |
| 任意模式 | ← → / 底栏按钮 | 切换照片，重置为适配模式 | — |

> 双击等价于两次单击（第二次单击回到适配）。不单独处理双击语义。

---

## 焦点图层

- 默认显示
- `F` 键 + 顶栏「焦点」按钮同步切换显示/隐藏
- 按钮激活：accent 色；隐藏：secondary 灰
- 切换照片时保持当前开关状态

---

## 性能：前后 10 张预加载

```
高清 LRU 缓存：_hd_cache，21 slots

PreloadManager（QObject + 工作线程池）：
  - 维护当前索引 + 照片列表
  - 进入全屏 / 切换照片时更新索引，触发预加载
  - 加载优先级：当前(0) → +1 → -1 → +2 → -2 → ... → ±10
  - 已在缓存中的跳过
  - 导航时取消超出 ±10 范围的低优先级任务

内存估算：21 × 2MB ≈ 42MB，安全
```

---

## 修改文件

| 文件 | 改动内容 |
|------|---------|
| `ui/fullscreen_viewer.py` | 重写 `_FullscreenImageLabel`（缩放/平移/光标）；`FullscreenViewer` 加焦点开关按钮 + `_HdCache` + `_PreloadManager` |
| `ui/results_browser_window.py` | `_enter_fullscreen` / `_fullscreen_prev` / `_fullscreen_next` 通知 PreloadManager 更新索引和照片列表 |

---

## 不变的部分

- `ui/thumbnail_grid.py`：无需修改
- `_thumb_cache`：保留，全屏 `show_photo()` 继续用它做即时预览
- `_ImageLoader`：保留，当高清缓存未命中时继续使用
