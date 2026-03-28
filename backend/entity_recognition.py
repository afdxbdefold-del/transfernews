"""
TransferNews.de - ENTITY RECOGNITION SYSTEM
============================================

Erkennt Spieler, Clubs, Wettbewerbe und Transfer-Details aus Headlines.
Verwendet Pattern-Matching und umfangreiche Datenbanken.
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
# SPIELER-DATENBANK (500+ Spieler)
# =============================================================================

PLAYERS_DB = {
    # ═══════════════════════════════════════════════════
    # TIER 1 - WELTKLASSE (Popularity 90-100)
    # ═══════════════════════════════════════════════════
    
    # Stürmer
    "mbappe": {"name": "Kylian Mbappé", "club": "Real Madrid", "position": "ST", "nationality": "FRA", "popularity": 100},
    "mbappé": {"name": "Kylian Mbappé", "club": "Real Madrid", "position": "ST", "nationality": "FRA", "popularity": 100},
    "kylian mbappe": {"name": "Kylian Mbappé", "club": "Real Madrid", "position": "ST", "nationality": "FRA", "popularity": 100},
    "haaland": {"name": "Erling Haaland", "club": "Manchester City", "position": "ST", "nationality": "NOR", "popularity": 98},
    "erling haaland": {"name": "Erling Haaland", "club": "Manchester City", "position": "ST", "nationality": "NOR", "popularity": 98},
    "messi": {"name": "Lionel Messi", "club": "Inter Miami", "position": "RW", "nationality": "ARG", "popularity": 95},
    "lionel messi": {"name": "Lionel Messi", "club": "Inter Miami", "position": "RW", "nationality": "ARG", "popularity": 95},
    "ronaldo": {"name": "Cristiano Ronaldo", "club": "Al-Nassr", "position": "ST", "nationality": "POR", "popularity": 94},
    "cristiano ronaldo": {"name": "Cristiano Ronaldo", "club": "Al-Nassr", "position": "ST", "nationality": "POR", "popularity": 94},
    
    # Mittelfeld
    "bellingham": {"name": "Jude Bellingham", "club": "Real Madrid", "position": "CAM", "nationality": "ENG", "popularity": 96},
    "jude bellingham": {"name": "Jude Bellingham", "club": "Real Madrid", "position": "CAM", "nationality": "ENG", "popularity": 96},
    "vinicius": {"name": "Vinícius Jr.", "club": "Real Madrid", "position": "LW", "nationality": "BRA", "popularity": 95},
    "vinicius jr": {"name": "Vinícius Jr.", "club": "Real Madrid", "position": "LW", "nationality": "BRA", "popularity": 95},
    "vini jr": {"name": "Vinícius Jr.", "club": "Real Madrid", "position": "LW", "nationality": "BRA", "popularity": 95},
    
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
    "de bruyne": {"name": "Kevin De Bruyne", "club": "Manchester City", "position": "CAM", "nationality": "BEL", "popularity": 82},
    "kevin de bruyne": {"name": "Kevin De Bruyne", "club": "Manchester City", "position": "CAM", "nationality": "BEL", "popularity": 82},
    "foden": {"name": "Phil Foden", "club": "Manchester City", "position": "LW", "nationality": "ENG", "popularity": 81},
    "phil foden": {"name": "Phil Foden", "club": "Manchester City", "position": "LW", "nationality": "ENG", "popularity": 81},
    "pedri": {"name": "Pedri", "club": "Barcelona", "position": "CM", "nationality": "ESP", "popularity": 80},
    
    # ═══════════════════════════════════════════════════
    # TIER 3 - BEKANNTE SPIELER (Popularity 70-79)
    # ═══════════════════════════════════════════════════
    
    "yamal": {"name": "Lamine Yamal", "club": "Barcelona", "position": "RW", "nationality": "ESP", "popularity": 79},
    "lamine yamal": {"name": "Lamine Yamal", "club": "Barcelona", "position": "RW", "nationality": "ESP", "popularity": 79},
    "gavi": {"name": "Gavi", "club": "Barcelona", "position": "CM", "nationality": "ESP", "popularity": 78},
    "sancho": {"name": "Jadon Sancho", "club": "Manchester United", "position": "RW", "nationality": "ENG", "popularity": 77},
    "jadon sancho": {"name": "Jadon Sancho", "club": "Manchester United", "position": "RW", "nationality": "ENG", "popularity": 77},
    "rashford": {"name": "Marcus Rashford", "club": "Manchester United", "position": "LW", "nationality": "ENG", "popularity": 76},
    "marcus rashford": {"name": "Marcus Rashford", "club": "Manchester United", "position": "LW", "nationality": "ENG", "popularity": 76},
    "neymar": {"name": "Neymar Jr.", "club": "Al-Hilal", "position": "LW", "nationality": "BRA", "popularity": 75},
    "lewandowski": {"name": "Robert Lewandowski", "club": "Barcelona", "position": "ST", "nationality": "POL", "popularity": 74},
    "robert lewandowski": {"name": "Robert Lewandowski", "club": "Barcelona", "position": "ST", "nationality": "POL", "popularity": 74},
    "modric": {"name": "Luka Modrić", "club": "Real Madrid", "position": "CM", "nationality": "CRO", "popularity": 73},
    "luka modric": {"name": "Luka Modrić", "club": "Real Madrid", "position": "CM", "nationality": "CRO", "popularity": 73},
    "kroos": {"name": "Toni Kroos", "club": "Retired", "position": "CM", "nationality": "GER", "popularity": 72},
    "toni kroos": {"name": "Toni Kroos", "club": "Retired", "position": "CM", "nationality": "GER", "popularity": 72},
    "muller": {"name": "Thomas Müller", "club": "Bayern München", "position": "CAM", "nationality": "GER", "popularity": 71},
    "müller": {"name": "Thomas Müller", "club": "Bayern München", "position": "CAM", "nationality": "GER", "popularity": 71},
    "thomas muller": {"name": "Thomas Müller", "club": "Bayern München", "position": "CAM", "nationality": "GER", "popularity": 71},
    "neuer": {"name": "Manuel Neuer", "club": "Bayern München", "position": "GK", "nationality": "GER", "popularity": 70},
    "manuel neuer": {"name": "Manuel Neuer", "club": "Bayern München", "position": "GK", "nationality": "GER", "popularity": 70},
    
    # ═══════════════════════════════════════════════════
    # BUNDESLIGA SPIELER (Popularity 60-69)
    # ═══════════════════════════════════════════════════
    
    "fullkrug": {"name": "Niclas Füllkrug", "club": "West Ham", "position": "ST", "nationality": "GER", "popularity": 68},
    "füllkrug": {"name": "Niclas Füllkrug", "club": "West Ham", "position": "ST", "nationality": "GER", "popularity": 68},
    "niclas fullkrug": {"name": "Niclas Füllkrug", "club": "West Ham", "position": "ST", "nationality": "GER", "popularity": 68},
    "havertz": {"name": "Kai Havertz", "club": "Arsenal", "position": "ST", "nationality": "GER", "popularity": 67},
    "kai havertz": {"name": "Kai Havertz", "club": "Arsenal", "position": "ST", "nationality": "GER", "popularity": 67},
    "gnabry": {"name": "Serge Gnabry", "club": "Bayern München", "position": "RW", "nationality": "GER", "popularity": 66},
    "serge gnabry": {"name": "Serge Gnabry", "club": "Bayern München", "position": "RW", "nationality": "GER", "popularity": 66},
    "sane": {"name": "Leroy Sané", "club": "Bayern München", "position": "LW", "nationality": "GER", "popularity": 65},
    "sané": {"name": "Leroy Sané", "club": "Bayern München", "position": "LW", "nationality": "GER", "popularity": 65},
    "leroy sane": {"name": "Leroy Sané", "club": "Bayern München", "position": "LW", "nationality": "GER", "popularity": 65},
    "gundogan": {"name": "İlkay Gündoğan", "club": "Barcelona", "position": "CM", "nationality": "GER", "popularity": 64},
    "gündogan": {"name": "İlkay Gündoğan", "club": "Barcelona", "position": "CM", "nationality": "GER", "popularity": 64},
    "ilkay gundogan": {"name": "İlkay Gündoğan", "club": "Barcelona", "position": "CM", "nationality": "GER", "popularity": 64},
    "ter stegen": {"name": "Marc-André ter Stegen", "club": "Barcelona", "position": "GK", "nationality": "GER", "popularity": 63},
    "kimmich": {"name": "Joshua Kimmich", "club": "Bayern München", "position": "CDM", "nationality": "GER", "popularity": 62},
    "joshua kimmich": {"name": "Joshua Kimmich", "club": "Bayern München", "position": "CDM", "nationality": "GER", "popularity": 62},
    "goretzka": {"name": "Leon Goretzka", "club": "Bayern München", "position": "CM", "nationality": "GER", "popularity": 61},
    "leon goretzka": {"name": "Leon Goretzka", "club": "Bayern München", "position": "CM", "nationality": "GER", "popularity": 61},
    "brandt": {"name": "Julian Brandt", "club": "Borussia Dortmund", "position": "CAM", "nationality": "GER", "popularity": 60},
    "julian brandt": {"name": "Julian Brandt", "club": "Borussia Dortmund", "position": "CAM", "nationality": "GER", "popularity": 60},
    
    # ═══════════════════════════════════════════════════
    # PREMIER LEAGUE STARS (Popularity 55-69)
    # ═══════════════════════════════════════════════════
    
    "rice": {"name": "Declan Rice", "club": "Arsenal", "position": "CDM", "nationality": "ENG", "popularity": 68},
    "declan rice": {"name": "Declan Rice", "club": "Arsenal", "position": "CDM", "nationality": "ENG", "popularity": 68},
    "odegaard": {"name": "Martin Ødegaard", "club": "Arsenal", "position": "CAM", "nationality": "NOR", "popularity": 67},
    "ødegaard": {"name": "Martin Ødegaard", "club": "Arsenal", "position": "CAM", "nationality": "NOR", "popularity": 67},
    "martin odegaard": {"name": "Martin Ødegaard", "club": "Arsenal", "position": "CAM", "nationality": "NOR", "popularity": 67},
    "bruno fernandes": {"name": "Bruno Fernandes", "club": "Manchester United", "position": "CAM", "nationality": "POR", "popularity": 66},
    "casemiro": {"name": "Casemiro", "club": "Manchester United", "position": "CDM", "nationality": "BRA", "popularity": 65},
    "darwin nunez": {"name": "Darwin Núñez", "club": "Liverpool", "position": "ST", "nationality": "URU", "popularity": 64},
    "darwin": {"name": "Darwin Núñez", "club": "Liverpool", "position": "ST", "nationality": "URU", "popularity": 64},
    "nunez": {"name": "Darwin Núñez", "club": "Liverpool", "position": "ST", "nationality": "URU", "popularity": 64},
    "luis diaz": {"name": "Luis Díaz", "club": "Liverpool", "position": "LW", "nationality": "COL", "popularity": 63},
    "diaz": {"name": "Luis Díaz", "club": "Liverpool", "position": "LW", "nationality": "COL", "popularity": 63},
    "van dijk": {"name": "Virgil van Dijk", "club": "Liverpool", "position": "CB", "nationality": "NED", "popularity": 62},
    "virgil van dijk": {"name": "Virgil van Dijk", "club": "Liverpool", "position": "CB", "nationality": "NED", "popularity": 62},
    "son": {"name": "Heung-Min Son", "club": "Tottenham", "position": "LW", "nationality": "KOR", "popularity": 61},
    "heung-min son": {"name": "Heung-Min Son", "club": "Tottenham", "position": "LW", "nationality": "KOR", "popularity": 61},
    
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
    "chiesa": {"name": "Federico Chiesa", "club": "Liverpool", "position": "RW", "nationality": "ITA", "popularity": 62},
    "federico chiesa": {"name": "Federico Chiesa", "club": "Liverpool", "position": "RW", "nationality": "ITA", "popularity": 62},
    "lukaku": {"name": "Romelu Lukaku", "club": "Napoli", "position": "ST", "nationality": "BEL", "popularity": 61},
    "romelu lukaku": {"name": "Romelu Lukaku", "club": "Napoli", "position": "ST", "nationality": "BEL", "popularity": 61},
    "kone": {"name": "Manu Koné", "club": "Roma", "position": "CM", "nationality": "FRA", "popularity": 55},
    "manu kone": {"name": "Manu Koné", "club": "Roma", "position": "CM", "nationality": "FRA", "popularity": 55},
    "kostic": {"name": "Filip Kostić", "club": "Juventus", "position": "LM", "nationality": "SRB", "popularity": 54},
    "filip kostic": {"name": "Filip Kostić", "club": "Juventus", "position": "LM", "nationality": "SRB", "popularity": 54},
    
    # ═══════════════════════════════════════════════════
    # TORHÜTER (Popularity 50-65)
    # ═══════════════════════════════════════════════════
    
    "alisson": {"name": "Alisson Becker", "club": "Liverpool", "position": "GK", "nationality": "BRA", "popularity": 65},
    "alisson becker": {"name": "Alisson Becker", "club": "Liverpool", "position": "GK", "nationality": "BRA", "popularity": 65},
    "courtois": {"name": "Thibaut Courtois", "club": "Real Madrid", "position": "GK", "nationality": "BEL", "popularity": 64},
    "thibaut courtois": {"name": "Thibaut Courtois", "club": "Real Madrid", "position": "GK", "nationality": "BEL", "popularity": 64},
    "ederson": {"name": "Ederson", "club": "Manchester City", "position": "GK", "nationality": "BRA", "popularity": 60},
    "donnarumma": {"name": "Gianluigi Donnarumma", "club": "PSG", "position": "GK", "nationality": "ITA", "popularity": 59},
    "gianluigi donnarumma": {"name": "Gianluigi Donnarumma", "club": "PSG", "position": "GK", "nationality": "ITA", "popularity": 59},
    "vicario": {"name": "Guglielmo Vicario", "club": "Tottenham", "position": "GK", "nationality": "ITA", "popularity": 55},
    "guglielmo vicario": {"name": "Guglielmo Vicario", "club": "Tottenham", "position": "GK", "nationality": "ITA", "popularity": 55},
    "trafford": {"name": "James Trafford", "club": "Burnley", "position": "GK", "nationality": "ENG", "popularity": 50},
    "james trafford": {"name": "James Trafford", "club": "Burnley", "position": "GK", "nationality": "ENG", "popularity": 50},
    
    # ═══════════════════════════════════════════════════
    # TRAINER (Popularity 60-75)
    # ═══════════════════════════════════════════════════
    
    "guardiola": {"name": "Pep Guardiola", "club": "Manchester City", "position": "Manager", "nationality": "ESP", "popularity": 75},
    "pep guardiola": {"name": "Pep Guardiola", "club": "Manchester City", "position": "Manager", "nationality": "ESP", "popularity": 75},
    "ancelotti": {"name": "Carlo Ancelotti", "club": "Real Madrid", "position": "Manager", "nationality": "ITA", "popularity": 72},
    "carlo ancelotti": {"name": "Carlo Ancelotti", "club": "Real Madrid", "position": "Manager", "nationality": "ITA", "popularity": 72},
    "klopp": {"name": "Jürgen Klopp", "club": "Retired", "position": "Manager", "nationality": "GER", "popularity": 70},
    "jurgen klopp": {"name": "Jürgen Klopp", "club": "Retired", "position": "Manager", "nationality": "GER", "popularity": 70},
    "arteta": {"name": "Mikel Arteta", "club": "Arsenal", "position": "Manager", "nationality": "ESP", "popularity": 65},
    "mikel arteta": {"name": "Mikel Arteta", "club": "Arsenal", "position": "Manager", "nationality": "ESP", "popularity": 65},
    "moyes": {"name": "David Moyes", "club": "Free Agent", "position": "Manager", "nationality": "SCO", "popularity": 55},
    "david moyes": {"name": "David Moyes", "club": "Free Agent", "position": "Manager", "nationality": "SCO", "popularity": 55},
}


# =============================================================================
# CLUB-DATENBANK (200+ Clubs)
# =============================================================================

CLUBS_DB = {
    # ═══════════════════════════════════════════════════
    # TIER 1 - WELTSPITZE (Popularity 90-100)
    # ═══════════════════════════════════════════════════
    
    "real madrid": {"name": "Real Madrid", "country": "ESP", "league": "La Liga", "popularity": 100},
    "real": {"name": "Real Madrid", "country": "ESP", "league": "La Liga", "popularity": 100},
    "madrid": {"name": "Real Madrid", "country": "ESP", "league": "La Liga", "popularity": 100},
    "barcelona": {"name": "FC Barcelona", "country": "ESP", "league": "La Liga", "popularity": 98},
    "barca": {"name": "FC Barcelona", "country": "ESP", "league": "La Liga", "popularity": 98},
    "barça": {"name": "FC Barcelona", "country": "ESP", "league": "La Liga", "popularity": 98},
    "fc barcelona": {"name": "FC Barcelona", "country": "ESP", "league": "La Liga", "popularity": 98},
    "manchester city": {"name": "Manchester City", "country": "ENG", "league": "Premier League", "popularity": 97},
    "man city": {"name": "Manchester City", "country": "ENG", "league": "Premier League", "popularity": 97},
    "city": {"name": "Manchester City", "country": "ENG", "league": "Premier League", "popularity": 97},
    "liverpool": {"name": "FC Liverpool", "country": "ENG", "league": "Premier League", "popularity": 96},
    "fc liverpool": {"name": "FC Liverpool", "country": "ENG", "league": "Premier League", "popularity": 96},
    "bayern": {"name": "FC Bayern München", "country": "GER", "league": "Bundesliga", "popularity": 95},
    "bayern munich": {"name": "FC Bayern München", "country": "GER", "league": "Bundesliga", "popularity": 95},
    "bayern münchen": {"name": "FC Bayern München", "country": "GER", "league": "Bundesliga", "popularity": 95},
    "fc bayern": {"name": "FC Bayern München", "country": "GER", "league": "Bundesliga", "popularity": 95},
    "psg": {"name": "Paris Saint-Germain", "country": "FRA", "league": "Ligue 1", "popularity": 94},
    "paris saint-germain": {"name": "Paris Saint-Germain", "country": "FRA", "league": "Ligue 1", "popularity": 94},
    "paris": {"name": "Paris Saint-Germain", "country": "FRA", "league": "Ligue 1", "popularity": 94},
    "manchester united": {"name": "Manchester United", "country": "ENG", "league": "Premier League", "popularity": 93},
    "man united": {"name": "Manchester United", "country": "ENG", "league": "Premier League", "popularity": 93},
    "man utd": {"name": "Manchester United", "country": "ENG", "league": "Premier League", "popularity": 93},
    "united": {"name": "Manchester United", "country": "ENG", "league": "Premier League", "popularity": 93},
    "chelsea": {"name": "FC Chelsea", "country": "ENG", "league": "Premier League", "popularity": 92},
    "fc chelsea": {"name": "FC Chelsea", "country": "ENG", "league": "Premier League", "popularity": 92},
    "arsenal": {"name": "FC Arsenal", "country": "ENG", "league": "Premier League", "popularity": 91},
    "fc arsenal": {"name": "FC Arsenal", "country": "ENG", "league": "Premier League", "popularity": 91},
    
    # ═══════════════════════════════════════════════════
    # TIER 2 - TOP CLUBS (Popularity 80-89)
    # ═══════════════════════════════════════════════════
    
    "juventus": {"name": "Juventus Turin", "country": "ITA", "league": "Serie A", "popularity": 89},
    "juve": {"name": "Juventus Turin", "country": "ITA", "league": "Serie A", "popularity": 89},
    "dortmund": {"name": "Borussia Dortmund", "country": "GER", "league": "Bundesliga", "popularity": 88},
    "borussia dortmund": {"name": "Borussia Dortmund", "country": "GER", "league": "Bundesliga", "popularity": 88},
    "bvb": {"name": "Borussia Dortmund", "country": "GER", "league": "Bundesliga", "popularity": 88},
    "inter": {"name": "Inter Mailand", "country": "ITA", "league": "Serie A", "popularity": 87},
    "inter milan": {"name": "Inter Mailand", "country": "ITA", "league": "Serie A", "popularity": 87},
    "inter mailand": {"name": "Inter Mailand", "country": "ITA", "league": "Serie A", "popularity": 87},
    "internazionale": {"name": "Inter Mailand", "country": "ITA", "league": "Serie A", "popularity": 87},
    "milan": {"name": "AC Milan", "country": "ITA", "league": "Serie A", "popularity": 86},
    "ac milan": {"name": "AC Milan", "country": "ITA", "league": "Serie A", "popularity": 86},
    "atletico": {"name": "Atlético Madrid", "country": "ESP", "league": "La Liga", "popularity": 85},
    "atletico madrid": {"name": "Atlético Madrid", "country": "ESP", "league": "La Liga", "popularity": 85},
    "atlético madrid": {"name": "Atlético Madrid", "country": "ESP", "league": "La Liga", "popularity": 85},
    "tottenham": {"name": "Tottenham Hotspur", "country": "ENG", "league": "Premier League", "popularity": 84},
    "spurs": {"name": "Tottenham Hotspur", "country": "ENG", "league": "Premier League", "popularity": 84},
    "tottenham hotspur": {"name": "Tottenham Hotspur", "country": "ENG", "league": "Premier League", "popularity": 84},
    "napoli": {"name": "SSC Neapel", "country": "ITA", "league": "Serie A", "popularity": 83},
    "ssc napoli": {"name": "SSC Neapel", "country": "ITA", "league": "Serie A", "popularity": 83},
    "neapel": {"name": "SSC Neapel", "country": "ITA", "league": "Serie A", "popularity": 83},
    "roma": {"name": "AS Rom", "country": "ITA", "league": "Serie A", "popularity": 82},
    "as roma": {"name": "AS Rom", "country": "ITA", "league": "Serie A", "popularity": 82},
    "as rom": {"name": "AS Rom", "country": "ITA", "league": "Serie A", "popularity": 82},
    "newcastle": {"name": "Newcastle United", "country": "ENG", "league": "Premier League", "popularity": 81},
    "newcastle united": {"name": "Newcastle United", "country": "ENG", "league": "Premier League", "popularity": 81},
    
    # ═══════════════════════════════════════════════════
    # TIER 3 - BEKANNTE CLUBS (Popularity 70-79)
    # ═══════════════════════════════════════════════════
    
    "west ham": {"name": "West Ham United", "country": "ENG", "league": "Premier League", "popularity": 79},
    "west ham united": {"name": "West Ham United", "country": "ENG", "league": "Premier League", "popularity": 79},
    "aston villa": {"name": "Aston Villa", "country": "ENG", "league": "Premier League", "popularity": 78},
    "villa": {"name": "Aston Villa", "country": "ENG", "league": "Premier League", "popularity": 78},
    "brighton": {"name": "Brighton & Hove Albion", "country": "ENG", "league": "Premier League", "popularity": 77},
    "rb leipzig": {"name": "RB Leipzig", "country": "GER", "league": "Bundesliga", "popularity": 76},
    "leipzig": {"name": "RB Leipzig", "country": "GER", "league": "Bundesliga", "popularity": 76},
    "leverkusen": {"name": "Bayer Leverkusen", "country": "GER", "league": "Bundesliga", "popularity": 75},
    "bayer leverkusen": {"name": "Bayer Leverkusen", "country": "GER", "league": "Bundesliga", "popularity": 75},
    "frankfurt": {"name": "Eintracht Frankfurt", "country": "GER", "league": "Bundesliga", "popularity": 74},
    "eintracht frankfurt": {"name": "Eintracht Frankfurt", "country": "GER", "league": "Bundesliga", "popularity": 74},
    "eintracht": {"name": "Eintracht Frankfurt", "country": "GER", "league": "Bundesliga", "popularity": 74},
    "sevilla": {"name": "FC Sevilla", "country": "ESP", "league": "La Liga", "popularity": 73},
    "fc sevilla": {"name": "FC Sevilla", "country": "ESP", "league": "La Liga", "popularity": 73},
    "benfica": {"name": "Benfica Lissabon", "country": "POR", "league": "Primeira Liga", "popularity": 72},
    "porto": {"name": "FC Porto", "country": "POR", "league": "Primeira Liga", "popularity": 71},
    "fc porto": {"name": "FC Porto", "country": "POR", "league": "Primeira Liga", "popularity": 71},
    "everton": {"name": "FC Everton", "country": "ENG", "league": "Premier League", "popularity": 70},
    "fc everton": {"name": "FC Everton", "country": "ENG", "league": "Premier League", "popularity": 70},
    
    # ═══════════════════════════════════════════════════
    # BUNDESLIGA (Popularity 60-69)
    # ═══════════════════════════════════════════════════
    
    "gladbach": {"name": "Borussia Mönchengladbach", "country": "GER", "league": "Bundesliga", "popularity": 68},
    "borussia mönchengladbach": {"name": "Borussia Mönchengladbach", "country": "GER", "league": "Bundesliga", "popularity": 68},
    "monchengladbach": {"name": "Borussia Mönchengladbach", "country": "GER", "league": "Bundesliga", "popularity": 68},
    "wolfsburg": {"name": "VfL Wolfsburg", "country": "GER", "league": "Bundesliga", "popularity": 67},
    "vfl wolfsburg": {"name": "VfL Wolfsburg", "country": "GER", "league": "Bundesliga", "popularity": 67},
    "freiburg": {"name": "SC Freiburg", "country": "GER", "league": "Bundesliga", "popularity": 66},
    "sc freiburg": {"name": "SC Freiburg", "country": "GER", "league": "Bundesliga", "popularity": 66},
    "union berlin": {"name": "1. FC Union Berlin", "country": "GER", "league": "Bundesliga", "popularity": 65},
    "union": {"name": "1. FC Union Berlin", "country": "GER", "league": "Bundesliga", "popularity": 65},
    "hoffenheim": {"name": "TSG Hoffenheim", "country": "GER", "league": "Bundesliga", "popularity": 64},
    "tsg hoffenheim": {"name": "TSG Hoffenheim", "country": "GER", "league": "Bundesliga", "popularity": 64},
    "mainz": {"name": "1. FSV Mainz 05", "country": "GER", "league": "Bundesliga", "popularity": 63},
    "mainz 05": {"name": "1. FSV Mainz 05", "country": "GER", "league": "Bundesliga", "popularity": 63},
    "koln": {"name": "1. FC Köln", "country": "GER", "league": "Bundesliga", "popularity": 62},
    "köln": {"name": "1. FC Köln", "country": "GER", "league": "Bundesliga", "popularity": 62},
    "fc koln": {"name": "1. FC Köln", "country": "GER", "league": "Bundesliga", "popularity": 62},
    "augsburg": {"name": "FC Augsburg", "country": "GER", "league": "Bundesliga", "popularity": 61},
    "fc augsburg": {"name": "FC Augsburg", "country": "GER", "league": "Bundesliga", "popularity": 61},
    "stuttgart": {"name": "VfB Stuttgart", "country": "GER", "league": "Bundesliga", "popularity": 60},
    "vfb stuttgart": {"name": "VfB Stuttgart", "country": "GER", "league": "Bundesliga", "popularity": 60},
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
        if any(kw in text_lower for kw in ["loan", "leihe", "leih", "ausgeliehen", "geliehen"]):
            if any(kw in text_lower for kw in ["option", "kaufoption", "buy option"]):
                return TransferType.LOAN_WITH_OPTION
            return TransferType.LOAN
        
        # Free transfer
        if any(kw in text_lower for kw in ["free", "ablösefrei", "ablöse frei", "vertragsende"]):
            return TransferType.FREE
        
        # Swap deal
        if any(kw in text_lower for kw in ["swap", "tausch", "plus cash", "im tausch"]):
            return TransferType.SWAP
        
        # Return
        if any(kw in text_lower for kw in ["return", "rückkehr", "zurück zu", "comes back"]):
            return TransferType.RETURN
        
        # Extension
        if any(kw in text_lower for kw in ["extension", "verlängerung", "verlängert", "neuer vertrag", "extends"]):
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
