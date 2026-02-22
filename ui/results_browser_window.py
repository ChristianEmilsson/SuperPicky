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
import subprocess
import sys

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStatusBar,
    QSlider, QComboBox, QMessageBox, QSizePolicy, QApplication,
    QStackedWidget, QMenu
)
from PySide6.QtCore import Qt, Signal, Slot, QProcess
from PySide6.QtGui import QAction, QKeyEvent, QIcon, QFont

from ui.styles import COLORS, GLOBAL_STYLE, FONTS
from ui.filter_panel import FilterPanel
from ui.thumbnail_grid import ThumbnailGrid
from ui.detail_panel import DetailPanel
from ui.fullscreen_viewer import FullscreenViewer
from ui.comparison_viewer import ComparisonViewer
from typing import Optional

from tools.i18n import get_i18n
from tools.report_db import ReportDB


# ============================================================
#  C4 — 右键菜单实现（应用列表来自用户配置）
# ============================================================


def _show_context_menu_impl(parent_widget, photo: dict, pos, directory: str):
    """构建并显示右键菜单（C4）。外部应用列表从 advanced_config 读取。"""
    from advanced_config import get_advanced_config

    filepath = photo.get("original_path") or photo.get("current_path") or ""
    if not filepath:
        fn = photo.get("filename", "")
        if fn and directory:
            filepath = os.path.join(directory, fn)

    menu = QMenu(parent_widget)
    menu.setStyleSheet(f"""
        QMenu {{
            background-color: {COLORS['bg_elevated']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            padding: 4px;
        }}
        QMenu::item {{ padding: 6px 16px; border-radius: 4px; }}
        QMenu::item:selected {{ background-color: {COLORS['bg_card']}; }}
        QMenu::separator {{ height: 1px; background: {COLORS['border_subtle']}; margin: 4px 8px; }}
    """)

    # 在 Finder/Explorer 中显示
    def _reveal():
        if sys.platform == "darwin" and filepath:
            # QProcess.startDetached 不受 Python subprocess 沙盒限制
            QProcess.startDetached("open", ["--reveal", filepath])
        elif sys.platform == "win32" and filepath:
            QProcess.startDetached("explorer", ["/select,", filepath.replace("/", "\\")])

    finder_action = QAction("🔍  在 Finder 中显示", parent_widget)
    # 有路径即启用（open --reveal 在文件不存在时会打开父目录，不会崩溃）
    finder_action.setEnabled(bool(filepath))
    finder_action.triggered.connect(_reveal)
    menu.addAction(finder_action)

    # 用户配置的外部应用列表（设置 → 外部应用）
    external_apps = get_advanced_config().get_external_apps()
    if external_apps:
        menu.addSeparator()
        for app in external_apps:
            app_name = app.get("name", "")
            app_path = app.get("path", "")
            if not app_name or not app_path:
                continue
            act = QAction(f"🖼  用 {app_name} 打开", parent_widget)
            act.setEnabled(bool(filepath))

            def _open_in_app(_checked=False, _fp=filepath, _ap=app_path):
                if sys.platform == "darwin" and _fp:
                    QProcess.startDetached("open", ["-a", _ap, _fp])
                elif sys.platform == "win32" and _fp:
                    QProcess.startDetached(_ap, [_fp])

            act.triggered.connect(_open_in_app)
            menu.addAction(act)
    else:
        # 未配置时提示用户去设置
        menu.addSeparator()
        hint_action = QAction("⚙️  在设置中添加外部应用…", parent_widget)
        hint_action.setEnabled(False)
        menu.addAction(hint_action)

    menu.addSeparator()

    # 复制路径
    copy_action = QAction("📋  复制文件路径", parent_widget)
    copy_action.setEnabled(bool(filepath))
    if filepath:
        def _copy_path(_checked=False, _fp=filepath):
            QApplication.clipboard().setText(_fp)
        copy_action.triggered.connect(_copy_path)
    menu.addAction(copy_action)

    menu.exec(pos)


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
        self.setFocusPolicy(Qt.StrongFocus)  # 确保窗口能接收键盘事件

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

        file_menu = menubar.addMenu(self.i18n.t("menu.file"))

        file_menu.addSeparator()

        close_action = QAction(self.i18n.t("buttons.close"), self)
        close_action.setShortcut("Ctrl+W")
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)

    def _setup_ui(self):
        """
        布局：外层 QHBoxLayout = [QStackedWidget (左/中)] + [DetailPanel (右，始终可见)]
        QStackedWidget:
          Page 0 — 过滤面板 + 缩略图网格（两栏）
          Page 1 — 全屏查看器
        DetailPanel 在 Stack 外部，Tab 键开关可见性。
        """
        outer = QWidget()
        self.setCentralWidget(outer)
        outer_h = QHBoxLayout(outer)
        outer_h.setContentsMargins(0, 0, 0, 0)
        outer_h.setSpacing(0)

        # ── Stack（左/中部分）──────────────────────────────────────
        self._stack = QStackedWidget()
        outer_h.addWidget(self._stack, 1)

        # Page 0: 过滤面板 + 缩略图网格
        two_col = QWidget()
        main_h = QHBoxLayout(two_col)
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
        self._thumb_grid.multi_selection_changed.connect(self._on_multi_selection_changed)
        center_layout.addWidget(self._thumb_grid, 1)

        main_h.addWidget(center_widget, 1)
        self._stack.addWidget(two_col)            # index 0

        # Page 1: 全屏查看器
        self._fullscreen = FullscreenViewer(self.i18n, self)
        self._fullscreen.close_requested.connect(self._exit_fullscreen)
        self._fullscreen.prev_requested.connect(self._fullscreen_prev)
        self._fullscreen.next_requested.connect(self._fullscreen_next)
        self._stack.addWidget(self._fullscreen)   # index 1

        # Page 2: 对比查看器（C5）
        self._comparison = ComparisonViewer(self.i18n, self)
        self._comparison.close_requested.connect(self._exit_comparison)
        self._comparison.rating_changed.connect(self._on_rating_changed)
        self._stack.addWidget(self._comparison)   # index 2

        # ── 右侧详情面板（始终显示，Tab 键开关）──────────────────
        self._detail_panel = DetailPanel(self.i18n, self)
        self._detail_panel.prev_requested.connect(self._prev_photo)
        self._detail_panel.next_requested.connect(self._next_photo)
        self._detail_panel.rating_change_requested.connect(self._on_rating_changed)
        outer_h.addWidget(self._detail_panel, 0)

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

        # P2: 返回主界面按钮（最左侧）
        back_btn = QPushButton(self.i18n.t("browser.back"))
        back_btn.setObjectName("tertiary")
        back_btn.setFixedHeight(32)
        back_btn.setToolTip(self.i18n.t("browser.back_tooltip"))
        back_btn.clicked.connect(self._go_back_to_main)
        layout.addWidget(back_btn)

        layout.addSpacing(8)

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

        layout.addSpacing(16)

        # 多选计数标签（C3，默认隐藏）
        self._select_count_label = QLabel("")
        self._select_count_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['accent']};
                font-size: 12px;
                background: transparent;
            }}
        """)
        self._select_count_label.hide()
        layout.addWidget(self._select_count_label)

        # 对比按钮（C5，多选2张时显示）
        self._compare_btn = QPushButton("🔀 对比")
        self._compare_btn.setObjectName("secondary")
        self._compare_btn.setFixedHeight(32)
        self._compare_btn.hide()
        self._compare_btn.clicked.connect(self._enter_comparison)
        layout.addWidget(self._compare_btn)

        # 缩略图尺寸滑块
        size_label = QLabel(self.i18n.t("browser.size_label"))
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
        counts = self._db.get_statistics().get("by_rating", {})
        self._filter_panel.update_rating_counts(counts)
        species = self._db.get_distinct_species()
        self._filter_panel.update_species_list(species)

        self.setWindowTitle(f"{self.i18n.t('browser.title')} — {short_name}")

    # ------------------------------------------------------------------
    #  私有槽
    # ------------------------------------------------------------------

    @Slot()
    def _go_back_to_main(self):
        """P2: 隐藏结果浏览器，将主窗口置前。"""
        self.hide()
        if self.parent() is not None:
            self.parent().show()
            self.parent().raise_()
            self.parent().activateWindow()
        else:
            # 无父窗口时尝试激活同应用的其他窗口
            app = QApplication.instance()
            if app:
                for widget in app.topLevelWidgets():
                    if widget is not self and widget.isVisible():
                        widget.raise_()
                        widget.activateWindow()
                        break

    def _resolve_photo_paths(self, photo: dict) -> dict:
        """将 photo dict 中的相对路径解析为相对于当前目录的绝对路径。"""
        _PATH_KEYS = ('original_path', 'current_path', 'temp_jpeg_path',
                      'debug_crop_path', 'yolo_debug_path')
        resolved = dict(photo)
        for key in _PATH_KEYS:
            val = photo.get(key)
            if val and not os.path.isabs(val):
                resolved[key] = os.path.join(self._directory, val)
        # 注入 burst_total 供缩略图角标显示
        bid = resolved.get("burst_id")
        if bid is not None and hasattr(self, '_burst_totals'):
            resolved["burst_total"] = self._burst_totals.get(bid, 1)
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
        self._detail_panel.show_photo(photo)
        self._detail_panel._switch_view(True)   # 进入全屏 → 切到裁切图
        self._stack.setCurrentIndex(1)
        self._fullscreen.setFocus()  # 确保全屏 viewer 获得键盘焦点

    @Slot()
    def _exit_fullscreen(self):
        """返回 grid 视图。"""
        self._stack.setCurrentIndex(0)
        self._detail_panel._switch_view(False)  # 退出全屏 → 切回全图
        self.setFocus()  # 确保窗口拿回焦点

    @Slot()
    def _fullscreen_prev(self):
        """全屏模式：上一张。"""
        photo = self._thumb_grid.select_prev()
        if photo:
            self._fullscreen.show_photo(photo)
            self._detail_panel.show_photo(photo)

    @Slot()
    def _fullscreen_next(self):
        """全屏模式：下一张。"""
        photo = self._thumb_grid.select_next()
        if photo:
            self._fullscreen.show_photo(photo)
            self._detail_panel.show_photo(photo)

    @Slot(str, int)
    def _on_rating_changed(self, filename: str, new_rating: int):
        """详情面板评分修改：写入 DB + 刷新缩略图角标。"""
        if self._db:
            self._db.update_photo(filename, {"rating": new_rating})
        for p in self._filtered_photos:
            if p.get("filename") == filename:
                p["rating"] = new_rating
                break
        self._thumb_grid.refresh_photo(filename, new_rating)

    @Slot(list)
    def _on_multi_selection_changed(self, photos: list):
        """C3：多选状态变化，更新工具栏显示。"""
        n = len(photos)
        if n > 1:
            self._select_count_label.setText(f"已选 {n} 张")
            self._select_count_label.show()
        else:
            self._select_count_label.hide()
        # C5：仅当选中 2 张时显示对比按钮
        self._compare_btn.setVisible(n == 2)

    def _show_context_menu(self, photo: dict, pos):
        """C4：右键菜单（由 ThumbnailGrid 通过 parent chain 调用）。"""
        _show_context_menu_impl(self, photo, pos, self._directory)

    def _enter_comparison(self):
        """C5：进入 2-up 对比视图（ResultsBrowserWindow）。"""
        photos = self._thumb_grid.get_multi_selected_photos()
        if len(photos) >= 2:
            self._comparison.show_pair(photos[0], photos[1])
            self._detail_panel.hide()   # 对比模式不显示详情面板
            self._stack.setCurrentIndex(2)
            self._comparison.setFocus()

    def _exit_comparison(self):
        """C5：退出对比视图，回到 grid（ResultsBrowserWindow）。"""
        self._detail_panel.show()
        self._stack.setCurrentIndex(0)
        self.setFocus()

    @Slot(int)
    def _on_size_changed(self, value: int):
        self._thumb_grid.set_thumb_size(value)

    # ------------------------------------------------------------------
    #  键盘快捷键
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        in_fullscreen = (self._stack.currentIndex() == 1)

        if key in (Qt.Key_Left, Qt.Key_Up):
            if in_fullscreen:
                self._fullscreen_prev()
            else:
                self._prev_photo()
        elif key in (Qt.Key_Right, Qt.Key_Down):
            if in_fullscreen:
                self._fullscreen_next()
            else:
                self._next_photo()
        elif key == Qt.Key_Tab:
            # Tab: 开关右侧详情面板
            self._detail_panel.setVisible(not self._detail_panel.isVisible())
        elif key == Qt.Key_Plus or key == Qt.Key_Equal:
            self._size_slider.setValue(min(300, self._size_slider.value() + 20))
        elif key == Qt.Key_Minus:
            self._size_slider.setValue(max(80, self._size_slider.value() - 20))
        elif key == Qt.Key_Escape:
            current_page = self._stack.currentIndex()
            if current_page == 1:
                self._exit_fullscreen()
            elif current_page == 2:
                self._exit_comparison()
            else:
                # grid 模式：有多选时先清选，否则关闭窗口
                if self._thumb_grid.get_multi_selected_photos():
                    self._thumb_grid.clear_multi_select()
                else:
                    self.close()
        elif key == Qt.Key_C:
            if not in_fullscreen and self._stack.currentIndex() == 0:
                photos = self._thumb_grid.get_multi_selected_photos()
                if len(photos) >= 2:
                    self._enter_comparison()
        elif key == Qt.Key_F:
            if in_fullscreen:
                self._fullscreen.toggle_focus()
            else:
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


# ============================================================
#  ResultsBrowserWidget — 嵌入式浏览器（供主窗口 QStackedWidget 使用）
# ============================================================

class ResultsBrowserWidget(QWidget):
    """
    与 ResultsBrowserWindow 相同的三栏布局，但以 QWidget 形式嵌入主窗口 QStackedWidget。
    信号 back_requested 在用户点击「返回」时发出。
    """
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.i18n = get_i18n()
        self._db: Optional[ReportDB] = None
        self._directory: str = ""
        self._all_photos: list = []
        self._filtered_photos: list = []

        self.setStyleSheet(GLOBAL_STYLE)
        self.setFocusPolicy(Qt.StrongFocus)
        self._setup_ui()

    # ------------------------------------------------------------------
    #  UI 构建
    # ------------------------------------------------------------------

    def _setup_ui(self):
        main_v = QVBoxLayout(self)
        main_v.setContentsMargins(0, 0, 0, 0)
        main_v.setSpacing(0)

        self._toolbar = self._build_toolbar()
        main_v.addWidget(self._toolbar)

        outer_h = QHBoxLayout()
        outer_h.setContentsMargins(0, 0, 0, 0)
        outer_h.setSpacing(0)
        main_v.addLayout(outer_h, 1)

        self._stack = QStackedWidget()
        outer_h.addWidget(self._stack, 1)

        # Page 0: 过滤面板 + 缩略图网格
        two_col = QWidget()
        main_h = QHBoxLayout(two_col)
        main_h.setContentsMargins(0, 0, 0, 0)
        main_h.setSpacing(0)

        self._filter_panel = FilterPanel(self.i18n, self)
        self._filter_panel.filters_changed.connect(self._apply_filters)
        main_h.addWidget(self._filter_panel)

        center_widget = QWidget()
        center_widget.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        self._thumb_grid = ThumbnailGrid(self.i18n, self)
        self._thumb_grid.photo_selected.connect(self._on_photo_selected)
        self._thumb_grid.photo_double_clicked.connect(self._enter_fullscreen)
        self._thumb_grid.multi_selection_changed.connect(self._on_multi_selection_changed)
        center_layout.addWidget(self._thumb_grid, 1)

        main_h.addWidget(center_widget, 1)
        self._stack.addWidget(two_col)

        # Page 1: 全屏查看器
        self._fullscreen = FullscreenViewer(self.i18n, self)
        self._fullscreen.close_requested.connect(self._exit_fullscreen)
        self._fullscreen.prev_requested.connect(self._fullscreen_prev)
        self._fullscreen.next_requested.connect(self._fullscreen_next)
        self._stack.addWidget(self._fullscreen)

        # Page 2: 对比查看器（C5）
        self._comparison = ComparisonViewer(self.i18n, self)
        self._comparison.close_requested.connect(self._exit_comparison)
        self._comparison.rating_changed.connect(self._on_rating_changed)
        self._stack.addWidget(self._comparison)

        # 右侧详情面板
        self._detail_panel = DetailPanel(self.i18n, self)
        self._detail_panel.prev_requested.connect(self._prev_photo)
        self._detail_panel.next_requested.connect(self._next_photo)
        self._detail_panel.rating_change_requested.connect(self._on_rating_changed)
        outer_h.addWidget(self._detail_panel, 0)

        # 底部状态栏（简单 label）
        self._status_label = QLabel("—")
        self._status_label.setFixedHeight(24)
        self._status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['bg_elevated']};
                color: {COLORS['text_secondary']};
                font-size: 11px;
                border-top: 1px solid {COLORS['border_subtle']};
                padding: 4px 16px;
            }}
        """)
        main_v.addWidget(self._status_label)

    def _build_toolbar(self) -> QWidget:
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

        back_btn = QPushButton(self.i18n.t("browser.back"))
        back_btn.setObjectName("tertiary")
        back_btn.setFixedHeight(32)
        back_btn.setToolTip(self.i18n.t("browser.back_tooltip"))
        back_btn.clicked.connect(self.back_requested)
        layout.addWidget(back_btn)

        layout.addSpacing(8)

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

        layout.addSpacing(16)

        # 多选计数标签（C3，默认隐藏）
        self._select_count_label = QLabel("")
        self._select_count_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['accent']};
                font-size: 12px;
                background: transparent;
            }}
        """)
        self._select_count_label.hide()
        layout.addWidget(self._select_count_label)

        # 对比按钮（C5，默认隐藏，多选2张时显示）
        self._compare_btn = QPushButton("🔀 对比")
        self._compare_btn.setObjectName("secondary")
        self._compare_btn.setFixedHeight(32)
        self._compare_btn.hide()
        self._compare_btn.clicked.connect(self._enter_comparison)
        layout.addWidget(self._compare_btn)

        size_label = QLabel(self.i18n.t("browser.size_label"))
        size_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; background: transparent;")
        layout.addWidget(size_label)

        self._size_slider = QSlider(Qt.Horizontal)
        self._size_slider.setRange(80, 300)
        self._size_slider.setValue(160)
        self._size_slider.setFixedWidth(100)
        self._size_slider.valueChanged.connect(self._on_size_changed)
        layout.addWidget(self._size_slider)

        return bar

    # ------------------------------------------------------------------
    #  公共接口
    # ------------------------------------------------------------------

    def open_directory(self, directory: str):
        """加载指定目录的 report.db 并刷新界面。"""
        if not directory:
            return

        db_path = os.path.join(directory, ".superpicky", "report.db")
        if not os.path.exists(db_path):
            QMessageBox.information(
                self,
                self.i18n.t("browser.no_db"),
                f"{directory}\n\n{self.i18n.t('browser.no_db_hint')}"
            )
            return

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

        self._all_photos = self._db.get_all_photos()
        self._compute_burst_ids()
        self._filter_panel.reset_all()
        counts = self._db.get_statistics().get("by_rating", {})
        self._filter_panel.update_rating_counts(counts)
        species = self._db.get_distinct_species()
        self._filter_panel.update_species_list(species)

    def _compute_burst_ids(self):
        """基于 date_time_original 做秒级 burst 分组，写回 DB。"""
        if not self._db:
            return

        photos = self._db.get_all_photos()
        # 只处理有时间戳且尚未分配 burst_id 的照片
        untagged = [p for p in photos if p.get("burst_id") is None and p.get("date_time_original")]
        if not untagged:
            return

        # 按时间戳排序
        def _ts(p):
            return p.get("date_time_original", "") or ""

        untagged.sort(key=_ts)

        # 秒级分组（≤1 秒时间差视为同一 burst）
        burst_map = {}   # {filename: (burst_id, burst_position)}
        burst_id = 0
        group: list = []

        def _flush_group(grp, bid):
            if len(grp) > 1:
                for pos, photo in enumerate(grp, 1):
                    burst_map[photo["filename"]] = (bid, pos)

        prev_ts = None
        for photo in untagged:
            ts = photo.get("date_time_original", "")
            if prev_ts is None or ts != prev_ts:
                if group:
                    _flush_group(group, burst_id)
                    burst_id += 1
                group = [photo]
            else:
                group.append(photo)
            prev_ts = ts

        if group:
            _flush_group(group, burst_id)

        if burst_map:
            self._db.update_burst_ids(burst_map)
            # 重新加载（含 burst 字段）
            self._all_photos = self._db.get_all_photos()

        # 构建 {burst_id: total_count} 供角标显示用
        from collections import Counter
        self._burst_totals: dict = Counter(
            p["burst_id"] for p in self._all_photos if p.get("burst_id") is not None
        )

    def cleanup(self):
        """释放 DB 连接（切换回处理页前调用）。"""
        if self._db:
            try:
                self._db.close()
            except Exception:
                pass
            self._db = None

    # ------------------------------------------------------------------
    #  私有槽
    # ------------------------------------------------------------------

    def _resolve_photo_paths(self, photo: dict) -> dict:
        _PATH_KEYS = ('original_path', 'current_path', 'temp_jpeg_path',
                      'debug_crop_path', 'yolo_debug_path')
        resolved = dict(photo)
        for key in _PATH_KEYS:
            val = photo.get(key)
            if val and not os.path.isabs(val):
                resolved[key] = os.path.join(self._directory, val)
        # 注入 burst_total 供缩略图角标显示
        bid = resolved.get("burst_id")
        if bid is not None and hasattr(self, '_burst_totals'):
            resolved["burst_total"] = self._burst_totals.get(bid, 1)
        return resolved

    @Slot(dict)
    def _apply_filters(self, filters: dict):
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
        if self._filtered_photos:
            first = self._filtered_photos[0]
            self._thumb_grid.select_photo(first.get("filename", ""))
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
        self._fullscreen.show_photo(photo)
        self._detail_panel.show_photo(photo)
        self._detail_panel._switch_view(True)
        self._toolbar.hide()
        self._stack.setCurrentIndex(1)
        self._fullscreen.setFocus()

    @Slot()
    def _exit_fullscreen(self):
        self._toolbar.show()
        self._stack.setCurrentIndex(0)
        self._detail_panel._switch_view(False)
        self.setFocus()

    @Slot()
    def _fullscreen_prev(self):
        photo = self._thumb_grid.select_prev()
        if photo:
            self._fullscreen.show_photo(photo)
            self._detail_panel.show_photo(photo)

    @Slot()
    def _fullscreen_next(self):
        photo = self._thumb_grid.select_next()
        if photo:
            self._fullscreen.show_photo(photo)
            self._detail_panel.show_photo(photo)

    @Slot(str, int)
    def _on_rating_changed(self, filename: str, new_rating: int):
        """详情面板评分修改：写入 DB + 刷新缩略图角标。"""
        if self._db:
            self._db.update_photo(filename, {"rating": new_rating})
        for p in self._filtered_photos:
            if p.get("filename") == filename:
                p["rating"] = new_rating
                break
        self._thumb_grid.refresh_photo(filename, new_rating)

    @Slot(list)
    def _on_multi_selection_changed(self, photos: list):
        """C3：多选状态变化，更新工具栏显示。"""
        n = len(photos)
        if n > 1:
            self._select_count_label.setText(f"已选 {n} 张")
            self._select_count_label.show()
        else:
            self._select_count_label.hide()
        # C5：仅当选中 2 张时显示对比按钮
        self._compare_btn.setVisible(n == 2)

    def _show_context_menu(self, photo: dict, pos):
        """C4：右键菜单（由 ThumbnailGrid 通过 parent chain 调用）。"""
        _show_context_menu_impl(self, photo, pos, self._directory)

    def _enter_comparison(self):
        """C5：进入 2-up 对比视图。"""
        photos = self._thumb_grid.get_multi_selected_photos()
        if len(photos) >= 2:
            self._comparison.show_pair(photos[0], photos[1])
            self._toolbar.hide()
            self._detail_panel.hide()   # 对比模式不显示详情面板
            self._stack.setCurrentIndex(2)
            self._comparison.setFocus()

    def _exit_comparison(self):
        """C5：退出对比视图，回到 grid。"""
        self._toolbar.show()
        self._detail_panel.show()
        self._stack.setCurrentIndex(0)
        self.setFocus()

    @Slot(int)
    def _on_size_changed(self, value: int):
        self._thumb_grid.set_thumb_size(value)

    def _update_status(self, total: int, filtered: int):
        t = self.i18n.t("browser.total_photos").format(total=total)
        f = self.i18n.t("browser.filtered_photos").format(count=filtered)
        self._status_label.setText(f"{t}  |  {f}")

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        in_fullscreen = (self._stack.currentIndex() == 1)

        if key in (Qt.Key_Left, Qt.Key_Up):
            if in_fullscreen:
                self._fullscreen_prev()
            else:
                self._prev_photo()
        elif key in (Qt.Key_Right, Qt.Key_Down):
            if in_fullscreen:
                self._fullscreen_next()
            else:
                self._next_photo()
        elif key == Qt.Key_Tab:
            self._detail_panel.setVisible(not self._detail_panel.isVisible())
        elif key == Qt.Key_Plus or key == Qt.Key_Equal:
            self._size_slider.setValue(min(300, self._size_slider.value() + 20))
        elif key == Qt.Key_Minus:
            self._size_slider.setValue(max(80, self._size_slider.value() - 20))
        elif key == Qt.Key_Escape:
            current_page = self._stack.currentIndex()
            if current_page == 1:
                self._exit_fullscreen()
            elif current_page == 2:
                self._exit_comparison()
            else:
                # grid 模式：有多选时先清选，否则返回主界面
                if self._thumb_grid.get_multi_selected_photos():
                    self._thumb_grid.clear_multi_select()
                else:
                    self.back_requested.emit()
        elif key == Qt.Key_C:
            if not in_fullscreen and self._stack.currentIndex() == 0:
                photos = self._thumb_grid.get_multi_selected_photos()
                if len(photos) >= 2:
                    self._enter_comparison()
        elif key == Qt.Key_F:
            if in_fullscreen:
                self._fullscreen.toggle_focus()
            else:
                self._detail_panel._switch_view(not self._detail_panel._use_crop_view)
        else:
            super().keyPressEvent(event)
