# -*- coding: utf-8 -*-
"""
SuperPicky - 选鸟结果图片浏览器主窗口
ResultsBrowserWindow(QMainWindow): 三栏布局
  左栏: FilterPanel  — 评分/对焦/曝光/飞行/鸟种 筛选
  中栏: ThumbnailGrid — 缩略图网格（异步加载）
  右栏: DetailPanel  — 大图预览 + 元数据

入口:
  1. 主窗口菜单栏「查看结果」
  2. 处理完成后弹窗「查看选片结果」按钮
"""

import os

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFileDialog, QStatusBar,
    QSlider, QComboBox, QMessageBox, QSizePolicy, QApplication,
    QStackedWidget
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction, QKeyEvent, QIcon, QFont

from ui.styles import COLORS, GLOBAL_STYLE, FONTS
from ui.filter_panel import FilterPanel
from ui.thumbnail_grid import ThumbnailGrid
from ui.detail_panel import DetailPanel
from ui.fullscreen_viewer import FullscreenViewer
from typing import Optional

from tools.i18n import get_i18n
from tools.report_db import ReportDB


class ResultsBrowserWindow(QMainWindow):
    """
    独立的选鸟结果浏览器窗口。

    可以在主窗口之外独立显示/隐藏，不会阻塞主窗口操作。
    """
    closed = Signal()   # 窗口关闭时通知主窗口

    def __init__(self, parent=None):
        super().__init__(parent)
        self.i18n = get_i18n()
        self._db: Optional[ReportDB] = None
        self._directory: str = ""
        self._all_photos: list = []     # 当前目录所有照片
        self._filtered_photos: list = [] # 当前筛选后的照片

        self._setup_window()
        self._setup_menu()
        self._setup_ui()
        self._setup_statusbar()

    # ------------------------------------------------------------------
    #  窗口配置
    # ------------------------------------------------------------------

    def _setup_window(self):
        self.setWindowTitle(self.i18n.t("browser.title"))
        self.setMinimumSize(1000, 680)
        self.resize(1280, 780)
        self.setStyleSheet(GLOBAL_STYLE)

        # 尝试复用主窗口图标
        try:
            import sys
            resource_base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(__file__)))
            icon_path = os.path.join(resource_base, "img", "icon.png")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass

    def _setup_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件" if not self.i18n.current_lang.startswith('en') else "File")

        open_action = QAction(self.i18n.t("browser.open_dir"), self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._browse_directory)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        close_action = QAction("关闭" if not self.i18n.current_lang.startswith('en') else "Close", self)
        close_action.setShortcut("Ctrl+W")
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)

    def _setup_ui(self):
        """QStackedWidget 双页: Page 0 三栏布局 / Page 1 全屏查看器"""
        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        # ── Page 0: 三栏布局 ──────────────────────────────────────
        three_col = QWidget()
        main_h = QHBoxLayout(three_col)
        main_h.setContentsMargins(0, 0, 0, 0)
        main_h.setSpacing(0)

        # 左侧：过滤面板
        self._filter_panel = FilterPanel(self.i18n, self)
        self._filter_panel.filters_changed.connect(self._apply_filters)
        main_h.addWidget(self._filter_panel)

        # 中央：网格 + 工具栏
        center_widget = QWidget()
        center_widget.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        toolbar = self._build_toolbar()
        center_layout.addWidget(toolbar)

        self._thumb_grid = ThumbnailGrid(self.i18n, self)
        self._thumb_grid.photo_selected.connect(self._on_photo_selected)
        self._thumb_grid.photo_double_clicked.connect(self._enter_fullscreen)
        center_layout.addWidget(self._thumb_grid, 1)

        main_h.addWidget(center_widget, 1)

        # 右侧：详情面板
        self._detail_panel = DetailPanel(self.i18n, self)
        self._detail_panel.prev_requested.connect(self._prev_photo)
        self._detail_panel.next_requested.connect(self._next_photo)
        main_h.addWidget(self._detail_panel)

        self._stack.addWidget(three_col)          # index 0

        # ── Page 1: 全屏查看器 ───────────────────────────────────
        self._fullscreen = FullscreenViewer(self.i18n, self)
        self._fullscreen.close_requested.connect(self._exit_fullscreen)
        self._fullscreen.prev_requested.connect(self._fullscreen_prev)
        self._fullscreen.next_requested.connect(self._fullscreen_next)
        self._stack.addWidget(self._fullscreen)   # index 1

    def _build_toolbar(self) -> QWidget:
        """构建网格顶部工具栏（目录选择 + 缩略图尺寸滑块）。"""
        bar = QWidget()
        bar.setFixedHeight(52)
        bar.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_elevated']};
                border-bottom: 1px solid {COLORS['border_subtle']};
            }}
        """)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        # 目录显示标签
        self._dir_label = QLabel(self.i18n.t("browser.open_dir"))
        self._dir_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 12px;
                font-family: {FONTS['mono']};
                background: transparent;
            }}
        """)
        self._dir_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self._dir_label)

        # 打开目录按钮
        open_btn = QPushButton("📂")
        open_btn.setObjectName("secondary")
        open_btn.setFixedSize(32, 32)
        open_btn.setToolTip(self.i18n.t("browser.open_dir"))
        open_btn.clicked.connect(self._browse_directory)
        layout.addWidget(open_btn)

        layout.addSpacing(16)

        # 缩略图尺寸滑块
        size_label = QLabel("SIZE")
        size_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; background: transparent;")
        layout.addWidget(size_label)

        self._size_slider = QSlider(Qt.Horizontal)
        self._size_slider.setRange(80, 300)
        self._size_slider.setValue(160)
        self._size_slider.setFixedWidth(100)
        self._size_slider.valueChanged.connect(self._on_size_changed)
        layout.addWidget(self._size_slider)

        return bar

    def _setup_statusbar(self):
        self._status_bar = QStatusBar()
        self._status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {COLORS['bg_elevated']};
                color: {COLORS['text_secondary']};
                font-size: 11px;
                border-top: 1px solid {COLORS['border_subtle']};
            }}
        """)
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("—")

    # ------------------------------------------------------------------
    #  公共接口
    # ------------------------------------------------------------------

    def open_directory(self, directory: str):
        """加载指定目录的 report.db 并刷新界面。"""
        if not directory:
            return

        db_path = os.path.join(directory, ".superpicky", "report.db")
        if not os.path.exists(db_path):
            self._show_no_db_hint(directory)
            return

        # 关闭旧数据库
        if self._db:
            try:
                self._db.close()
            except Exception:
                pass

        try:
            self._db = ReportDB(directory)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

        self._directory = directory
        short_name = os.path.basename(directory) or directory
        self._dir_label.setText(short_name)
        self._dir_label.setToolTip(directory)

        # 加载数据
        self._all_photos = self._db.get_all_photos()

        # 先重置筛选（会触发 filters_changed -> _apply_filters 加载缩略图）
        self._filter_panel.reset_all()

        # 重置后再更新计数/鸟种（确保是最终显示状态，不被后续事件覆盖）
        counts = self._db.get_rating_counts()
        self._filter_panel.update_rating_counts(counts)
        species = self._db.get_distinct_species()
        self._filter_panel.update_species_list(species)

        self.setWindowTitle(f"{self.i18n.t('browser.title')} — {short_name}")

    # ------------------------------------------------------------------
    #  私有槽
    # ------------------------------------------------------------------

    @Slot()
    def _browse_directory(self):
        """弹出目录选择对话框。"""
        directory = QFileDialog.getExistingDirectory(
            self,
            self.i18n.t("browser.open_dir"),
            self._directory or os.path.expanduser("~")
        )
        if directory:
            self.open_directory(directory)

    def _resolve_photo_paths(self, photo: dict) -> dict:
        """将 photo dict 中的相对路径解析为相对于当前目录的绝对路径。"""
        _PATH_KEYS = ('original_path', 'current_path', 'temp_jpeg_path',
                      'debug_crop_path', 'yolo_debug_path')
        resolved = dict(photo)
        for key in _PATH_KEYS:
            val = photo.get(key)
            if val and not os.path.isabs(val):
                resolved[key] = os.path.join(self._directory, val)
        return resolved

    @Slot(dict)
    def _apply_filters(self, filters: dict):
        """根据过滤面板的条件刷新缩略图网格。"""
        if not self._db:
            self._thumb_grid.load_photos([])
            self._update_status(0, 0)
            return

        raw_photos = self._db.get_photos_by_filters(filters)
        self._filtered_photos = [self._resolve_photo_paths(p) for p in raw_photos]
        self._thumb_grid.load_photos(self._filtered_photos)
        self._fullscreen.set_photo_list(self._filtered_photos)

        total = len(self._all_photos)
        filtered = len(self._filtered_photos)
        self._update_status(total, filtered)

        # 自动选中第一张
        if self._filtered_photos:
            first = self._filtered_photos[0]
            fn = first.get("filename", "")
            self._thumb_grid.select_photo(fn)
            self._detail_panel.show_photo(first)
        else:
            self._detail_panel.clear()

    @Slot(dict)
    def _on_photo_selected(self, photo: dict):
        self._detail_panel.show_photo(photo)

    @Slot()
    def _prev_photo(self):
        photo = self._thumb_grid.select_prev()
        if photo:
            self._detail_panel.show_photo(photo)

    @Slot()
    def _next_photo(self):
        photo = self._thumb_grid.select_next()
        if photo:
            self._detail_panel.show_photo(photo)

    @Slot(dict)
    def _enter_fullscreen(self, photo: dict):
        """双击缩略图 → 进入全屏查看器。"""
        self._fullscreen.show_photo(photo)
        self._stack.setCurrentIndex(1)

    @Slot()
    def _exit_fullscreen(self):
        """返回三栏 grid 视图。"""
        self._stack.setCurrentIndex(0)

    @Slot()
    def _fullscreen_prev(self):
        """全屏模式：上一张。"""
        photo = self._thumb_grid.select_prev()
        if photo:
            self._fullscreen.show_photo(photo)

    @Slot()
    def _fullscreen_next(self):
        """全屏模式：下一张。"""
        photo = self._thumb_grid.select_next()
        if photo:
            self._fullscreen.show_photo(photo)

    @Slot(int)
    def _on_size_changed(self, value: int):
        self._thumb_grid.set_thumb_size(value)

    # ------------------------------------------------------------------
    #  键盘快捷键
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key == Qt.Key_Left:
            self._prev_photo()
        elif key == Qt.Key_Right:
            self._next_photo()
        elif key == Qt.Key_Plus or key == Qt.Key_Equal:
            self._size_slider.setValue(min(300, self._size_slider.value() + 20))
        elif key == Qt.Key_Minus:
            self._size_slider.setValue(max(80, self._size_slider.value() - 20))
        elif key == Qt.Key_Escape:
            if self._stack.currentIndex() == 1:
                self._exit_fullscreen()   # 全屏时 Escape = 返回 grid
            else:
                self.close()              # 普通模式 Escape = 关闭窗口
        elif key == Qt.Key_F:
            if self._stack.currentIndex() == 1:
                # 全屏模式：切换焦点叠加层
                self._fullscreen.toggle_focus()
            else:
                # 普通模式：切换裁切/全图
                self._detail_panel._switch_view(not self._detail_panel._use_crop_view)
        else:
            super().keyPressEvent(event)

    # ------------------------------------------------------------------
    #  工具方法
    # ------------------------------------------------------------------

    def _update_status(self, total: int, filtered: int):
        t = self.i18n.t("browser.total_photos").format(total=total)
        f = self.i18n.t("browser.filtered_photos").format(count=filtered)
        self._status_bar.showMessage(f"{t}  |  {f}")

    def _show_no_db_hint(self, directory: str):
        QMessageBox.information(
            self,
            self.i18n.t("browser.no_db"),
            f"{directory}\n\n{self.i18n.t('browser.no_db_hint')}"
        )

    # ------------------------------------------------------------------
    #  窗口关闭
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        if self._db:
            try:
                self._db.close()
            except Exception:
                pass
            self._db = None
        self.closed.emit()
        super().closeEvent(event)
