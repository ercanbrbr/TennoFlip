from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QLineEdit, QPushButton, QDialog)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from ui.common import PriceToggle

class NumericTableWidgetItem(QTableWidgetItem):
    def __lt__(self, other):
        try:
            t1 = self.text().replace('p', '').replace(',', '').strip()
            t2 = other.text().replace('p', '').replace(',', '').strip()
            f1 = float(t1) if t1 and t1 != 'N/A' else -1.0
            f2 = float(t2) if t2 and t2 != 'N/A' else -1.0
            return f1 < f2
        except ValueError:
            return super().__lt__(other)

class RarityTableWidgetItem(QTableWidgetItem):
    RARITY_ORDER = {"Common": 0, "Uncommon": 1, "Rare": 2, "Legendary": 3}
    def __lt__(self, other):
        v1 = self.RARITY_ORDER.get(self.text(), 99)
        v2 = self.RARITY_ORDER.get(other.text(), 99)
        return v1 < v2

class CollectionDetailsPopup(QDialog):
    def __init__(self, pack_name, parent=None, mode="avg"):
        super().__init__(parent)
        self.setWindowTitle(f"Collection: {pack_name}")
        self.resize(500, 600)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)
        
        from services.vosfor_calculator import VosforCalculator
        from data.database import Database
        
        calc = VosforCalculator()
        db = Database()
        pack = calc.PACKS.get(pack_name)
        
        if not pack:
            self.layout.addWidget(QLabel("Pack info not found."))
            return

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Arcane", "Rarity", "Price (R0)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.setShowGrid(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.layout.addWidget(self.table)
        
        self.header = QLabel(f"Collection: {pack_name} ({mode.title()})")
        self.header.setObjectName("header")
        self.layout.insertWidget(0, self.header)
        
        rows = []
        for tier_name, slugs in pack['tiers'].items():
            for slug in slugs:
                item = db.get_item_by_slug(slug)
                price_val = 0
                if item:
                    item_id = item['id']
                    p = db.get_arcane_price(item_id)
                    if p:
                        if mode == "cheapest":
                             price_val = p.get('low_r0', 0)
                        else:
                             price_val = p.get('avg_r0', 0)
                
                price_str = f"{price_val:.1f}p" if price_val > 0 else "N/A"
                rows.append((slug.replace("_", " ").title(), tier_name.capitalize(), price_str))
        
        self.table.setRowCount(len(rows))
        for i, (name, tier, price) in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(name))
            self.table.setItem(i, 1, RarityTableWidgetItem(tier))
            self.table.setItem(i, 2, NumericTableWidgetItem(price))
        
        self.table.setSortingEnabled(True)

class ArcanePacksWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.show_cheapest = False
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(10)
        
        self.header = QLabel("Arcane Packs Expected Value (Vosfor)")
        self.header.setObjectName("header")
        self.layout.addWidget(self.header)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search packs/values...")
        self.search_bar.textChanged.connect(self.filter_packs)
        controls.addWidget(self.search_bar)

        self.toggle_widget = PriceToggle()
        self.toggle_widget.toggled.connect(self.toggle_price_mode)
        controls.addWidget(self.toggle_widget)

        self.btn = QPushButton("Calculate EVs")
        self.btn.setObjectName("primary_action")
        self.btn.clicked.connect(self.calculate)
        controls.addWidget(self.btn)
        self.layout.addLayout(controls)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Pack Name", "Cost", "Expected Value (p)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSortingEnabled(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.setShowGrid(True)
        self.table.doubleClicked.connect(self.show_collection)
        self.layout.addWidget(self.table)
        
        self.calc_thread = None
        self.results = []
        
        QTimer.singleShot(500, self.calculate)

    def toggle_price_mode(self, show_cheapest):
        self.show_cheapest = show_cheapest
        self.calculate()

    def calculate(self):
        if self.calc_thread and self.calc_thread.isRunning():
            return
        
        mode = "cheapest" if self.show_cheapest else "avg"
        self.calc_thread = EVThread(mode)
        self.calc_thread.result_ready.connect(self.on_results_ready)
        self.calc_thread.start()
        
    def on_results_ready(self, results):
        self.results = results
        self.populate_table()

    def populate_table(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self.results))
        for row, r in enumerate(self.results):
            self.table.setItem(row, 0, QTableWidgetItem(r['name']))
            self.table.setItem(row, 1, NumericTableWidgetItem(str(r['cost'])))
            self.table.setItem(row, 2, NumericTableWidgetItem(f"{r['ev']:.1f}p"))
        self.table.sortItems(2, Qt.DescendingOrder)
        self.table.setSortingEnabled(True)
        self.filter_packs(self.search_bar.text())

    def filter_packs(self, text):
        text = text.lower()
        for row in range(self.table.rowCount()):
            visible = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    visible = True
                    break
            self.table.setRowHidden(row, not visible)

    def show_collection(self, index):
        pack_name = self.table.item(index.row(), 0).text()
        popup = CollectionDetailsPopup(pack_name, self, mode="cheapest" if self.show_cheapest else "avg")
        popup.exec()

class EVThread(QThread):
    result_ready = Signal(list)

    def __init__(self, mode="avg"):
        super().__init__()
        self.mode = mode

    def run(self):
        from services.vosfor_calculator import VosforCalculator
        calc = VosforCalculator()
        results = calc.calculate_all_packs(mode=self.mode)
        self.result_ready.emit(results)
