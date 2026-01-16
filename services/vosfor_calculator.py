from api.warframe_market import WarframeMarketAPI
from data.database import Database
from services.price_calculator import PriceCalculator

class VosforCalculator:
    PACKS = {
        "Cavia Collection": { 
             "cost": 200,
             "tiers": {
                 "uncommon": ["melee_fortification", "melee_retaliation"],
                 "rare": ["arcane_battery", "arcane_ice_storm", "melee_afflictions", "melee_animosity", "melee_exposure", "melee_influence", "melee_vortex", "secondary_fortifier", "secondary_surge"],
                 "legendary": ["melee_duplicate", "melee_crescendo"]
             },
             "tier_probs": {"uncommon": 0.45, "rare": 0.50, "legendary": 0.05}
        },
        "Duviri Collection": {
            "cost": 200,
            "tiers": {
                "uncommon": ["arcane_intention", "magus_aggress"],
                "rare": ["arcane_power_ramp", "primary_blight", "primary_exhilarate", "primary_obstruct", "shotgun_vendetta", "akimbo_slip_shot", "secondary_outburst"],
                "legendary": ["arcane_reaper", "longbow_sharpshot", "secondary_shiver"] 
            },
            "tier_probs": {"uncommon": 0.45, "rare": 0.50, "legendary": 0.05}
        },
        "Eidolon Collection": {
            "cost": 200,
            "tiers": {
                "common": ["arcane_consequence", "arcane_ice", "arcane_momentum", "arcane_nullifier", "arcane_tempo", "arcane_warmth"],
                "uncommon": ["arcane_acceleration", "arcane_agility", "arcane_awakening", "arcane_deflection", "arcane_eruption", "arcane_guardian", "arcane_healing", "arcane_phantasm", "arcane_resistance", "arcane_strike", "arcane_trickery", "arcane_velocity", "arcane_victory"],
                "rare": ["arcane_aegis", "arcane_arachne", "arcane_avenger", "arcane_fury", "arcane_precision", "arcane_pulse", "arcane_rage", "arcane_ultimatum"],
                "legendary": ["arcane_barrier", "arcane_energize", "arcane_grace"]
            },
            "tier_probs": {"common": 0.40, "uncommon": 0.35, "rare": 0.20, "legendary": 0.05} 
        },
        "Holdfasts Collection": { 
            "cost": 200,
            "tiers": {
                "rare": ["arcane_blessing", "arcane_rise", "molt_augmented", "molt_efficiency", "molt_reconstruct", "molt_vigor", "fractalized_reset", "primary_frostbite", "cascadia_accuracy", "cascadia_empowered", "cascadia_flare", "cascadia_overcharge", "conjunction_voltage", "emergence_dissipate", "emergence_renewed", "emergence_savior", "eternal_eradicate", "eternal_logistics", "eternal_onslaught"]
            },
             "tier_probs": {"rare": 1.0} 
        },
        "Höllvania Collection": { 
             "cost": 200,
             "tiers": {
                 "rare": ["arcane_bellicose", "arcane_camisado", "arcane_crepuscular", "arcane_impetus", "arcane_truculence", "melee_doughty", "primary_crux", "secondary_enervate"],
                 "legendary": ["arcane_escapist", "arcane_hot_shot", "arcane_universal_fallout"]
             },
             "tier_probs": {"rare": 0.95, "legendary": 0.05}
        },
        "Necralisk Collection": {
            "cost": 200,
            "tiers": {
                 "rare": ["arcane_double_back", "arcane_steadfast", "theorem_contagion", "theorem_demulcent", "theorem_infection", "primary_plated_round", "secondary_encumber", "secondary_kinship", "residual_boils", "residual_malodor", "residual_shock", "residual_viremia"]
            },
            "tier_probs": {"rare": 1.0}
        },
        "Ostron Collection": {
            "cost": 200,
            "tiers": {
                "common": ["magus_husk", "magus_vigor", "virtuos_null", "virtuos_tempo"],
                "uncommon": ["exodia_triumph", "exodia_valor", "magus_cadence", "magus_cloud", "magus_replenish", "virtuos_fury", "virtuos_strike"],
                "rare": ["exodia_brave", "exodia_force", "exodia_hunt", "exodia_might", "magus_elevate", "magus_nourish", "virtuos_ghost", "virtuos_shadow"]
            },
            "tier_probs": {"common": 0.10, "uncommon": 0.30, "rare": 0.60}
        },
        "Solaris Collection": {
            "cost": 200,
            "tiers": {
                "common": ["magus_accelerant", "magus_anomaly", "magus_drive", "magus_firewall", "magus_overload", "virtuos_spike", "virtuos_surge"],
                "uncommon": ["magus_glitch", "magus_repair", "virtuos_forge", "virtuos_trojan"],
                "rare": ["pax_bolt", "pax_charge", "pax_seeker", "pax_soar", "magus_destruct", "magus_lockdown", "magus_melt", "magus_revert"]
            },
            "tier_probs": {"common": 0.15, "uncommon": 0.15, "rare": 0.70}
        },
        "Steel Path Collection": {
            "cost": 200,
            "tiers": {
                "rare": ["arcane_blade_charger", "arcane_bodyguard", "arcane_pistoleer", "arcane_primary_charger", "arcane_tanker", "primary_deadhead", "primary_dexterity", "primary_merciless", "secondary_deadhead", "secondary_dexterity", "secondary_merciless"]
            },
             "tier_probs": {"rare": 1.0}
        },
        "Descendia Collection": {
            "cost": 200,
            "tiers": {
                "rare": ["arcane_circumvent", "arcane_concentration", "arcane_expertise", "arcane_persistence", "primary_bulwark", "primary_debilitate", "primary_overcharge", "secondary_irradiate", "melee_careen"]
            },
            "tier_probs": {"rare": 1.0}
        }
    }
    
    def __init__(self):
        self.api = WarframeMarketAPI()
        self.db = Database()

    def calculate_all_packs(self, mode="avg"):
        """Calculates expected values for all arcane packs based on current market prices and drop probabilities."""
        results = []
        for name, data in self.PACKS.items():
            cost = data['cost']
            tiers = data['tiers']
            tier_probs = data.get('tier_probs', {})
            
            pack_total_ev = 0
            
            for tier_name, slugs in tiers.items():
                if not slugs: continue
                prob = tier_probs.get(tier_name, 0)
                if prob == 0: continue
                
                tier_prices = []
                for slug in slugs:
                    item = self.db.get_item_by_slug(slug)
                    if not item: continue
                    item_id = item['id']
                    
                    p = self.db.get_arcane_price(item_id)
                    price = 0
                    
                    if p:
                        if mode == "cheapest":
                            price = p.get('low_r0', 0)
                        else:
                            price = p.get('avg_r0', 0)
                    else:
                        orders = self.api.get_orders(slug)
                        avg_r0 = PriceCalculator.calculate_price(orders, "arcane", rank=0)
                        low_r0 = PriceCalculator.calculate_cheapest(orders, rank=0)
                        avg_max = PriceCalculator.calculate_price(orders, "arcane", rank=5)
                        low_max = PriceCalculator.calculate_cheapest(orders, rank=5)
                        
                        self.db.save_arcane_price(item_id, 5, avg_r0, avg_max, 0, low_r0, low_max, 0)
                        price = low_r0 if mode == "cheapest" else avg_r0
                    
                    if price <= 0: price = 0
                    tier_prices.append(price)
                
                if tier_prices:
                    avg_tier_val = sum(tier_prices) / len(tier_prices)
                    pack_total_ev += avg_tier_val * prob
            
            total_ev_3x = pack_total_ev * 3
            
            results.append({
                "name": name,
                "cost": cost,
                "ev": total_ev_3x
            })
            
        return results
