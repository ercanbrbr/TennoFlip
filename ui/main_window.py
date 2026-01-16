from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QStackedWidget, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from ui.item_table import ItemTableWidget
from ui.arcane_packs import ArcanePacksWidget
from ui.styles import get_styles
from data.database import Database
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tenno Flip")
        self.resize(700, 700)
        
        # Set Window Icon
        base_dir = os.path.dirname(os.path.dirname(__file__))
        logo_path = os.path.join(base_dir, "assets", "logo", "logo.png")
        self.setWindowIcon(QIcon(logo_path))
        
        self.db = Database()
        self.current_theme = self.db.get_setting("theme", "dark")
        self.setStyleSheet(get_styles(self.current_theme))
        
        main_widget = QWidget()
        main_widget.setObjectName("main_container")
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        top_bar_widget = QWidget()
        top_bar_widget.setObjectName("topbar_container")
        top_bar_widget.setFixedHeight(41)
        top_bar_layout = QHBoxLayout(top_bar_widget)
        top_bar_layout.setContentsMargins(0, 0, 10, 0)
        top_bar_layout.setSpacing(0)
        
        self.sidebar = QListWidget()
        self.sidebar.setObjectName("topbar")
        self.sidebar.setFlow(QListWidget.LeftToRight)
        self.sidebar.setFixedHeight(41)
        self.sidebar.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sidebar.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sidebar.addItems(["Warframes", "Primary", "Secondary", "Melee", "Arcanes", "Arcane Packs"])
        self.sidebar.currentRowChanged.connect(self.display_section)
        top_bar_layout.addWidget(self.sidebar, 1)
        
        theme_icon = "☀️" if self.current_theme == "light" else "🌙"
        self.theme_btn = QPushButton(theme_icon)
        self.theme_btn.setObjectName("theme_toggle")
        self.theme_btn.setFixedSize(32, 32)
        self.theme_btn.clicked.connect(self.toggle_theme)
        top_bar_layout.addWidget(self.theme_btn)
        
        main_layout.addWidget(top_bar_widget)
        
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)
        
        self.warframe_page = ItemTableWidget("warframe")
        self.primary_page = ItemTableWidget("primary")
        self.secondary_page = ItemTableWidget("secondary")
        self.melee_page = ItemTableWidget("melee")
        self.arcanes_page = ItemTableWidget("arcane")
        self.packs_page = ArcanePacksWidget()
        
        self.content_stack.addWidget(self.warframe_page)
        self.content_stack.addWidget(self.primary_page)
        self.content_stack.addWidget(self.secondary_page)
        self.content_stack.addWidget(self.melee_page)
        self.content_stack.addWidget(self.arcanes_page)
        self.content_stack.addWidget(self.packs_page) 
        
        self.sidebar.setCurrentRow(0)

    def display_section(self, index):
        self.content_stack.setCurrentIndex(index)

    def toggle_theme(self):
        if self.current_theme == "dark":
            self.current_theme = "light"
            self.theme_btn.setText("☀️")
        else:
            self.current_theme = "dark"
            self.theme_btn.setText("🌙")
        
        self.db.set_setting("theme", self.current_theme)
        self.setStyleSheet(get_styles(self.current_theme))
