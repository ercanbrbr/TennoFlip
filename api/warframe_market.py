import requests
import time
from threading import Lock
from datetime import datetime

class WarframeMarketAPI:
    ITEMS_URL_V2 = "https://api.warframe.market/v2/items"
    ORDERS_URL_V2 = "https://api.warframe.market/v2/orders/item/{url_name}"
    
    HEADERS = {
        "Platform": "pc",
        "Language": "en",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://warframe.market/"
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.last_request_time = 0
        self.rate_limit_delay = 0.34
        self.lock = Lock()

    def _log_call(self, url, status_code=None):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        if status_code:
            print(f"[{timestamp}] API RESPONSE: {status_code} | URL: {url}")
        else:
            print(f"[{timestamp}] API REQUEST: GET | URL: {url}")

    def _wait_for_rate_limit(self):
        with self.lock:
            current_time = time.time()
            elapsed = current_time - self.last_request_time
            if elapsed < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - elapsed)
            self.last_request_time = time.time()

    def get_items(self):
        """Fetches all items from the API."""
        self._wait_for_rate_limit()
        try:
            self._log_call(self.ITEMS_URL_V2)
            response = self.session.get(self.ITEMS_URL_V2)
            self._log_call(self.ITEMS_URL_V2, response.status_code)
            response.raise_for_status()
            data = response.json()
            items = []
            for i in data.get("data", []):
                items.append({
                    "id": i.get("id"),
                    "url_name": i.get("slug"), 
                    "item_name": i.get("en", {}).get("item_name", i.get("slug").replace("_", " ").title()),
                    "thumb": i.get("thumb"),
                    "tags": i.get("tags", []),
                    "max_rank": i.get("max_rank", -1)
                })
            return items
        except requests.RequestException as e:
            print(f"Error fetching items (V2): {e}")
            return []

    def get_orders(self, url_name):
        """Fetches active orders for a specific item."""
        self._wait_for_rate_limit()
        url = self.ORDERS_URL_V2.format(url_name=url_name)
        try:
            self._log_call(url)
            response = self.session.get(url)
            self._log_call(url, response.status_code)
            if response.status_code == 404:
                return []
            response.raise_for_status()
            
            data = response.json()
            orders = data.get("data", [])
            
            normalized_orders = []
            for o in orders:
                normalized = o.copy()
                if "type" in o and "order_type" not in o:
                    normalized["order_type"] = o["type"]
                if "rank" in o and "mod_rank" not in o:
                    normalized["mod_rank"] = o["rank"]
                normalized_orders.append(normalized)
                
            return normalized_orders
            
        except requests.RequestException as e:
            print(f"Error fetching orders for {url_name}: {e}")
            return []

    def get_item_details(self, url_name):
        """Fetches detailed information about a specific item, including set parts if any."""
        self._wait_for_rate_limit()
        url = f"https://api.warframe.market/v2/items/{url_name}" 
        try:
            self._log_call(url)
            response = self.session.get(url)
            self._log_call(url, response.status_code)
            if response.status_code == 404:
                 url_v1 = f"https://api.warframe.market/v1/items/{url_name}"
                 self._log_call(url_v1)
                 response = self.session.get(url_v1)
                 self._log_call(url_v1, response.status_code)
            
            response.raise_for_status()
            data = response.json()
            
            payload = data.get("data", {})
            if not payload:
                 payload = data.get("payload", {}).get("item", {})
            
            items_in_set = payload.get("items_in_set", [])
            if not items_in_set:
                set_parts = payload.get("setParts", [])
                if set_parts and isinstance(set_parts[0], str):
                    items_in_set = [{"url_name": slug, "en": {"item_name": slug.replace("_", " ").title()}} for slug in set_parts]
                elif set_parts:
                    items_in_set = set_parts

            normalized_set = []
            for item in items_in_set:
                slug = item.get("slug") or item.get("url_name")
                if not slug: continue
                
                name = item.get("en", {}).get("item_name")
                if not name and "item_name" in item: name = item["item_name"]
                if not name: name = slug.replace("_", " ").title()
                
                normalized_set.append({
                    "id": item.get("id"),
                    "slug": slug,
                    "url_name": slug,
                    "item_name": name,
                    "en": {"item_name": name}
                })
            return normalized_set
            
        except requests.RequestException as e:
             print(f"Error fetching details for {url_name}: {e}")
             return []
