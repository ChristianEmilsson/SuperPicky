# -*- coding: utf-8 -*-
"""
SuperPicky - 关于对话框
PySide6 版本
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QPushButton, QScrollArea, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class AboutDialog(QDialog):
    """关于对话框"""
    
    def __init__(self, parent=None, i18n=None):
        super().__init__(parent)
        self.i18n = i18n
        self._setup_ui()
    
    def _setup_ui(self):
        """设置 UI"""
        self.setWindowTitle(self.i18n.t("menu.about") if self.i18n else "关于")
        self.setFixedSize(700, 600)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 内容文本
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont("Arial", 13))
        self.text_edit.setPlainText(self._get_content())
        layout.addWidget(self.text_edit)
        
        # 关闭按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _get_content(self) -> str:
        """获取关于内容"""
        return """慧眼选鸟 (SuperPicky)

版本: V3.6.0 (PySide6)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

开发者: 詹姆斯·于震 (James Yu)
   澳籍华裔职业摄影师
   《詹姆斯的风景摄影笔记》三部曲作者

联系: james@jamesphotography.com.au
网站: jamesphotography.com.au
YouTube: @JamesZhenYu

鸟眼识别模型训练：Jordan Yu 
鸟类飞行姿态模型训练：Jordan Yu

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

詹姆斯的免费工具:

• 慧眼选鸟 - AI 鸟类摄影选片
• 慧眼识鸟 - AI 鸟种识别 (Lightroom插件)
• 慧眼找鸟 - eBird信息检索 (Web)
• 慧眼去星 - AI 银河去星 (Photoshop插件)
• 图忆作品集 - 鸟种统计 (iOS)
• 镜书 - AI 旅游日记 (iOS)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

使用的开源模型:
• YOLO11 - 鸟类检测
• PyIQA-NIMA - 美学评分

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

© 2024-2025 詹姆斯·于震
"""
