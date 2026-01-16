import unittest
import sqlite3
import json
import time
from data.database import Database

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Use existing specific path or transient DB?
        # Since Database() currently hardcodes the path in __init__ (probably),
        # we might need to modify it or subclass it to test safely without touching production DB.
        # Let's inspect Database.__init__ first or assume we can override.
        # Given the previous context, we didn't check __init__, but it usually takes no args.
        # We will subclass for testing to override connection.
        
        class TestDB(Database):
            def __init__(self):
                self.conn = sqlite3.connect(':memory:')
                self.create_tables()

        self.db = TestDB()

    def tearDown(self):
        self.db.close()

    def test_save_and_get_item(self):
        items = [{
            "id": "item1",
            "url_name": "frost_prime_set",
            "item_name": "Frost Prime Set",
            "tags": ["set", "warframe"]
        }]
        
        self.db.save_items(items)
        
        fetched = self.db.get_item_by_slug("frost_prime_set")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["item_name"], "Frost Prime Set")
        self.assertEqual(fetched["item_type"], "set") 

    def test_item_classification_filtering(self):
        # "junk_item" has no valid tags, should be skipped
        items = [
            {"id": "1", "url_name": "valid_arcane", "item_name": "Arcane Energize", "tags": ["arcane_enhancement"]},
            {"id": "2", "url_name": "junk", "item_name": "Junk Item", "tags": ["nothing"]}
        ]
        self.db.save_items(items)
        
        self.assertIsNotNone(self.db.get_item_by_slug("valid_arcane"))
        self.assertIsNone(self.db.get_item_by_slug("junk"))

    def test_save_and_get_arcane_price(self):
        item_id = "test_arcane_id"
        self.db.save_arcane_price(
            item_id, max_rank=5, 
            avg_r0=10.0, avg_max=100.0, avg_flip=10.0,
            low_r0=5.0, low_max=90.0, low_flip=15.0
        )
        
        price = self.db.get_arcane_price(item_id)
        self.assertIsNotNone(price)
        self.assertEqual(price['avg_r0'], 10.0)
        self.assertEqual(price['low_max'], 90.0)
        self.assertEqual(price['max_rank'], 5)

    def test_save_and_get_set_price(self):
        item_id = "test_set_id"
        self.db.save_set_price(item_id, avg_price=50.0, low_price=45.0)
        
        price = self.db.get_set_price(item_id)
        self.assertIsNotNone(price)
        self.assertEqual(price['avg'], 50.0)
        self.assertEqual(price['low'], 45.0)

    def test_parts_relation(self):
        set_id = 1
        part_item_id = "part_1"
        
        # Insert a fake part item first so join works if using strict relational integrity,
        # but pure sqlite without PRAGMA foreign_keys=ON might simplify it.
        # The schema uses FOREIGN KEY, but enforcement depends on connection.
        # Let's add the item to be safe.
        self.db.save_items([{
            "id": part_item_id, "url_name": "part_1", "item_name": "Part 1", "tags": ["component"]
        }])
        
        self.db.save_part_price(set_id, part_item_id, 10.0, 5.0)
        
        parts = self.db.get_parts_prices(set_id)
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0]['name'], "Part 1")
        self.assertEqual(parts[0]['avg'], 10.0)

if __name__ == '__main__':
    unittest.main()
