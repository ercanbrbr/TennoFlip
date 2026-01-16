class PriceCalculator:
    @staticmethod
    def calculate_price(orders, item_type=None, rank=None):
        """Calculates the average price based on a set of orders, using specific rules for Arcanes vs normal items."""
        sells = []
        is_arcane = (item_type == "arcane")
        
        for order in orders:
            if order.get("order_type") != "sell":
                continue
            
            user = order.get("user", {})
            status = user.get("status", "offline")
            
            if not is_arcane and status not in ("online", "ingame"):
                continue
            
            order_rank = order.get("mod_rank")
            
            if rank is not None:
                if order_rank != rank:
                    continue
            else:
                if item_type == "mod" or item_type == "arcane":
                    if order_rank is not None and order_rank != 0:
                        continue
            
            sells.append(order["platinum"])
        
        sells.sort()
        
        if is_arcane:
            valid_orders = sells[2:]
            if not valid_orders:
                return 0.0
            target_slice = valid_orders[:15]
            return sum(target_slice) / len(target_slice)
        else:
            top_30 = sells[:30]
            if not top_30:
                return 0.0
            slice_size = min(5, len(top_30))
            target_slice = top_30[:slice_size]
            return sum(target_slice) / slice_size

    @staticmethod
    def calculate_cheapest(orders, rank=None):
        """Finds the absolute lowest price from 'ingame' users."""
        cheapest = float('inf')
        found = False
        
        for order in orders:
            if order.get("order_type") != "sell":
                continue
            
            user = order.get("user", {})
            if user.get("status") != "ingame":
                continue
                
            if rank is not None and order.get("mod_rank") != rank:
                continue
                
            plat = order.get("platinum", float('inf'))
            if plat < cheapest:
                cheapest = plat
                found = True
        
        return cheapest if found else -1.0

    @staticmethod
    def calculate_rank_prices(orders, item_type=None):
        """Calculates prices for all available ranks of a mod or arcane."""
        if item_type not in ("mod", "arcane"):
            return {}
            
        max_rank = 0
        for order in orders:
            r = order.get("mod_rank")
            if r is not None and r > max_rank:
                max_rank = r
        
        if max_rank > 10: max_rank = 10
        
        prices = {}
        if item_type == "arcane":
            ranks_to_check = [0, max_rank]
        else:
            ranks_to_check = range(max_rank + 1)

        for rank in ranks_to_check:
            p = PriceCalculator.calculate_price(orders, item_type, rank=rank)
            if p > 0:
                prices[rank] = p
                
        return prices
