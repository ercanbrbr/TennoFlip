from dataclasses import dataclass, field
from typing import List

@dataclass
class Item:
    id: str
    name: str
    url_name: str
    type: str  # 'warframe', 'weapon', 'arcane', 'mod', 'pack'
    price: float = 0.0
    thumb: str = ""

@dataclass
class RankedItem(Item):
    rank: int = 0
    max_rank: int = 0

@dataclass
class SetItem(Item):
    parts: List[str] = field(default_factory=list)
