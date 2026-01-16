import sqlite3
import time
import sys
from pathlib import Path
import json

class Database:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent
            
        self.db_file = base_dir / "cache.db"
        self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # We drop the old tables if they exist with old schema to avoid conflicts
        # However, to be safe, we just create the new ones. 
        # If the user wants a migration, it's better to start fresh since they restructured everything.
        
        # Check if old table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='items'")
        if cursor.fetchone():
            # Check if schema matches. If not, we might need a reset.
            # For simplicity and given the user request "I redesign the databases", 
            # we will drop and recreate if the schema is old.
            try:
                cursor.execute("SELECT item_type FROM items LIMIT 1")
            except sqlite3.OperationalError:
                # Old table has item_type but maybe different columns. 
                # Actually, let's just drop if any of the new tables don't exist.
                pass

        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS "items" (
                "id" TEXT NOT NULL,
                "url_name" TEXT NOT NULL,
                "item_name" TEXT NOT NULL,
                "item_type" TEXT NOT NULL,
                "tags" TEXT NOT NULL,
                PRIMARY KEY("id")
            );
            
            CREATE TABLE IF NOT EXISTS "arcanes" (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "item_id" TEXT,
                "max_rank" INTEGER,
                "avg_price_rank0" REAL,
                "avg_price_max_rank" REAL,
                "avg_flip" REAL,
                "low_price_rank0" REAL,
                "low_price_max_rank0" REAL,
                "low_flip" REAL,
                "timestamp" REAL,
                FOREIGN KEY("item_id") REFERENCES "items"("id")
            );
            
            CREATE TABLE IF NOT EXISTS "sets" (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "item_id" TEXT,
                "avg_price" REAL,
                "low_price" REAL,
                "timestamp" REAL,
                FOREIGN KEY("item_id") REFERENCES "items"("id")
            );
            
            CREATE TABLE IF NOT EXISTS "parts" (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "set_id" INTEGER,
                "item_id" TEXT,
                "avg_price" REAL,
                "low_price" REAL,
                "timestamp" REAL,
                FOREIGN KEY("set_id") REFERENCES "sets"("id"),
                FOREIGN KEY("item_id") REFERENCES "items"("id")
            );
            
            CREATE TABLE IF NOT EXISTS "settings" (
                "key" TEXT PRIMARY KEY,
                "value" TEXT
            );
        ''')
        self.conn.commit()

    def save_items(self, items):
        """Bulk saves items to the database after filtering by type."""
        cursor = self.conn.cursor()
        for item in items:
            tags = item.get("tags", [])
            # Classification
            item_type = None
            if 'arcane' in tags or 'arcane_enhancement' in tags:
                item_type = 'arcane'
            elif 'set' in tags:
                item_type = 'set'
            elif 'warframe' in tags or 'component' in tags:
                item_type = 'warframe' if 'warframe' in tags or any(t in tags for t in ['chassis', 'systems', 'neuroptics']) else 'weapon'
            elif 'weapon' in tags or any(t in tags for t in ['primary', 'secondary', 'melee', 'blade', 'barrel', 'receiver', 'stock', 'handle', 'pouch', 'stars', 'link', 'string', 'limbs', 'grip']):
                item_type = 'weapon'
            
            if not item_type:
                continue
                
            cursor.execute('''
                INSERT OR REPLACE INTO items (id, url_name, item_name, item_type, tags)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                item.get("id"),
                item.get("url_name"),
                item.get("item_name"),
                item_type,
                json.dumps(tags)
            ))
        self.conn.commit()

    def get_all_items(self, item_type=None):
        cursor = self.conn.cursor()
        if item_type:
            cursor.execute("SELECT id, url_name, item_name, item_type, tags FROM items WHERE item_type = ?", (item_type,))
        else:
            cursor.execute("SELECT id, url_name, item_name, item_type, tags FROM items")
        
        results = []
        for r in cursor.fetchall():
            results.append({
                "id": r[0],
                "url_name": r[1],
                "item_name": r[2],
                "item_type": r[3],
                "tags": json.loads(r[4])
            })
        return results

    def get_item_by_id(self, item_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, url_name, item_name, item_type, tags FROM items WHERE id = ?", (item_id,))
        r = cursor.fetchone()
        if r:
            return {"id": r[0], "url_name": r[1], "item_name": r[2], "item_type": r[3], "tags": json.loads(r[4])}
        return None

    def get_item_by_slug(self, slug):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, url_name, item_name, item_type, tags FROM items WHERE url_name = ?", (slug,))
        r = cursor.fetchone()
        if r:
            return {"id": r[0], "url_name": r[1], "item_name": r[2], "item_type": r[3], "tags": json.loads(r[4])}
        return None

    def save_arcane_price(self, item_id, max_rank, avg_r0, avg_max, avg_flip, low_r0, low_max, low_flip):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO arcanes (item_id, max_rank, avg_price_rank0, avg_price_max_rank, avg_flip, low_price_rank0, low_price_max_rank0, low_flip, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (item_id, max_rank, avg_r0, avg_max, avg_flip, low_r0, low_max, low_flip, time.time()))
        self.conn.commit()

    def get_arcane_price(self, item_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT max_rank, avg_price_rank0, avg_price_max_rank, avg_flip, low_price_rank0, low_price_max_rank0, low_flip, timestamp FROM arcanes WHERE item_id = ? ORDER BY timestamp DESC LIMIT 1", (item_id,))
        r = cursor.fetchone()
        if r:
            return {
                "max_rank": r[0], "avg_r0": r[1], "avg_max": r[2], "avg_flip": r[3],
                "low_r0": r[4], "low_max": r[5], "low_flip": r[6], "timestamp": r[7]
            }
        return None

    def save_set_price(self, item_id, avg_price, low_price):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO sets (item_id, avg_price, low_price, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (item_id, avg_price, low_price, time.time()))
        set_id = cursor.lastrowid
        self.conn.commit()
        return set_id

    def get_set_price(self, item_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, avg_price, low_price, timestamp FROM sets WHERE item_id = ? ORDER BY timestamp DESC LIMIT 1", (item_id,))
        r = cursor.fetchone()
        if r:
            return {"id": r[0], "avg": r[1], "low": r[2], "timestamp": r[3]}
        return None

    def save_part_price(self, set_id, item_id, avg_price, low_price):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO parts (set_id, item_id, avg_price, low_price, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (set_id, item_id, avg_price, low_price, time.time()))
        self.conn.commit()

    def get_parts_prices(self, set_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT p.item_id, i.item_name, p.avg_price, p.low_price 
            FROM parts p
            JOIN items i ON p.item_id = i.id
            WHERE p.set_id = ?
        ''', (set_id,))
        results = []
        for r in cursor.fetchall():
            results.append({"id": r[0], "name": r[1], "avg": r[2], "low": r[3]})
        return results

    def get_setting(self, key, default=None):
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        r = cursor.fetchone()
        return r[0] if r else default

    def set_setting(self, key, value):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        self.conn.commit()

    def close(self):
        self.conn.close()
