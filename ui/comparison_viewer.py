# -*- coding: utf-8 -*-
"""
SuperPicky - 2-up 对比查看器（C5）
ComparisonViewer: 两张图片并排显示，支持键盘快速评分
"""

import os
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent

from ui.styles import COLORS, FONTS
from ui.fullscreen_viewer import _FullscreenImageLabel, _ImageLoader


class ComparisonViewer(QWidget):
    """
    2-up 对比查看器。

    布局：
      [顶栏 52px]  ← 返回 | 文件A ★★★ | 文件B ★★
      [图片区]     Photo A  |  Photo B   (1:1 分割)
      [底栏 44px]  评分按钮 A  |  评分按钮 B

    键盘：
      1-5     : 给左侧照片打分
      Q/W/E/R/T : 给右侧照片打分 (1-5)
      Escape  : 退出对比视图

    信号：
      close_requested()         请求退出对比视图
      rating_changed(str, int)  (filename, new_rating)
    """
    close_requested = Signal()
    rating_changed = Signal(str, int)

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self._photo_a: Optional[dict] = None
        self._photo_b: Optional[dict] = None
        self._loader_a: Optional[_ImageLoader] = None
        self._loader_b: Optional[_ImageLoader] = None

        self.setStyleSheet(f"background-color: {COLORS['bg_void']};")
        self.setFocusPolicy(Qt.StrongFocus)
        self._build_ui()

    # ------------------------------------------------------------------
    #  UI 构建
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶栏
        layout.addWidget(self._build_top_bar())

        # 图片区（左右各占 50%）
        img_area = QWidget()
        img_area.setStyleSheet(f"background-color: {COLORS['bg_void']};")
        img_h = QHBoxLayout(img_area)
        img_h.setContentsMargins(0, 0, 0, 0)
        img_h.setSpacing(2)

        self._img_a = _FullscreenImageLabel()
        self._img_b = _FullscreenImageLabel()
        # C5 同步缩放/平移：互相设为 peer
        self._img_a.set_sync_peer(self._img_b)
        self._img_b.set_sync_peer(self._img_a)
        img_h.addWidget(self._img_a, 1)
        img_h.addWidget(self._img_b, 1)
        layout.addWidget(img_area, 1)

        # 底栏
        layout.addWidget(self._build_bottom_bar())

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

        back_btn = QPushButton(self.i18n.t("browser.back"))
        back_btn.setObjectName("secondary")
        back_btn.setFixedHeight(36)
        back_btn.setMinimumWidth(100)
        back_btn.clicked.connect(self.close_requested)
        h.addWidget(back_btn)

        h.addStretch()

        # 左侧文件名 + 评分
        self._name_a = QLabel("")
        self._name_a.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 12px;
                font-family: {FONTS['mono']};
                background: transparent;
            }}
        """)
        self._name_a.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        h.addWidget(self._name_a)

        self._rating_a = QLabel("")
        self._rating_a.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['star_gold']};
                font-size: 14px;
                background: transparent;
                min-width: 60px;
            }}
        """)
        self._rating_a.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        h.addWidget(self._rating_a)

        sep = QLabel("|")
        sep.setStyleSheet(f"color: {COLORS['border']}; font-size: 16px; background: transparent;")
        h.addWidget(sep)

        # 右侧文件名 + 评分
        self._rating_b = QLabel("")
        self._rating_b.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['star_gold']};
                font-size: 14px;
                background: transparent;
                min-width: 60px;
            }}
        """)
        self._rating_b.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        h.addWidget(self._rating_b)

        self._name_b = QLabel("")
        self._name_b.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 12px;
                font-family: {FONTS['mono']};
                background: transparent;
            }}
        """)
        self._name_b.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        h.addWidget(self._name_b)

        h.addStretch()
        return bar

    def _build_bottom_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(52)
        bar.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(26, 26, 26, 210);
                border-top: 1px solid {COLORS['border_subtle']};
            }}
        """)
        h = QHBoxLayout(bar)
        h.setContentsMargins(16, 0, 16, 0)
        h.setSpacing(8)

        # 左侧评分按钮（1-5 对应键盘 1-5）
        lbl_a = QLabel("A:")
        lbl_a.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent;")
        h.addWidget(lbl_a)

        for i in range(1, 6):
            btn = QPushButton(f"{'★' * i if i <= 3 else f'{i}★'}")
            btn.setObjectName("secondary")
            btn.setFixedHeight(32)
            btn.setFixedWidth(44)
            btn.setToolTip(f"给左侧照片打 {i}★ (键盘 {i})")
            _i = i
            btn.clicked.connect(lambda _=None, stars=_i: self._rate_left(stars))
            h.addWidget(btn)

        h.addStretch()

        # 右侧评分按钮（1-5 对应键盘 Q-T）
        _keys = ["Q", "W", "E", "R", "T"]
        for i in range(1, 6):
            btn = QPushButton(f"{'★' * i if i <= 3 else f'{i}★'}")
            btn.setObjectName("secondary")
            btn.setFixedHeight(32)
            btn.setFixedWidth(44)
            btn.setToolTip(f"给右侧照片打 {i}★ (键盘 {_keys[i-1]})")
            _i = i
            btn.clicked.connect(lambda _=None, stars=_i: self._rate_right(stars))
            h.addWidget(btn)

        lbl_b = QLabel(":B")
        lbl_b.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent;")
        h.addWidget(lbl_b)

        return bar

    # ------------------------------------------------------------------
    #  公共接口
    # ------------------------------------------------------------------

    def show_pair(self, photo_a: dict, photo_b: dict):
        """显示两张照片进行对比。"""
        self._photo_a = photo_a
        self._photo_b = photo_b
        self._refresh_labels()
        self._load_image(photo_a, self._img_a, 'a')
        self._load_image(photo_b, self._img_b, 'b')

    # ------------------------------------------------------------------
    #  内部
    # ------------------------------------------------------------------

    def _refresh_labels(self):
        """刷新顶栏文件名和评分标签。"""
        _RATING_TEXT = {5: "★★★★★", 4: "★★★★", 3: "★★★", 2: "★★", 1: "★", 0: "0", -1: "—"}
        if self._photo_a:
            self._name_a.setText(self._photo_a.get("filename", ""))
            self._rating_a.setText(_RATING_TEXT.get(self._photo_a.get("rating", 0), ""))
        if self._photo_b:
            self._name_b.setText(self._photo_b.get("filename", ""))
            self._rating_b.setText(_RATING_TEXT.get(self._photo_b.get("rating", 0), ""))

    def _load_image(self, photo: dict, img_label: _FullscreenImageLabel, side: str):
        """加载图片到指定侧的 label。"""
        # 优先显示缩略图缓存
        try:
            from ui.thumbnail_grid import _thumb_cache
            fn = photo.get("filename", "")
            cached = _thumb_cache.get(fn)
            if cached and not cached.isNull():
                img_label.set_pixmap(cached)
        except Exception:
            pass

        # 设置焦点叠加
        img_label.set_focus(
            photo.get("focus_x"),
            photo.get("focus_y"),
            photo.get("focus_status")
        )

        # 解析高清路径
        path = self._resolve_path(photo)
        if not path:
            return

        loader_attr = f"_loader_{side}"
        old_loader = getattr(self, loader_attr, None)
        if old_loader and old_loader.isRunning():
            old_loader.cancel()
            old_loader.wait(100)

        loader = _ImageLoader(path, self)
        loader.ready.connect(lambda px, lbl=img_label: lbl.set_pixmap(px) if not px.isNull() else None)
        loader.start()
        setattr(self, loader_attr, loader)

    def _resolve_path(self, photo: dict) -> Optional[str]:
        """按优先级解析高清图路径。"""
        for key in ("temp_jpeg_path", "yolo_debug_path", "debug_crop_path", "original_path", "current_path"):
            p = photo.get(key)
            if p and os.path.exists(p):
                ext = os.path.splitext(p)[1].lower()
                if key in ("temp_jpeg_path", "yolo_debug_path", "debug_crop_path") or ext in ('.jpg', '.jpeg'):
                    return p
        return None

    def _rate_left(self, stars: int):
        """给左侧照片打分。"""
        if not self._photo_a:
            return
        self._photo_a["rating"] = stars
        fn = self._photo_a.get("filename", "")
        self.rating_changed.emit(fn, stars)
        self._refresh_labels()

    def _rate_right(self, stars: int):
        """给右侧照片打分。"""
        if not self._photo_b:
            return
        self._photo_b["rating"] = stars
        fn = self._photo_b.get("filename", "")
        self.rating_changed.emit(fn, stars)
        self._refresh_labels()

    # ------------------------------------------------------------------
    #  键盘快捷键
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        # 左侧评分（1-5 数字键）
        if key == Qt.Key_1:
            self._rate_left(1)
        elif key == Qt.Key_2:
            self._rate_left(2)
        elif key == Qt.Key_3:
            self._rate_left(3)
        elif key == Qt.Key_4:
            self._rate_left(4)
        elif key == Qt.Key_5:
            self._rate_left(5)
        # 右侧评分（Q-T）
        elif key == Qt.Key_Q:
            self._rate_right(1)
        elif key == Qt.Key_W:
            self._rate_right(2)
        elif key == Qt.Key_E:
            self._rate_right(3)
        elif key == Qt.Key_R:
            self._rate_right(4)
        elif key == Qt.Key_T:
            self._rate_right(5)
        elif key == Qt.Key_Escape:
            self.close_requested.emit()
        else:
            super().keyPressEvent(event)
