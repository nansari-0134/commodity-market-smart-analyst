"""
Commodity Entity Linker & Multi-Product Relationship Resolver.
Maps news text, wire headlines, and catalyst notes to one or more physical commodities
with deterministic relevance weighting and matched taxonomy keywords.
"""

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional, Set


@dataclass
class MatchedCommodityEntity:
    commodity_code: str
    relevance_score: Decimal
    is_primary: bool
    matched_keywords: List[str]


# Institutional keyword taxonomy for commodity physical and futures markets
COMMODITY_TAXONOMY: Dict[str, Dict] = {
    "CL": {
        "primary_terms": ["crude oil", "wti", "west texas intermediate", "light sweet crude", "cushing"],
        "secondary_terms": ["opec", "opec+", "petroleum", "barrel", "bpd", "oil supply", "oil demand", "drilling rigs", "spr"],
        "cross_links": [("BRENT", Decimal("0.850")), ("RB", Decimal("0.650")), ("HO", Decimal("0.650"))],
    },
    "BRENT": {
        "primary_terms": ["brent crude", "brent", "north sea crude", "forties", "ekofisk", "oseberg"],
        "secondary_terms": ["opec", "tanker", "red sea", "atlantic basin", "crude cargo", "floating storage"],
        "cross_links": [("CL", Decimal("0.850")), ("HO", Decimal("0.700")), ("GO", Decimal("0.750"))],
    },
    "NG": {
        "primary_terms": ["natural gas", "henry hub", "natgas", "lng", "liquefied natural gas"],
        "secondary_terms": ["feedgas", "gas storage", "bcf", "freeport lng", "cheniere", "heating degree days", "hdd", "cdd"],
        "cross_links": [("HO", Decimal("0.450")), ("EUA_CARBON", Decimal("0.400"))],
    },
    "RB": {
        "primary_terms": ["gasoline", "rbob", "motor gasoline", "petrol", "pump price"],
        "secondary_terms": ["refinery utilization", "crack spread", "gasoline inventories", "summer blend", "driving season"],
        "cross_links": [("CL", Decimal("0.700")), ("HO", Decimal("0.600"))],
    },
    "HO": {
        "primary_terms": ["heating oil", "ultra-low sulfur diesel", "ulsd", "distillate", "diesel"],
        "secondary_terms": ["middle distillates", "refinery runs", "heating season", "trucking fuel"],
        "cross_links": [("CL", Decimal("0.700")), ("RB", Decimal("0.600")), ("GO", Decimal("0.850"))],
    },
    "GO": {
        "primary_terms": ["gasoil", "low sulfur gasoil", "ice gasoil"],
        "secondary_terms": ["european diesel", "ara barges", "distillate cracks"],
        "cross_links": [("HO", Decimal("0.850")), ("BRENT", Decimal("0.750"))],
    },
    "CORN": {
        "primary_terms": ["corn", "maize", "cbot corn", "us corn"],
        "secondary_terms": ["ethanol", "wasde", "corn belt", "usda", "bushel", "crop progress", "grain harvest"],
        "cross_links": [("SOYBEANS", Decimal("0.650")), ("WHEAT_SRW", Decimal("0.500")), ("SUGAR_11", Decimal("0.350"))],
    },
    "SOYBEANS": {
        "primary_terms": ["soybean", "soybeans", "soya", "cbot soybeans"],
        "secondary_terms": ["soybean crush", "brazil soybean", "conab", "wasde", "crush margin", "pod fill"],
        "cross_links": [("SOYOIL", Decimal("0.800")), ("CORN", Decimal("0.650")), ("PALM_OIL", Decimal("0.500"))],
    },
    "SOYOIL": {
        "primary_terms": ["soy oil", "soyoil", "soybean oil"],
        "secondary_terms": ["vegetable oil", "biodiesel", "renewable diesel", "crush spread"],
        "cross_links": [("PALM_OIL", Decimal("0.750")), ("SOYBEANS", Decimal("0.800"))],
    },
    "WHEAT_SRW": {
        "primary_terms": ["wheat", "soft red winter wheat", "chicago wheat", "srw wheat"],
        "secondary_terms": ["black sea grain", "ukraine grain", "russia wheat", "wasde", "winter wheat", "spring wheat"],
        "cross_links": [("CORN", Decimal("0.500")), ("SOYBEANS", Decimal("0.400"))],
    },
    "PALM_OIL": {
        "primary_terms": ["palm oil", "crude palm oil", "cpo", "malaysian palm"],
        "secondary_terms": ["bursa malaysia", "mpob", "indonesia export levy", "tropical oils"],
        "cross_links": [("SOYOIL", Decimal("0.750")), ("SOYBEANS", Decimal("0.450"))],
    },
    "SUGAR_11": {
        "primary_terms": ["sugar", "raw sugar", "sugar #11", "white sugar"],
        "secondary_terms": ["unica", "cane crush", "brazil sugar", "india sugar", "ethanol parity", "centrifugal sugar"],
        "cross_links": [("CL", Decimal("0.400")), ("CORN", Decimal("0.350"))],
    },
    "COFFEE_ARABICA": {
        "primary_terms": ["coffee", "arabica", "coffee arabica", "robusta", "ice coffee"],
        "secondary_terms": ["brazil frost", "minas gerais", "vietnam coffee", "conab coffee", "green coffee"],
        "cross_links": [("COCOA", Decimal("0.350")), ("SUGAR_11", Decimal("0.300"))],
    },
    "COCOA": {
        "primary_terms": ["cocoa", "cocoa bean", "ice cocoa"],
        "secondary_terms": ["ivory coast", "ghana cocoa", "west africa cocoa", "cocoa arrivals", "conching"],
        "cross_links": [("COFFEE_ARABICA", Decimal("0.350"))],
    },
    "COTTON_2": {
        "primary_terms": ["cotton", "cotton #2", "upland cotton"],
        "secondary_terms": ["textile demand", "spinning mills", "texas cotton", "usda cotton"],
        "cross_links": [],
    },
    "GOLD": {
        "primary_terms": ["gold", "bullion", "xau", "spot gold", "comex gold"],
        "secondary_terms": ["federal reserve", "fomc", "interest rate", "rate cut", "real yields", "central bank buying", "safe haven"],
        "cross_links": [("SILVER", Decimal("0.850")), ("COPPER", Decimal("0.450")), ("CL", Decimal("0.400"))],
    },
    "SILVER": {
        "primary_terms": ["silver", "xag", "spot silver", "comex silver"],
        "secondary_terms": ["photovoltaic", "solar silver", "precious metals", "gold-silver ratio", "industrial demand"],
        "cross_links": [("GOLD", Decimal("0.850")), ("COPPER", Decimal("0.550"))],
    },
    "COPPER": {
        "primary_terms": ["copper", "comex copper", "lme copper", "dr copper"],
        "secondary_terms": ["chile copper", "codelco", "smelter", "tc/rc", "power grid", "ev demand", "china stimulus"],
        "cross_links": [("ALUMINUM", Decimal("0.700")), ("IRON_ORE", Decimal("0.650")), ("SILVER", Decimal("0.500"))],
    },
    "ALUMINUM": {
        "primary_terms": ["aluminum", "lme aluminum", "bauxite", "alumina"],
        "secondary_terms": ["smelter curtailment", "power costs", "china aluminum", "automotive demand"],
        "cross_links": [("COPPER", Decimal("0.700")), ("EUA_CARBON", Decimal("0.450"))],
    },
    "IRON_ORE": {
        "primary_terms": ["iron ore", "iron ore fines", "dalian iron ore", "sgx iron ore"],
        "secondary_terms": ["steel mills", "blast furnace", "crude steel", "tangshan", "china construction"],
        "cross_links": [("COPPER", Decimal("0.650")), ("ALUMINUM", Decimal("0.550"))],
    },
    "LIVE_CATTLE": {
        "primary_terms": ["live cattle", "feeder cattle", "beef", "slaughter rates"],
        "secondary_terms": ["feedlot", "cattle on feed", "packer margins", "box beef"],
        "cross_links": [("LEAN_HOGS", Decimal("0.600")), ("CORN", Decimal("0.450"))],
    },
    "LEAN_HOGS": {
        "primary_terms": ["lean hogs", "pork", "hog slaughter"],
        "secondary_terms": ["pork cutout", "hog herd", "prrs", "african swine fever"],
        "cross_links": [("LIVE_CATTLE", Decimal("0.600")), ("CORN", Decimal("0.400")), ("SOYBEANS", Decimal("0.350"))],
    },
    "EUA_CARBON": {
        "primary_terms": ["carbon", "eua", "european union allowance", "carbon credits"],
        "secondary_terms": ["eu ets", "emissions trading", "fit for 55", "decarbonization", "coal phase-out"],
        "cross_links": [("NG", Decimal("0.400")), ("HO", Decimal("0.350"))],
    },
}


class CommodityEntityLinker:
    """
    Deterministic multi-commodity entity resolution engine.
    Scans free text, matches taxonomy keywords, applies cross-asset correlation rules,
    and returns scored commodity matches.
    """

    def __init__(self, taxonomy: Optional[Dict[str, Dict]] = None):
        self.taxonomy = taxonomy or COMMODITY_TAXONOMY

    def link_entities(
        self,
        text: str,
        explicit_primary_code: Optional[str] = None,
        min_relevance_threshold: Decimal = Decimal("0.300"),
    ) -> List[MatchedCommodityEntity]:
        """
        Analyze text, link all relevant commodities, and compute relevance scores.
        Ensures a news item can point to multiple commodities with distinct relevance scores.
        """
        if not text:
            return []

        text_lower = text.lower()
        direct_matches: Dict[str, List[str]] = {}
        direct_scores: Dict[str, Decimal] = {}

        # 1. Direct taxonomy matching
        for code, data in self.taxonomy.items():
            matched_kws = []
            score = Decimal("0.000")

            # Check primary terms (stronger weight)
            for term in data.get("primary_terms", []):
                pattern = r"\b" + re.escape(term) + r"\b"
                hits = len(re.findall(pattern, text_lower))
                if hits > 0:
                    matched_kws.append(term)
                    score += Decimal("0.500") + Decimal(str(min(hits * 0.15, 0.45)))

            # Check secondary terms (medium weight)
            for term in data.get("secondary_terms", []):
                pattern = r"\b" + re.escape(term) + r"\b"
                hits = len(re.findall(pattern, text_lower))
                if hits > 0:
                    matched_kws.append(term)
                    score += Decimal("0.250") + Decimal(str(min(hits * 0.10, 0.25)))

            if matched_kws:
                direct_matches[code] = matched_kws
                direct_scores[code] = min(score, Decimal("1.000"))

        # If an explicit primary code was passed, boost it to top priority
        if explicit_primary_code and explicit_primary_code in self.taxonomy:
            direct_scores[explicit_primary_code] = max(
                direct_scores.get(explicit_primary_code, Decimal("0.000")),
                Decimal("1.000")
            )
            if explicit_primary_code not in direct_matches:
                direct_matches[explicit_primary_code] = ["explicit_primary"]

        # 2. Cross-link propagation for co-integrated and substitute commodities
        expanded_scores: Dict[str, Decimal] = dict(direct_scores)
        expanded_matches: Dict[str, List[str]] = dict(direct_matches)

        for source_code, source_score in direct_scores.items():
            cross_links = self.taxonomy.get(source_code, {}).get("cross_links", [])
            for target_code, weight in cross_links:
                derived_score = (source_score * weight).quantize(Decimal("0.001"))
                if derived_score > expanded_scores.get(target_code, Decimal("0.000")):
                    expanded_scores[target_code] = derived_score
                    if target_code not in expanded_matches:
                        expanded_matches[target_code] = [f"cross_linked_from_{source_code.lower()}"]

        # 3. Filter by relevance threshold and format results
        candidates = []
        for code, score in expanded_scores.items():
            if score >= min_relevance_threshold:
                candidates.append((code, score, expanded_matches.get(code, [])))

        # Sort descending by relevance score
        candidates.sort(key=lambda x: x[1], reverse=True)

        if not candidates:
            return []

        # Determine primary commodity (highest relevance score, or explicit primary)
        primary_code = explicit_primary_code if (explicit_primary_code and any(c[0] == explicit_primary_code for c in candidates)) else candidates[0][0]

        results: List[MatchedCommodityEntity] = []
        for code, score, kws in candidates:
            results.append(
                MatchedCommodityEntity(
                    commodity_code=code,
                    relevance_score=score.quantize(Decimal("0.001")),
                    is_primary=(code == primary_code),
                    matched_keywords=kws,
                )
            )

        return results
