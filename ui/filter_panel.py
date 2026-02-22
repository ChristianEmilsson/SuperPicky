# -*- coding: utf-8 -*-
"""
SuperPicky - 结果浏览器左侧过滤面板
FilterPanel: 评分 / 对焦状态 / 曝光状态 / 飞行状态 / 鸟种 筛选
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QButtonGroup, QAbstractButton,
    QComboBox, QScrollArea, QFrame, QSizePolicy, QRadioButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ui.styles import COLORS, FONTS


# 评分按钮的配置 (rating_value, 显示文字, 颜色)
_RATING_CONFIGS = [
    (3,  "★★★",  COLORS['star_gold']),
    (2,  "★★",   COLORS['star_gold']),
    (1,  "★",    COLORS['star_gold']),
    (0,  "0",    COLORS['text_tertiary']),
    (-1, "—",    COLORS['text_muted']),
]

# 对焦状态颜色
_FOCUS_COLORS = {
    "BEST":  COLORS['accent'],
    "GOOD":  COLORS['success'],
    "BAD":   COLORS['warning'],
    "WORST": COLORS['error'],
}

_EXPOSURE_LABELS_ZH = {
    "GOOD":        "正常",
    "OVEREXPOSED": "过曝",
    "UNDEREXPOSED": "欠曝",
}
_EXPOSURE_LABELS_EN = {
    "GOOD":        "Normal",
    "OVEREXPOSED": "Overexposed",
    "UNDEREXPOSED": "Underexposed",
}


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"""
        QLabel {{
            color: {COLORS['text_tertiary']};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 1px;
            background: transparent;
        }}
    """)
    return lbl


class FilterPanel(QWidget):
    """
    左侧筛选面板。

    发出信号 filters_changed(dict) 通知外部刷新图片网格。
    """
    filters_changed = Signal(dict)

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self._rating_counts: dict = {}      # {rating: count}
        self._species_list: list = []        # 鸟种列表

        self.setFixedWidth(220)
        self.setStyleSheet(f"background-color: {COLORS['bg_elevated']}; border-right: 1px solid {COLORS['border_subtle']};")

        self._build_ui()

    # ------------------------------------------------------------------
    #  UI 构建
    # ------------------------------------------------------------------

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # 内部可滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet(f"background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(20)

        # --- 评分筛选 ---
        layout.addWidget(_section_label(self.i18n.t("browser.filter_rating")))
        rating_widget = self._build_rating_buttons()
        layout.addWidget(rating_widget)

        # --- 分隔线 ---
        layout.addWidget(self._divider())

        # --- 对焦状态 ---
        layout.addWidget(_section_label("FOCUS"))
        focus_widget = self._build_focus_checkboxes()
        layout.addWidget(focus_widget)

        layout.addWidget(self._divider())

        # --- 曝光状态 ---
        layout.addWidget(_section_label("EXPOSURE"))
        exposure_widget = self._build_exposure_checkboxes()
        layout.addWidget(exposure_widget)

        layout.addWidget(self._divider())

        # --- 飞行状态 ---
        layout.addWidget(_section_label("FLIGHT"))
        flight_widget = self._build_flight_radios()
        layout.addWidget(flight_widget)

        layout.addWidget(self._divider())

        # --- 鸟种 ---
        layout.addWidget(_section_label("SPECIES"))
        self.species_combo = QComboBox()
        self.species_combo.addItem("— All —", "")
        self.species_combo.currentIndexChanged.connect(self._emit_filters)
        layout.addWidget(self.species_combo)

        layout.addStretch()

        # --- 重置按钮 ---
        reset_btn = QPushButton(self.i18n.t("browser.reset_filter"))
        reset_btn.setObjectName("secondary")
        reset_btn.clicked.connect(self.reset_all)
        layout.addWidget(reset_btn)

        scroll.setWidget(container)
        outer.addWidget(scroll)

    def _build_rating_buttons(self) -> QWidget:
        """构建评分多选按钮组"""
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._rating_btns: dict = {}  # rating -> QPushButton

        for rating, label_text, color in _RATING_CONFIGS:
            btn = QPushButton(label_text)
            btn.setCheckable(True)
            btn.setChecked(True)
            btn.setProperty("rating", rating)
            btn.setStyleSheet(self._rating_btn_style(color, checked=True))
            btn.toggled.connect(lambda checked, r=rating, c=color, b=btn:
                                self._on_rating_toggled(r, c, b, checked))
            self._rating_btns[rating] = btn
            layout.addWidget(btn)

        return w

    def _rating_btn_style(self, color: str, checked: bool) -> str:
        if checked:
            return f"""
                QPushButton {{
                    background-color: {COLORS['bg_card']};
                    border: 1px solid {color};
                    border-radius: 6px;
                    padding: 6px 12px;
                    color: {color};
                    font-size: 13px;
                    text-align: left;
                }}
                QPushButton:hover {{ background-color: {COLORS['bg_input']}; }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: transparent;
                    border: 1px solid {COLORS['border']};
                    border-radius: 6px;
                    padding: 6px 12px;
                    color: {COLORS['text_muted']};
                    font-size: 13px;
                    text-align: left;
                }}
                QPushButton:hover {{ background-color: {COLORS['bg_card']}; }}
            """

    def _build_focus_checkboxes(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._focus_cbs: dict = {}  # status -> QCheckBox
        labels = {"BEST": "BEST", "GOOD": "GOOD", "BAD": "BAD", "WORST": "WORST"}

        for status, label_text in labels.items():
            cb = QCheckBox(label_text)
            cb.setChecked(True)
            color = _FOCUS_COLORS.get(status, COLORS['text_secondary'])
            cb.setStyleSheet(f"""
                QCheckBox {{ color: {color}; font-size: 12px; }}
                QCheckBox::indicator:checked {{ background-color: {color}; border-color: {color}; }}
            """)
            cb.stateChanged.connect(self._emit_filters)
            self._focus_cbs[status] = cb
            layout.addWidget(cb)

        return w

    def _build_exposure_checkboxes(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._exposure_cbs: dict = {}
        lang = getattr(self.i18n, 'current_lang', 'zh_CN')
        labels = _EXPOSURE_LABELS_EN if lang.startswith('en') else _EXPOSURE_LABELS_ZH

        for status, label_text in labels.items():
            cb = QCheckBox(label_text)
            cb.setChecked(True)
            cb.stateChanged.connect(self._emit_filters)
            self._exposure_cbs[status] = cb
            layout.addWidget(cb)

        return w

    def _build_flight_radios(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._flight_group = QButtonGroup(self)
        lang = getattr(self.i18n, 'current_lang', 'zh_CN')
        is_zh = not lang.startswith('en')

        options = [
            (None, "全部" if is_zh else "All"),
            (1,    "飞行中" if is_zh else "Flying"),
            (0,    "非飞行" if is_zh else "Non-flying"),
        ]
        for value, label_text in options:
            rb = QRadioButton(label_text)
            rb.setProperty("flight_value", value)
            rb.toggled.connect(self._emit_filters)
            self._flight_group.addButton(rb)
            layout.addWidget(rb)
            if value is None:
                rb.setChecked(True)

        return w

    def _divider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"background-color: {COLORS['border_subtle']}; max-height: 1px; border: none;")
        return line

    # ------------------------------------------------------------------
    #  数据更新
    # ------------------------------------------------------------------

    def update_rating_counts(self, counts: dict):
        """更新各评分数量徽章。counts: {rating: count}"""
        self._rating_counts = counts
        lang = getattr(self.i18n, 'current_lang', 'zh_CN')
        is_zh = not lang.startswith('en')

        label_map = {
            3: "★★★",
            2: "★★",
            1: "★",
            0: "0",
            -1: ("无鸟" if is_zh else "No Bird"),
        }
        for rating, btn in self._rating_btns.items():
            base = label_map.get(rating, str(rating))
            cnt = counts.get(rating, 0)
            btn.setText(f"{base}  {cnt}")

    def update_species_list(self, species: list):
        """更新鸟种下拉列表。"""
        self._species_list = species
        self.species_combo.blockSignals(True)
        current = self.species_combo.currentData()
        self.species_combo.clear()
        lang = getattr(self.i18n, 'current_lang', 'zh_CN')
        self.species_combo.addItem("— All —" if lang.startswith('en') else "— 全部 —", "")
        for sp in species:
            self.species_combo.addItem(sp, sp)
        # 恢复之前的选择
        idx = self.species_combo.findData(current)
        if idx >= 0:
            self.species_combo.setCurrentIndex(idx)
        self.species_combo.blockSignals(False)

    # ------------------------------------------------------------------
    #  筛选状态读取
    # ------------------------------------------------------------------

    def get_filters(self) -> dict:
        """返回当前筛选条件字典。"""
        # 评分
        selected_ratings = [
            r for r, btn in self._rating_btns.items() if btn.isChecked()
        ]

        # 对焦
        selected_focus = [
            s for s, cb in self._focus_cbs.items() if cb.isChecked()
        ]

        # 曝光
        selected_exposure = [
            s for s, cb in self._exposure_cbs.items() if cb.isChecked()
        ]

        # 飞行
        is_flying = None
        for btn in self._flight_group.buttons():
            if btn.isChecked():
                is_flying = btn.property("flight_value")
                break

        # 鸟种
        bird_species = self.species_combo.currentData() or ""

        return {
            "ratings":          selected_ratings,
            "focus_statuses":   selected_focus,
            "exposure_statuses": selected_exposure,
            "is_flying":        is_flying,
            "bird_species_cn":  bird_species,
        }

    # ------------------------------------------------------------------
    #  重置
    # ------------------------------------------------------------------

    def reset_all(self):
        """重置所有筛选条件。"""
        # 评分全选
        for btn in self._rating_btns.values():
            btn.blockSignals(True)
            btn.setChecked(True)
            btn.blockSignals(False)

        # 对焦全选
        for cb in self._focus_cbs.values():
            cb.blockSignals(True)
            cb.setChecked(True)
            cb.blockSignals(False)

        # 曝光全选
        for cb in self._exposure_cbs.values():
            cb.blockSignals(True)
            cb.setChecked(True)
            cb.blockSignals(False)

        # 飞行 -> 全部
        for btn in self._flight_group.buttons():
            if btn.property("flight_value") is None:
                btn.blockSignals(True)
                btn.setChecked(True)
                btn.blockSignals(False)

        # 鸟种 -> 全部
        self.species_combo.blockSignals(True)
        self.species_combo.setCurrentIndex(0)
        self.species_combo.blockSignals(False)

        self._emit_filters()

    # ------------------------------------------------------------------
    #  信号
    # ------------------------------------------------------------------

    def _on_rating_toggled(self, rating, color, btn, checked):
        btn.setStyleSheet(self._rating_btn_style(color, checked))
        self._emit_filters()

    def _emit_filters(self, *_):
        self.filters_changed.emit(self.get_filters())
