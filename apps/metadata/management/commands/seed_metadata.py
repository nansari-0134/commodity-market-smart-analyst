"""
Management command to seed canonical data domains, units of measure, and frequencies.
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.metadata.models import (
    DataDomainMaster,
    DataDomainCategory,
    UnitMaster,
    UnitType,
    FrequencyMaster,
)


class Command(BaseCommand):
    help = "Seeds canonical 33 data domains, standard units of measure, and observation frequencies."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding canonical metadata taxonomy..."))
        with transaction.atomic():
            self._seed_domains()
            self._seed_frequencies()
            self._seed_units()
        self.stdout.write(self.style.SUCCESS("Metadata taxonomy successfully seeded."))

    def _seed_domains(self):
        self.stdout.write("Seeding canonical data domains (Section 12)...")

        # Top-level domains
        top_domains = [
            # MARKET
            {
                "code": "EXCHANGE_MARKET_DATA",
                "name": "Exchange Market Data",
                "category": DataDomainCategory.MARKET,
                "display_order": 1,
                "description": "Ticks, trades, bid/ask, L1/L2 microstructure, OHLCV, volume, open interest, official settlements.",
            },
            {
                "code": "CONTRACT_REFERENCE_DATA",
                "name": "Contract & Reference Data",
                "category": DataDomainCategory.MARKET,
                "display_order": 2,
                "description": "Instrument master, contract specifications, tick sizes, delivery dates, roll calendars.",
            },
            {
                "code": "ORDER_BOOK_MICROSTRUCTURE",
                "name": "Order Book & Microstructure",
                "category": DataDomainCategory.MARKET,
                "display_order": 3,
                "description": "Market depth, queue dynamics, spread distributions, liquidity imbalances.",
            },
            {
                "code": "FUTURES_CURVES",
                "name": "Futures Curves & Spreads",
                "category": DataDomainCategory.MARKET,
                "display_order": 4,
                "description": "Contango, backwardation, calendar spreads, roll yields, curvature, carry, seasonal curves.",
            },
            {
                "code": "OPTIONS",
                "name": "Options & Volatility",
                "category": DataDomainCategory.MARKET,
                "display_order": 5,
                "description": "Implied volatility, skew, smile, Greeks, open interest, risk reversals, expected moves.",
            },
            # PHYSICAL
            {
                "code": "FUNDAMENTALS",
                "name": "Commodity Fundamentals",
                "category": DataDomainCategory.PHYSICAL,
                "display_order": 6,
                "description": "Umbrella domain for physical balance sheets: supply, demand, inventory, and balances.",
            },
            {
                "code": "TRADE_FLOWS",
                "name": "Global Trade Flows",
                "category": DataDomainCategory.PHYSICAL,
                "display_order": 7,
                "description": "Import/export volumes, origins, destinations, grades, shipping manifests, customs data.",
            },
            {
                "code": "PHYSICAL_MARKET",
                "name": "Physical Cash & Basis",
                "category": DataDomainCategory.PHYSICAL,
                "display_order": 8,
                "description": "Spot cash prices, regional basis differentials, grade premiums/discounts, refining margins.",
            },
            {
                "code": "LOGISTICS_INFRASTRUCTURE",
                "name": "Logistics & Storage Infrastructure",
                "category": DataDomainCategory.PHYSICAL,
                "display_order": 9,
                "description": "Pipelines, tank farms, dry/wet shipping, port congestion, turnaround times.",
            },
            # WEATHER
            {
                "code": "WEATHER",
                "name": "Weather & Climate",
                "category": DataDomainCategory.WEATHER,
                "display_order": 10,
                "description": "Temperature, HDD, CDD, precipitation, drought indices, hurricane tracks, forecast revisions.",
            },
            # MACRO
            {
                "code": "MACRO",
                "name": "Macroeconomics",
                "category": DataDomainCategory.MACRO,
                "display_order": 11,
                "description": "GDP, inflation, industrial production, PMI, employment, consumer sentiment.",
            },
            {
                "code": "INTEREST_RATES",
                "name": "Interest Rates & Yield Curves",
                "category": DataDomainCategory.MACRO,
                "display_order": 12,
                "description": "Central bank policy rates, sovereign yield curves, credit spreads, real rates.",
            },
            {
                "code": "FX",
                "name": "Foreign Exchange",
                "category": DataDomainCategory.MACRO,
                "display_order": 13,
                "description": "Currency pairs, trade-weighted currency indices (DXY), emerging market commodity currencies.",
            },
            {
                "code": "POSITIONING",
                "name": "Market Positioning",
                "category": DataDomainCategory.MACRO,
                "display_order": 14,
                "description": "CFTC Commitments of Traders, managed money, commercial producer hedging, open interest concentration.",
            },
            # QUALITATIVE
            {
                "code": "EVENTS",
                "name": "Market Events & Calendar",
                "category": DataDomainCategory.QUALITATIVE,
                "display_order": 15,
                "description": "Scheduled releases, USDA WASDE, EIA reports, OPEC meetings, policy announcements, surprise metrics.",
            },
            {
                "code": "NEWS",
                "name": "News & Market Narratives",
                "category": DataDomainCategory.QUALITATIVE,
                "display_order": 16,
                "description": "Verified news events, expectation shifts, geopolitical developments, sanctions, disruptions.",
            },
            {
                "code": "GOVERNMENT_REPORTS",
                "name": "Government & Regulatory Reports",
                "category": DataDomainCategory.QUALITATIVE,
                "display_order": 17,
                "description": "Official statistical publications (EIA, USDA, IEA, Eurostat, China NBS).",
            },
            {
                "code": "COMPANY_ANNOUNCEMENTS",
                "name": "Company & Producer Announcements",
                "category": DataDomainCategory.QUALITATIVE,
                "display_order": 18,
                "description": "Mining, drilling, and agribusiness production reports, guidance, maintenance outages.",
            },
            {
                "code": "ANALYST_RESEARCH",
                "name": "Analyst & Research Documents",
                "category": DataDomainCategory.QUALITATIVE,
                "display_order": 19,
                "description": "Investment bank and independent quantitative commodity research notes.",
            },
            # DERIVED
            {
                "code": "CROSS_COMMODITY",
                "name": "Cross-Commodity Relationships",
                "category": DataDomainCategory.DERIVED,
                "display_order": 20,
                "description": "Cracks (WTI/Brent/Gasoil/RBOB), sparks (Gas/Power), crushes (Soy/Meal/Oil), ratios, cointegration.",
            },
            {
                "code": "HISTORICAL_NARRATIVES",
                "name": "Historical Analogue Narratives",
                "category": DataDomainCategory.DERIVED,
                "display_order": 21,
                "description": "Historical regime matching, scenario outcomes, post-mortem research.",
            },
        ]

        domains_by_code = {}
        for d in top_domains:
            obj, _ = DataDomainMaster.objects.update_or_create(
                code=d["code"],
                defaults={
                    "name": d["name"],
                    "category": d["category"],
                    "display_order": d["display_order"],
                    "description": d["description"],
                    "parent": None,
                },
            )
            domains_by_code[d["code"]] = obj

        # Subdomains (Hierarchical children)
        subdomains = [
            # Under FUNDAMENTALS
            {
                "code": "SUPPLY",
                "name": "Supply & Production",
                "parent": "FUNDAMENTALS",
                "category": DataDomainCategory.PHYSICAL,
                "display_order": 1,
                "description": "Extraction, refinery runs, mine production, crop planting/harvest, facility utilization, outages.",
            },
            {
                "code": "DEMAND",
                "name": "Demand & Consumption",
                "parent": "FUNDAMENTALS",
                "category": DataDomainCategory.PHYSICAL,
                "display_order": 2,
                "description": "Apparent consumption, industrial demand, transportation, petrochemical, feed demand.",
            },
            {
                "code": "INVENTORIES",
                "name": "Inventories & Stocks",
                "parent": "FUNDAMENTALS",
                "category": DataDomainCategory.PHYSICAL,
                "display_order": 3,
                "description": "Commercial stocks, strategic reserves (SPR), warehouse inventories, days of forward supply.",
            },
            {
                "code": "SUPPLY_DEMAND_BALANCES",
                "name": "Supply-Demand Balances",
                "parent": "FUNDAMENTALS",
                "category": DataDomainCategory.PHYSICAL,
                "display_order": 4,
                "description": "Explicit commodity balance equations: Supply + Imports - Exports - Demand +/- Stock Change.",
            },
            # Under TRADE_FLOWS
            {
                "code": "IMPORTS",
                "name": "Imports",
                "parent": "TRADE_FLOWS",
                "category": DataDomainCategory.PHYSICAL,
                "display_order": 1,
                "description": "Seaborne and pipeline import volumes, clearance dates, source country concentration.",
            },
            {
                "code": "EXPORTS",
                "name": "Exports",
                "parent": "TRADE_FLOWS",
                "category": DataDomainCategory.PHYSICAL,
                "display_order": 2,
                "description": "Export loadings, port manifests, destination tracking, export quota compliance.",
            },
            # Under PHYSICAL_MARKET
            {
                "code": "BASIS_DIFFERENTIALS",
                "name": "Basis & Price Differentials",
                "parent": "PHYSICAL_MARKET",
                "category": DataDomainCategory.PHYSICAL,
                "display_order": 1,
                "description": "Cash minus futures basis, regional hub premiums, sulfur/gravity crude differentials.",
            },
            # Under LOGISTICS_INFRASTRUCTURE
            {
                "code": "STORAGE_CAPACITY",
                "name": "Storage Capacity & Utilization",
                "parent": "LOGISTICS_INFRASTRUCTURE",
                "category": DataDomainCategory.PHYSICAL,
                "display_order": 1,
                "description": "Cushing tank farm capacity, underground gas salt caverns, floating storage.",
            },
            {
                "code": "FREIGHT",
                "name": "Freight & Shipping Rates",
                "parent": "LOGISTICS_INFRASTRUCTURE",
                "category": DataDomainCategory.PHYSICAL,
                "display_order": 2,
                "description": "Baltic Dry Index, VLCC / Suezmax Worldscale tanker rates, clean product tankers.",
            },
            {
                "code": "SHIPPING",
                "name": "Maritime & Vessel Tracking",
                "parent": "LOGISTICS_INFRASTRUCTURE",
                "category": DataDomainCategory.PHYSICAL,
                "display_order": 3,
                "description": "AIS tracking, laden/ballast vessel status, choke point transits (Suez, Panama, Hormuz).",
            },
            {
                "code": "PORTS",
                "name": "Ports & Terminals",
                "parent": "LOGISTICS_INFRASTRUCTURE",
                "category": DataDomainCategory.PHYSICAL,
                "display_order": 4,
                "description": "Port throughput, wait times, loading berth occupancy.",
            },
            {
                "code": "PIPELINES",
                "name": "Pipelines & Transport",
                "parent": "LOGISTICS_INFRASTRUCTURE",
                "category": DataDomainCategory.PHYSICAL,
                "display_order": 5,
                "description": "Natural gas pipeline nominations, crude pipeline throughput, operational restrictions.",
            },
            # Under POSITIONING
            {
                "code": "CFTC_COT",
                "name": "CFTC Commitments of Traders",
                "parent": "POSITIONING",
                "category": DataDomainCategory.MACRO,
                "display_order": 1,
                "description": "Disaggregated and Legacy COT: Managed Money, Producer/Merchant, Swap Dealers, Non-Commercial.",
            },
        ]

        for sub in subdomains:
            parent_obj = domains_by_code.get(sub["parent"])
            DataDomainMaster.objects.update_or_create(
                code=sub["code"],
                defaults={
                    "name": sub["name"],
                    "category": sub["category"],
                    "parent": parent_obj,
                    "display_order": sub["display_order"],
                    "description": sub["description"],
                },
            )

        self.stdout.write(f"  -> Total Data Domains: {DataDomainMaster.objects.count()}")

    def _seed_frequencies(self):
        self.stdout.write("Seeding standard observation frequencies...")
        frequencies = [
            {"code": "TICK", "name": "Tick-by-Tick", "interval": 0, "regular": False, "desc": "Real-time market ticks"},
            {"code": "1S", "name": "1-Second", "interval": 1, "regular": True, "desc": "High-frequency aggregate bars"},
            {"code": "1M", "name": "1-Minute", "interval": 60, "regular": True, "desc": "1-Minute intraday bars"},
            {"code": "5M", "name": "5-Minute", "interval": 300, "regular": True, "desc": "5-Minute intraday bars"},
            {"code": "15M", "name": "15-Minute", "interval": 900, "regular": True, "desc": "15-Minute intraday bars"},
            {"code": "30M", "name": "30-Minute", "interval": 1800, "regular": True, "desc": "30-Minute trading session bars"},
            {"code": "1H", "name": "1-Hour", "interval": 3600, "regular": True, "desc": "Hourly bars"},
            {"code": "2H", "name": "2-Hour", "interval": 7200, "regular": True, "desc": "2-Hour aggregate bars"},
            {"code": "4H", "name": "4-Hour", "interval": 14400, "regular": True, "desc": "4-Hour swing trading bars"},
            {"code": "DAILY", "name": "Daily", "interval": 86400, "regular": True, "desc": "Daily settlement / close"},
            {"code": "WEEKLY", "name": "Weekly", "interval": 604800, "regular": True, "desc": "Weekly reports (EIA, CFTC, Baker Hughes)"},
            {"code": "MONTHLY", "name": "Monthly", "interval": 2592000, "regular": True, "desc": "Monthly agency reports (WASDE, OPEC MOMR)"},
            {"code": "QUARTERLY", "name": "Quarterly", "interval": 7776000, "regular": True, "desc": "Quarterly financial / trade statistics"},
            {"code": "ANNUAL", "name": "Annual", "interval": 31536000, "regular": True, "desc": "Annual reserves & balances"},
            {"code": "EVENT_DRIVEN", "name": "Event-Driven", "interval": None, "regular": False, "desc": "Ad-hoc news and unexpected events"},
        ]
        for f in frequencies:
            FrequencyMaster.objects.update_or_create(
                code=f["code"],
                defaults={
                    "name": f["name"],
                    "standard_interval_seconds": f["interval"],
                    "is_regular": f["regular"],
                    "description": f["desc"],
                },
            )
        self.stdout.write(f"  -> Total Frequencies: {FrequencyMaster.objects.count()}")

    def _seed_units(self):
        self.stdout.write("Seeding commodity units of measure (UOM)...")

        # Base units first
        base_units = [
            # Volume base: Barrel (42 US gallons)
            {"code": "BBL", "name": "Barrels", "symbol": "bbl", "type": UnitType.VOLUME, "desc": "Standard 42-gallon crude barrel"},
            # Natural Gas volume base: MCF (Thousand Cubic Feet)
            {"code": "MCF", "name": "Thousand Cubic Feet", "symbol": "Mcf", "type": UnitType.VOLUME, "desc": "Base volume for natural gas pipeline measurement"},
            # Mass base: Metric Ton (1000 kg)
            {"code": "MT", "name": "Metric Tons", "symbol": "t", "type": UnitType.MASS, "desc": "1,000 kilograms"},
            # Energy base: MMBtu (Million British Thermal Units)
            {"code": "MMBTU", "name": "Million British Thermal Units", "symbol": "MMBtu", "type": UnitType.ENERGY, "desc": "Standard gas energy measure"},
            # Currency base: USD
            {"code": "USD", "name": "US Dollar", "symbol": "$", "type": UnitType.CURRENCY, "desc": "Primary global commodity quote currency"},
            # Ratio base: Unitless Ratio
            {"code": "RATIO", "name": "Unitless Ratio", "symbol": "", "type": UnitType.RATIO, "desc": "Standard mathematical ratio"},
            # Index base
            {"code": "INDEX_PTS", "name": "Index Points", "symbol": "pts", "type": UnitType.INDEX, "desc": "Financial index level"},
            # Count base
            {"code": "COUNT", "name": "Unit Count", "symbol": "#", "type": UnitType.COUNT, "desc": "Generic count of units or vessels"},
            # Temperature base: Celsius
            {"code": "DEG_C", "name": "Degrees Celsius", "symbol": "°C", "type": UnitType.TEMPERATURE, "desc": "Celsius temperature"},
        ]

        units_by_code = {}
        for b in base_units:
            obj, _ = UnitMaster.objects.update_or_create(
                code=b["code"],
                defaults={
                    "name": b["name"],
                    "symbol": b["symbol"],
                    "unit_type": b["type"],
                    "base_unit": None,
                    "conversion_factor": Decimal("1.0"),
                    "description": b["desc"],
                },
            )
            # Self-reference base_unit
            if not obj.base_unit_id:
                obj.base_unit = obj
                obj.save(update_fields=["base_unit"])
            units_by_code[b["code"]] = obj

        # Derived units
        derived_units = [
            # Volume derived from BBL
            {"code": "MBBL", "name": "Thousand Barrels", "symbol": "kbbl", "type": UnitType.VOLUME, "base": "BBL", "factor": Decimal("1000.0"), "desc": "1,000 Barrels"},
            {"code": "MMBBL", "name": "Million Barrels", "symbol": "MMbbl", "type": UnitType.VOLUME, "base": "BBL", "factor": Decimal("1000000.0"), "desc": "1,000,000 Barrels"},
            {"code": "GAL", "name": "US Gallons", "symbol": "gal", "type": UnitType.VOLUME, "base": "BBL", "factor": Decimal("0.02380952"), "desc": "1 US Gallon = 1/42 bbl"},
            {"code": "L", "name": "Litres", "symbol": "L", "type": UnitType.VOLUME, "base": "BBL", "factor": Decimal("0.00628981"), "desc": "Standard Litre"},

            # Volume derived from MCF (Natural Gas)
            {"code": "MMCF", "name": "Million Cubic Feet", "symbol": "MMcf", "type": UnitType.VOLUME, "base": "MCF", "factor": Decimal("1000.0"), "desc": "1,000 Mcf"},
            {"code": "BCF", "name": "Billion Cubic Feet", "symbol": "Bcf", "type": UnitType.VOLUME, "base": "MCF", "factor": Decimal("1000000.0"), "desc": "1,000,000 Mcf - EIA weekly storage quote standard"},
            {"code": "TCF", "name": "Trillion Cubic Feet", "symbol": "Tcf", "type": UnitType.VOLUME, "base": "MCF", "factor": Decimal("1000000000.0"), "desc": "National gas reserves"},

            # Mass derived from MT
            {"code": "KG", "name": "Kilograms", "symbol": "kg", "type": UnitType.MASS, "base": "MT", "factor": Decimal("0.001"), "desc": "1 Kilogram = 0.001 MT"},
            {"code": "G", "name": "Grams", "symbol": "g", "type": UnitType.MASS, "base": "MT", "factor": Decimal("0.000001"), "desc": "1 Gram = 0.000001 MT"},
            {"code": "LB", "name": "Pounds", "symbol": "lb", "type": UnitType.MASS, "base": "MT", "factor": Decimal("0.00045359"), "desc": "1 Avoirdupois Pound"},
            {"code": "BU", "name": "Bushels (Grain average)", "symbol": "bu", "type": UnitType.MASS, "base": "MT", "factor": Decimal("0.02540117"), "desc": "Average grain bushel ~ 56 lbs"},
            {"code": "CWT", "name": "Hundredweight", "symbol": "cwt", "type": UnitType.MASS, "base": "MT", "factor": Decimal("0.04535924"), "desc": "100 lbs - CME Livestock & Rice quote unit"},
            {"code": "BALES", "name": "Cotton Bales (480-lb)", "symbol": "bales", "type": UnitType.MASS, "base": "MT", "factor": Decimal("0.21772434"), "desc": "Standard 480-lb cotton bale"},
            {"code": "TOZ", "name": "Troy Ounces", "symbol": "oz t", "type": UnitType.MASS, "base": "MT", "factor": Decimal("0.00003110"), "desc": "Precious metals troy ounce (31.1035g)"},

            # Energy derived from MMBTU
            {"code": "GJ", "name": "Gigajoules", "symbol": "GJ", "type": UnitType.ENERGY, "base": "MMBTU", "factor": Decimal("0.94781712"), "desc": "1 Gigajoule ~ 0.9478 MMBtu"},
            {"code": "MWH", "name": "Megawatt-Hours", "symbol": "MWh", "type": UnitType.ENERGY, "base": "MMBTU", "factor": Decimal("3.41214163"), "desc": "1 MWh = 3.412 MMBtu"},
            {"code": "THERM", "name": "Therms", "symbol": "thm", "type": UnitType.ENERGY, "base": "MMBTU", "factor": Decimal("0.1"), "desc": "1 Therm = 0.1 MMBtu"},
            {"code": "BOE", "name": "Barrels of Oil Equivalent", "symbol": "boe", "type": UnitType.ENERGY, "base": "MMBTU", "factor": Decimal("5.8"), "desc": "1 BOE ~ 5.8 MMBtu energy equivalent"},

            # Currency
            {"code": "EUR", "name": "Euro", "symbol": "€", "type": UnitType.CURRENCY, "base": "USD", "factor": Decimal("1.08"), "desc": "Euro currency"},
            {"code": "GBP", "name": "British Pound", "symbol": "£", "type": UnitType.CURRENCY, "base": "USD", "factor": Decimal("1.29"), "desc": "British Pound"},
            {"code": "CNY", "name": "Chinese Yuan", "symbol": "¥", "type": UnitType.CURRENCY, "base": "USD", "factor": Decimal("0.14"), "desc": "Renminbi / Yuan"},
            {"code": "BRL", "name": "Brazilian Real", "symbol": "R$", "type": UnitType.CURRENCY, "base": "USD", "factor": Decimal("0.18"), "desc": "Brazilian Real (B3 quote currency)"},
            {"code": "MYR", "name": "Malaysian Ringgit", "symbol": "RM", "type": UnitType.CURRENCY, "base": "USD", "factor": Decimal("0.23"), "desc": "Malaysian Ringgit (BMD Palm Oil quote currency)"},
            {"code": "AED", "name": "UAE Dirham", "symbol": "د.إ", "type": UnitType.CURRENCY, "base": "USD", "factor": Decimal("0.2723"), "desc": "UAE Dirham (ICE Abu Dhabi base)"},
            {"code": "INR", "name": "Indian Rupee", "symbol": "₹", "type": UnitType.CURRENCY, "base": "USD", "factor": Decimal("0.012"), "desc": "Indian Rupee (MCX quote currency)"},
            {"code": "JPY", "name": "Japanese Yen", "symbol": "¥", "type": UnitType.CURRENCY, "base": "USD", "factor": Decimal("0.0067"), "desc": "Japanese Yen (TOCOM/OSE quote currency)"},

            # Price per Unit
            {"code": "USD_BBL", "name": "US Dollars per Barrel", "symbol": "$/bbl", "type": UnitType.PRICE_PER_UNIT, "base": None, "factor": Decimal("1.0"), "desc": "Crude oil / refined products price quote"},
            {"code": "USD_MT", "name": "US Dollars per Metric Ton", "symbol": "$/t", "type": UnitType.PRICE_PER_UNIT, "base": None, "factor": Decimal("1.0"), "desc": "Bulk metals & agricultural freight quote"},
            {"code": "USD_MMBTU", "name": "US Dollars per MMBtu", "symbol": "$/MMBtu", "type": UnitType.PRICE_PER_UNIT, "base": None, "factor": Decimal("1.0"), "desc": "Natural gas / LNG benchmark quote"},
            {"code": "USC_BU", "name": "US Cents per Bushel", "symbol": "¢/bu", "type": UnitType.PRICE_PER_UNIT, "base": None, "factor": Decimal("1.0"), "desc": "CME grains price quote convention"},
            {"code": "USC_LB", "name": "US Cents per Pound", "symbol": "¢/lb", "type": UnitType.PRICE_PER_UNIT, "base": None, "factor": Decimal("1.0"), "desc": "COMEX Copper, ICE Sugar #11, Coffee, Cotton"},
            {"code": "USD_CWT", "name": "US Dollars per Hundredweight", "symbol": "$/cwt", "type": UnitType.PRICE_PER_UNIT, "base": None, "factor": Decimal("1.0"), "desc": "CME Live Cattle, Feeder Cattle, Lean Hogs"},
            {"code": "USD_TOZ", "name": "US Dollars per Troy Ounce", "symbol": "$/oz t", "type": UnitType.PRICE_PER_UNIT, "base": None, "factor": Decimal("1.0"), "desc": "Precious metals spot & futures price quote"},
            {"code": "USD_MWH", "name": "US Dollars per Megawatt-Hour", "symbol": "$/MWh", "type": UnitType.PRICE_PER_UNIT, "base": None, "factor": Decimal("1.0"), "desc": "Electricity power contract quote"},
            {"code": "USD_DAY", "name": "US Dollars per Day", "symbol": "$/day", "type": UnitType.PRICE_PER_UNIT, "base": None, "factor": Decimal("1.0"), "desc": "Baltic Dry Exchange daily vessel time charter rate"},
            {"code": "WS_PTS", "name": "Worldscale Points", "symbol": "WS", "type": UnitType.PRICE_PER_UNIT, "base": None, "factor": Decimal("1.0"), "desc": "Dirty & Clean tanker freight index points"},

            # Ratios
            {"code": "PERCENT", "name": "Percentage", "symbol": "%", "type": UnitType.RATIO, "base": "RATIO", "factor": Decimal("0.01"), "desc": "1% = 0.01"},
            {"code": "BPS", "name": "Basis Points", "symbol": "bps", "type": UnitType.RATIO, "base": "RATIO", "factor": Decimal("0.0001"), "desc": "1 bps = 0.0001"},

            # Temperature
            {"code": "DEG_F", "name": "Degrees Fahrenheit", "symbol": "°F", "type": UnitType.TEMPERATURE, "base": "DEG_C", "factor": Decimal("1.0"), "desc": "Fahrenheit temperature"},
            {"code": "HDD", "name": "Heating Degree Days", "symbol": "HDD", "type": UnitType.TEMPERATURE, "base": None, "factor": Decimal("1.0"), "desc": "Weather demand metric for heating"},
            {"code": "CDD", "name": "Cooling Degree Days", "symbol": "CDD", "type": UnitType.TEMPERATURE, "base": None, "factor": Decimal("1.0"), "desc": "Weather demand metric for air conditioning"},
        ]

        for d in derived_units:
            base_obj = units_by_code.get(d["base"]) if d["base"] else None
            UnitMaster.objects.update_or_create(
                code=d["code"],
                defaults={
                    "name": d["name"],
                    "symbol": d["symbol"],
                    "unit_type": d["type"],
                    "base_unit": base_obj,
                    "conversion_factor": d["factor"],
                    "description": d["desc"],
                },
            )

        self.stdout.write(f"  -> Total Units of Measure: {UnitMaster.objects.count()}")
