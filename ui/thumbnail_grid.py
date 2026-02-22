# -*- coding: utf-8 -*-
"""
SuperPicky - 结果浏览器缩略图网格
ThumbnailGrid: 网格视图 + 异步缩略图加载
ThumbnailCard: 单张照片卡片（评分角标 + 对焦指示点）
ThumbnailLoader: QThread 后台加载缩略图
"""

import os
from collections import OrderedDict
from typing import Optional

from PySide6.QtWidgets import (
    QScrollArea, QWidget, QGridLayout, QLabel, QFrame,
    QVBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QThread, QObject, Slot, QSize, QTimer
from PySide6.QtGui import QPixmap, QColor, QPainter, QPen, QFont, QBrush

from ui.styles import COLORS, FONTS


# 对焦状态指示颜色
_FOCUS_DOT_COLORS = {
    "BEST":  QColor(COLORS['accent']),
    "GOOD":  QColor(COLORS['success']),
    "BAD":   QColor(COLORS['warning']),
    "WORST": QColor(COLORS['error']),
}

# 评分标签颜色
_RATING_COLORS = {
    3: QColor(COLORS['star_gold']),
    2: QColor(COLORS['star_gold']),
    1: QColor(COLORS['star_gold']),
    0: QColor(COLORS['text_muted']),
    -1: QColor(COLORS['text_muted']),
}

_DEFAULT_THUMB_SIZE = 160


# ============================================================
#  LRU 缩略图缓存
# ============================================================

class _LRUCache:
    def __init__(self, maxsize: int = 500):
        self._cache: OrderedDict = OrderedDict()
        self._maxsize = maxsize

    def get(self, key) -> Optional[QPixmap]:
        if key not in self._cache:
            return None
        self._cache.move_to_end(key)
        return self._cache[key]

    def put(self, key, value: QPixmap):
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)


_thumb_cache = _LRUCache(500)


# ============================================================
#  ThumbnailLoader — 后台异步加载
# ============================================================

class _LoaderSignals(QObject):
    thumbnail_ready = Signal(str, object)   # filename, QPixmap
    load_error = Signal(str)


class ThumbnailLoader(QThread):
    """
    后台线程，按需加载缩略图 QPixmap。

    优先级：debug_crop_path > temp_jpeg_path > 原始 JPG
    """

    def __init__(self, tasks: list, thumb_size: int, parent=None):
        """
        Args:
            tasks: list of photo dicts (含 filename, debug_crop_path, temp_jpeg_path, original_path)
            thumb_size: 输出正方形尺寸（像素）
        """
        super().__init__(parent)
        self._tasks = tasks
        self._thumb_size = thumb_size
        self.signals = _LoaderSignals()
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        size = QSize(self._thumb_size, self._thumb_size)

        for photo in self._tasks:
            if self._cancelled:
                break

            filename = photo.get("filename", "")

            # 先查缓存
            cached = _thumb_cache.get(filename)
            if cached is not None:
                self.signals.thumbnail_ready.emit(filename, cached)
                continue

            pixmap = self._load_pixmap(photo)
            if pixmap and not pixmap.isNull():
                # 等比缩放后居中裁切
                pixmap = pixmap.scaled(
                    size,
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation
                )
                # 居中裁切到正方形
                if pixmap.width() > self._thumb_size or pixmap.height() > self._thumb_size:
                    x = (pixmap.width() - self._thumb_size) // 2
                    y = (pixmap.height() - self._thumb_size) // 2
                    pixmap = pixmap.copy(x, y, self._thumb_size, self._thumb_size)
                _thumb_cache.put(filename, pixmap)
                self.signals.thumbnail_ready.emit(filename, pixmap)
            else:
                self.signals.thumbnail_ready.emit(filename, QPixmap())

    def _load_pixmap(self, photo: dict) -> Optional[QPixmap]:
        """按优先级查找可用图片文件并加载。"""
        candidates = []

        # 1. yolo_debug_path（全图 + 检测框，构图感更好）
        ydp = photo.get("yolo_debug_path")
        if ydp and os.path.exists(ydp):
            candidates.append(ydp)

        # 2. debug_crop_path（裁切图，备用）
        dcp = photo.get("debug_crop_path")
        if dcp and os.path.exists(dcp):
            candidates.append(dcp)

        # 3. temp_jpeg_path（全图 JPEG 预览）
        tjp = photo.get("temp_jpeg_path")
        if tjp and os.path.exists(tjp):
            candidates.append(tjp)

        # 4. original_path（直接找原始 JPG）
        op = photo.get("original_path") or photo.get("current_path")
        if op and os.path.exists(op):
            ext = os.path.splitext(op)[1].lower()
            if ext in ('.jpg', '.jpeg'):
                candidates.append(op)

        for path in candidates:
            px = QPixmap(path)
            if not px.isNull():
                return px

        return None


# ============================================================
#  ThumbnailCard — 单张照片卡片
# ============================================================

class ThumbnailCard(QFrame):
    """
    单张照片的缩略图卡片。

    信号 clicked(photo_dict) 在用户单击时发出。
    信号 double_clicked(photo_dict) 在用户双击时发出。
    """
    clicked = Signal(dict)
    double_clicked = Signal(dict)

    def __init__(self, photo: dict, thumb_size: int = _DEFAULT_THUMB_SIZE, parent=None):
        super().__init__(parent)
        self.photo = photo
        self._thumb_size = thumb_size
        self._selected = False

        self.setFixedSize(thumb_size + 8, thumb_size + 32)
        self.setStyleSheet(self._normal_style())
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.ClickFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # 图片 label
        self.img_label = QLabel()
        self.img_label.setFixedSize(thumb_size, thumb_size)
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['bg_void']};
                border-radius: 6px;
                color: {COLORS['text_muted']};
                font-size: 11px;
            }}
        """)
        self.img_label.setText("...")
        layout.addWidget(self.img_label)

        # 文件名 label
        self.name_label = QLabel(photo.get("filename", ""))
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_muted']};
                font-size: 10px;
                background: transparent;
            }}
        """)
        self.name_label.setMaximumWidth(thumb_size + 4)
        layout.addWidget(self.name_label)

    def set_pixmap(self, pixmap: QPixmap):
        if pixmap.isNull():
            self.img_label.setText("—")
        else:
            self.img_label.setPixmap(pixmap)
            self.img_label.setText("")
        # 在图片上绘制叠加层（评分 + 对焦状态）
        self._draw_overlays()

    def _draw_overlays(self):
        """在 img_label 的 pixmap 上绘制评分角标和对焦指示点。"""
        base = self.img_label.pixmap()
        if base is None or base.isNull():
            return

        overlay = QPixmap(base)
        painter = QPainter(overlay)
        painter.setRenderHint(QPainter.Antialiasing)

        rating = self.photo.get("rating", 0)
        focus = self.photo.get("focus_status")

        # 右上角：评分星标（小圆角矩形）
        if rating and rating > 0:
            stars = "★" * rating
            color = _RATING_COLORS.get(rating, QColor(COLORS['text_muted']))
            bg = QColor(0, 0, 0, 160)
            painter.setPen(Qt.NoPen)
            painter.setBrush(bg)
            rect_w, rect_h = 36, 16
            x = overlay.width() - rect_w - 4
            painter.drawRoundedRect(x, 4, rect_w, rect_h, 4, 4)
            painter.setPen(color)
            font = QFont()
            font.setPixelSize(10)
            painter.setFont(font)
            painter.drawText(x, 4, rect_w, rect_h, Qt.AlignCenter, stars)

        # 右下角：对焦状态圆点
        if focus and focus in _FOCUS_DOT_COLORS:
            dot_color = _FOCUS_DOT_COLORS[focus]
            painter.setPen(Qt.NoPen)
            painter.setBrush(dot_color)
            painter.drawEllipse(overlay.width() - 12, overlay.height() - 12, 8, 8)

        # 左下角：burst 编号角标
        burst_id = self.photo.get("burst_id")
        burst_pos = self.photo.get("burst_position")
        if burst_id is not None and burst_pos is not None:
            burst_text = f"B{burst_id + 1}/{burst_pos}"
            bg = QColor(0, 0, 0, 160)
            painter.setPen(Qt.NoPen)
            painter.setBrush(bg)
            rect_w, rect_h = 38, 16
            painter.drawRoundedRect(4, overlay.height() - rect_h - 4, rect_w, rect_h, 4, 4)
            painter.setPen(QColor(220, 220, 220))
            font = QFont()
            font.setPixelSize(9)
            painter.setFont(font)
            painter.drawText(4, overlay.height() - rect_h - 4, rect_w, rect_h, Qt.AlignCenter, burst_text)

        painter.end()
        self.img_label.setPixmap(overlay)

    def set_selected(self, selected: bool):
        self._selected = selected
        self.setStyleSheet(self._selected_style() if selected else self._normal_style())

    def _normal_style(self):
        return f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 8px;
            }}
            QFrame:hover {{
                border: 1px solid {COLORS['text_muted']};
                background-color: {COLORS['bg_elevated']};
            }}
        """

    def _selected_style(self):
        return f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 2px solid {COLORS['accent']};
                border-radius: 8px;
            }}
        """

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.photo)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self.photo)
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Left, Qt.Key_Up, Qt.Key_Right, Qt.Key_Down):
            # 沿 parent 链找到 ThumbnailGrid 并代理箭头键
            # 层级：card → _container → viewport → ThumbnailGrid
            node = self.parent()
            while node is not None:
                if isinstance(node, ThumbnailGrid):
                    node.keyPressEvent(event)
                    return
                node = node.parent()
        super().keyPressEvent(event)


# ============================================================
#  ThumbnailGrid — 缩略图网格
# ============================================================

class ThumbnailGrid(QScrollArea):
    """
    照片缩略图网格。

    信号 photo_selected(photo_dict) 在用户选中一张照片时发出。
    信号 photo_double_clicked(photo_dict) 在用户双击缩略图时发出。
    """
    photo_selected = Signal(dict)
    photo_double_clicked = Signal(dict)

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self._thumb_size = _DEFAULT_THUMB_SIZE
        self._photos: list = []
        self._cards: dict = {}         # filename -> ThumbnailCard
        self._selected_filename: str = ""
        self._loader: Optional[ThumbnailLoader] = None

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet(f"QScrollArea {{ background-color: {COLORS['bg_primary']}; border: none; }}")
        self.setFocusPolicy(Qt.StrongFocus)

        self._container = QWidget()
        self._container.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        self._grid = QGridLayout(self._container)
        self._grid.setSpacing(8)
        self._grid.setContentsMargins(16, 16, 16, 16)
        self.setWidget(self._container)

        # 空状态 label
        self._empty_label = QLabel(self.i18n.t("browser.no_results"))
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_muted']};
                font-size: 14px;
                background: transparent;
            }}
        """)
        self._grid.addWidget(self._empty_label, 0, 0, 1, 1)

    # ------------------------------------------------------------------
    #  公共接口
    # ------------------------------------------------------------------

    def load_photos(self, photos: list):
        """加载照片列表并重建网格。"""
        # 取消上一个加载任务
        if self._loader and self._loader.isRunning():
            self._loader.cancel()
            self._loader.wait(500)

        self._photos = photos
        self._cards.clear()
        self._selected_filename = ""

        # 清空旧卡片
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not photos:
            self._empty_label = QLabel(self.i18n.t("browser.no_results"))
            self._empty_label.setAlignment(Qt.AlignCenter)
            self._empty_label.setStyleSheet(
                f"color: {COLORS['text_muted']}; font-size: 14px; background: transparent;"
            )
            self._grid.addWidget(self._empty_label, 0, 0, 1, 1)
            return

        # 动态计算列数
        col_count = max(1, (self.width() - 32) // (self._thumb_size + 8))

        # 创建所有卡片（先占位）
        for idx, photo in enumerate(photos):
            row, col = divmod(idx, col_count)
            card = ThumbnailCard(photo, self._thumb_size)
            card.clicked.connect(self._on_card_clicked)
            card.double_clicked.connect(lambda p: self.photo_double_clicked.emit(p))
            self._cards[photo.get("filename", "")] = card
            self._grid.addWidget(card, row, col)

        # 启动异步加载
        self._loader = ThumbnailLoader(photos, self._thumb_size, self)
        self._loader.signals.thumbnail_ready.connect(self._on_thumbnail_ready)
        self._loader.start()

    def set_thumb_size(self, size: int):
        """调整缩略图尺寸并重新加载。"""
        if size != self._thumb_size:
            self._thumb_size = size
            self.load_photos(self._photos)

    def select_photo(self, filename: str):
        """高亮选中指定文件名的卡片。"""
        if self._selected_filename and self._selected_filename in self._cards:
            self._cards[self._selected_filename].set_selected(False)
        self._selected_filename = filename
        if filename in self._cards:
            self._cards[filename].set_selected(True)
            # 滚动到可见区域
            card = self._cards[filename]
            self.ensureWidgetVisible(card)

    def select_next(self) -> Optional[dict]:
        """选中下一张，返回 photo dict；已在末尾则返回 None。"""
        return self._select_adjacent(1)

    def select_prev(self) -> Optional[dict]:
        """选中上一张，返回 photo dict；已在开头则返回 None。"""
        return self._select_adjacent(-1)

    # ------------------------------------------------------------------
    #  内部
    # ------------------------------------------------------------------

    def _select_adjacent(self, delta: int) -> Optional[dict]:
        if not self._photos:
            return None
        filenames = [p.get("filename", "") for p in self._photos]
        try:
            idx = filenames.index(self._selected_filename)
        except ValueError:
            idx = -1
        new_idx = idx + delta
        if 0 <= new_idx < len(self._photos):
            photo = self._photos[new_idx]
            self.select_photo(photo.get("filename", ""))
            self.photo_selected.emit(photo)
            return photo
        return None

    @Slot(str, object)
    def _on_thumbnail_ready(self, filename: str, pixmap):
        card = self._cards.get(filename)
        if card:
            card.set_pixmap(pixmap)

    def _on_card_clicked(self, photo: dict):
        filename = photo.get("filename", "")
        self.select_photo(filename)
        self.photo_selected.emit(photo)

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_Left, Qt.Key_Up):
            self._select_adjacent(-1)
        elif key in (Qt.Key_Right, Qt.Key_Down):
            self._select_adjacent(1)
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 窗口改变大小时延迟重排网格
        QTimer.singleShot(100, lambda: self.load_photos(self._photos))
