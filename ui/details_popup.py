from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox)
from PySide6.QtCore import QThread, Signal
from api.warframe_market import WarframeMarketAPI
from services.price_calculator import PriceCalculator
import time

class DetailsFetcher(QThread):
    data_ready = Signal(dict)

    def __init__(self, url_name, item_type):
        super().__init__()
        self.url_name = url_name
        self.item_type = item_type
        self.api = WarframeMarketAPI()
        from data.database import Database
        self.db = Database()

    def run(self):
        item = self.db.get_item_by_slug(self.url_name)
        if not item:
             self.data_ready.emit({"orders_count": 0, "price": -1, "rank_prices": {}, "components": []})
             return
             
        item_id = item['id']
        is_arcane = self.item_type == "arcane"
        
        max_rank = 5
        if is_arcane:
            cached_chk = self.db.get_arcane_price(item_id)
            if cached_chk and cached_chk.get('max_rank'):
                max_rank = cached_chk['max_rank']
        
        orders = []
        price = -1.0
        price_low = -1.0
        rank_prices = {}
        rank_prices_low = {}
        
        hit = False
        if is_arcane:
            cached = self.db.get_arcane_price(item_id)
            if cached and (time.time() - cached['timestamp'] < 3600):
                price = cached['avg_r0']
                price_low = cached['low_r0']
                rank_prices = {
                    max_rank: cached['avg_max']
                }
                rank_prices_low = {
                    max_rank: cached['low_max']
                }
                hit = True
        else:
            cached = self.db.get_set_price(item_id)
            if cached and (time.time() - cached['timestamp'] < 3600):
                price = cached['avg']
                price_low = cached['low']
                hit = True

        if not hit:
            orders = self.api.get_orders(self.url_name)
            price = PriceCalculator.calculate_price(orders, self.item_type, rank=0 if is_arcane else -1)
            price_low = PriceCalculator.calculate_cheapest(orders, rank=0 if is_arcane else -1)
            
            if is_arcane:
                rank_prices_raw = PriceCalculator.calculate_rank_prices(orders, self.item_type)
                detected_max_rank = 0
                if orders:
                    sell_orders = [o for o in orders if o.get("order_type") == "sell"]
                    if sell_orders:
                        detected_max_rank = max(o.get("mod_rank", 0) for o in sell_orders)
                if detected_max_rank <= 0: detected_max_rank = max_rank
                
                avg_max = rank_prices_raw.get(detected_max_rank, -1)
                low_max = PriceCalculator.calculate_cheapest(orders, rank=detected_max_rank)
                
                required_count = (detected_max_rank + 1) * (detected_max_rank + 2) // 2
                flip_avg = (required_count * price) - avg_max if price > 0 and avg_max > 0 else 0
                flip_low = (required_count * price_low) - low_max if price_low > 0 and low_max > 0 else 0
                
                self.db.save_arcane_price(item_id, detected_max_rank, price, avg_max, flip_avg, price_low, low_max, flip_low)
                rank_prices = {detected_max_rank: avg_max}
                rank_prices_low = {detected_max_rank: low_max}
            else:
                self.db.save_set_price(item_id, price, price_low)

        # Handle components
        component_prices = []
        if not is_arcane:
            set_cached = self.db.get_set_price(item_id)
            if set_cached:
                parts = self.db.get_parts_prices(set_cached['id'])
                if parts:
                    for p in parts:
                        component_prices.append({"name": p['name'], "price": p['avg'], "low": p['low']})
            
            if not component_prices:
                items_in_set = self.api.get_item_details(self.url_name)
                if items_in_set:
                    # Determine set_id again
                    set_cached = self.db.get_set_price(item_id)
                    if not set_cached:
                         orders_set = self.api.get_orders(self.url_name)
                         p_set = PriceCalculator.calculate_price(orders_set, self.item_type)
                         c_set = PriceCalculator.calculate_cheapest(orders_set)
                         set_id = self.db.save_set_price(item_id, p_set, c_set)
                    else:
                         set_id = set_cached['id']
                         
                    for item_part in items_in_set:
                        # Identifier could be a slug or an ID depending on API response format
                        identifier = item_part.get("url_name") or item_part.get("slug")
                        if not identifier: continue
                        
                        resolved = self.db.get_item_by_id(identifier)
                        if not resolved:
                            resolved = self.db.get_item_by_slug(identifier)
                            
                        if resolved:
                            c_id = resolved['id']
                            c_slug = resolved['url_name']
                            c_name = resolved['item_name']
                        else:
                            # If not found in DB, rely on what we have, but it might be an ID
                            c_id = identifier
                            c_slug = identifier
                            c_name = item_part.get("en", {}).get("item_name", identifier)

                        # CRITICAL: Filter out the set itself to avoid duplicate pricing
                        if c_id == item_id or c_slug == self.url_name: 
                            continue

                        c_orders = self.api.get_orders(c_slug)
                        c_price = PriceCalculator.calculate_price(c_orders, "item")
                        c_cheap = PriceCalculator.calculate_cheapest(c_orders)
                        
                        if resolved:
                             self.db.save_part_price(set_id, c_id, c_price, c_cheap)
                        
                        component_prices.append({"name": c_name, "price": c_price, "low": c_cheap})

        self.data_ready.emit({
            "orders_count": len(orders),
            "price": price,
            "price_low": price_low,
            "rank_prices": rank_prices,
            "rank_prices_low": rank_prices_low,
            "components": component_prices
        })

class DetailsPopup(QDialog):
    def __init__(self, item_name, url_name, item_type, show_cheapest=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Details: {item_name}")
        self.resize(500, 600)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)
        
        self.item_type = item_type
        self.show_cheapest = show_cheapest
        self.current_data = None
        
        self.header = QLabel(f"Fetching data for {item_name}...")
        self.header.setObjectName("header")
        self.layout.addWidget(self.header)
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Component / Rank", "Price"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.layout.addWidget(self.table)
        
        self.fetcher = DetailsFetcher(url_name, item_type)
        self.fetcher.data_ready.connect(self.populate)
        self.fetcher.start()
        
    def populate(self, data):
        self.current_data = data
        if data['orders_count'] > 0:
            self.header.setText(f"Market Data (Live - Orders: {data['orders_count']})")
        else:
            self.header.setText("Market Data (Local Cache)")
            
        self.refresh_table()
        
    def refresh_table(self):
        if not self.current_data:
            return
            
        data = self.current_data
        
        self.table.setRowCount(0)
        
        rows = []
        
        main_label = "Rank 0" if self.item_type == "arcane" else "Market Set Price"
        p_val = data.get('price_low', -1) if self.show_cheapest else data['price']
        rows.append((main_label, f"{p_val:.1f}p"))
        
        r_prices = data.get('rank_prices_low', {}) if self.show_cheapest else data.get('rank_prices', {})
        for rank, price in sorted(r_prices.items()):
            rows.append((f"Rank {rank}", f"{price:.1f}p"))
            
        components = data.get("components", [])
        if components:
            rows.append(("--- Components ---", ""))
            total_parts_price = 0
            for c in components:
                price_val = c.get('low', c['price']) if self.show_cheapest else c['price']
                parts_label = c['name']
                if self.show_cheapest:
                    parts_label += " (Low)"
                rows.append((parts_label, f"{price_val:.1f}p"))
                total_parts_price += price_val
            rows.append(("Sum of Components", f"{total_parts_price:.1f}p"))
            
        self.table.setRowCount(len(rows))
        for i, (label, val) in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(label))
            self.table.setItem(i, 1, QTableWidgetItem(val))
