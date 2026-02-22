# -*- coding: utf-8 -*-
"""
SuperPicky - 全屏图片查看器
FullscreenViewer: 全屏大图 + 焦点叠加指示
_FullscreenImageLabel: 支持滚轮缩放 + paintEvent 绘制焦点圆圈/十字
"""

import os
import threading as _threading
from collections import OrderedDict
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QThread, Slot
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QBrush

from ui.styles import COLORS, FONTS


# 焦点状态颜色映射
_FOCUS_COLORS = {
    "BEST":  QColor("#00d4aa"),   # accent 青绿
    "GOOD":  QColor("#22c55e"),   # success 绿
    "BAD":   QColor("#eab308"),   # warning 黄
    "WORST": QColor("#ef4444"),   # error 红
}


# ============================================================
#  高清图 LRU 缓存（模块级，21 slots，键为绝对路径）
# ============================================================


class _HdCache:
    """
    高清图片 LRU 缓存，键为文件绝对路径字符串。
    存储 QImage（线程安全），主线程读取时转换为 QPixmap。
    """

    def __init__(self, maxsize: int = 21):
        self._cache: OrderedDict = OrderedDict()
        self._maxsize = maxsize
        self._lock = _threading.Lock()

    def get(self, key: str) -> Optional[QImage]:
        with self._lock:
            if key not in self._cache:
                return None
            self._cache.move_to_end(key)
            return self._cache[key]

    def put(self, key: str, value: QImage):
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = value
            if len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)


_hd_cache = _HdCache(21)


# ============================================================
#  预加载工作线程
# ============================================================


class _PreloadWorker(QThread):
    """
    按优先级顺序预加载高清图片到 _hd_cache。
    调用 restart(paths) 可安全地重置任务列表并重新开始。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._paths: list = []
        self._cancelled: bool = False
        self._pending_restart: bool = False
        self._lock = _threading.Lock()
        self.finished.connect(self._check_restart)

    def restart(self, paths: list):
        """设置新的预加载路径列表，非阻塞地（重）启动。"""
        with self._lock:
            self._paths = list(paths)
        if self.isRunning():
            # 通知当前 run() 尽快退出，run() 结束后由 _check_restart 接力启动
            self._cancelled = True
            self._pending_restart = True
        else:
            self._cancelled = False
            self._pending_restart = False
            self.start()

    def _check_restart(self):
        """run() 结束后检查是否有新的预加载任务等待启动（主线程执行）。"""
        if self._pending_restart:
            self._pending_restart = False
            self._cancelled = False
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
            # QImage 可在工作线程安全使用；QPixmap 须在主线程转换
            img = QImage(path)
            if not img.isNull() and not self._cancelled:
                _hd_cache.put(path, img)


# ============================================================
#  后台异步图片加载器（复用 detail_panel 的实现思路）
# ============================================================

class _ImageLoader(QThread):
    """后台线程加载 QPixmap，避免主线程阻塞。"""
    ready = Signal(object)   # QPixmap

    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self._path = path
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        if self._cancelled:
            return
        if self._path and os.path.exists(self._path):
            px = QPixmap(self._path)
            if not self._cancelled:
                self.ready.emit(px)
        else:
            if not self._cancelled:
                self.ready.emit(QPixmap())


# ============================================================
#  _FullscreenImageLabel — 图片显示 + 焦点叠加 + 滚轮缩放
# ============================================================

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


# ============================================================
#  FullscreenViewer — 全屏查看器主组件
# ============================================================

class FullscreenViewer(QWidget):
    """
    全屏图片查看器（嵌入 QStackedWidget 的 Page 1）。

    信号:
        close_requested()   用户请求返回 grid
        prev_requested()    用户请求上一张
        next_requested()    用户请求下一张
    """
    close_requested = Signal()
    prev_requested = Signal()
    next_requested = Signal()

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self._loader: Optional[_ImageLoader] = None
        self._preload_worker = _PreloadWorker(self)   # 预加载工作线程
        self._photos: list = []                        # 当前完整照片列表

        self.setStyleSheet(f"background-color: {COLORS['bg_void']};")
        self.setFocusPolicy(Qt.StrongFocus)            # 允许接收键盘事件
        self._build_ui()

    # ------------------------------------------------------------------
    #  UI 构建
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- 顶栏 52px ---
        top_bar = self._build_top_bar()
        layout.addWidget(top_bar)

        # --- 图片区域（stretch=1）---
        self._img_label = _FullscreenImageLabel()
        layout.addWidget(self._img_label, 1)

        # --- 底部导航栏 44px ---
        bottom_bar = self._build_bottom_bar()
        layout.addWidget(bottom_bar)

    def _build_top_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(52)
        bar.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(26, 26, 26, 210);
                border-bottom: 1px solid {COLORS['border_subtle']};
            }}
        """)
        h = QHBoxLayout(bar)
        h.setContentsMargins(16, 0, 16, 0)
        h.setSpacing(12)

        # 返回按钮
        back_btn = QPushButton("← 返回")
        back_btn.setObjectName("secondary")
        back_btn.setFixedHeight(36)
        back_btn.setMinimumWidth(100)
        back_btn.clicked.connect(self.close_requested)
        h.addWidget(back_btn)

        # 焦点图层开关按钮
        self._focus_btn = QPushButton("焦 ●")
        self._focus_btn.setFixedHeight(36)
        self._focus_btn.setMinimumWidth(80)
        self._focus_btn.setToolTip("切换焦点叠加显示 (F)")
        self._focus_btn.clicked.connect(self._on_focus_btn_clicked)
        h.addWidget(self._focus_btn)
        # 初始 objectName="" → 默认 accent 色（由 app QSS 自动选中）

        h.addStretch()

        # 文件名标签
        self._filename_label = QLabel("")
        self._filename_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 13px;
                font-family: {FONTS['mono']};
                background: transparent;
            }}
        """)
        self._filename_label.setAlignment(Qt.AlignCenter)
        h.addWidget(self._filename_label)

        # 评分标签
        self._rating_label = QLabel("")
        self._rating_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['star_gold']};
                font-size: 16px;
                background: transparent;
                min-width: 60px;
            }}
        """)
        self._rating_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        h.addWidget(self._rating_label)

        return bar

    def _build_bottom_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(44)
        bar.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(26, 26, 26, 210);
                border-top: 1px solid {COLORS['border_subtle']};
            }}
        """)
        h = QHBoxLayout(bar)
        h.setContentsMargins(16, 0, 16, 0)
        h.setSpacing(12)

        h.addStretch()

        prev_btn = QPushButton("◀ 上一张")
        prev_btn.setObjectName("secondary")
        prev_btn.setFixedHeight(32)
        prev_btn.setFixedWidth(100)
        prev_btn.clicked.connect(self.prev_requested)
        h.addWidget(prev_btn)

        next_btn = QPushButton("下一张 ▶")
        next_btn.setObjectName("secondary")
        next_btn.setFixedHeight(32)
        next_btn.setFixedWidth(100)
        next_btn.clicked.connect(self.next_requested)
        h.addWidget(next_btn)

        h.addStretch()

        return bar

    # ------------------------------------------------------------------
    #  焦点图层控制
    # ------------------------------------------------------------------

    def toggle_focus(self):
        """切换焦点叠加（供外部 F 键调用 + 内部按钮调用）。"""
        self._img_label.toggle_focus()
        self._update_focus_btn_style(self._img_label.focus_visible)

    def _on_focus_btn_clicked(self):
        self.toggle_focus()

    def _update_focus_btn_style(self, visible: bool):
        """visible=True → accent 主按钮色；False → secondary 灰色；两种状态均用浅灰文字。"""
        self._focus_btn.setObjectName("" if visible else "secondary")
        self._focus_btn.style().unpolish(self._focus_btn)
        self._focus_btn.style().polish(self._focus_btn)
        # 两种状态都强制浅灰文字，避免深色背景下出现黑字
        self._focus_btn.setStyleSheet(f"color: {COLORS['text_secondary']};")

    # ------------------------------------------------------------------
    #  公共接口
    # ------------------------------------------------------------------

    def set_photo_list(self, photos: list):
        """
        由 ResultsBrowserWindow 在过滤结果变化时调用，
        更新全屏查看器持有的照片列表（用于计算预加载范围）。
        """
        self._photos = photos

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

        # 3. 取消上一个加载任务，断开信号防止旧图覆盖新显示
        if self._loader:
            self._loader.cancel()
            if self._loader.isRunning():
                self._loader.wait(100)
            try:
                self._loader.ready.disconnect()
            except RuntimeError:
                pass
            self._loader = None

        # 4. 优先检查高清缓存（存的是 QImage，需在主线程转为 QPixmap）
        hd_path = self._resolve_hd_path(photo)
        if hd_path:
            cached_img = _hd_cache.get(hd_path)
            if cached_img and not cached_img.isNull():
                self._img_label.set_pixmap(QPixmap.fromImage(cached_img))
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

        # 确保全屏 viewer 持有键盘焦点（切换照片后维持焦点）
        self.setFocus()

    # ------------------------------------------------------------------
    #  内部
    # ------------------------------------------------------------------

    def _resolve_hd_path(self, photo: dict) -> Optional[str]:
        """按优先级解析高清图路径：temp_jpeg_path → yolo_debug_path。"""
        tjp = photo.get("temp_jpeg_path")
        if tjp and os.path.exists(tjp):
            return tjp
        ydp = photo.get("yolo_debug_path")
        if ydp and os.path.exists(ydp):
            return ydp
        # 最后回退到原始 JPEG
        op = photo.get("original_path") or photo.get("current_path")
        if op and os.path.exists(op):
            ext = os.path.splitext(op)[1].lower()
            if ext in ('.jpg', '.jpeg'):
                return op
        return None

    @Slot(object)
    def _on_image_ready(self, pixmap: QPixmap, path: str = ""):
        """后台加载完成：转存为 QImage 进高清缓存，并更新图片显示。"""
        if not pixmap.isNull():
            if path:
                # QPixmap.toImage() 在主线程执行，线程安全
                _hd_cache.put(path, pixmap.toImage())
            self._img_label.set_pixmap(pixmap)

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

    # ------------------------------------------------------------------
    #  键盘事件（左右箭头导航，F 切换焦点，Escape 返回）
    # ------------------------------------------------------------------

    def keyPressEvent(self, event):
        from PySide6.QtCore import Qt as _Qt
        key = event.key()
        if key in (_Qt.Key_Left, _Qt.Key_Up):
            self.prev_requested.emit()
        elif key in (_Qt.Key_Right, _Qt.Key_Down):
            self.next_requested.emit()
        elif key == _Qt.Key_F:
            self.toggle_focus()
        elif key == _Qt.Key_Escape:
            self.close_requested.emit()
        else:
            super().keyPressEvent(event)
