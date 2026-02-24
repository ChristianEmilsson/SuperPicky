# 全屏查看器 v2 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 升级 `ui/fullscreen_viewer.py` 为 Lightroom 风格：单击缩放到鼠标位置 100% / 再次单击回适配；拖拽平移；焦点图层 F 键+顶栏按钮可开关；前后 ±10 张高清预加载（LRU 21 slots）。

**Architecture:** 重写 `_FullscreenImageLabel`，使用 `(_draw_ox, _draw_oy, _display_scale)` 坐标系统统一管理缩放/平移，`_fit_mode=True` 时 paintEvent 自动重算适配值；新增模块级 `_HdCache`（LRU 21 slots）和 `_PreloadWorker`（QThread）；`FullscreenViewer` 新增 `set_photo_list()` 接口，`show_photo()` 优先命中高清缓存再回落到 `_ImageLoader`。

**Tech Stack:** PySide6（QLabel, QThread, QPainter, Qt cursors）, Python 3.10+

---

## 保留现有机制（不改动）

- `_thumb_cache`（thumbnail_grid.py）：500 张缩略图 LRU，`show_photo()` 继续用作即时预览
- `_ImageLoader`（detail_panel.py 风格）：高清图未命中缓存时继续使用
- `ThumbnailGrid.photo_double_clicked`、`ThumbnailCard.double_clicked`：无需修改
- `results_browser_window.py` 的 `_enter_fullscreen`、`_exit_fullscreen`：逻辑不变，只新增两处调用

---

## 坐标系说明（Task 1 实现基础）

```
_draw_ox, _draw_oy  : 图片左上角在 QLabel 坐标系中的位置（浮点像素）
_display_scale      : 当前显示缩放比（1.0 = 原始分辨率 100%）
_fit_mode           : True = 自动适配窗口（paintEvent 每帧重算）
                      False = 手动缩放/平移（使用存储值）
```

焦点叠加屏幕坐标（任意缩放/平移状态下均成立）：
```
fx_screen = _draw_ox + focus_x * img_w * _display_scale
fy_screen = _draw_oy + focus_y * img_h * _display_scale
```

---

## Task 1：重写 `_FullscreenImageLabel`

**Files:**
- Modify: `ui/fullscreen_viewer.py`（完整替换 `_FullscreenImageLabel` 类）

**Step 1: 替换类定义和 `__init__`**

用以下代码完整替换 `_FullscreenImageLabel` 类（从类定义到最后一个方法）：

```python
class _FullscreenImageLabel(QLabel):
    """
    全屏图片标签。
    - 单击（适配模式）→ 以鼠标位置为中心缩放到 100%
    - 单击（缩放模式）→ 返回适配模式
    - 拖拽（缩放模式）→ 平移图片
    - 滚轮（任意模式）→ 以鼠标为中心缩放 0.1x~8x
    - toggle_focus()  → 切换焦点叠加显示/隐藏
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap: Optional[QPixmap] = None
        self._focus_x: Optional[float] = None
        self._focus_y: Optional[float] = None
        self._focus_status: Optional[str] = None
        self._focus_visible: bool = True

        # 缩放/平移状态
        self._fit_mode: bool = True
        self._draw_ox: float = 0.0       # 图片左上角 x（label 坐标）
        self._draw_oy: float = 0.0       # 图片左上角 y（label 坐标）
        self._display_scale: float = 1.0

        # 拖拽状态
        self._drag_active: bool = False
        self._drag_start_x: float = 0.0
        self._drag_start_y: float = 0.0
        self._drag_ox_start: float = 0.0
        self._drag_oy_start: float = 0.0

        # 双击吸收标志（防止第二次 release 误触发 click 逻辑）
        self._double_click_pending: bool = False

        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(200, 200)
        self.setStyleSheet(f"background-color: {COLORS['bg_void']};")
        self.setCursor(Qt.CrossCursor)

    # ── 公共接口 ────────────────────────────────────────────

    def set_pixmap(self, pixmap: QPixmap):
        """设置图片，重置为适配模式。"""
        self._pixmap = pixmap
        self._fit_mode = True
        self._drag_active = False
        self.setCursor(Qt.CrossCursor)
        self.update()

    def set_focus(self, focus_x: Optional[float], focus_y: Optional[float],
                  focus_status: Optional[str]):
        """设置焦点坐标（归一化 0.0~1.0）和状态。"""
        self._focus_x = focus_x
        self._focus_y = focus_y
        self._focus_status = focus_status
        self.update()

    def toggle_focus(self):
        """切换焦点叠加显示/隐藏。"""
        self._focus_visible = not self._focus_visible
        self.update()

    @property
    def focus_visible(self) -> bool:
        return self._focus_visible

    # ── 内部辅助 ─────────────────────────────────────────────

    def _get_fit_transform(self):
        """计算适配模式下的 (scale, ox, oy)，不修改状态。"""
        if self._pixmap is None or self._pixmap.isNull():
            return 1.0, 0.0, 0.0
        img_w = self._pixmap.width()
        img_h = self._pixmap.height()
        label_w = self.width() or 1
        label_h = self.height() or 1
        if img_w == 0 or img_h == 0:
            return 1.0, 0.0, 0.0
        scale = min(label_w / img_w, label_h / img_h)
        ox = (label_w - img_w * scale) / 2.0
        oy = (label_h - img_h * scale) / 2.0
        return scale, ox, oy

    def _ensure_manual_state(self):
        """
        若当前在 fit_mode，将 _draw_ox/_oy/_display_scale 同步为当前适配值，
        以便后续 wheel/click 事件可直接使用这些字段做坐标变换。
        """
        if self._fit_mode:
            scale, ox, oy = self._get_fit_transform()
            self._display_scale = scale
            self._draw_ox = ox
            self._draw_oy = oy

    def _zoom_to_100(self, mx: float, my: float):
        """以屏幕坐标 (mx, my) 为中心，切换到 100% 缩放。"""
        self._ensure_manual_state()
        # 计算鼠标下方的图片像素坐标
        img_px = (mx - self._draw_ox) / self._display_scale
        img_py = (my - self._draw_oy) / self._display_scale
        # 缩放到 100%，使 img_px 保持在 mx 位置
        self._draw_ox = mx - img_px * 1.0
        self._draw_oy = my - img_py * 1.0
        self._display_scale = 1.0
        self._fit_mode = False
        self.setCursor(Qt.OpenHandCursor)
        self.update()

    def _draw_focus_overlay(self, painter: QPainter, fx: float, fy: float):
        """在 (fx, fy) 处绘制焦点圆圈 + 十字线 + 中心点。"""
        dot_color = _FOCUS_COLORS[self._focus_status]

        # 半透明填充圆（r=18, alpha=160）
        fill = QColor(dot_color)
        fill.setAlpha(160)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(fill))
        painter.drawEllipse(int(fx) - 18, int(fy) - 18, 36, 36)

        # 白色十字线（±30px，线宽 1.5，alpha=200）
        pen = QPen(QColor(255, 255, 255, 200))
        pen.setWidthF(1.5)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawLine(int(fx) - 30, int(fy), int(fx) + 30, int(fy))
        painter.drawLine(int(fx), int(fy) - 30, int(fx), int(fy) + 30)

        # 中心白色小圆点（r=3）
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 220)))
        painter.drawEllipse(int(fx) - 3, int(fy) - 3, 6, 6)

    # ── Qt 事件重写 ──────────────────────────────────────────

    def paintEvent(self, event):
        if self._pixmap is None or self._pixmap.isNull():
            super().paintEvent(event)
            return

        img_w = self._pixmap.width()
        img_h = self._pixmap.height()
        if img_w == 0 or img_h == 0:
            super().paintEvent(event)
            return

        # 适配模式：每帧重算坐标（支持窗口 resize）
        if self._fit_mode:
            scale, ox, oy = self._get_fit_transform()
            self._display_scale = scale
            self._draw_ox = ox
            self._draw_oy = oy
        else:
            scale = self._display_scale
            ox = self._draw_ox
            oy = self._draw_oy

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # 绘制缩放后的图片
        target_w = max(1, int(img_w * scale))
        target_h = max(1, int(img_h * scale))
        scaled_px = self._pixmap.scaled(
            target_w, target_h,
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation
        )
        painter.drawPixmap(int(ox), int(oy), scaled_px)

        # 焦点叠加（仅在可见且坐标/状态有效时绘制）
        if (self._focus_visible
                and self._focus_x is not None
                and self._focus_y is not None
                and self._focus_status in _FOCUS_COLORS):
            fx_s = ox + self._focus_x * img_w * scale
            fy_s = oy + self._focus_y * img_h * scale
            self._draw_focus_overlay(painter, fx_s, fy_s)

        painter.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 适配模式下窗口 resize → 重绘（paintEvent 自动重算）
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position()
            self._drag_start_x = pos.x()
            self._drag_start_y = pos.y()
            self._drag_ox_start = self._draw_ox
            self._drag_oy_start = self._draw_oy
            self._drag_active = False
            if not self._fit_mode:
                self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and not self._fit_mode:
            pos = event.position()
            dx = pos.x() - self._drag_start_x
            dy = pos.y() - self._drag_start_y
            if not self._drag_active and (abs(dx) > 3 or abs(dy) > 3):
                self._drag_active = True
            if self._drag_active:
                self._draw_ox = self._drag_ox_start + dx
                self._draw_oy = self._drag_oy_start + dy
                self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 双击第二次 release：吸收，不触发 click 逻辑
            if self._double_click_pending:
                self._double_click_pending = False
                self._drag_active = False
                self.setCursor(Qt.OpenHandCursor if not self._fit_mode else Qt.CrossCursor)
                super().mouseReleaseEvent(event)
                return

            if not self._drag_active:
                # 纯点击（无拖拽移动）
                pos = event.position()
                mx, my = pos.x(), pos.y()
                if self._fit_mode:
                    self._zoom_to_100(mx, my)
                else:
                    # 回到适配模式
                    self._fit_mode = True
                    self.setCursor(Qt.CrossCursor)
                    self.update()
            else:
                # 拖拽结束，恢复张开手光标
                if not self._fit_mode:
                    self.setCursor(Qt.OpenHandCursor)
            self._drag_active = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        """标记双击，防止第二次 release 误触发 click 逻辑。"""
        if event.button() == Qt.LeftButton:
            self._double_click_pending = True
        super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event):
        if self._pixmap is None or self._pixmap.isNull():
            return
        # 同步手动状态（fit_mode 下先获取当前适配值）
        self._ensure_manual_state()

        pos = event.position()
        mx, my = pos.x(), pos.y()

        # 鼠标下方的图片像素坐标
        img_px = (mx - self._draw_ox) / self._display_scale
        img_py = (my - self._draw_oy) / self._display_scale

        # 计算新缩放
        delta = event.angleDelta().y()
        factor = 1.15 if delta > 0 else 1.0 / 1.15
        new_scale = max(0.1, min(8.0, self._display_scale * factor))

        # 重新定位使鼠标下方图片像素不变
        self._draw_ox = mx - img_px * new_scale
        self._draw_oy = my - img_py * new_scale
        self._display_scale = new_scale
        self._fit_mode = False
        self.setCursor(Qt.OpenHandCursor)
        self.update()
```

**Step 2: 语法验证**

```bash
python3 -m py_compile ui/fullscreen_viewer.py
```

预期：无输出（通过）。

---

## Task 2：焦点图层开关按钮 + 移除旧 double_clicked 连接

**Files:**
- Modify: `ui/fullscreen_viewer.py`（`FullscreenViewer` 类）

**Step 1: 移除 `_build_ui()` 中的旧 double_clicked 连接**

找到并删除这一行（v1 遗留，v2 的 `_FullscreenImageLabel` 已无此信号）：
```python
self._img_label.double_clicked.connect(self.close_requested)
```

**Step 2: 在 `_build_top_bar()` 中添加焦点切换按钮**

在 `back_btn` 和 `h.addStretch()` 之间插入：

```python
# 焦点图层开关按钮
self._focus_btn = QPushButton("焦 ●")
self._focus_btn.setFixedHeight(32)
self._focus_btn.setFixedWidth(64)
self._focus_btn.setToolTip("切换焦点叠加显示 (F)")
self._focus_btn.clicked.connect(self._on_focus_btn_clicked)
h.addWidget(self._focus_btn)
self._update_focus_btn_style(True)   # 初始：显示（accent 色）
```

**Step 3: 在 `FullscreenViewer` 添加三个方法**

```python
def toggle_focus(self):
    """切换焦点叠加（供外部 F 键调用 + 内部按钮调用）。"""
    self._img_label.toggle_focus()
    self._update_focus_btn_style(self._img_label.focus_visible)

def _on_focus_btn_clicked(self):
    self.toggle_focus()

def _update_focus_btn_style(self, visible: bool):
    """visible=True → accent 主按钮色；False → secondary 灰色。"""
    self._focus_btn.setObjectName("" if visible else "secondary")
    self._focus_btn.style().unpolish(self._focus_btn)
    self._focus_btn.style().polish(self._focus_btn)
```

**Step 4: 语法验证**

```bash
python3 -m py_compile ui/fullscreen_viewer.py
```

---

## Task 3：添加 `_HdCache` 和 `_PreloadWorker`

**Files:**
- Modify: `ui/fullscreen_viewer.py`（在模块顶部，`_FOCUS_COLORS` 字典之后插入）

**Step 1: 插入 `_HdCache` 类和模块级实例**

```python
# ============================================================
#  高清图 LRU 缓存（模块级，21 slots，键为绝对路径）
# ============================================================

from collections import OrderedDict

class _HdCache:
    """高清图片 LRU 缓存，键为文件绝对路径字符串。"""

    def __init__(self, maxsize: int = 21):
        self._cache: OrderedDict = OrderedDict()
        self._maxsize = maxsize

    def get(self, key: str) -> Optional[QPixmap]:
        if key not in self._cache:
            return None
        self._cache.move_to_end(key)
        return self._cache[key]

    def put(self, key: str, value: QPixmap):
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)


_hd_cache = _HdCache(21)
```

注意：`from collections import OrderedDict` 已在 thumbnail_grid.py 中使用，这里在类定义前直接 import 即可，或移至文件顶部 import 区。

**Step 2: 插入 `_PreloadWorker` 类**

```python
# ============================================================
#  预加载工作线程
# ============================================================

import threading as _threading

class _PreloadWorker(QThread):
    """
    按优先级顺序预加载高清图片到 _hd_cache。
    调用 restart(paths) 可安全地重置任务列表并重新开始。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._paths: list = []
        self._cancelled: bool = False
        self._lock = _threading.Lock()

    def restart(self, paths: list):
        """设置新的预加载路径列表，取消当前任务后重启。"""
        self._cancelled = True
        self.wait(300)          # 最多等 300ms 让当前任务响应取消
        with self._lock:
            self._paths = list(paths)
            self._cancelled = False
        if not self.isRunning():
            self.start()

    def run(self):
        with self._lock:
            paths = list(self._paths)
        for path in paths:
            if self._cancelled:
                break
            if not path or not os.path.exists(path):
                continue
            if _hd_cache.get(path) is not None:
                continue        # 已在缓存，跳过
            px = QPixmap(path)
            if not px.isNull() and not self._cancelled:
                _hd_cache.put(path, px)
```

**Step 3: 语法验证**

```bash
python3 -m py_compile ui/fullscreen_viewer.py
```

---

## Task 4：更新 `FullscreenViewer` — 预加载集成

**Files:**
- Modify: `ui/fullscreen_viewer.py`（`FullscreenViewer` 类）

**Step 1: `__init__` 中新增 `_preload_worker` 和 `_photos`**

在 `self._loader: Optional[_ImageLoader] = None` 后添加：

```python
self._preload_worker = _PreloadWorker(self)   # 预加载工作线程
self._photos: list = []                        # 当前完整照片列表
```

**Step 2: 新增 `set_photo_list()`**

```python
def set_photo_list(self, photos: list):
    """
    由 ResultsBrowserWindow 在过滤结果变化时调用，
    更新全屏查看器持有的照片列表（用于计算预加载范围）。
    """
    self._photos = photos
```

**Step 3: 替换 `show_photo()`**

完整替换旧的 `show_photo()` 方法：

```python
def show_photo(self, photo: dict):
    """
    展示一张照片。流程：
    1. 更新顶栏（文件名、评分）
    2. 立即显示缩略图缓存（零延迟反馈）
    3. 设置焦点叠加坐标
    4. 优先检查高清 LRU 缓存（可能已被预加载命中）
    5. 未命中则启动 _ImageLoader 异步加载
    6. 触发 ±10 张预加载
    """
    filename = photo.get("filename", "")
    self._filename_label.setText(filename)

    rating = photo.get("rating", 0)
    self._rating_label.setText({3: "★★★", 2: "★★", 1: "★"}.get(rating, ""))

    # 1. 立即显示缩略图缓存
    try:
        from ui.thumbnail_grid import _thumb_cache
        cached = _thumb_cache.get(filename)
        if cached and not cached.isNull():
            self._img_label.set_pixmap(cached)
    except Exception:
        pass

    # 2. 焦点叠加
    self._img_label.set_focus(
        photo.get("focus_x"),
        photo.get("focus_y"),
        photo.get("focus_status")
    )

    # 3. 取消上一个加载任务
    if self._loader and self._loader.isRunning():
        self._loader.cancel()
        self._loader.wait(100)
        self._loader = None

    # 4. 优先检查高清缓存
    hd_path = self._resolve_hd_path(photo)
    if hd_path:
        cached_hd = _hd_cache.get(hd_path)
        if cached_hd and not cached_hd.isNull():
            self._img_label.set_pixmap(cached_hd)
        else:
            # 5. 后台加载，完成后存入高清缓存
            self._loader = _ImageLoader(hd_path, self)
            _path_capture = hd_path
            self._loader.ready.connect(
                lambda px, p=_path_capture: self._on_image_ready(px, p)
            )
            self._loader.start()

    # 6. 触发 ±10 预加载
    self._trigger_preload(photo)
```

**Step 4: 替换 `_on_image_ready()`**

```python
@Slot(object)
def _on_image_ready(self, pixmap: QPixmap, path: str = ""):
    """后台加载完成：存入高清缓存并更新图片显示。"""
    if not pixmap.isNull():
        if path:
            _hd_cache.put(path, pixmap)
        self._img_label.set_pixmap(pixmap)
```

**Step 5: 新增 `_trigger_preload()`**

```python
def _trigger_preload(self, current_photo: dict):
    """
    以 current_photo 为中心，按优先级
    0, +1, -1, +2, -2, ..., ±10 触发高清预加载。
    """
    if not self._photos:
        return
    filenames = [p.get("filename", "") for p in self._photos]
    fn = current_photo.get("filename", "")
    try:
        idx = filenames.index(fn)
    except ValueError:
        return

    n = len(self._photos)
    ordered_paths = []

    # 生成优先级偏移列表：0, +1, -1, +2, -2, ..., ±10
    offsets = [0]
    for d in range(1, 11):
        offsets.append(d)
        offsets.append(-d)

    for offset in offsets:
        i = idx + offset
        if 0 <= i < n:
            path = self._resolve_hd_path(self._photos[i])
            if path and path not in ordered_paths:
                ordered_paths.append(path)

    self._preload_worker.restart(ordered_paths)
```

**Step 6: 语法验证**

```bash
python3 -m py_compile ui/fullscreen_viewer.py
```

---

## Task 5：更新 `results_browser_window.py`

**Files:**
- Modify: `ui/results_browser_window.py`

**Step 1: `_apply_filters()` 中通知全屏查看器照片列表**

在 `self._thumb_grid.load_photos(self._filtered_photos)` 之后（约当前位置的下一行）添加：

```python
self._fullscreen.set_photo_list(self._filtered_photos)
```

**Step 2: 更新 `keyPressEvent` 中 F 键处理**

将现有：
```python
elif key == Qt.Key_F:
    # F 键切换裁切/全图（通过 detail panel 的内部状态）
    self._detail_panel._switch_view(not self._detail_panel._use_crop_view)
```

替换为：
```python
elif key == Qt.Key_F:
    if self._stack.currentIndex() == 1:
        self._fullscreen.toggle_focus()     # 全屏模式：切换焦点图层
    else:
        self._detail_panel._switch_view(not self._detail_panel._use_crop_view)
```

**Step 3: 语法验证**

```bash
python3 -m py_compile ui/results_browser_window.py
```

---

## Task 6：完整语法验证 + 提交

**Step 1: 验证所有修改文件**

```bash
python3 -m py_compile ui/fullscreen_viewer.py ui/results_browser_window.py
```

预期：无输出（静默通过）。

**Step 2: 提交**

```bash
git add ui/fullscreen_viewer.py ui/results_browser_window.py
git commit -m "feat: 全屏查看器 v2 — Lightroom 交互 + 焦点图层开关 + ±10 预加载"
```

---

## 验证清单（人工测试）

1. 重启 GUI，打开一个包含 report.db 的目录
2. 双击缩略图 → 进入全屏，立即显示缩略图，随后替换高清图
3. 单击图片 → 以点击位置为中心缩放到 100%，光标变为张开手
4. 缩放后拖拽 → 图片跟随鼠标平移，光标变为握紧手，松开后恢复张开手
5. 单击图片 → 回到适配模式，光标变为十字
6. 滚轮缩放 → 以鼠标为中心平滑缩放
7. F 键 / 顶栏「焦 ●」按钮 → 焦点圆圈显示/隐藏，按钮颜色同步变化
8. ← → 方向键 / 底栏按钮 → 切换照片，重置为适配模式
9. 快速切换多张 → 后续照片几乎立即显示高清（命中预加载缓存）
10. Escape / 返回按钮 → 回到 grid，窗口不关闭
