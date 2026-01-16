from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton)
from PySide6.QtCore import Qt, QThread, Signal
from api.warframe_market import WarframeMarketAPI
from data.database import Database
from services.price_calculator import PriceCalculator
from ui.details_popup import DetailsPopup
from ui.common import PriceToggle
import time

class DataLoader(QThread):
    data_loaded = Signal(list)

    def __init__(self, item_type):
        super().__init__()
        self.item_type = item_type
        self.api = WarframeMarketAPI()
        self.db = Database()

    def run(self):
        items = self.db.get_all_items()
        
        if not items:
            api_items = self.api.get_items()
            self.db.save_items(api_items)
            items = self.db.get_all_items()
        
        filtered = []
        
        for x in items:
            tags = x.get('tags', [])
            
            if self.item_type == 'warframe':
                if 'set' in tags and 'warframe' in tags:
                    filtered.append(x)
            
            elif self.item_type == 'primary':
                if 'set' in tags and 'primary' in tags and 'weapon' in tags:
                     filtered.append(x)
            elif self.item_type == 'secondary':
                if 'set' in tags and 'secondary' in tags and 'weapon' in tags:
                     filtered.append(x)
            elif self.item_type == 'melee':
                if 'set' in tags and 'melee' in tags and 'weapon' in tags:
                     filtered.append(x)
            
            elif self.item_type == 'arcane':
                if 'arcane_enhancement' in tags or 'arcane' in tags:
                    filtered.append(x)

        if not filtered and items and self.item_type == 'unknown':
             filtered = items 
             
        self.data_loaded.emit(filtered)

class PriceFetcherThread(QThread):
    price_updated = Signal(str, dict, dict) 

    def __init__(self):
        super().__init__()
        self.queue = []
        self.running = True
        self.api = WarframeMarketAPI()
        self.db = Database()

    def add_to_queue(self, items, force_refresh=False):
        for item in items:
            entry = item + (force_refresh,)
            if entry not in self.queue:
                self.queue.append(entry)

    def run(self):
        while self.running:
            if not self.queue:
                self.msleep(100)
                continue
            
            item_id, url_name, item_type, max_rank, force_refresh = self.queue.pop(0)
            is_arcane = (item_type == 'arcane')
            target_max_rank = max_rank
            
            db_max_rank = target_max_rank
            if is_arcane and (db_max_rank <= 0 or db_max_rank > 5):
                db_max_rank = 5
                
            cached_arcane = None
            cached_set = None
            
            if is_arcane:
                cached_arcane = self.db.get_arcane_price(item_id)
            else:
                cached_set = self.db.get_set_price(item_id)
            
            hit = False
            if not force_refresh:
                if is_arcane and cached_arcane and (time.time() - cached_arcane['timestamp'] < 3600):
                    hit = True
                elif not is_arcane and cached_set and (time.time() - cached_set['timestamp'] < 3600):
                    hit = True
            
            if hit:
                if is_arcane:
                    data_r0 = {'avg': cached_arcane['avg_r0'], 'cheapest': cached_arcane['low_r0']}
                    data_rmax = {'avg': cached_arcane['avg_max'], 'cheapest': cached_arcane['low_max'], 'flip': cached_arcane['low_flip'], 'flip_avg': cached_arcane['avg_flip']}
                    self.price_updated.emit(url_name, data_r0, data_rmax)
                else:
                    data_price = {'avg': cached_set['avg'], 'cheapest': cached_set['low']}
                    self.price_updated.emit(url_name, data_price, {})
                continue

            orders = self.api.get_orders(url_name)
            
            if is_arcane:
                sell_orders = [o for o in orders if o.get("order_type") == "sell"]
                detected_rank = target_max_rank
                if sell_orders:
                    detected_rank = max(o.get("mod_rank", 0) for o in sell_orders)
                if detected_rank <= 0: detected_rank = 5
                
                target_max_rank = detected_rank

                avg_r0 = PriceCalculator.calculate_price(orders, "arcane", rank=0)
                cheap_r0 = PriceCalculator.calculate_cheapest(orders, rank=0)
                
                avg_rmax = PriceCalculator.calculate_price(orders, "arcane", rank=target_max_rank)
                cheap_rmax = PriceCalculator.calculate_cheapest(orders, rank=target_max_rank)
                
                required_count = (target_max_rank + 1) * (target_max_rank + 2) // 2
                
                flip_cheap = 0
                if cheap_r0 > 0 and cheap_rmax > 0:
                    flip_cheap = (required_count * cheap_r0) - cheap_rmax
                
                flip_avg = 0
                if avg_r0 > 0 and avg_rmax > 0:
                    flip_avg = (required_count * avg_r0) - avg_rmax
                
                self.db.save_arcane_price(item_id, target_max_rank, avg_r0, avg_rmax, flip_avg, cheap_r0, cheap_rmax, flip_cheap)
                
                self.price_updated.emit(url_name, 
                    {'avg': avg_r0, 'cheapest': cheap_r0}, 
                    {'avg': avg_rmax, 'cheapest': cheap_rmax, 'flip': flip_cheap, 'flip_avg': flip_avg}
                )
            else:
                avg = PriceCalculator.calculate_price(orders, "item")
                cheap = PriceCalculator.calculate_cheapest(orders)
                self.db.save_set_price(item_id, avg, cheap)
                self.price_updated.emit(url_name, {'avg': avg, 'cheapest': cheap}, {})

    def stop(self):
        self.running = False


class NumericTableWidgetItem(QTableWidgetItem):
    def __lt__(self, other):
        try:
            t1 = self.text().replace('p', '').strip()
            t2 = other.text().replace('p', '').strip()
            f1 = float(t1) if t1 and t1 != '...' else -1.0
            f2 = float(t2) if t2 and t2 != '...' else -1.0
            return f1 < f2
        except ValueError:
            return super().__lt__(other)



class ItemTableWidget(QWidget):
    def __init__(self, category):
        super().__init__()
        self.category = category
        self.show_cheapest = False
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(10)
        
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(6)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.filter_items)
        controls_layout.addWidget(self.search_bar)
        
        self.toggle_widget = PriceToggle()
        self.toggle_widget.toggled.connect(self.toggle_price_mode)
        controls_layout.addWidget(self.toggle_widget)

        self.refresh_btn = QPushButton("Refresh Data")
        self.refresh_btn.clicked.connect(self.load_data)
        controls_layout.addWidget(self.refresh_btn)

        self.get_filtered_prices_btn = QPushButton("Get Prices (Visible)")
        self.get_filtered_prices_btn.setObjectName("primary_action")
        self.get_filtered_prices_btn.clicked.connect(self.fetch_visible_prices)
        controls_layout.addWidget(self.get_filtered_prices_btn)
        
        self.layout.addLayout(controls_layout)
        
        self.table = QTableWidget()
        self.db = Database()
        
        if self.category == 'arcane':
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels(["Item Name", "Price (R0)", "Price (Max)", "Flip Profit"])
        else:
            self.table.setColumnCount(2)
            self.table.setHorizontalHeaderLabels(["Item Name", "Price"])
            
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.doubleClicked.connect(self.open_details)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.setShowGrid(True)
        self.layout.addWidget(self.table)
        
        self.items = []
        self.full_items = []
        
        self.price_fetcher = PriceFetcherThread()
        self.price_fetcher.price_updated.connect(self.update_price_cell)
        self.price_fetcher.start()

        self.load_data()

    def toggle_price_mode(self, show_cheapest):
        self.show_cheapest = show_cheapest
        self.refresh_table_values()

    def refresh_table_values(self):
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            if not name_item: continue
            
            p1_item = self.table.item(row, 1)
            p1_avg = name_item.data(Qt.UserRole + 2)
            p1_cheap = name_item.data(Qt.UserRole + 3)
            
            val1 = p1_cheap if self.show_cheapest else p1_avg
            if val1 and val1 > 0:
                p1_item.setText(f"{val1:.1f}p")
            
            if self.category == 'arcane':
                p2_item = self.table.item(row, 2)
                p2_avg = name_item.data(Qt.UserRole + 4)
                p2_cheap = name_item.data(Qt.UserRole + 5)
                
                val2 = p2_cheap if self.show_cheapest else p2_avg
                if val2 and val2 > 0:
                    p2_item.setText(f"{val2:.1f}p")
                
                flip_item = self.table.item(row, 3)
                flip_val_cheap = name_item.data(Qt.UserRole + 6)
                flip_val_avg = name_item.data(Qt.UserRole + 7)
                
                flip_val = flip_val_cheap if self.show_cheapest else flip_val_avg
                
                if flip_val is not None:
                    flip_item.setText(f"{flip_val:.1f}p")
                    if flip_val > 0:
                        flip_item.setForeground(Qt.green)
                    elif flip_val < 0:
                        flip_item.setForeground(Qt.red)
                    else:
                         flip_item.setForeground(Qt.gray)

    def load_data(self):
        self.loader = DataLoader(self.category)
        self.loader.data_loaded.connect(self.on_data_loaded)
        self.loader.start()

    def on_data_loaded(self, items):
        self.full_items = items
        self.items = items
        self.populate_table()

    def populate_table(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self.table.setRowCount(len(self.items))
        
        is_arcane = (self.category == 'arcane')
        
        for row, item in enumerate(self.items):
            url_name = item['url_name']
            item_id = item['id']
            name_item = QTableWidgetItem(item['item_name'])
            name_item.setData(Qt.UserRole, url_name) 
            name_item.setData(Qt.UserRole + 10, item_id) # Store internal ID
            
            p1_avg, p1_cheap = -1.0, -1.0
            p2_avg, p2_cheap, f_cheap, f_avg = -1.0, -1.0, 0.0, 0.0
            
            max_rank = 5 # Default
            
            if is_arcane:
                cached_arcane = self.db.get_arcane_price(item_id)
                if cached_arcane:
                    p1_avg = cached_arcane['avg_r0']
                    p1_cheap = cached_arcane['low_r0']
                    p2_avg = cached_arcane['avg_max']
                    p2_cheap = cached_arcane['low_max']
                    f_cheap = cached_arcane['low_flip']
                    f_avg = cached_arcane['avg_flip']
                    if cached_arcane.get('max_rank'):
                        max_rank = cached_arcane['max_rank']
            else:
                cached_set = self.db.get_set_price(item_id)
                if cached_set:
                    p1_avg = cached_set['avg']
                    p1_cheap = cached_set['low']
            
            name_item.setData(Qt.UserRole + 1, max_rank)
            
            name_item.setData(Qt.UserRole + 2, p1_avg)
            name_item.setData(Qt.UserRole + 3, p1_cheap)
            name_item.setData(Qt.UserRole + 4, p2_avg)
            name_item.setData(Qt.UserRole + 5, p2_cheap)
            name_item.setData(Qt.UserRole + 6, f_cheap)
            name_item.setData(Qt.UserRole + 7, f_avg)
            
            price_item = NumericTableWidgetItem("...") 
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, price_item)
            
            if is_arcane:
                self.table.setItem(row, 2, NumericTableWidgetItem("..."))
                self.table.setItem(row, 3, NumericTableWidgetItem("..."))

        self.refresh_table_values()
        self.table.setSortingEnabled(True)
        if self.search_bar.text():
            self.filter_items(self.search_bar.text())

    def filter_items(self, text):
        text = text.lower()
        self.items = [i for i in self.full_items if text in i['item_name'].lower()]
        
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                self.table.setRowHidden(row, text not in item.text().lower())

    def fetch_visible_prices(self):
        requests = []
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                item = self.table.item(row, 0)
                if item:
                    url_name = item.data(Qt.UserRole)
                    item_id = item.data(Qt.UserRole + 10)
                    max_rank = item.data(Qt.UserRole + 1)
                    requests.append((item_id, url_name, self.category, max_rank))
        self.price_fetcher.add_to_queue(requests, force_refresh=True)
        
    def update_price_cell(self, url_name, data_r0, data_max):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.UserRole) == url_name:
                item.setData(Qt.UserRole + 2, data_r0.get('avg', -1.0))
                item.setData(Qt.UserRole + 3, data_r0.get('cheapest', -1.0))
                
                if self.category == 'arcane' and data_max:
                    item.setData(Qt.UserRole + 4, data_max.get('avg', -1.0))
                    item.setData(Qt.UserRole + 5, data_max.get('cheapest', -1.0))
                    item.setData(Qt.UserRole + 6, data_max.get('flip', 0.0))
                    item.setData(Qt.UserRole + 7, data_max.get('flip_avg', 0.0))
                
                self.refresh_table_values()
                break
                
    def open_details(self, index):
        row = index.row()
        item_name = self.table.item(row, 0).text()
        url_name = self.table.item(row, 0).data(Qt.UserRole)
        
        popup = DetailsPopup(item_name, url_name, self.category, self.show_cheapest, self)
        popup.exec()
