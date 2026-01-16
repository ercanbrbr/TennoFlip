import unittest
from services.price_calculator import PriceCalculator

class TestPriceCalculator(unittest.TestCase):
    def setUp(self):
        self.sample_orders_online = [
            {"order_type": "sell", "platinum": 10, "user": {"status": "online"}, "mod_rank": 0},
            {"order_type": "sell", "platinum": 20, "user": {"status": "online"}, "mod_rank": 0},
            {"order_type": "sell", "platinum": 30, "user": {"status": "online"}, "mod_rank": 0},
            {"order_type": "sell", "platinum": 100, "user": {"status": "offline"}, "mod_rank": 0}, # Should be ignored
            {"order_type": "buy", "platinum": 50, "user": {"status": "online"}, "mod_rank": 0}   # Should be ignored
        ]

        self.sample_orders_ingame = [
            {"order_type": "sell", "platinum": 5, "user": {"status": "ingame"}, "mod_rank": 0},
            {"order_type": "sell", "platinum": 15, "user": {"status": "ingame"}, "mod_rank": 0},
        ]

        self.arcane_orders = [
            # Mixed ranks
            {"order_type": "sell", "platinum": 10, "user": {"status": "online"}, "mod_rank": 0},
            {"order_type": "sell", "platinum": 20, "user": {"status": "online"}, "mod_rank": 0},
            {"order_type": "sell", "platinum": 30, "user": {"status": "online"}, "mod_rank": 0},
            {"order_type": "sell", "platinum": 500, "user": {"status": "online"}, "mod_rank": 5}, # Max rank
            {"order_type": "sell", "platinum": 550, "user": {"status": "online"}, "mod_rank": 5},
        ]

    def test_calculate_price_item(self):
        # Top 30 items, take first 5, avg them.
        # Online users only
        orders = self.sample_orders_online
        price = PriceCalculator.calculate_price(orders, "item")
        # Prices: 10, 20, 30. Avg = 20.0
        self.assertEqual(price, 20.0)

    def test_calculate_price_item_ingame(self):
        # Ingame users should also be counted
        orders = self.sample_orders_online + self.sample_orders_ingame
        # Prices: 5, 10, 15, 20, 30. (Sorted: 5, 10, 15, 20, 30)
        # Avg of top 5 (all of them) = 80 / 5 = 16.0
        price = PriceCalculator.calculate_price(orders, "item")
        self.assertEqual(price, 16.0)

    def test_calculate_cheapest_item(self):
        # Cheapest 'ingame' user
        orders = self.sample_orders_online + self.sample_orders_ingame
        price = PriceCalculator.calculate_cheapest(orders)
        # 5 is the cheapest ingame
        self.assertEqual(price, 5.0)

    def test_calculate_cheapest_no_ingame(self):
        orders = self.sample_orders_online # No 'ingame' users
        price = PriceCalculator.calculate_cheapest(orders)
        self.assertEqual(price, -1.0)

    def test_calculate_price_arcane_rank0(self):
        # Arcane logic: exclude first 2, take next 15 avg (outlier protection)
        # We need more data points to test exclusion
        orders = [
            {"order_type": "sell", "platinum": p, "user": {"status": "online"}, "mod_rank": 0}
            for p in [10, 10, 20, 20, 20] # 10, 10 excluded. 20, 20, 20 used.
        ]
        price = PriceCalculator.calculate_price(orders, "arcane", rank=0)
        self.assertEqual(price, 20.0)

    def test_calculate_price_arcane_rank5(self):
        orders = self.arcane_orders
        price = PriceCalculator.calculate_price(orders, "arcane", rank=5)
        # Prices for rank 5: 500, 550.
        # Arcane logic excludes first 2 orders?
        # If < 2 valid orders, returns 0.0 per code step 125 logic line 33: valid_orders = sells[2:]
        # Wait, if I have 2 orders, it returns 0. Let's add more.
        
        extra_orders = [
            {"order_type": "sell", "platinum": 600, "user": {"status": "online"}, "mod_rank": 5}
        ]
        orders.extend(extra_orders)
        # Prices: 500, 550, 600.
        # Exclude first 2 (500, 550). Left with [600]. Avg = 600.
        price = PriceCalculator.calculate_price(orders, "arcane", rank=5)
        self.assertEqual(price, 600.0)

    def test_calculate_rank_prices(self):
        orders = self.arcane_orders
        # Need more orders for rank 5 to satisfy outlier logic (skips first 2)
        extra_orders = [
             {"order_type": "sell", "platinum": 600, "user": {"status": "online"}, "mod_rank": 5},
             {"order_type": "sell", "platinum": 600, "user": {"status": "online"}, "mod_rank": 5}
        ]
        orders.extend(extra_orders)
        
        # Ranks present: 0 and 5
        prices = PriceCalculator.calculate_rank_prices(orders, "arcane")
        self.assertIn(0, prices)
        self.assertIn(5, prices)
        # Rank 1-4 should not be in keys for arcane unless present and max_rank logic handled
        self.assertNotIn(1, prices)

if __name__ == '__main__':
    unittest.main()
