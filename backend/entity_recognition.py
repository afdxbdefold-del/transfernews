"""
TransferNews.de - ENTITY RECOGNITION SYSTEM
============================================

Erkennt Spieler, Clubs, Wettbewerbe und Transfer-Details aus Headlines.
Verwendet Pattern-Matching und umfangreiche Datenbanken.

ERWEITERT: 29. März 2026
- 800+ Spieler aus Top 5 Ligen + internationale Stars
- 300+ Clubs weltweit
- Verbesserte Alias-Erkennung
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TransferType(Enum):
    PERMANENT = "permanent"
    LOAN = "loan"
    LOAN_WITH_OPTION = "loan_option"
    FREE = "free"
    SWAP = "swap"
    RETURN = "return"
    EXTENSION = "extension"
    UNKNOWN = "unknown"


@dataclass
class EntityMatch:
    """Erkannte Entität"""
    name: str
    canonical_name: str
    slug: str
    confidence: float
    entity_type: str  # player, club, competition
    metadata: Dict


# =============================================================================
# SPIELER-DATENBANK (800+ Spieler)
# =============================================================================

PLAYERS_DB = {
    # ═══════════════════════════════════════════════════
    # TIER 1 - WELTKLASSE (Popularity 90-100)
    # ═══════════════════════════════════════════════════
    
    # Stürmer Weltklasse
    "mbappe": {"name": "Kylian Mbappé", "club": "Real Madrid", "position": "ST", "nationality": "FRA", "popularity": 100},
    "mbappé": {"name": "Kylian Mbappé", "club": "Real Madrid", "position": "ST", "nationality": "FRA", "popularity": 100},
    "kylian mbappe": {"name": "Kylian Mbappé", "club": "Real Madrid", "position": "ST", "nationality": "FRA", "popularity": 100},
    "haaland": {"name": "Erling Haaland", "club": "Manchester City", "position": "ST", "nationality": "NOR", "popularity": 98},
    "erling haaland": {"name": "Erling Haaland", "club": "Manchester City", "position": "ST", "nationality": "NOR", "popularity": 98},
    "messi": {"name": "Lionel Messi", "club": "Inter Miami", "position": "RW", "nationality": "ARG", "popularity": 95},
    "lionel messi": {"name": "Lionel Messi", "club": "Inter Miami", "position": "RW", "nationality": "ARG", "popularity": 95},
    "ronaldo": {"name": "Cristiano Ronaldo", "club": "Al-Nassr", "position": "ST", "nationality": "POR", "popularity": 94},
    "cristiano ronaldo": {"name": "Cristiano Ronaldo", "club": "Al-Nassr", "position": "ST", "nationality": "POR", "popularity": 94},
    "cr7": {"name": "Cristiano Ronaldo", "club": "Al-Nassr", "position": "ST", "nationality": "POR", "popularity": 94},
    
    # Mittelfeld/Flügel Weltklasse
    "bellingham": {"name": "Jude Bellingham", "club": "Real Madrid", "position": "CAM", "nationality": "ENG", "popularity": 96},
    "jude bellingham": {"name": "Jude Bellingham", "club": "Real Madrid", "position": "CAM", "nationality": "ENG", "popularity": 96},
    "vinicius": {"name": "Vinícius Jr.", "club": "Real Madrid", "position": "LW", "nationality": "BRA", "popularity": 95},
    "vinicius jr": {"name": "Vinícius Jr.", "club": "Real Madrid", "position": "LW", "nationality": "BRA", "popularity": 95},
    "vini jr": {"name": "Vinícius Jr.", "club": "Real Madrid", "position": "LW", "nationality": "BRA", "popularity": 95},
    "vini": {"name": "Vinícius Jr.", "club": "Real Madrid", "position": "LW", "nationality": "BRA", "popularity": 95},
    
    # ═══════════════════════════════════════════════════
    # TIER 2 - TOP STARS (Popularity 80-89)
    # ═══════════════════════════════════════════════════
    
    "salah": {"name": "Mohamed Salah", "club": "Liverpool", "position": "RW", "nationality": "EGY", "popularity": 89},
    "mohamed salah": {"name": "Mohamed Salah", "club": "Liverpool", "position": "RW", "nationality": "EGY", "popularity": 89},
    "mo salah": {"name": "Mohamed Salah", "club": "Liverpool", "position": "RW", "nationality": "EGY", "popularity": 89},
    "kane": {"name": "Harry Kane", "club": "Bayern München", "position": "ST", "nationality": "ENG", "popularity": 88},
    "harry kane": {"name": "Harry Kane", "club": "Bayern München", "position": "ST", "nationality": "ENG", "popularity": 88},
    "musiala": {"name": "Jamal Musiala", "club": "Bayern München", "position": "CAM", "nationality": "GER", "popularity": 87},
    "jamal musiala": {"name": "Jamal Musiala", "club": "Bayern München", "position": "CAM", "nationality": "GER", "popularity": 87},
    "wirtz": {"name": "Florian Wirtz", "club": "Bayer Leverkusen", "position": "CAM", "nationality": "GER", "popularity": 86},
    "florian wirtz": {"name": "Florian Wirtz", "club": "Bayer Leverkusen", "position": "CAM", "nationality": "GER", "popularity": 86},
    "saka": {"name": "Bukayo Saka", "club": "Arsenal", "position": "RW", "nationality": "ENG", "popularity": 85},
    "bukayo saka": {"name": "Bukayo Saka", "club": "Arsenal", "position": "RW", "nationality": "ENG", "popularity": 85},
    "palmer": {"name": "Cole Palmer", "club": "Chelsea", "position": "CAM", "nationality": "ENG", "popularity": 84},
    "cole palmer": {"name": "Cole Palmer", "club": "Chelsea", "position": "CAM", "nationality": "ENG", "popularity": 84},
    "rodri": {"name": "Rodri", "club": "Manchester City", "position": "CDM", "nationality": "ESP", "popularity": 83},
    "rodrigo hernandez": {"name": "Rodri", "club": "Manchester City", "position": "CDM", "nationality": "ESP", "popularity": 83},
    "de bruyne": {"name": "Kevin De Bruyne", "club": "Manchester City", "position": "CAM", "nationality": "BEL", "popularity": 82},
    "kevin de bruyne": {"name": "Kevin De Bruyne", "club": "Manchester City", "position": "CAM", "nationality": "BEL", "popularity": 82},
    "kdb": {"name": "Kevin De Bruyne", "club": "Manchester City", "position": "CAM", "nationality": "BEL", "popularity": 82},
    "foden": {"name": "Phil Foden", "club": "Manchester City", "position": "LW", "nationality": "ENG", "popularity": 81},
    "phil foden": {"name": "Phil Foden", "club": "Manchester City", "position": "LW", "nationality": "ENG", "popularity": 81},
    "pedri": {"name": "Pedri", "club": "Barcelona", "position": "CM", "nationality": "ESP", "popularity": 80},
    "pedri gonzalez": {"name": "Pedri", "club": "Barcelona", "position": "CM", "nationality": "ESP", "popularity": 80},
    
    # ═══════════════════════════════════════════════════
    # TIER 3 - BEKANNTE SPIELER (Popularity 70-79)
    # ═══════════════════════════════════════════════════
    
    "yamal": {"name": "Lamine Yamal", "club": "Barcelona", "position": "RW", "nationality": "ESP", "popularity": 79},
    "lamine yamal": {"name": "Lamine Yamal", "club": "Barcelona", "position": "RW", "nationality": "ESP", "popularity": 79},
    "gavi": {"name": "Gavi", "club": "Barcelona", "position": "CM", "nationality": "ESP", "popularity": 78},
    "pablo gavi": {"name": "Gavi", "club": "Barcelona", "position": "CM", "nationality": "ESP", "popularity": 78},
    "sancho": {"name": "Jadon Sancho", "club": "Manchester United", "position": "RW", "nationality": "ENG", "popularity": 77},
    "jadon sancho": {"name": "Jadon Sancho", "club": "Manchester United", "position": "RW", "nationality": "ENG", "popularity": 77},
    "rashford": {"name": "Marcus Rashford", "club": "Manchester United", "position": "LW", "nationality": "ENG", "popularity": 76},
    "marcus rashford": {"name": "Marcus Rashford", "club": "Manchester United", "position": "LW", "nationality": "ENG", "popularity": 76},
    "neymar": {"name": "Neymar Jr.", "club": "Al-Hilal", "position": "LW", "nationality": "BRA", "popularity": 75},
    "neymar jr": {"name": "Neymar Jr.", "club": "Al-Hilal", "position": "LW", "nationality": "BRA", "popularity": 75},
    "lewandowski": {"name": "Robert Lewandowski", "club": "Barcelona", "position": "ST", "nationality": "POL", "popularity": 74},
    "robert lewandowski": {"name": "Robert Lewandowski", "club": "Barcelona", "position": "ST", "nationality": "POL", "popularity": 74},
    "lewy": {"name": "Robert Lewandowski", "club": "Barcelona", "position": "ST", "nationality": "POL", "popularity": 74},
    "modric": {"name": "Luka Modrić", "club": "Real Madrid", "position": "CM", "nationality": "CRO", "popularity": 73},
    "luka modric": {"name": "Luka Modrić", "club": "Real Madrid", "position": "CM", "nationality": "CRO", "popularity": 73},
    "kroos": {"name": "Toni Kroos", "club": "Retired", "position": "CM", "nationality": "GER", "popularity": 72},
    "toni kroos": {"name": "Toni Kroos", "club": "Retired", "position": "CM", "nationality": "GER", "popularity": 72},
    "muller": {"name": "Thomas Müller", "club": "Bayern München", "position": "CAM", "nationality": "GER", "popularity": 71},
    "müller": {"name": "Thomas Müller", "club": "Bayern München", "position": "CAM", "nationality": "GER", "popularity": 71},
    "thomas muller": {"name": "Thomas Müller", "club": "Bayern München", "position": "CAM", "nationality": "GER", "popularity": 71},
    "thomas müller": {"name": "Thomas Müller", "club": "Bayern München", "position": "CAM", "nationality": "GER", "popularity": 71},
    "neuer": {"name": "Manuel Neuer", "club": "Bayern München", "position": "GK", "nationality": "GER", "popularity": 70},
    "manuel neuer": {"name": "Manuel Neuer", "club": "Bayern München", "position": "GK", "nationality": "GER", "popularity": 70},
    
    # ═══════════════════════════════════════════════════
    # BUNDESLIGA SPIELER (Popularity 55-69)
    # ═══════════════════════════════════════════════════
    
    # Bayern München
    "fullkrug": {"name": "Niclas Füllkrug", "club": "West Ham", "position": "ST", "nationality": "GER", "popularity": 68},
    "füllkrug": {"name": "Niclas Füllkrug", "club": "West Ham", "position": "ST", "nationality": "GER", "popularity": 68},
    "niclas fullkrug": {"name": "Niclas Füllkrug", "club": "West Ham", "position": "ST", "nationality": "GER", "popularity": 68},
    "niclas füllkrug": {"name": "Niclas Füllkrug", "club": "West Ham", "position": "ST", "nationality": "GER", "popularity": 68},
    "gnabry": {"name": "Serge Gnabry", "club": "Bayern München", "position": "RW", "nationality": "GER", "popularity": 66},
    "serge gnabry": {"name": "Serge Gnabry", "club": "Bayern München", "position": "RW", "nationality": "GER", "popularity": 66},
    "sane": {"name": "Leroy Sané", "club": "Bayern München", "position": "LW", "nationality": "GER", "popularity": 65},
    "sané": {"name": "Leroy Sané", "club": "Bayern München", "position": "LW", "nationality": "GER", "popularity": 65},
    "leroy sane": {"name": "Leroy Sané", "club": "Bayern München", "position": "LW", "nationality": "GER", "popularity": 65},
    "leroy sané": {"name": "Leroy Sané", "club": "Bayern München", "position": "LW", "nationality": "GER", "popularity": 65},
    "kimmich": {"name": "Joshua Kimmich", "club": "Bayern München", "position": "CDM", "nationality": "GER", "popularity": 62},
    "joshua kimmich": {"name": "Joshua Kimmich", "club": "Bayern München", "position": "CDM", "nationality": "GER", "popularity": 62},
    "goretzka": {"name": "Leon Goretzka", "club": "Bayern München", "position": "CM", "nationality": "GER", "popularity": 61},
    "leon goretzka": {"name": "Leon Goretzka", "club": "Bayern München", "position": "CM", "nationality": "GER", "popularity": 61},
    "upamecano": {"name": "Dayot Upamecano", "club": "Bayern München", "position": "CB", "nationality": "FRA", "popularity": 60},
    "dayot upamecano": {"name": "Dayot Upamecano", "club": "Bayern München", "position": "CB", "nationality": "FRA", "popularity": 60},
    "coman": {"name": "Kingsley Coman", "club": "Bayern München", "position": "RW", "nationality": "FRA", "popularity": 59},
    "kingsley coman": {"name": "Kingsley Coman", "club": "Bayern München", "position": "RW", "nationality": "FRA", "popularity": 59},
    "davies": {"name": "Alphonso Davies", "club": "Bayern München", "position": "LB", "nationality": "CAN", "popularity": 63},
    "alphonso davies": {"name": "Alphonso Davies", "club": "Bayern München", "position": "LB", "nationality": "CAN", "popularity": 63},
    "tel": {"name": "Mathys Tel", "club": "Bayern München", "position": "ST", "nationality": "FRA", "popularity": 55},
    "mathys tel": {"name": "Mathys Tel", "club": "Bayern München", "position": "ST", "nationality": "FRA", "popularity": 55},
    "kim min-jae": {"name": "Kim Min-jae", "club": "Bayern München", "position": "CB", "nationality": "KOR", "popularity": 58},
    "kim": {"name": "Kim Min-jae", "club": "Bayern München", "position": "CB", "nationality": "KOR", "popularity": 58},
    
    # Borussia Dortmund
    "brandt": {"name": "Julian Brandt", "club": "Borussia Dortmund", "position": "CAM", "nationality": "GER", "popularity": 60},
    "julian brandt": {"name": "Julian Brandt", "club": "Borussia Dortmund", "position": "CAM", "nationality": "GER", "popularity": 60},
    "reus": {"name": "Marco Reus", "club": "Free Agent", "position": "CAM", "nationality": "GER", "popularity": 62},
    "marco reus": {"name": "Marco Reus", "club": "Free Agent", "position": "CAM", "nationality": "GER", "popularity": 62},
    "sabitzer": {"name": "Marcel Sabitzer", "club": "Borussia Dortmund", "position": "CM", "nationality": "AUT", "popularity": 55},
    "marcel sabitzer": {"name": "Marcel Sabitzer", "club": "Borussia Dortmund", "position": "CM", "nationality": "AUT", "popularity": 55},
    "adeyemi": {"name": "Karim Adeyemi", "club": "Borussia Dortmund", "position": "LW", "nationality": "GER", "popularity": 57},
    "karim adeyemi": {"name": "Karim Adeyemi", "club": "Borussia Dortmund", "position": "LW", "nationality": "GER", "popularity": 57},
    "schlotterbeck": {"name": "Nico Schlotterbeck", "club": "Borussia Dortmund", "position": "CB", "nationality": "GER", "popularity": 56},
    "nico schlotterbeck": {"name": "Nico Schlotterbeck", "club": "Borussia Dortmund", "position": "CB", "nationality": "GER", "popularity": 56},
    "hummels": {"name": "Mats Hummels", "club": "Roma", "position": "CB", "nationality": "GER", "popularity": 60},
    "mats hummels": {"name": "Mats Hummels", "club": "Roma", "position": "CB", "nationality": "GER", "popularity": 60},
    "maatsen": {"name": "Ian Maatsen", "club": "Aston Villa", "position": "LB", "nationality": "NED", "popularity": 52},
    "ian maatsen": {"name": "Ian Maatsen", "club": "Aston Villa", "position": "LB", "nationality": "NED", "popularity": 52},
    "nmecha": {"name": "Lukas Nmecha", "club": "Borussia Dortmund", "position": "ST", "nationality": "GER", "popularity": 48},
    "lukas nmecha": {"name": "Lukas Nmecha", "club": "Borussia Dortmund", "position": "ST", "nationality": "GER", "popularity": 48},
    "guirassy": {"name": "Serhou Guirassy", "club": "Borussia Dortmund", "position": "ST", "nationality": "GUI", "popularity": 58},
    "serhou guirassy": {"name": "Serhou Guirassy", "club": "Borussia Dortmund", "position": "ST", "nationality": "GUI", "popularity": 58},
    
    # Bayer Leverkusen
    "xhaka": {"name": "Granit Xhaka", "club": "Bayer Leverkusen", "position": "CM", "nationality": "SUI", "popularity": 62},
    "granit xhaka": {"name": "Granit Xhaka", "club": "Bayer Leverkusen", "position": "CM", "nationality": "SUI", "popularity": 62},
    "schick": {"name": "Patrik Schick", "club": "Bayer Leverkusen", "position": "ST", "nationality": "CZE", "popularity": 55},
    "patrik schick": {"name": "Patrik Schick", "club": "Bayer Leverkusen", "position": "ST", "nationality": "CZE", "popularity": 55},
    "boniface": {"name": "Victor Boniface", "club": "Bayer Leverkusen", "position": "ST", "nationality": "NGA", "popularity": 58},
    "victor boniface": {"name": "Victor Boniface", "club": "Bayer Leverkusen", "position": "ST", "nationality": "NGA", "popularity": 58},
    "frimpong": {"name": "Jeremie Frimpong", "club": "Bayer Leverkusen", "position": "RB", "nationality": "NED", "popularity": 55},
    "jeremie frimpong": {"name": "Jeremie Frimpong", "club": "Bayer Leverkusen", "position": "RB", "nationality": "NED", "popularity": 55},
    "grimaldo": {"name": "Alejandro Grimaldo", "club": "Bayer Leverkusen", "position": "LB", "nationality": "ESP", "popularity": 54},
    "alejandro grimaldo": {"name": "Alejandro Grimaldo", "club": "Bayer Leverkusen", "position": "LB", "nationality": "ESP", "popularity": 54},
    
    # RB Leipzig
    "xavi simons": {"name": "Xavi Simons", "club": "RB Leipzig", "position": "CAM", "nationality": "NED", "popularity": 65},
    "simons": {"name": "Xavi Simons", "club": "RB Leipzig", "position": "CAM", "nationality": "NED", "popularity": 65},
    "openda": {"name": "Loïs Openda", "club": "RB Leipzig", "position": "ST", "nationality": "BEL", "popularity": 58},
    "lois openda": {"name": "Loïs Openda", "club": "RB Leipzig", "position": "ST", "nationality": "BEL", "popularity": 58},
    "sesko": {"name": "Benjamin Šeško", "club": "RB Leipzig", "position": "ST", "nationality": "SVN", "popularity": 60},
    "benjamin sesko": {"name": "Benjamin Šeško", "club": "RB Leipzig", "position": "ST", "nationality": "SVN", "popularity": 60},
    "nkunku": {"name": "Christopher Nkunku", "club": "Chelsea", "position": "CAM", "nationality": "FRA", "popularity": 65},
    "christopher nkunku": {"name": "Christopher Nkunku", "club": "Chelsea", "position": "CAM", "nationality": "FRA", "popularity": 65},
    
    # Eintracht Frankfurt
    "gotze": {"name": "Mario Götze", "club": "Eintracht Frankfurt", "position": "CAM", "nationality": "GER", "popularity": 58},
    "götze": {"name": "Mario Götze", "club": "Eintracht Frankfurt", "position": "CAM", "nationality": "GER", "popularity": 58},
    "mario gotze": {"name": "Mario Götze", "club": "Eintracht Frankfurt", "position": "CAM", "nationality": "GER", "popularity": 58},
    "mario götze": {"name": "Mario Götze", "club": "Eintracht Frankfurt", "position": "CAM", "nationality": "GER", "popularity": 58},
    "marmoush": {"name": "Omar Marmoush", "club": "Eintracht Frankfurt", "position": "LW", "nationality": "EGY", "popularity": 56},
    "omar marmoush": {"name": "Omar Marmoush", "club": "Eintracht Frankfurt", "position": "LW", "nationality": "EGY", "popularity": 56},
    "ekitike": {"name": "Hugo Ekitike", "club": "Eintracht Frankfurt", "position": "ST", "nationality": "FRA", "popularity": 52},
    "hugo ekitike": {"name": "Hugo Ekitike", "club": "Eintracht Frankfurt", "position": "ST", "nationality": "FRA", "popularity": 52},
    
    # VfB Stuttgart
    "undav": {"name": "Deniz Undav", "club": "VfB Stuttgart", "position": "ST", "nationality": "GER", "popularity": 55},
    "deniz undav": {"name": "Deniz Undav", "club": "VfB Stuttgart", "position": "ST", "nationality": "GER", "popularity": 55},
    "guirassy": {"name": "Serhou Guirassy", "club": "Borussia Dortmund", "position": "ST", "nationality": "GUI", "popularity": 58},
    "mittelstadt": {"name": "Maximilian Mittelstädt", "club": "VfB Stuttgart", "position": "LB", "nationality": "GER", "popularity": 52},
    "maximilian mittelstadt": {"name": "Maximilian Mittelstädt", "club": "VfB Stuttgart", "position": "LB", "nationality": "GER", "popularity": 52},
    "anton": {"name": "Waldemar Anton", "club": "Borussia Dortmund", "position": "CB", "nationality": "GER", "popularity": 50},
    "waldemar anton": {"name": "Waldemar Anton", "club": "Borussia Dortmund", "position": "CB", "nationality": "GER", "popularity": 50},
    
    # Weitere Bundesliga
    "havertz": {"name": "Kai Havertz", "club": "Arsenal", "position": "ST", "nationality": "GER", "popularity": 67},
    "kai havertz": {"name": "Kai Havertz", "club": "Arsenal", "position": "ST", "nationality": "GER", "popularity": 67},
    "gundogan": {"name": "İlkay Gündoğan", "club": "Barcelona", "position": "CM", "nationality": "GER", "popularity": 64},
    "gündogan": {"name": "İlkay Gündoğan", "club": "Barcelona", "position": "CM", "nationality": "GER", "popularity": 64},
    "ilkay gundogan": {"name": "İlkay Gündoğan", "club": "Barcelona", "position": "CM", "nationality": "GER", "popularity": 64},
    "ilkay gündogan": {"name": "İlkay Gündoğan", "club": "Barcelona", "position": "CM", "nationality": "GER", "popularity": 64},
    "ter stegen": {"name": "Marc-André ter Stegen", "club": "Barcelona", "position": "GK", "nationality": "GER", "popularity": 63},
    "marc-andre ter stegen": {"name": "Marc-André ter Stegen", "club": "Barcelona", "position": "GK", "nationality": "GER", "popularity": 63},
    "rudiger": {"name": "Antonio Rüdiger", "club": "Real Madrid", "position": "CB", "nationality": "GER", "popularity": 62},
    "rüdiger": {"name": "Antonio Rüdiger", "club": "Real Madrid", "position": "CB", "nationality": "GER", "popularity": 62},
    "antonio rudiger": {"name": "Antonio Rüdiger", "club": "Real Madrid", "position": "CB", "nationality": "GER", "popularity": 62},
    "antonio rüdiger": {"name": "Antonio Rüdiger", "club": "Real Madrid", "position": "CB", "nationality": "GER", "popularity": 62},
    "tah": {"name": "Jonathan Tah", "club": "Bayer Leverkusen", "position": "CB", "nationality": "GER", "popularity": 58},
    "jonathan tah": {"name": "Jonathan Tah", "club": "Bayer Leverkusen", "position": "CB", "nationality": "GER", "popularity": 58},
    "andrich": {"name": "Robert Andrich", "club": "Bayer Leverkusen", "position": "CDM", "nationality": "GER", "popularity": 52},
    "robert andrich": {"name": "Robert Andrich", "club": "Bayer Leverkusen", "position": "CDM", "nationality": "GER", "popularity": 52},
    
    # ═══════════════════════════════════════════════════
    # PREMIER LEAGUE STARS (Popularity 55-69)
    # ═══════════════════════════════════════════════════
    
    # Arsenal
    "rice": {"name": "Declan Rice", "club": "Arsenal", "position": "CDM", "nationality": "ENG", "popularity": 68},
    "declan rice": {"name": "Declan Rice", "club": "Arsenal", "position": "CDM", "nationality": "ENG", "popularity": 68},
    "odegaard": {"name": "Martin Ødegaard", "club": "Arsenal", "position": "CAM", "nationality": "NOR", "popularity": 67},
    "ødegaard": {"name": "Martin Ødegaard", "club": "Arsenal", "position": "CAM", "nationality": "NOR", "popularity": 67},
    "martin odegaard": {"name": "Martin Ødegaard", "club": "Arsenal", "position": "CAM", "nationality": "NOR", "popularity": 67},
    "martinelli": {"name": "Gabriel Martinelli", "club": "Arsenal", "position": "LW", "nationality": "BRA", "popularity": 65},
    "gabriel martinelli": {"name": "Gabriel Martinelli", "club": "Arsenal", "position": "LW", "nationality": "BRA", "popularity": 65},
    "saliba": {"name": "William Saliba", "club": "Arsenal", "position": "CB", "nationality": "FRA", "popularity": 63},
    "william saliba": {"name": "William Saliba", "club": "Arsenal", "position": "CB", "nationality": "FRA", "popularity": 63},
    "gabriel": {"name": "Gabriel Magalhães", "club": "Arsenal", "position": "CB", "nationality": "BRA", "popularity": 60},
    "gabriel magalhaes": {"name": "Gabriel Magalhães", "club": "Arsenal", "position": "CB", "nationality": "BRA", "popularity": 60},
    "trossard": {"name": "Leandro Trossard", "club": "Arsenal", "position": "LW", "nationality": "BEL", "popularity": 58},
    "leandro trossard": {"name": "Leandro Trossard", "club": "Arsenal", "position": "LW", "nationality": "BEL", "popularity": 58},
    "raya": {"name": "David Raya", "club": "Arsenal", "position": "GK", "nationality": "ESP", "popularity": 55},
    "david raya": {"name": "David Raya", "club": "Arsenal", "position": "GK", "nationality": "ESP", "popularity": 55},
    
    # Manchester United
    "bruno fernandes": {"name": "Bruno Fernandes", "club": "Manchester United", "position": "CAM", "nationality": "POR", "popularity": 66},
    "bruno": {"name": "Bruno Fernandes", "club": "Manchester United", "position": "CAM", "nationality": "POR", "popularity": 66},
    "casemiro": {"name": "Casemiro", "club": "Manchester United", "position": "CDM", "nationality": "BRA", "popularity": 65},
    "hojlund": {"name": "Rasmus Højlund", "club": "Manchester United", "position": "ST", "nationality": "DEN", "popularity": 60},
    "højlund": {"name": "Rasmus Højlund", "club": "Manchester United", "position": "ST", "nationality": "DEN", "popularity": 60},
    "rasmus hojlund": {"name": "Rasmus Højlund", "club": "Manchester United", "position": "ST", "nationality": "DEN", "popularity": 60},
    "garnacho": {"name": "Alejandro Garnacho", "club": "Manchester United", "position": "LW", "nationality": "ARG", "popularity": 62},
    "alejandro garnacho": {"name": "Alejandro Garnacho", "club": "Manchester United", "position": "LW", "nationality": "ARG", "popularity": 62},
    "mainoo": {"name": "Kobbie Mainoo", "club": "Manchester United", "position": "CM", "nationality": "ENG", "popularity": 58},
    "kobbie mainoo": {"name": "Kobbie Mainoo", "club": "Manchester United", "position": "CM", "nationality": "ENG", "popularity": 58},
    "onana": {"name": "André Onana", "club": "Manchester United", "position": "GK", "nationality": "CMR", "popularity": 57},
    "andre onana": {"name": "André Onana", "club": "Manchester United", "position": "GK", "nationality": "CMR", "popularity": 57},
    "martinez": {"name": "Lisandro Martínez", "club": "Manchester United", "position": "CB", "nationality": "ARG", "popularity": 58},
    "lisandro martinez": {"name": "Lisandro Martínez", "club": "Manchester United", "position": "CB", "nationality": "ARG", "popularity": 58},
    
    # Liverpool
    "darwin nunez": {"name": "Darwin Núñez", "club": "Liverpool", "position": "ST", "nationality": "URU", "popularity": 64},
    "darwin": {"name": "Darwin Núñez", "club": "Liverpool", "position": "ST", "nationality": "URU", "popularity": 64},
    "nunez": {"name": "Darwin Núñez", "club": "Liverpool", "position": "ST", "nationality": "URU", "popularity": 64},
    "luis diaz": {"name": "Luis Díaz", "club": "Liverpool", "position": "LW", "nationality": "COL", "popularity": 63},
    "diaz": {"name": "Luis Díaz", "club": "Liverpool", "position": "LW", "nationality": "COL", "popularity": 63},
    "van dijk": {"name": "Virgil van Dijk", "club": "Liverpool", "position": "CB", "nationality": "NED", "popularity": 62},
    "virgil van dijk": {"name": "Virgil van Dijk", "club": "Liverpool", "position": "CB", "nationality": "NED", "popularity": 62},
    "szoboszlai": {"name": "Dominik Szoboszlai", "club": "Liverpool", "position": "CAM", "nationality": "HUN", "popularity": 60},
    "dominik szoboszlai": {"name": "Dominik Szoboszlai", "club": "Liverpool", "position": "CAM", "nationality": "HUN", "popularity": 60},
    "mac allister": {"name": "Alexis Mac Allister", "club": "Liverpool", "position": "CM", "nationality": "ARG", "popularity": 58},
    "alexis mac allister": {"name": "Alexis Mac Allister", "club": "Liverpool", "position": "CM", "nationality": "ARG", "popularity": 58},
    "alisson": {"name": "Alisson Becker", "club": "Liverpool", "position": "GK", "nationality": "BRA", "popularity": 65},
    "alisson becker": {"name": "Alisson Becker", "club": "Liverpool", "position": "GK", "nationality": "BRA", "popularity": 65},
    "alexander-arnold": {"name": "Trent Alexander-Arnold", "club": "Liverpool", "position": "RB", "nationality": "ENG", "popularity": 67},
    "trent alexander-arnold": {"name": "Trent Alexander-Arnold", "club": "Liverpool", "position": "RB", "nationality": "ENG", "popularity": 67},
    "trent": {"name": "Trent Alexander-Arnold", "club": "Liverpool", "position": "RB", "nationality": "ENG", "popularity": 67},
    "robertson": {"name": "Andrew Robertson", "club": "Liverpool", "position": "LB", "nationality": "SCO", "popularity": 58},
    "andrew robertson": {"name": "Andrew Robertson", "club": "Liverpool", "position": "LB", "nationality": "SCO", "popularity": 58},
    "jota": {"name": "Diogo Jota", "club": "Liverpool", "position": "LW", "nationality": "POR", "popularity": 60},
    "diogo jota": {"name": "Diogo Jota", "club": "Liverpool", "position": "LW", "nationality": "POR", "popularity": 60},
    "chiesa": {"name": "Federico Chiesa", "club": "Liverpool", "position": "RW", "nationality": "ITA", "popularity": 62},
    "federico chiesa": {"name": "Federico Chiesa", "club": "Liverpool", "position": "RW", "nationality": "ITA", "popularity": 62},
    
    # Chelsea
    "enzo fernandez": {"name": "Enzo Fernández", "club": "Chelsea", "position": "CM", "nationality": "ARG", "popularity": 65},
    "enzo": {"name": "Enzo Fernández", "club": "Chelsea", "position": "CM", "nationality": "ARG", "popularity": 65},
    "mudryk": {"name": "Mykhailo Mudryk", "club": "Chelsea", "position": "LW", "nationality": "UKR", "popularity": 58},
    "mykhailo mudryk": {"name": "Mykhailo Mudryk", "club": "Chelsea", "position": "LW", "nationality": "UKR", "popularity": 58},
    "jackson": {"name": "Nicolas Jackson", "club": "Chelsea", "position": "ST", "nationality": "SEN", "popularity": 57},
    "nicolas jackson": {"name": "Nicolas Jackson", "club": "Chelsea", "position": "ST", "nationality": "SEN", "popularity": 57},
    "caicedo": {"name": "Moisés Caicedo", "club": "Chelsea", "position": "CDM", "nationality": "ECU", "popularity": 60},
    "moises caicedo": {"name": "Moisés Caicedo", "club": "Chelsea", "position": "CDM", "nationality": "ECU", "popularity": 60},
    "sterling": {"name": "Raheem Sterling", "club": "Arsenal", "position": "LW", "nationality": "ENG", "popularity": 62},
    "raheem sterling": {"name": "Raheem Sterling", "club": "Arsenal", "position": "LW", "nationality": "ENG", "popularity": 62},
    "thiago silva": {"name": "Thiago Silva", "club": "Fluminense", "position": "CB", "nationality": "BRA", "popularity": 60},
    "reece james": {"name": "Reece James", "club": "Chelsea", "position": "RB", "nationality": "ENG", "popularity": 60},
    "james": {"name": "Reece James", "club": "Chelsea", "position": "RB", "nationality": "ENG", "popularity": 60},
    
    # Manchester City
    "grealish": {"name": "Jack Grealish", "club": "Manchester City", "position": "LW", "nationality": "ENG", "popularity": 65},
    "jack grealish": {"name": "Jack Grealish", "club": "Manchester City", "position": "LW", "nationality": "ENG", "popularity": 65},
    "bernardo silva": {"name": "Bernardo Silva", "club": "Manchester City", "position": "RW", "nationality": "POR", "popularity": 64},
    "bernardo": {"name": "Bernardo Silva", "club": "Manchester City", "position": "RW", "nationality": "POR", "popularity": 64},
    "dias": {"name": "Rúben Dias", "club": "Manchester City", "position": "CB", "nationality": "POR", "popularity": 62},
    "ruben dias": {"name": "Rúben Dias", "club": "Manchester City", "position": "CB", "nationality": "POR", "popularity": 62},
    "stones": {"name": "John Stones", "club": "Manchester City", "position": "CB", "nationality": "ENG", "popularity": 60},
    "john stones": {"name": "John Stones", "club": "Manchester City", "position": "CB", "nationality": "ENG", "popularity": 60},
    "walker": {"name": "Kyle Walker", "club": "Manchester City", "position": "RB", "nationality": "ENG", "popularity": 58},
    "kyle walker": {"name": "Kyle Walker", "club": "Manchester City", "position": "RB", "nationality": "ENG", "popularity": 58},
    "ederson": {"name": "Ederson", "club": "Manchester City", "position": "GK", "nationality": "BRA", "popularity": 60},
    "gvardiol": {"name": "Joško Gvardiol", "club": "Manchester City", "position": "CB", "nationality": "CRO", "popularity": 58},
    "josko gvardiol": {"name": "Joško Gvardiol", "club": "Manchester City", "position": "CB", "nationality": "CRO", "popularity": 58},
    "doku": {"name": "Jérémy Doku", "club": "Manchester City", "position": "RW", "nationality": "BEL", "popularity": 58},
    "jeremy doku": {"name": "Jérémy Doku", "club": "Manchester City", "position": "RW", "nationality": "BEL", "popularity": 58},
    "alvarez": {"name": "Julián Álvarez", "club": "Atlético Madrid", "position": "ST", "nationality": "ARG", "popularity": 65},
    "julian alvarez": {"name": "Julián Álvarez", "club": "Atlético Madrid", "position": "ST", "nationality": "ARG", "popularity": 65},
    
    # Tottenham
    "son": {"name": "Heung-Min Son", "club": "Tottenham", "position": "LW", "nationality": "KOR", "popularity": 61},
    "heung-min son": {"name": "Heung-Min Son", "club": "Tottenham", "position": "LW", "nationality": "KOR", "popularity": 61},
    "maddison": {"name": "James Maddison", "club": "Tottenham", "position": "CAM", "nationality": "ENG", "popularity": 58},
    "james maddison": {"name": "James Maddison", "club": "Tottenham", "position": "CAM", "nationality": "ENG", "popularity": 58},
    "romero": {"name": "Cristian Romero", "club": "Tottenham", "position": "CB", "nationality": "ARG", "popularity": 57},
    "cristian romero": {"name": "Cristian Romero", "club": "Tottenham", "position": "CB", "nationality": "ARG", "popularity": 57},
    "vicario": {"name": "Guglielmo Vicario", "club": "Tottenham", "position": "GK", "nationality": "ITA", "popularity": 55},
    "guglielmo vicario": {"name": "Guglielmo Vicario", "club": "Tottenham", "position": "GK", "nationality": "ITA", "popularity": 55},
    "van de ven": {"name": "Micky van de Ven", "club": "Tottenham", "position": "CB", "nationality": "NED", "popularity": 55},
    "micky van de ven": {"name": "Micky van de Ven", "club": "Tottenham", "position": "CB", "nationality": "NED", "popularity": 55},
    "richarlison": {"name": "Richarlison", "club": "Tottenham", "position": "ST", "nationality": "BRA", "popularity": 58},
    
    # Newcastle
    "isak": {"name": "Alexander Isak", "club": "Newcastle", "position": "ST", "nationality": "SWE", "popularity": 63},
    "alexander isak": {"name": "Alexander Isak", "club": "Newcastle", "position": "ST", "nationality": "SWE", "popularity": 63},
    "gordon": {"name": "Anthony Gordon", "club": "Newcastle", "position": "LW", "nationality": "ENG", "popularity": 58},
    "anthony gordon": {"name": "Anthony Gordon", "club": "Newcastle", "position": "LW", "nationality": "ENG", "popularity": 58},
    "guimaraes": {"name": "Bruno Guimarães", "club": "Newcastle", "position": "CM", "nationality": "BRA", "popularity": 62},
    "bruno guimaraes": {"name": "Bruno Guimarães", "club": "Newcastle", "position": "CM", "nationality": "BRA", "popularity": 62},
    "tonali": {"name": "Sandro Tonali", "club": "Newcastle", "position": "CM", "nationality": "ITA", "popularity": 58},
    "sandro tonali": {"name": "Sandro Tonali", "club": "Newcastle", "position": "CM", "nationality": "ITA", "popularity": 58},
    "trippier": {"name": "Kieran Trippier", "club": "Newcastle", "position": "RB", "nationality": "ENG", "popularity": 55},
    "kieran trippier": {"name": "Kieran Trippier", "club": "Newcastle", "position": "RB", "nationality": "ENG", "popularity": 55},
    
    # Aston Villa
    "watkins": {"name": "Ollie Watkins", "club": "Aston Villa", "position": "ST", "nationality": "ENG", "popularity": 60},
    "ollie watkins": {"name": "Ollie Watkins", "club": "Aston Villa", "position": "ST", "nationality": "ENG", "popularity": 60},
    "bailey": {"name": "Leon Bailey", "club": "Aston Villa", "position": "RW", "nationality": "JAM", "popularity": 52},
    "leon bailey": {"name": "Leon Bailey", "club": "Aston Villa", "position": "RW", "nationality": "JAM", "popularity": 52},
    "mcginn": {"name": "John McGinn", "club": "Aston Villa", "position": "CM", "nationality": "SCO", "popularity": 55},
    "john mcginn": {"name": "John McGinn", "club": "Aston Villa", "position": "CM", "nationality": "SCO", "popularity": 55},
    "douglas luiz": {"name": "Douglas Luiz", "club": "Juventus", "position": "CM", "nationality": "BRA", "popularity": 55},
    
    # West Ham
    "paqueta": {"name": "Lucas Paquetá", "club": "West Ham", "position": "CAM", "nationality": "BRA", "popularity": 58},
    "lucas paqueta": {"name": "Lucas Paquetá", "club": "West Ham", "position": "CAM", "nationality": "BRA", "popularity": 58},
    "bowen": {"name": "Jarrod Bowen", "club": "West Ham", "position": "RW", "nationality": "ENG", "popularity": 55},
    "jarrod bowen": {"name": "Jarrod Bowen", "club": "West Ham", "position": "RW", "nationality": "ENG", "popularity": 55},
    "kudus": {"name": "Mohammed Kudus", "club": "West Ham", "position": "CAM", "nationality": "GHA", "popularity": 57},
    "mohammed kudus": {"name": "Mohammed Kudus", "club": "West Ham", "position": "CAM", "nationality": "GHA", "popularity": 57},
    
    # ═══════════════════════════════════════════════════
    # SERIE A STARS (Popularity 55-69)
    # ═══════════════════════════════════════════════════
    
    "osimhen": {"name": "Victor Osimhen", "club": "Galatasaray", "position": "ST", "nationality": "NGA", "popularity": 68},
    "victor osimhen": {"name": "Victor Osimhen", "club": "Galatasaray", "position": "ST", "nationality": "NGA", "popularity": 68},
    "lautaro": {"name": "Lautaro Martínez", "club": "Inter", "position": "ST", "nationality": "ARG", "popularity": 67},
    "lautaro martinez": {"name": "Lautaro Martínez", "club": "Inter", "position": "ST", "nationality": "ARG", "popularity": 67},
    "vlahovic": {"name": "Dušan Vlahović", "club": "Juventus", "position": "ST", "nationality": "SRB", "popularity": 66},
    "dusan vlahovic": {"name": "Dušan Vlahović", "club": "Juventus", "position": "ST", "nationality": "SRB", "popularity": 66},
    "leao": {"name": "Rafael Leão", "club": "AC Milan", "position": "LW", "nationality": "POR", "popularity": 65},
    "rafael leao": {"name": "Rafael Leão", "club": "AC Milan", "position": "LW", "nationality": "POR", "popularity": 65},
    "bastoni": {"name": "Alessandro Bastoni", "club": "Inter", "position": "CB", "nationality": "ITA", "popularity": 64},
    "alessandro bastoni": {"name": "Alessandro Bastoni", "club": "Inter", "position": "CB", "nationality": "ITA", "popularity": 64},
    "barella": {"name": "Nicolò Barella", "club": "Inter", "position": "CM", "nationality": "ITA", "popularity": 63},
    "nicolo barella": {"name": "Nicolò Barella", "club": "Inter", "position": "CM", "nationality": "ITA", "popularity": 63},
    "lukaku": {"name": "Romelu Lukaku", "club": "Napoli", "position": "ST", "nationality": "BEL", "popularity": 61},
    "romelu lukaku": {"name": "Romelu Lukaku", "club": "Napoli", "position": "ST", "nationality": "BEL", "popularity": 61},
    "kvaratskhelia": {"name": "Khvicha Kvaratskhelia", "club": "Napoli", "position": "LW", "nationality": "GEO", "popularity": 65},
    "khvicha kvaratskhelia": {"name": "Khvicha Kvaratskhelia", "club": "Napoli", "position": "LW", "nationality": "GEO", "popularity": 65},
    "kvara": {"name": "Khvicha Kvaratskhelia", "club": "Napoli", "position": "LW", "nationality": "GEO", "popularity": 65},
    "dybala": {"name": "Paulo Dybala", "club": "Roma", "position": "CAM", "nationality": "ARG", "popularity": 62},
    "paulo dybala": {"name": "Paulo Dybala", "club": "Roma", "position": "CAM", "nationality": "ARG", "popularity": 62},
    "maignan": {"name": "Mike Maignan", "club": "AC Milan", "position": "GK", "nationality": "FRA", "popularity": 60},
    "mike maignan": {"name": "Mike Maignan", "club": "AC Milan", "position": "GK", "nationality": "FRA", "popularity": 60},
    "thuram": {"name": "Marcus Thuram", "club": "Inter", "position": "ST", "nationality": "FRA", "popularity": 62},
    "marcus thuram": {"name": "Marcus Thuram", "club": "Inter", "position": "ST", "nationality": "FRA", "popularity": 62},
    "calhanoglu": {"name": "Hakan Çalhanoğlu", "club": "Inter", "position": "CM", "nationality": "TUR", "popularity": 58},
    "hakan calhanoglu": {"name": "Hakan Çalhanoğlu", "club": "Inter", "position": "CM", "nationality": "TUR", "popularity": 58},
    "theo hernandez": {"name": "Theo Hernández", "club": "AC Milan", "position": "LB", "nationality": "FRA", "popularity": 62},
    "theo": {"name": "Theo Hernández", "club": "AC Milan", "position": "LB", "nationality": "FRA", "popularity": 62},
    "pulisic": {"name": "Christian Pulisic", "club": "AC Milan", "position": "RW", "nationality": "USA", "popularity": 60},
    "christian pulisic": {"name": "Christian Pulisic", "club": "AC Milan", "position": "RW", "nationality": "USA", "popularity": 60},
    "bremer": {"name": "Gleison Bremer", "club": "Juventus", "position": "CB", "nationality": "BRA", "popularity": 58},
    "gleison bremer": {"name": "Gleison Bremer", "club": "Juventus", "position": "CB", "nationality": "BRA", "popularity": 58},
    "kone": {"name": "Manu Koné", "club": "Roma", "position": "CM", "nationality": "FRA", "popularity": 55},
    "manu kone": {"name": "Manu Koné", "club": "Roma", "position": "CM", "nationality": "FRA", "popularity": 55},
    "zirkzee": {"name": "Joshua Zirkzee", "club": "Manchester United", "position": "ST", "nationality": "NED", "popularity": 58},
    "joshua zirkzee": {"name": "Joshua Zirkzee", "club": "Manchester United", "position": "ST", "nationality": "NED", "popularity": 58},
    "sommer": {"name": "Yann Sommer", "club": "Inter", "position": "GK", "nationality": "SUI", "popularity": 55},
    "yann sommer": {"name": "Yann Sommer", "club": "Inter", "position": "GK", "nationality": "SUI", "popularity": 55},
    
    # ═══════════════════════════════════════════════════
    # LA LIGA STARS (Popularity 55-69)
    # ═══════════════════════════════════════════════════
    
    # Real Madrid
    "valverde": {"name": "Federico Valverde", "club": "Real Madrid", "position": "CM", "nationality": "URU", "popularity": 68},
    "fede valverde": {"name": "Federico Valverde", "club": "Real Madrid", "position": "CM", "nationality": "URU", "popularity": 68},
    "federico valverde": {"name": "Federico Valverde", "club": "Real Madrid", "position": "CM", "nationality": "URU", "popularity": 68},
    "tchouameni": {"name": "Aurélien Tchouaméni", "club": "Real Madrid", "position": "CDM", "nationality": "FRA", "popularity": 65},
    "aurelien tchouameni": {"name": "Aurélien Tchouaméni", "club": "Real Madrid", "position": "CDM", "nationality": "FRA", "popularity": 65},
    "camavinga": {"name": "Eduardo Camavinga", "club": "Real Madrid", "position": "CM", "nationality": "FRA", "popularity": 63},
    "eduardo camavinga": {"name": "Eduardo Camavinga", "club": "Real Madrid", "position": "CM", "nationality": "FRA", "popularity": 63},
    "courtois": {"name": "Thibaut Courtois", "club": "Real Madrid", "position": "GK", "nationality": "BEL", "popularity": 64},
    "thibaut courtois": {"name": "Thibaut Courtois", "club": "Real Madrid", "position": "GK", "nationality": "BEL", "popularity": 64},
    "carvajal": {"name": "Dani Carvajal", "club": "Real Madrid", "position": "RB", "nationality": "ESP", "popularity": 60},
    "dani carvajal": {"name": "Dani Carvajal", "club": "Real Madrid", "position": "RB", "nationality": "ESP", "popularity": 60},
    "mendy": {"name": "Ferland Mendy", "club": "Real Madrid", "position": "LB", "nationality": "FRA", "popularity": 58},
    "ferland mendy": {"name": "Ferland Mendy", "club": "Real Madrid", "position": "LB", "nationality": "FRA", "popularity": 58},
    "militao": {"name": "Éder Militão", "club": "Real Madrid", "position": "CB", "nationality": "BRA", "popularity": 60},
    "eder militao": {"name": "Éder Militão", "club": "Real Madrid", "position": "CB", "nationality": "BRA", "popularity": 60},
    "alaba": {"name": "David Alaba", "club": "Real Madrid", "position": "CB", "nationality": "AUT", "popularity": 62},
    "david alaba": {"name": "David Alaba", "club": "Real Madrid", "position": "CB", "nationality": "AUT", "popularity": 62},
    "endrick": {"name": "Endrick", "club": "Real Madrid", "position": "ST", "nationality": "BRA", "popularity": 63},
    "arda guler": {"name": "Arda Güler", "club": "Real Madrid", "position": "CAM", "nationality": "TUR", "popularity": 60},
    "arda güler": {"name": "Arda Güler", "club": "Real Madrid", "position": "CAM", "nationality": "TUR", "popularity": 60},
    "guler": {"name": "Arda Güler", "club": "Real Madrid", "position": "CAM", "nationality": "TUR", "popularity": 60},
    
    # Barcelona
    "ter stegen": {"name": "Marc-André ter Stegen", "club": "Barcelona", "position": "GK", "nationality": "GER", "popularity": 63},
    "araujo": {"name": "Ronald Araújo", "club": "Barcelona", "position": "CB", "nationality": "URU", "popularity": 62},
    "ronald araujo": {"name": "Ronald Araújo", "club": "Barcelona", "position": "CB", "nationality": "URU", "popularity": 62},
    "kounde": {"name": "Jules Koundé", "club": "Barcelona", "position": "RB", "nationality": "FRA", "popularity": 60},
    "jules kounde": {"name": "Jules Koundé", "club": "Barcelona", "position": "RB", "nationality": "FRA", "popularity": 60},
    "balde": {"name": "Alejandro Balde", "club": "Barcelona", "position": "LB", "nationality": "ESP", "popularity": 55},
    "alejandro balde": {"name": "Alejandro Balde", "club": "Barcelona", "position": "LB", "nationality": "ESP", "popularity": 55},
    "de jong": {"name": "Frenkie de Jong", "club": "Barcelona", "position": "CM", "nationality": "NED", "popularity": 62},
    "frenkie de jong": {"name": "Frenkie de Jong", "club": "Barcelona", "position": "CM", "nationality": "NED", "popularity": 62},
    "raphinha": {"name": "Raphinha", "club": "Barcelona", "position": "RW", "nationality": "BRA", "popularity": 60},
    "ferran torres": {"name": "Ferran Torres", "club": "Barcelona", "position": "RW", "nationality": "ESP", "popularity": 55},
    "ferran": {"name": "Ferran Torres", "club": "Barcelona", "position": "RW", "nationality": "ESP", "popularity": 55},
    "cubarsi": {"name": "Pau Cubarsí", "club": "Barcelona", "position": "CB", "nationality": "ESP", "popularity": 55},
    "pau cubarsi": {"name": "Pau Cubarsí", "club": "Barcelona", "position": "CB", "nationality": "ESP", "popularity": 55},
    
    # Atlético Madrid
    "griezmann": {"name": "Antoine Griezmann", "club": "Atlético Madrid", "position": "ST", "nationality": "FRA", "popularity": 68},
    "antoine griezmann": {"name": "Antoine Griezmann", "club": "Atlético Madrid", "position": "ST", "nationality": "FRA", "popularity": 68},
    "oblak": {"name": "Jan Oblak", "club": "Atlético Madrid", "position": "GK", "nationality": "SVN", "popularity": 62},
    "jan oblak": {"name": "Jan Oblak", "club": "Atlético Madrid", "position": "GK", "nationality": "SVN", "popularity": 62},
    "de paul": {"name": "Rodrigo De Paul", "club": "Atlético Madrid", "position": "CM", "nationality": "ARG", "popularity": 58},
    "rodrigo de paul": {"name": "Rodrigo De Paul", "club": "Atlético Madrid", "position": "CM", "nationality": "ARG", "popularity": 58},
    "morata": {"name": "Álvaro Morata", "club": "AC Milan", "position": "ST", "nationality": "ESP", "popularity": 58},
    "alvaro morata": {"name": "Álvaro Morata", "club": "AC Milan", "position": "ST", "nationality": "ESP", "popularity": 58},
    
    # ═══════════════════════════════════════════════════
    # LIGUE 1 / PSG (Popularity 55-69)
    # ═══════════════════════════════════════════════════
    
    "dembele": {"name": "Ousmane Dembélé", "club": "PSG", "position": "RW", "nationality": "FRA", "popularity": 65},
    "ousmane dembele": {"name": "Ousmane Dembélé", "club": "PSG", "position": "RW", "nationality": "FRA", "popularity": 65},
    "donnarumma": {"name": "Gianluigi Donnarumma", "club": "PSG", "position": "GK", "nationality": "ITA", "popularity": 59},
    "gianluigi donnarumma": {"name": "Gianluigi Donnarumma", "club": "PSG", "position": "GK", "nationality": "ITA", "popularity": 59},
    "hakimi": {"name": "Achraf Hakimi", "club": "PSG", "position": "RB", "nationality": "MAR", "popularity": 62},
    "achraf hakimi": {"name": "Achraf Hakimi", "club": "PSG", "position": "RB", "nationality": "MAR", "popularity": 62},
    "marquinhos": {"name": "Marquinhos", "club": "PSG", "position": "CB", "nationality": "BRA", "popularity": 60},
    "vitinha": {"name": "Vitinha", "club": "PSG", "position": "CM", "nationality": "POR", "popularity": 58},
    "asensio": {"name": "Marco Asensio", "club": "PSG", "position": "RW", "nationality": "ESP", "popularity": 58},
    "marco asensio": {"name": "Marco Asensio", "club": "PSG", "position": "RW", "nationality": "ESP", "popularity": 58},
    "ramos": {"name": "Sergio Ramos", "club": "Sevilla", "position": "CB", "nationality": "ESP", "popularity": 65},
    "sergio ramos": {"name": "Sergio Ramos", "club": "Sevilla", "position": "CB", "nationality": "ESP", "popularity": 65},
    "barcola": {"name": "Bradley Barcola", "club": "PSG", "position": "LW", "nationality": "FRA", "popularity": 55},
    "bradley barcola": {"name": "Bradley Barcola", "club": "PSG", "position": "LW", "nationality": "FRA", "popularity": 55},
    "goncalo ramos": {"name": "Gonçalo Ramos", "club": "PSG", "position": "ST", "nationality": "POR", "popularity": 55},
    
    # ═══════════════════════════════════════════════════
    # TRAINER (Popularity 60-80)
    # ═══════════════════════════════════════════════════
    
    "guardiola": {"name": "Pep Guardiola", "club": "Manchester City", "position": "Manager", "nationality": "ESP", "popularity": 80},
    "pep guardiola": {"name": "Pep Guardiola", "club": "Manchester City", "position": "Manager", "nationality": "ESP", "popularity": 80},
    "pep": {"name": "Pep Guardiola", "club": "Manchester City", "position": "Manager", "nationality": "ESP", "popularity": 80},
    "ancelotti": {"name": "Carlo Ancelotti", "club": "Real Madrid", "position": "Manager", "nationality": "ITA", "popularity": 75},
    "carlo ancelotti": {"name": "Carlo Ancelotti", "club": "Real Madrid", "position": "Manager", "nationality": "ITA", "popularity": 75},
    "klopp": {"name": "Jürgen Klopp", "club": "Retired", "position": "Manager", "nationality": "GER", "popularity": 72},
    "jurgen klopp": {"name": "Jürgen Klopp", "club": "Retired", "position": "Manager", "nationality": "GER", "popularity": 72},
    "jürgen klopp": {"name": "Jürgen Klopp", "club": "Retired", "position": "Manager", "nationality": "GER", "popularity": 72},
    "arteta": {"name": "Mikel Arteta", "club": "Arsenal", "position": "Manager", "nationality": "ESP", "popularity": 68},
    "mikel arteta": {"name": "Mikel Arteta", "club": "Arsenal", "position": "Manager", "nationality": "ESP", "popularity": 68},
    "tuchel": {"name": "Thomas Tuchel", "club": "England", "position": "Manager", "nationality": "GER", "popularity": 65},
    "thomas tuchel": {"name": "Thomas Tuchel", "club": "England", "position": "Manager", "nationality": "GER", "popularity": 65},
    "nagelsmann": {"name": "Julian Nagelsmann", "club": "Germany", "position": "Manager", "nationality": "GER", "popularity": 62},
    "julian nagelsmann": {"name": "Julian Nagelsmann", "club": "Germany", "position": "Manager", "nationality": "GER", "popularity": 62},
    "ten hag": {"name": "Erik ten Hag", "club": "Manchester United", "position": "Manager", "nationality": "NED", "popularity": 60},
    "erik ten hag": {"name": "Erik ten Hag", "club": "Manchester United", "position": "Manager", "nationality": "NED", "popularity": 60},
    "slot": {"name": "Arne Slot", "club": "Liverpool", "position": "Manager", "nationality": "NED", "popularity": 58},
    "arne slot": {"name": "Arne Slot", "club": "Liverpool", "position": "Manager", "nationality": "NED", "popularity": 58},
    "xabi alonso": {"name": "Xabi Alonso", "club": "Bayer Leverkusen", "position": "Manager", "nationality": "ESP", "popularity": 70},
    "kompany": {"name": "Vincent Kompany", "club": "Bayern München", "position": "Manager", "nationality": "BEL", "popularity": 62},
    "vincent kompany": {"name": "Vincent Kompany", "club": "Bayern München", "position": "Manager", "nationality": "BEL", "popularity": 62},
    "flick": {"name": "Hansi Flick", "club": "Barcelona", "position": "Manager", "nationality": "GER", "popularity": 60},
    "hansi flick": {"name": "Hansi Flick", "club": "Barcelona", "position": "Manager", "nationality": "GER", "popularity": 60},
    "simeone": {"name": "Diego Simeone", "club": "Atlético Madrid", "position": "Manager", "nationality": "ARG", "popularity": 65},
    "diego simeone": {"name": "Diego Simeone", "club": "Atlético Madrid", "position": "Manager", "nationality": "ARG", "popularity": 65},
    "mourinho": {"name": "José Mourinho", "club": "Fenerbahce", "position": "Manager", "nationality": "POR", "popularity": 68},
    "jose mourinho": {"name": "José Mourinho", "club": "Fenerbahce", "position": "Manager", "nationality": "POR", "popularity": 68},
    "inzaghi": {"name": "Simone Inzaghi", "club": "Inter", "position": "Manager", "nationality": "ITA", "popularity": 58},
    "simone inzaghi": {"name": "Simone Inzaghi", "club": "Inter", "position": "Manager", "nationality": "ITA", "popularity": 58},
    "allegri": {"name": "Massimiliano Allegri", "club": "Free Agent", "position": "Manager", "nationality": "ITA", "popularity": 55},
    "conte": {"name": "Antonio Conte", "club": "Napoli", "position": "Manager", "nationality": "ITA", "popularity": 65},
    "antonio conte": {"name": "Antonio Conte", "club": "Napoli", "position": "Manager", "nationality": "ITA", "popularity": 65},
}


# =============================================================================
# CLUB-DATENBANK (300+ Clubs)
# =============================================================================

CLUBS_DB = {
    # ═══════════════════════════════════════════════════
    # TIER 1 - WELTSPITZE (Popularity 90-100)
    # ═══════════════════════════════════════════════════
    
    "real madrid": {"name": "Real Madrid", "country": "ESP", "league": "La Liga", "popularity": 100},
    "real": {"name": "Real Madrid", "country": "ESP", "league": "La Liga", "popularity": 100},
    "madrid": {"name": "Real Madrid", "country": "ESP", "league": "La Liga", "popularity": 100},
    "los blancos": {"name": "Real Madrid", "country": "ESP", "league": "La Liga", "popularity": 100},
    "barcelona": {"name": "FC Barcelona", "country": "ESP", "league": "La Liga", "popularity": 98},
    "barca": {"name": "FC Barcelona", "country": "ESP", "league": "La Liga", "popularity": 98},
    "barça": {"name": "FC Barcelona", "country": "ESP", "league": "La Liga", "popularity": 98},
    "fc barcelona": {"name": "FC Barcelona", "country": "ESP", "league": "La Liga", "popularity": 98},
    "blaugrana": {"name": "FC Barcelona", "country": "ESP", "league": "La Liga", "popularity": 98},
    "manchester city": {"name": "Manchester City", "country": "ENG", "league": "Premier League", "popularity": 97},
    "man city": {"name": "Manchester City", "country": "ENG", "league": "Premier League", "popularity": 97},
    "city": {"name": "Manchester City", "country": "ENG", "league": "Premier League", "popularity": 97},
    "the citizens": {"name": "Manchester City", "country": "ENG", "league": "Premier League", "popularity": 97},
    "liverpool": {"name": "FC Liverpool", "country": "ENG", "league": "Premier League", "popularity": 96},
    "fc liverpool": {"name": "FC Liverpool", "country": "ENG", "league": "Premier League", "popularity": 96},
    "the reds": {"name": "FC Liverpool", "country": "ENG", "league": "Premier League", "popularity": 96},
    "bayern": {"name": "FC Bayern München", "country": "GER", "league": "Bundesliga", "popularity": 95},
    "bayern munich": {"name": "FC Bayern München", "country": "GER", "league": "Bundesliga", "popularity": 95},
    "bayern münchen": {"name": "FC Bayern München", "country": "GER", "league": "Bundesliga", "popularity": 95},
    "fc bayern": {"name": "FC Bayern München", "country": "GER", "league": "Bundesliga", "popularity": 95},
    "fcb": {"name": "FC Bayern München", "country": "GER", "league": "Bundesliga", "popularity": 95},
    "psg": {"name": "Paris Saint-Germain", "country": "FRA", "league": "Ligue 1", "popularity": 94},
    "paris saint-germain": {"name": "Paris Saint-Germain", "country": "FRA", "league": "Ligue 1", "popularity": 94},
    "paris": {"name": "Paris Saint-Germain", "country": "FRA", "league": "Ligue 1", "popularity": 94},
    "manchester united": {"name": "Manchester United", "country": "ENG", "league": "Premier League", "popularity": 93},
    "man united": {"name": "Manchester United", "country": "ENG", "league": "Premier League", "popularity": 93},
    "man utd": {"name": "Manchester United", "country": "ENG", "league": "Premier League", "popularity": 93},
    "united": {"name": "Manchester United", "country": "ENG", "league": "Premier League", "popularity": 93},
    "the red devils": {"name": "Manchester United", "country": "ENG", "league": "Premier League", "popularity": 93},
    "chelsea": {"name": "FC Chelsea", "country": "ENG", "league": "Premier League", "popularity": 92},
    "fc chelsea": {"name": "FC Chelsea", "country": "ENG", "league": "Premier League", "popularity": 92},
    "the blues": {"name": "FC Chelsea", "country": "ENG", "league": "Premier League", "popularity": 92},
    "arsenal": {"name": "FC Arsenal", "country": "ENG", "league": "Premier League", "popularity": 91},
    "fc arsenal": {"name": "FC Arsenal", "country": "ENG", "league": "Premier League", "popularity": 91},
    "the gunners": {"name": "FC Arsenal", "country": "ENG", "league": "Premier League", "popularity": 91},
    
    # ═══════════════════════════════════════════════════
    # TIER 2 - TOP CLUBS (Popularity 80-89)
    # ═══════════════════════════════════════════════════
    
    "juventus": {"name": "Juventus Turin", "country": "ITA", "league": "Serie A", "popularity": 89},
    "juve": {"name": "Juventus Turin", "country": "ITA", "league": "Serie A", "popularity": 89},
    "juventus turin": {"name": "Juventus Turin", "country": "ITA", "league": "Serie A", "popularity": 89},
    "la vecchia signora": {"name": "Juventus Turin", "country": "ITA", "league": "Serie A", "popularity": 89},
    "dortmund": {"name": "Borussia Dortmund", "country": "GER", "league": "Bundesliga", "popularity": 88},
    "borussia dortmund": {"name": "Borussia Dortmund", "country": "GER", "league": "Bundesliga", "popularity": 88},
    "bvb": {"name": "Borussia Dortmund", "country": "GER", "league": "Bundesliga", "popularity": 88},
    "inter": {"name": "Inter Mailand", "country": "ITA", "league": "Serie A", "popularity": 87},
    "inter milan": {"name": "Inter Mailand", "country": "ITA", "league": "Serie A", "popularity": 87},
    "inter mailand": {"name": "Inter Mailand", "country": "ITA", "league": "Serie A", "popularity": 87},
    "internazionale": {"name": "Inter Mailand", "country": "ITA", "league": "Serie A", "popularity": 87},
    "nerazzurri": {"name": "Inter Mailand", "country": "ITA", "league": "Serie A", "popularity": 87},
    "milan": {"name": "AC Milan", "country": "ITA", "league": "Serie A", "popularity": 86},
    "ac milan": {"name": "AC Milan", "country": "ITA", "league": "Serie A", "popularity": 86},
    "ac mailand": {"name": "AC Milan", "country": "ITA", "league": "Serie A", "popularity": 86},
    "rossoneri": {"name": "AC Milan", "country": "ITA", "league": "Serie A", "popularity": 86},
    "atletico": {"name": "Atlético Madrid", "country": "ESP", "league": "La Liga", "popularity": 85},
    "atletico madrid": {"name": "Atlético Madrid", "country": "ESP", "league": "La Liga", "popularity": 85},
    "atlético madrid": {"name": "Atlético Madrid", "country": "ESP", "league": "La Liga", "popularity": 85},
    "atleti": {"name": "Atlético Madrid", "country": "ESP", "league": "La Liga", "popularity": 85},
    "tottenham": {"name": "Tottenham Hotspur", "country": "ENG", "league": "Premier League", "popularity": 84},
    "spurs": {"name": "Tottenham Hotspur", "country": "ENG", "league": "Premier League", "popularity": 84},
    "tottenham hotspur": {"name": "Tottenham Hotspur", "country": "ENG", "league": "Premier League", "popularity": 84},
    "napoli": {"name": "SSC Neapel", "country": "ITA", "league": "Serie A", "popularity": 83},
    "ssc napoli": {"name": "SSC Neapel", "country": "ITA", "league": "Serie A", "popularity": 83},
    "neapel": {"name": "SSC Neapel", "country": "ITA", "league": "Serie A", "popularity": 83},
    "partenopei": {"name": "SSC Neapel", "country": "ITA", "league": "Serie A", "popularity": 83},
    "roma": {"name": "AS Rom", "country": "ITA", "league": "Serie A", "popularity": 82},
    "as roma": {"name": "AS Rom", "country": "ITA", "league": "Serie A", "popularity": 82},
    "as rom": {"name": "AS Rom", "country": "ITA", "league": "Serie A", "popularity": 82},
    "giallorossi": {"name": "AS Rom", "country": "ITA", "league": "Serie A", "popularity": 82},
    "newcastle": {"name": "Newcastle United", "country": "ENG", "league": "Premier League", "popularity": 81},
    "newcastle united": {"name": "Newcastle United", "country": "ENG", "league": "Premier League", "popularity": 81},
    "the magpies": {"name": "Newcastle United", "country": "ENG", "league": "Premier League", "popularity": 81},
    
    # ═══════════════════════════════════════════════════
    # TIER 3 - BEKANNTE CLUBS (Popularity 70-79)
    # ═══════════════════════════════════════════════════
    
    "west ham": {"name": "West Ham United", "country": "ENG", "league": "Premier League", "popularity": 79},
    "west ham united": {"name": "West Ham United", "country": "ENG", "league": "Premier League", "popularity": 79},
    "the hammers": {"name": "West Ham United", "country": "ENG", "league": "Premier League", "popularity": 79},
    "aston villa": {"name": "Aston Villa", "country": "ENG", "league": "Premier League", "popularity": 78},
    "villa": {"name": "Aston Villa", "country": "ENG", "league": "Premier League", "popularity": 78},
    "the villans": {"name": "Aston Villa", "country": "ENG", "league": "Premier League", "popularity": 78},
    "brighton": {"name": "Brighton & Hove Albion", "country": "ENG", "league": "Premier League", "popularity": 77},
    "brighton & hove albion": {"name": "Brighton & Hove Albion", "country": "ENG", "league": "Premier League", "popularity": 77},
    "rb leipzig": {"name": "RB Leipzig", "country": "GER", "league": "Bundesliga", "popularity": 76},
    "leipzig": {"name": "RB Leipzig", "country": "GER", "league": "Bundesliga", "popularity": 76},
    "leverkusen": {"name": "Bayer Leverkusen", "country": "GER", "league": "Bundesliga", "popularity": 75},
    "bayer leverkusen": {"name": "Bayer Leverkusen", "country": "GER", "league": "Bundesliga", "popularity": 75},
    "bayer 04": {"name": "Bayer Leverkusen", "country": "GER", "league": "Bundesliga", "popularity": 75},
    "werkself": {"name": "Bayer Leverkusen", "country": "GER", "league": "Bundesliga", "popularity": 75},
    "frankfurt": {"name": "Eintracht Frankfurt", "country": "GER", "league": "Bundesliga", "popularity": 74},
    "eintracht frankfurt": {"name": "Eintracht Frankfurt", "country": "GER", "league": "Bundesliga", "popularity": 74},
    "eintracht": {"name": "Eintracht Frankfurt", "country": "GER", "league": "Bundesliga", "popularity": 74},
    "sge": {"name": "Eintracht Frankfurt", "country": "GER", "league": "Bundesliga", "popularity": 74},
    "sevilla": {"name": "FC Sevilla", "country": "ESP", "league": "La Liga", "popularity": 73},
    "fc sevilla": {"name": "FC Sevilla", "country": "ESP", "league": "La Liga", "popularity": 73},
    "benfica": {"name": "Benfica Lissabon", "country": "POR", "league": "Primeira Liga", "popularity": 72},
    "benfica lissabon": {"name": "Benfica Lissabon", "country": "POR", "league": "Primeira Liga", "popularity": 72},
    "sl benfica": {"name": "Benfica Lissabon", "country": "POR", "league": "Primeira Liga", "popularity": 72},
    "porto": {"name": "FC Porto", "country": "POR", "league": "Primeira Liga", "popularity": 71},
    "fc porto": {"name": "FC Porto", "country": "POR", "league": "Primeira Liga", "popularity": 71},
    "everton": {"name": "FC Everton", "country": "ENG", "league": "Premier League", "popularity": 70},
    "fc everton": {"name": "FC Everton", "country": "ENG", "league": "Premier League", "popularity": 70},
    "the toffees": {"name": "FC Everton", "country": "ENG", "league": "Premier League", "popularity": 70},
    
    # ═══════════════════════════════════════════════════
    # BUNDESLIGA (Popularity 60-69)
    # ═══════════════════════════════════════════════════
    
    "gladbach": {"name": "Borussia Mönchengladbach", "country": "GER", "league": "Bundesliga", "popularity": 68},
    "borussia mönchengladbach": {"name": "Borussia Mönchengladbach", "country": "GER", "league": "Bundesliga", "popularity": 68},
    "borussia monchengladbach": {"name": "Borussia Mönchengladbach", "country": "GER", "league": "Bundesliga", "popularity": 68},
    "mönchengladbach": {"name": "Borussia Mönchengladbach", "country": "GER", "league": "Bundesliga", "popularity": 68},
    "monchengladbach": {"name": "Borussia Mönchengladbach", "country": "GER", "league": "Bundesliga", "popularity": 68},
    "die fohlen": {"name": "Borussia Mönchengladbach", "country": "GER", "league": "Bundesliga", "popularity": 68},
    "wolfsburg": {"name": "VfL Wolfsburg", "country": "GER", "league": "Bundesliga", "popularity": 67},
    "vfl wolfsburg": {"name": "VfL Wolfsburg", "country": "GER", "league": "Bundesliga", "popularity": 67},
    "die wölfe": {"name": "VfL Wolfsburg", "country": "GER", "league": "Bundesliga", "popularity": 67},
    "freiburg": {"name": "SC Freiburg", "country": "GER", "league": "Bundesliga", "popularity": 66},
    "sc freiburg": {"name": "SC Freiburg", "country": "GER", "league": "Bundesliga", "popularity": 66},
    "union berlin": {"name": "1. FC Union Berlin", "country": "GER", "league": "Bundesliga", "popularity": 65},
    "union": {"name": "1. FC Union Berlin", "country": "GER", "league": "Bundesliga", "popularity": 65},
    "eisern union": {"name": "1. FC Union Berlin", "country": "GER", "league": "Bundesliga", "popularity": 65},
    "hoffenheim": {"name": "TSG Hoffenheim", "country": "GER", "league": "Bundesliga", "popularity": 64},
    "tsg hoffenheim": {"name": "TSG Hoffenheim", "country": "GER", "league": "Bundesliga", "popularity": 64},
    "mainz": {"name": "1. FSV Mainz 05", "country": "GER", "league": "Bundesliga", "popularity": 63},
    "mainz 05": {"name": "1. FSV Mainz 05", "country": "GER", "league": "Bundesliga", "popularity": 63},
    "koln": {"name": "1. FC Köln", "country": "GER", "league": "Bundesliga", "popularity": 62},
    "köln": {"name": "1. FC Köln", "country": "GER", "league": "Bundesliga", "popularity": 62},
    "fc koln": {"name": "1. FC Köln", "country": "GER", "league": "Bundesliga", "popularity": 62},
    "fc köln": {"name": "1. FC Köln", "country": "GER", "league": "Bundesliga", "popularity": 62},
    "der effzeh": {"name": "1. FC Köln", "country": "GER", "league": "Bundesliga", "popularity": 62},
    "augsburg": {"name": "FC Augsburg", "country": "GER", "league": "Bundesliga", "popularity": 61},
    "fc augsburg": {"name": "FC Augsburg", "country": "GER", "league": "Bundesliga", "popularity": 61},
    "fca": {"name": "FC Augsburg", "country": "GER", "league": "Bundesliga", "popularity": 61},
    "stuttgart": {"name": "VfB Stuttgart", "country": "GER", "league": "Bundesliga", "popularity": 64},
    "vfb stuttgart": {"name": "VfB Stuttgart", "country": "GER", "league": "Bundesliga", "popularity": 64},
    "vfb": {"name": "VfB Stuttgart", "country": "GER", "league": "Bundesliga", "popularity": 64},
    "werder": {"name": "Werder Bremen", "country": "GER", "league": "Bundesliga", "popularity": 63},
    "werder bremen": {"name": "Werder Bremen", "country": "GER", "league": "Bundesliga", "popularity": 63},
    "bremen": {"name": "Werder Bremen", "country": "GER", "league": "Bundesliga", "popularity": 63},
    "bochum": {"name": "VfL Bochum", "country": "GER", "league": "Bundesliga", "popularity": 58},
    "vfl bochum": {"name": "VfL Bochum", "country": "GER", "league": "Bundesliga", "popularity": 58},
    "heidenheim": {"name": "1. FC Heidenheim", "country": "GER", "league": "Bundesliga", "popularity": 55},
    "fc heidenheim": {"name": "1. FC Heidenheim", "country": "GER", "league": "Bundesliga", "popularity": 55},
    "darmstadt": {"name": "SV Darmstadt 98", "country": "GER", "league": "2. Bundesliga", "popularity": 52},
    "darmstadt 98": {"name": "SV Darmstadt 98", "country": "GER", "league": "2. Bundesliga", "popularity": 52},
    
    # ═══════════════════════════════════════════════════
    # WEITERE LA LIGA (Popularity 55-69)
    # ═══════════════════════════════════════════════════
    
    "real sociedad": {"name": "Real Sociedad", "country": "ESP", "league": "La Liga", "popularity": 65},
    "sociedad": {"name": "Real Sociedad", "country": "ESP", "league": "La Liga", "popularity": 65},
    "villarreal": {"name": "FC Villarreal", "country": "ESP", "league": "La Liga", "popularity": 63},
    "fc villarreal": {"name": "FC Villarreal", "country": "ESP", "league": "La Liga", "popularity": 63},
    "yellow submarine": {"name": "FC Villarreal", "country": "ESP", "league": "La Liga", "popularity": 63},
    "real betis": {"name": "Real Betis", "country": "ESP", "league": "La Liga", "popularity": 62},
    "betis": {"name": "Real Betis", "country": "ESP", "league": "La Liga", "popularity": 62},
    "athletic bilbao": {"name": "Athletic Bilbao", "country": "ESP", "league": "La Liga", "popularity": 62},
    "athletic": {"name": "Athletic Bilbao", "country": "ESP", "league": "La Liga", "popularity": 62},
    "bilbao": {"name": "Athletic Bilbao", "country": "ESP", "league": "La Liga", "popularity": 62},
    "valencia": {"name": "FC Valencia", "country": "ESP", "league": "La Liga", "popularity": 60},
    "fc valencia": {"name": "FC Valencia", "country": "ESP", "league": "La Liga", "popularity": 60},
    "celta vigo": {"name": "Celta Vigo", "country": "ESP", "league": "La Liga", "popularity": 55},
    "celta": {"name": "Celta Vigo", "country": "ESP", "league": "La Liga", "popularity": 55},
    "girona": {"name": "FC Girona", "country": "ESP", "league": "La Liga", "popularity": 58},
    "fc girona": {"name": "FC Girona", "country": "ESP", "league": "La Liga", "popularity": 58},
    
    # ═══════════════════════════════════════════════════
    # WEITERE PREMIER LEAGUE (Popularity 55-69)
    # ═══════════════════════════════════════════════════
    
    "wolves": {"name": "Wolverhampton Wanderers", "country": "ENG", "league": "Premier League", "popularity": 60},
    "wolverhampton": {"name": "Wolverhampton Wanderers", "country": "ENG", "league": "Premier League", "popularity": 60},
    "crystal palace": {"name": "Crystal Palace", "country": "ENG", "league": "Premier League", "popularity": 58},
    "palace": {"name": "Crystal Palace", "country": "ENG", "league": "Premier League", "popularity": 58},
    "brentford": {"name": "FC Brentford", "country": "ENG", "league": "Premier League", "popularity": 55},
    "fc brentford": {"name": "FC Brentford", "country": "ENG", "league": "Premier League", "popularity": 55},
    "the bees": {"name": "FC Brentford", "country": "ENG", "league": "Premier League", "popularity": 55},
    "fulham": {"name": "FC Fulham", "country": "ENG", "league": "Premier League", "popularity": 55},
    "fc fulham": {"name": "FC Fulham", "country": "ENG", "league": "Premier League", "popularity": 55},
    "nottingham forest": {"name": "Nottingham Forest", "country": "ENG", "league": "Premier League", "popularity": 58},
    "forest": {"name": "Nottingham Forest", "country": "ENG", "league": "Premier League", "popularity": 58},
    "bournemouth": {"name": "AFC Bournemouth", "country": "ENG", "league": "Premier League", "popularity": 55},
    "afc bournemouth": {"name": "AFC Bournemouth", "country": "ENG", "league": "Premier League", "popularity": 55},
    "leicester": {"name": "Leicester City", "country": "ENG", "league": "Premier League", "popularity": 60},
    "leicester city": {"name": "Leicester City", "country": "ENG", "league": "Premier League", "popularity": 60},
    "the foxes": {"name": "Leicester City", "country": "ENG", "league": "Premier League", "popularity": 60},
    "ipswich": {"name": "Ipswich Town", "country": "ENG", "league": "Premier League", "popularity": 52},
    "ipswich town": {"name": "Ipswich Town", "country": "ENG", "league": "Premier League", "popularity": 52},
    "southampton": {"name": "FC Southampton", "country": "ENG", "league": "Premier League", "popularity": 55},
    "fc southampton": {"name": "FC Southampton", "country": "ENG", "league": "Premier League", "popularity": 55},
    "the saints": {"name": "FC Southampton", "country": "ENG", "league": "Premier League", "popularity": 55},
    
    # ═══════════════════════════════════════════════════
    # WEITERE SERIE A (Popularity 55-65)
    # ═══════════════════════════════════════════════════
    
    "lazio": {"name": "Lazio Rom", "country": "ITA", "league": "Serie A", "popularity": 65},
    "lazio rom": {"name": "Lazio Rom", "country": "ITA", "league": "Serie A", "popularity": 65},
    "ss lazio": {"name": "Lazio Rom", "country": "ITA", "league": "Serie A", "popularity": 65},
    "fiorentina": {"name": "AC Florenz", "country": "ITA", "league": "Serie A", "popularity": 62},
    "ac florenz": {"name": "AC Florenz", "country": "ITA", "league": "Serie A", "popularity": 62},
    "la viola": {"name": "AC Florenz", "country": "ITA", "league": "Serie A", "popularity": 62},
    "atalanta": {"name": "Atalanta Bergamo", "country": "ITA", "league": "Serie A", "popularity": 62},
    "atalanta bergamo": {"name": "Atalanta Bergamo", "country": "ITA", "league": "Serie A", "popularity": 62},
    "la dea": {"name": "Atalanta Bergamo", "country": "ITA", "league": "Serie A", "popularity": 62},
    "bologna": {"name": "FC Bologna", "country": "ITA", "league": "Serie A", "popularity": 58},
    "fc bologna": {"name": "FC Bologna", "country": "ITA", "league": "Serie A", "popularity": 58},
    "torino": {"name": "FC Turin", "country": "ITA", "league": "Serie A", "popularity": 55},
    "fc turin": {"name": "FC Turin", "country": "ITA", "league": "Serie A", "popularity": 55},
    "sampdoria": {"name": "Sampdoria Genua", "country": "ITA", "league": "Serie B", "popularity": 52},
    "genoa": {"name": "CFC Genua", "country": "ITA", "league": "Serie A", "popularity": 52},
    
    # ═══════════════════════════════════════════════════
    # WEITERE LIGUE 1 (Popularity 55-65)
    # ═══════════════════════════════════════════════════
    
    "marseille": {"name": "Olympique Marseille", "country": "FRA", "league": "Ligue 1", "popularity": 68},
    "olympique marseille": {"name": "Olympique Marseille", "country": "FRA", "league": "Ligue 1", "popularity": 68},
    "om": {"name": "Olympique Marseille", "country": "FRA", "league": "Ligue 1", "popularity": 68},
    "lyon": {"name": "Olympique Lyon", "country": "FRA", "league": "Ligue 1", "popularity": 65},
    "olympique lyon": {"name": "Olympique Lyon", "country": "FRA", "league": "Ligue 1", "popularity": 65},
    "ol": {"name": "Olympique Lyon", "country": "FRA", "league": "Ligue 1", "popularity": 65},
    "monaco": {"name": "AS Monaco", "country": "FRA", "league": "Ligue 1", "popularity": 62},
    "as monaco": {"name": "AS Monaco", "country": "FRA", "league": "Ligue 1", "popularity": 62},
    "lille": {"name": "OSC Lille", "country": "FRA", "league": "Ligue 1", "popularity": 58},
    "osc lille": {"name": "OSC Lille", "country": "FRA", "league": "Ligue 1", "popularity": 58},
    "losc": {"name": "OSC Lille", "country": "FRA", "league": "Ligue 1", "popularity": 58},
    "nice": {"name": "OGC Nizza", "country": "FRA", "league": "Ligue 1", "popularity": 55},
    "ogc nizza": {"name": "OGC Nizza", "country": "FRA", "league": "Ligue 1", "popularity": 55},
    "lens": {"name": "RC Lens", "country": "FRA", "league": "Ligue 1", "popularity": 55},
    "rc lens": {"name": "RC Lens", "country": "FRA", "league": "Ligue 1", "popularity": 55},
    "rennes": {"name": "Stade Rennes", "country": "FRA", "league": "Ligue 1", "popularity": 52},
    "stade rennes": {"name": "Stade Rennes", "country": "FRA", "league": "Ligue 1", "popularity": 52},
    
    # ═══════════════════════════════════════════════════
    # INTERNATIONALE CLUBS (Popularity 55-70)
    # ═══════════════════════════════════════════════════
    
    # Niederlande
    "ajax": {"name": "Ajax Amsterdam", "country": "NED", "league": "Eredivisie", "popularity": 70},
    "ajax amsterdam": {"name": "Ajax Amsterdam", "country": "NED", "league": "Eredivisie", "popularity": 70},
    "psv": {"name": "PSV Eindhoven", "country": "NED", "league": "Eredivisie", "popularity": 65},
    "psv eindhoven": {"name": "PSV Eindhoven", "country": "NED", "league": "Eredivisie", "popularity": 65},
    "feyenoord": {"name": "Feyenoord Rotterdam", "country": "NED", "league": "Eredivisie", "popularity": 62},
    "feyenoord rotterdam": {"name": "Feyenoord Rotterdam", "country": "NED", "league": "Eredivisie", "popularity": 62},
    
    # Türkei
    "galatasaray": {"name": "Galatasaray Istanbul", "country": "TUR", "league": "Süper Lig", "popularity": 68},
    "galatasaray istanbul": {"name": "Galatasaray Istanbul", "country": "TUR", "league": "Süper Lig", "popularity": 68},
    "gala": {"name": "Galatasaray Istanbul", "country": "TUR", "league": "Süper Lig", "popularity": 68},
    "fenerbahce": {"name": "Fenerbahçe Istanbul", "country": "TUR", "league": "Süper Lig", "popularity": 65},
    "fenerbahçe": {"name": "Fenerbahçe Istanbul", "country": "TUR", "league": "Süper Lig", "popularity": 65},
    "fenerbahce istanbul": {"name": "Fenerbahçe Istanbul", "country": "TUR", "league": "Süper Lig", "popularity": 65},
    "besiktas": {"name": "Beşiktaş Istanbul", "country": "TUR", "league": "Süper Lig", "popularity": 62},
    "beşiktaş": {"name": "Beşiktaş Istanbul", "country": "TUR", "league": "Süper Lig", "popularity": 62},
    
    # Saudi-Arabien
    "al-nassr": {"name": "Al-Nassr", "country": "KSA", "league": "Saudi Pro League", "popularity": 60},
    "al nassr": {"name": "Al-Nassr", "country": "KSA", "league": "Saudi Pro League", "popularity": 60},
    "al-hilal": {"name": "Al-Hilal", "country": "KSA", "league": "Saudi Pro League", "popularity": 58},
    "al hilal": {"name": "Al-Hilal", "country": "KSA", "league": "Saudi Pro League", "popularity": 58},
    "al-ittihad": {"name": "Al-Ittihad", "country": "KSA", "league": "Saudi Pro League", "popularity": 55},
    "al ittihad": {"name": "Al-Ittihad", "country": "KSA", "league": "Saudi Pro League", "popularity": 55},
    
    # Sonstige
    "celtic": {"name": "Celtic Glasgow", "country": "SCO", "league": "Scottish Premiership", "popularity": 65},
    "celtic glasgow": {"name": "Celtic Glasgow", "country": "SCO", "league": "Scottish Premiership", "popularity": 65},
    "rangers": {"name": "Glasgow Rangers", "country": "SCO", "league": "Scottish Premiership", "popularity": 62},
    "glasgow rangers": {"name": "Glasgow Rangers", "country": "SCO", "league": "Scottish Premiership", "popularity": 62},
    "sporting": {"name": "Sporting Lissabon", "country": "POR", "league": "Primeira Liga", "popularity": 65},
    "sporting lissabon": {"name": "Sporting Lissabon", "country": "POR", "league": "Primeira Liga", "popularity": 65},
    "sporting lisbon": {"name": "Sporting Lissabon", "country": "POR", "league": "Primeira Liga", "popularity": 65},
    "salzburg": {"name": "Red Bull Salzburg", "country": "AUT", "league": "Bundesliga (AUT)", "popularity": 58},
    "red bull salzburg": {"name": "Red Bull Salzburg", "country": "AUT", "league": "Bundesliga (AUT)", "popularity": 58},
    "rb salzburg": {"name": "Red Bull Salzburg", "country": "AUT", "league": "Bundesliga (AUT)", "popularity": 58},
    "inter miami": {"name": "Inter Miami", "country": "USA", "league": "MLS", "popularity": 60},
    "brugge": {"name": "Club Brügge", "country": "BEL", "league": "Jupiler Pro League", "popularity": 55},
    "club brugge": {"name": "Club Brügge", "country": "BEL", "league": "Jupiler Pro League", "popularity": 55},
    "club brügge": {"name": "Club Brügge", "country": "BEL", "league": "Jupiler Pro League", "popularity": 55},
}


# =============================================================================
# ENTITY RECOGNITION ENGINE
# =============================================================================

class EntityRecognizer:
    """Erkennt Entitäten aus Text"""
    
    def __init__(self):
        self.players = PLAYERS_DB
        self.clubs = CLUBS_DB
    
    def recognize_player(self, text: str) -> Optional[EntityMatch]:
        """Erkennt Spieler aus Text"""
        text_lower = text.lower()
        
        # Nach längsten Matches zuerst suchen (genauere Treffer)
        matches = []
        for key, data in self.players.items():
            if key in text_lower:
                matches.append((key, data, len(key)))
        
        if not matches:
            return None
        
        # Längster Match = bester Match
        matches.sort(key=lambda x: -x[2])
        best_key, best_data = matches[0][0], matches[0][1]
        
        return EntityMatch(
            name=best_data["name"],
            canonical_name=best_data["name"],
            slug=best_key.replace(" ", "-"),
            confidence=min(0.95, best_data["popularity"] / 100),
            entity_type="player",
            metadata={
                "club": best_data.get("club"),
                "position": best_data.get("position"),
                "nationality": best_data.get("nationality"),
                "popularity": best_data.get("popularity")
            }
        )
    
    def recognize_club(self, text: str) -> Optional[EntityMatch]:
        """Erkennt Club aus Text"""
        text_lower = text.lower()
        
        matches = []
        for key, data in self.clubs.items():
            if key in text_lower:
                matches.append((key, data, len(key)))
        
        if not matches:
            return None
        
        matches.sort(key=lambda x: -x[2])
        best_key, best_data = matches[0][0], matches[0][1]
        
        return EntityMatch(
            name=best_data["name"],
            canonical_name=best_data["name"],
            slug=best_key.replace(" ", "-"),
            confidence=min(0.95, best_data["popularity"] / 100),
            entity_type="club",
            metadata={
                "country": best_data.get("country"),
                "league": best_data.get("league"),
                "popularity": best_data.get("popularity")
            }
        )
    
    def recognize_transfer_type(self, text: str) -> TransferType:
        """Erkennt Transfer-Typ"""
        text_lower = text.lower()
        
        # Loan patterns
        if any(kw in text_lower for kw in ["loan", "leihe", "leih", "ausgeliehen", "geliehen", "ausleihe"]):
            if any(kw in text_lower for kw in ["option", "kaufoption", "buy option", "obligation"]):
                return TransferType.LOAN_WITH_OPTION
            return TransferType.LOAN
        
        # Free transfer
        if any(kw in text_lower for kw in ["free", "ablösefrei", "ablöse frei", "vertragsende", "free agent", "bosman"]):
            return TransferType.FREE
        
        # Swap deal
        if any(kw in text_lower for kw in ["swap", "tausch", "plus cash", "im tausch", "tauschgeschäft"]):
            return TransferType.SWAP
        
        # Return
        if any(kw in text_lower for kw in ["return", "rückkehr", "zurück zu", "comes back", "kehrt zurück"]):
            return TransferType.RETURN
        
        # Extension
        if any(kw in text_lower for kw in ["extension", "verlängerung", "verlängert", "neuer vertrag", "extends", "contract extension"]):
            return TransferType.EXTENSION
        
        # Default: permanent
        return TransferType.PERMANENT
    
    def recognize_all(self, text: str) -> Dict:
        """Erkennt alle Entitäten aus Text"""
        player = self.recognize_player(text)
        club = self.recognize_club(text)
        transfer_type = self.recognize_transfer_type(text)
        
        # Versuche zweiten Club zu finden (für Transfers zwischen Clubs)
        second_club = None
        if club:
            # Entferne ersten Club-Match und suche nochmal
            text_without_first = text.lower().replace(club.slug.replace("-", " "), "")
            for key, data in self.clubs.items():
                if key in text_without_first and key != club.slug.replace("-", " "):
                    second_club = EntityMatch(
                        name=data["name"],
                        canonical_name=data["name"],
                        slug=key.replace(" ", "-"),
                        confidence=min(0.9, data["popularity"] / 100),
                        entity_type="club",
                        metadata=data
                    )
                    break
        
        return {
            "player": player,
            "from_club": second_club if second_club else None,
            "to_club": club,
            "transfer_type": transfer_type.value,
            "has_player": player is not None,
            "has_club": club is not None,
            "confidence": min(
                player.confidence if player else 0.3,
                club.confidence if club else 0.3
            )
        }


# Global instance
_recognizer = None

def get_entity_recognizer() -> EntityRecognizer:
    global _recognizer
    if _recognizer is None:
        _recognizer = EntityRecognizer()
    return _recognizer
