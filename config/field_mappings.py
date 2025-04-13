#!/usr/bin/env python3
"""
Configuration file containing pattern definitions for mapping source columns to target fields.
Easily update this file to improve field detection accuracy without changing core logic.
"""

# Regular expression patterns for field detection
# Each target field has multiple possible patterns to match different naming conventions
FIELD_PATTERNS = {
    "SKU": [
        r"(?i)^(sku|item\s*(?:code|number|#|no)|product\s*(?:code|number|#|no)|part\s*(?:code|number|#|no)|stock\s*(?:code|number))$",
        r"(?i)^(article\s*(?:number|code|#|no)|catalog\s*(?:number|code|#|no)|reference\s*(?:number|code))$",
        r"(?i)^(inventory\s*(?:number|code|id)|prod[\.\_\-]?id|item[\.\_\-]?id|p[\.\_\-]?id|mpn)$",
        r"(?i)\b(sku|item\s*(?:code|number|#|no)|product\s*(?:code|number|#|no)|part\s*(?:code|number|#|no))\b"
    ],
    
    "Short Description": [
        r"(?i)^(short\s*desc|brief\s*desc|title|product\s*name|item\s*name|name|description\s*\(short\))$",
        r"(?i)^(product\s*title|item\s*title|short\s*title|short\s*text|headline)$",
        r"(?i)\b(short\s*desc|product\s*name|item\s*name|title)\b",
        r"(?i)^(name|headline|title)$"
    ],
    
    "Long Description": [
        r"(?i)^(long\s*desc|detailed\s*desc|full\s*desc|product\s*desc|item\s*desc|description|product\s*description|item\s*description|desc|details|full\s*description)$",
        r"(?i)^(features|specifications|product\s*details|extended\s*description|product\s*information)$",
        r"(?i)^(tech\s*specs|technical\s*description|full\s*text|product\s*specs)$",
        r"(?i)\b(long\s*desc|detailed\s*desc|full\s*desc|full\s*description|detailed\s*description)\b",
        r"(?i)(?<!short\s)(?<!product\s)(?<!item\s)\b(description)\b"
    ],
    
    "Model": [
        r"(?i)^(model|model\s*(?:code|number|#|no))$",
        r"(?i)^(version|product\s*model|device\s*model)$",
        r"(?i)\b(model\s*(?:code|number|#|no)|prod[\._\-]?model)\b"
    ],
    
    "Category Group": [
        r"(?i)^(category\s*group|main\s*category|top\s*category|product\s*group|dept|department|division|group)$",
        r"(?i)^(product\s*line|major\s*category|product\s*class|primary\s*category|series)$",
        r"(?i)\b(main\s*category|top\s*category|category\s*group|product\s*group)\b"
    ],
    
    "Category": [
        r"(?i)^(category|sub\s*category|product\s*category|product\s*type|group|family|system)$",
        r"(?i)^(class|classification|segment|product\s*segment|section)$",
        r"(?i)\b(category|prod[\._\-]?category|product\s*category)\b"
    ],
    
    "Manufacturer": [
        r"(?i)^(manufacturer|brand|maker|vendor|supplier|producer|company)$",
        r"(?i)^(oem|original\s*manufacturer|provider|source|origin)$",
        r"(?i)\b(manufacturer|brand|maker|vendor)\b",
        r"(?i)(?<!manufacturer\s)(?<!brand\s)\b(name)\b"
    ],
    
    "Manufacturer SKU": [
        r"(?i)^(mfr\s*(?:part|#|number|code|sku)|manufacturer\s*(?:part|#|number|code|sku)|vendor\s*(?:part|#|number|code|sku)|oem\s*(?:part|#|number|code))$",
        r"(?i)^(brand\s*(?:sku|number|code)|maker\s*(?:part|#|number|code)|external\s*(?:sku|id)|mpn)$",
        r"(?i)\b(mfr\s*(?:part|#|number|sku)|manufacturer\s*(?:part|#|number|sku)|vendor\s*(?:part|#|number|code))\b",
        r"(?i)\b(manufacturer[\._\-]?sku|vendor[\._\-]?sku|mfr[\._\-]?sku|mpn)\b"
    ],
    
    "Image URL": [
        r"(?i)^(image\s*(?:url|link|path)|photo\s*(?:url|link|path)|picture\s*(?:url|link|path)|img\s*(?:url|link|path)|product\s*(?:image|photo|picture))$",
        r"(?i)^(image|photo|picture|img|thumbnail|main\s*image|product\s*image)$",
        r"(?i)\b(image\s*(?:url|link|path)|photo\s*(?:url|link|path))\b",
        r"(?i)\b(img|image|photo|picture)(?:$|[\._\-])"
    ],
    
    "Document Name": [
        r"(?i)^(document\s*name|doc\s*name|file\s*name|manual\s*name|spec\s*sheet\s*name)$",
        r"(?i)^(pdf\s*name|attachment\s*name|documentation\s*name|document)$",
        r"(?i)\b(document\s*name|doc\s*name|manual\s*name)\b"
    ],
    
    "Document URL": [
        r"(?i)^(document\s*(?:url|link|path)|doc\s*(?:url|link|path)|manual\s*(?:url|link|path)|spec\s*(?:url|link|path)|pdf\s*(?:url|link|path)|document\s*url)$",
        r"(?i)^(documentation\s*(?:url|link)|attachment\s*(?:url|link)|data\s*sheet\s*(?:url|link))$",
        r"(?i)\b(document\s*(?:url|link|path)|manual\s*(?:url|link|path)|pdf\s*(?:url|link|path))\b",
        r"(?i)\b(document|manual|pdf)(?:$|[\._\-])"
    ],
    
    "Unit Of Measure": [
        r"(?i)^(uom|unit\s*(?:of\s*measure|measure|type)|sell\s*unit|packaging|pack\s*size|quantity\s*unit)$",
        r"(?i)^(measurement\s*unit|sales\s*unit|unit\s*size|package\s*type|qty\s*unit)$",
        r"(?i)\b(uom|unit\s*(?:of\s*measure|measure)|packaging)\b",
        r"(?i)(?<!weight\s)(?<!dimension\s)\b(unit)\b"
    ],
    
    # Price field patterns - critical for accurate price detection
    "Buy Cost": [
        r"(?i)^((?:buy|cost|wholesale|net|dealer|base)\s*(?:cost|price)|(?:cost|price)\s*(?:to|for)\s*(?:buy|dealer|distributor|reseller)|cost|price|unit\s*cost|dealer\s*cost)$",
        r"(?i)^(landed\s*cost|purchase\s*price|acquisition\s*cost|inventory\s*cost|stock\s*cost)$",
        r"(?i)^(direct\s*cost|factory\s*price|ex-works\s*price|supply\s*price)$",
        r"(?i)\b(buy\s*cost|cost\s*price|wholesale\s*cost|dealer\s*cost)\b",
        r"(?i)(?<!retail\s)(?<!sell\s)(?<!list\s)(?<!resale\s)\b(cost|price)\b"
    ],
    
    "Trade Price": [
        r"(?i)^((?:trade|dealer|distributor|reseller)\s*(?:cost|price)|price\s*(?:to|for)\s*(?:trade|dealer|distributor|reseller))$",
        r"(?i)^(wholesale\s*price|b2b\s*price|commercial\s*price|partner\s*price|channel\s*price)$",
        r"(?i)^(net\s*price|discount\s*price|special\s*price|contractor\s*price)$",
        r"(?i)\b(trade\s*price|dealer\s*price|distributor\s*price|reseller\s*price)\b",
        r"(?i)\b(wholesale\s*price|b2b\s*price|net\s*price|discount\s*price)\b"
    ],
    
    # Generic MSRP pattern - used when currency is unclear
    "MSRP": [
        r"(?i)^(msrp|srp|rrp|list\s*price|retail\s*price|resale\s*price|recommended\s*price|suggested\s*price)$",
        r"(?i)^(public\s*price|consumer\s*price|end\s*user\s*price|advertised\s*price|catalog\s*price|retail)$",
        r"(?i)\b(msrp|srp|rrp|list\s*price|retail\s*price|resale\s*price)\b",
        r"(?i)(?<!\w)(?<!dealer\s)(?<!trade\s)(?<!net\s)\b(price)\b(?!\s*to)(?!\s*for)",
        r"(?i)\b(retail|list|sell\s*price)\b"
    ],
    
    # Currency-specific MSRP patterns
    "MSRP GBP": [
        r"(?i)^((?:msrp|srp|rrp|list|retail|resale|recommended|suggested)\s*(?:price|cost)\s*(?:\(gbp\)|gbp|£|pounds?))$",
        r"(?i)^((?:price|cost)\s*(?:gbp|£|pounds?)|retail\s*gbp)$",
        r"(?i)^(uk\s*(?:price|retail|msrp|rrp))$",
        r"(?i)^(gbp|£|pounds?|price\s*gbp)$",
        r"(?i)\b((?:msrp|srp|rrp|list|retail)\s*(?:price|cost)\s*(?:gbp|£|pounds?))\b",
        r"(?i)\b(uk\s*(?:price|retail)|gbp\s*(?:price|retail))\b",
        r"(?i)\b(price\s*(?:gbp|£|in\s*pounds)|retail\s*(?:gbp|£))\b"
    ],
    
    "MSRP USD": [
        r"(?i)^((?:msrp|srp|rrp|list|retail|resale|recommended|suggested)\s*(?:price|cost)\s*(?:\(usd\)|usd|\$|dollars?))$",
        r"(?i)^((?:price|cost)\s*(?:usd|\$|dollars?)|retail\s*usd|price\s*usd)$",
        r"(?i)^(us\s*(?:price|retail|msrp|rrp))$",
        r"(?i)^(usd|\$|dollars?)$",
        r"(?i)\b((?:msrp|srp|rrp|list|retail)\s*(?:price|cost)\s*(?:usd|\$|dollars?))\b",
        r"(?i)\b(us\s*(?:price|retail)|usd\s*(?:price|retail))\b",
        r"(?i)\b(price\s*(?:usd|\$|in\s*dollars)|retail\s*(?:usd|\$))\b"
    ],
    
    "MSRP EUR": [
        r"(?i)^((?:msrp|srp|rrp|list|retail|resale|recommended|suggested)\s*(?:price|cost)\s*(?:\(eur\)|eur|€|euros?))$",
        r"(?i)^((?:price|cost)\s*(?:eur|€|euros?)|retail\s*eur|price\s*eur)$",
        r"(?i)^(eu\s*(?:price|retail|msrp|rrp))$",
        r"(?i)^(eur|€|euros?)$",
        r"(?i)\b((?:msrp|srp|rrp|list|retail)\s*(?:price|cost)\s*(?:eur|€|euros?))\b",
        r"(?i)\b(eu\s*(?:price|retail)|eur\s*(?:price|retail))\b",
        r"(?i)\b(price\s*(?:eur|€|in\s*euros)|retail\s*(?:eur|€))\b"
    ],
    
    "Discontinued": [
        r"(?i)^(discontinued|obsolete|eol|end\s*of\s*life|inactive|status)$",
        r"(?i)^(available|in\s*stock|active|discontinued\s*(?:flag|indicator))$",
        r"(?i)\b(discontinued|obsolete|eol|end\s*of\s*life)\b",
        r"(?i)\b(product\s*status|item\s*status)\b"
    ],
    
    # Additional fields observed in sample data
    "Warranty": [
        r"(?i)^((warranty|guarantee)\s*(period|terms|length)?|(product\s*)?warranty)$",
        r"(?i)^(coverage\s*term|included\s*warranty|support\s*duration)$",
        r"(?i)\b(warranty\s*(period|terms|length)|product\s*warranty)\b"
    ],
    
    "Release Date": [
        r"(?i)^(release|launch|availability|available)\s*(date)?$",
        r"(?i)^(market\s*date|first\s*available|intro\s*date)$",
        r"(?i)\b(release\s*date|launch\s*date|availability\s*date)\b",
        r"(?i)\b(date\s*(?:of|available|released))\b"
    ],
    
    "Color": [
        r"(?i)^(colou?r|finish|shade|paint)$",
        r"(?i)^(housing\s*colo?r|enclosure\s*finish|product\s*colo?r)$",
        r"(?i)\b(colo?r|finish|product\s*colo?r)\b"
    ],
    
    "Dimensions": [
        r"(?i)^(dimensions?|size|height|width|depth|length)$",
        r"(?i)^(product\s*(size|dimensions)|overall\s*dimensions)$",
        r"(?i)\b(dimensions?|product\s*dimensions|size\s*(?:h\s*x\s*w\s*x\s*d))\b",
        r"(?i)\b(height|width|depth|length)\b(?!\s*unit)"
    ],
    
    "Weight": [
        r"(?i)^(weight|product\s*weight|net\s*weight|gross\s*weight|shipping\s*weight)$",
        r"(?i)\b(weight|product\s*weight|net\s*weight|gross\s*weight)\b(?!\s*unit)"
    ],
    
    "Power": [
        r"(?i)^(power|wattage|output\s*power|power\s*rating|power\s*output)$",
        r"(?i)\b(power\s*consumption|power\s*usage|wattage|power\s*rating)\b"
    ],
    
    "Frequency Response": [
        r"(?i)^(frequency\s*(?:response|range|spectrum)|freq\s*resp|audio\s*range)$",
        r"(?i)\b(frequency\s*(?:response|range)|freq\s*resp)\b"
    ],
    
    "Coverage": [
        r"(?i)^(coverage|coverage\s*(?:angle|pattern)|dispersion)$",
        r"(?i)\b(coverage\s*(?:angle|pattern)|dispersion\s*(?:angle|pattern))\b"
    ],
    
    "Max SPL": [
        r"(?i)^(max\s*(?:spl|sound\s*pressure\s*level)|max\s*output|output\s*level)$",
        r"(?i)\b(max\s*spl|maximum\s*spl|peak\s*spl|spl\s*max)\b"
    ],
    
    "Channels": [
        r"(?i)^(channels|audio\s*channels|i\/o|inputs\s*outputs)$",
        r"(?i)\b(channels|number\s*of\s*channels|channel\s*count)\b"
    ],
    
    # Additional fields for training/services catalog
    "Group": [
        r"(?i)^(group|product\s*group|category\s*group|department)$",
        r"(?i)\b(group\s*name|group\s*id|product\s*group)\b"
    ],
    
    "Series": [
        r"(?i)^(series|product\s*series|model\s*series|family)$",
        r"(?i)\b(series\s*name|series\s*id|product\s*series)\b"
    ],
    
    "System": [
        r"(?i)^(system|product\s*system|solution)$",
        r"(?i)\b(system\s*name|system\s*id|product\s*system)\b"
    ],
    
    "Product": [
        r"(?i)^(product|item|part)$",
        r"(?i)\b(product\s*type|product\s*id)\b"
    ],
    
    "Retail GBP": [
        r"(?i)^(retail\s*(?:gbp|£|pounds?)|gbp|price\s*gbp|uk\s*price)$",
        r"(?i)\b(retail\s*(?:gbp|£|pounds?)|price\s*(?:gbp|£))\b"
    ]
}

# Special patterns for price hints in row-based format (when prices are in rows instead of columns)
ROW_PRICE_PATTERNS = {
    "Buy Cost": [
        r"(?i)(buy|cost|wholesale|net|dealer|base)(?:\s|-)(?:cost|price)",
        r"(?i)(cost|price)(?:\s|-)(?:to|for)(?:\s|-)(?:buy|dealer|distributor|reseller)",
        r"(?i)\b(cost|landed\s*cost|purchase\s*price|dealer\s*cost)\b",
        r"(?i)\b(buy\s*cost|cost\s*price|supply\s*price|inventory\s*cost)\b"
    ],
    "Trade Price": [
        r"(?i)(trade|dealer|distributor|reseller)(?:\s|-)(?:cost|price)",
        r"(?i)(price)(?:\s|-)(?:to|for)(?:\s|-)(?:trade|dealer|distributor|reseller)",
        r"(?i)\b(wholesale\s*price|b2b\s*price|trade\s*price|dealer\s*price)\b",
        r"(?i)\b(distributor\s*price|channel\s*price|partner\s*price)\b"
    ],
    "MSRP": [
        r"(?i)(msrp|srp|rrp|list|retail|resale|recommended|suggested)(?:\s|-)(?:price|cost)",
        r"(?i)\b(public\s*price|consumer\s*price|retail|sell\s*price|user\s*price)\b",
        r"(?i)\b(list\s*price|retail\s*price|msrp|rrp|srp)\b"
    ]
}

# Currency symbols and abbreviations for detection
CURRENCY_INDICATORS = {
    "GBP": ["£", "GBP", "pounds", "pound", "uk", "british", "sterling"],
    "USD": ["$", "USD", "dollars", "dollar", "us", "american", "usd$"],
    "EUR": ["€", "EUR", "euros", "euro", "eu", "european", "eur€"],
    "CAD": ["CAD", "C$", "canadian", "can", "cad$"],
    "AUD": ["AUD", "A$", "australian", "aus", "aud$"],
    "JPY": ["JPY", "¥", "yen", "japanese", "jpy¥"]
}

# Content-based currency detection patterns
CURRENCY_VALUE_PATTERNS = {
    "GBP": [r"£\s*[\d,]+(?:\.\d{2})?", r"gbp\s*[\d,]+(?:\.\d{2})?", r"[\d,]+(?:\.\d{2})?\s*pounds"],
    "USD": [r"\$\s*[\d,]+(?:\.\d{2})?", r"usd\s*[\d,]+(?:\.\d{2})?", r"[\d,]+(?:\.\d{2})?\s*dollars"],
    "EUR": [r"€\s*[\d,]+(?:\.\d{2})?", r"eur\s*[\d,]+(?:\.\d{2})?", r"[\d,]+(?:\.\d{2})?\s*euros?"]
}

# Manufacturer-specific custom patterns
MANUFACTURER_CUSTOM_PATTERNS = {
    "L-Acoustics": {
        "Training Product": [
            r"(?i)^training.*session", r"(?i)^seminar.*session", r"(?i)^education.*license",
            r"(?i)^training1seat", r"(?i)^seminar1seat"
        ],
        "Support Service": [
            r"(?i)^ambiance\s*(8|16|32)", r"(?i)^calibration$", r"(?i)^system\s*handover", 
            r"(?i)^show\s*support", r"(?i)^l-isa\s*show\s*support"
        ],
        "Travel": [
            r"(?i)^travel-", r"(?i)^travel\s*(short|medium|long|extra|local)"
        ],
        "Rental": [
            r"(?i)^.*rental", r"(?i)^.*studio\s*rental", r"(?i)^.*auditorium\s*rental"
        ]
    },
    "Adam Hall": {
        "Hardware": [
            r"(?i)^.*hardware.*", r"(?i)^.*accessories.*"
        ],
        "Textiles": [
            r"(?i)^.*molton.*", r"(?i)^.*cloth.*"
        ]
    },
    "Bose Professional": {
        "Portable PA": [
            r"(?i)^.*portable.*", r"(?i)^.*pa\s*system.*", r"(?i)^.*line\s*array\s*system.*"
        ],
        "Installed Sound": [
            r"(?i)^.*installed.*", r"(?i)^.*in-ceiling.*", r"(?i)^.*loudspeaker.*"
        ],
        "Electronics": [
            r"(?i)^.*amplifier.*", r"(?i)^.*processor.*"
        ],
        "Accessories": [
            r"(?i)^.*bracket.*", r"(?i)^.*bridge.*", r"(?i)^.*cable.*", r"(?i)^.*connector.*"
        ]
    }
}
    # Generic patterns for MSRP detection regardless of currency
GENERIC_MSRP_PATTERNS = [
    r"(?i)^(msrp|m\.?s\.?r\.?p\.?)$",
    r"(?i)^(manufacturer.?s?\s*suggested\s*retail\s*price)$",
    r"(?i)^(manufacturer.?s?\s*suggested\s*price)$",
    r"(?i)^(mfr\s*suggested\s*retail\s*price)$", 
    r"(?i)^(suggested\s*retail\s*price|srp)$",
    r"(?i)^(recommended\s*retail\s*price|rrp)$",
    r"(?i)^(list\s*price|retail\s*price|full\s*price)$",
    r"(?i)^(catalog\s*price|published\s*price|advertised\s*price)$",
    r"(?i)^(regular\s*price|reg\s*price|original\s*price|orig\s*price)$",
    r"(?i)^(retail|list|full\s*retail)$",
    r"(?i)^(uvp|pvpr|prix\s*conseill[ée])$",
    r"(?i)^(price\s*\(?msrp\)?|price\s*\(?retail\)?|price\s*\(?list\)?)$",
    r"(?i)^(msrp\s*price|retail\s*msrp|srp\s*price)$",
    r"(?i)^(man\.?\s*sug\.?\s*ret\.?\s*price)$",
    r"(?i)^(mfg\.?\s*sug\.?\s*price)$",
    r"(?i)^(sug\.?\s*ret\.?\s*price)$",
    r"(?i)^(market\s*price|standard\s*price|base\s*price)$",
    r"(?i)^(non\s*sale\s*price|non\s*discounted\s*price)$",
    r"(?i)^(map\s*price|map|minimum\s*advertised\s*price)$",
    r"(?i)^(msrp\s*price|price\s*msrp|retail\s*price)$",
    r"(?i)\b(msrp|m\.?s\.?r\.?p\.?|retail\s*price|list\s*price)\b"
]

# Common header synonyms for smarter pattern matching
HEADER_SYNONYMS = {
    "number": ["no", "#", "num", "code", "id"],
    "product": ["prod", "item", "part", "article"],
    "description": ["desc", "details", "info", "text", "specs", "specification"],
    "price": ["cost", "rate", "amount", "value"],
    "manufacturer": ["brand", "make", "maker", "vendor", "supplier", "company"],
    "category": ["cat", "group", "type", "class", "family", "department"]
}

# Field groups for better organization
FIELD_GROUPS = {
    "Basic Information": ["SKU", "Short Description", "Long Description", "Model", "Category Group", "Category", "Manufacturer", "Manufacturer SKU"],
    "Media": ["Image URL", "Document Name", "Document URL"],
    "Pricing": ["Buy Cost", "Trade Price", "MSRP", "MSRP GBP", "MSRP USD", "MSRP EUR", "Retail GBP"],
    "Product Details": ["Unit Of Measure", "Discontinued", "Warranty", "Release Date", "Color", "Dimensions", "Weight", "Power", "Frequency Response", "Coverage", "Max SPL", "Channels"],
    "Catalog Organization": ["Group", "Series", "System", "Product"]
}

# Required fields for validation
REQUIRED_FIELDS = ["SKU", "Short Description", "Manufacturer"]

# Default values for fields that should have a value
DEFAULT_VALUES = {
    "Discontinued": False,
    "Unit Of Measure": "Each"
}

# Common field value formats for content-based detection
FIELD_VALUE_FORMATS = {
    "SKU": [
        r"^[A-Z0-9]{5,15}$",  # Common format: 5-15 alphanumeric chars
        r"^[A-Z]{2,4}-[0-9]{3,8}$",  # PREFIX-NUMBER format
        r"^[0-9]{3,7}$"  # Simple numeric SKU
    ],
    "Dimensions": [
        r"^\d+(\.\d+)?\s*x\s*\d+(\.\d+)?\s*x\s*\d+(\.\d+)?\s*(mm|cm|m|in|ft)?$",
        r"^[HWD]:\s*\d+(\.\d+)?\s*x\s*\d+(\.\d+)?\s*x\s*\d+(\.\d+)?\s*(mm|cm|m|in|ft)?$"
    ],
    "Weight": [
        r"^\d+(\.\d+)?\s*(kg|g|lb|oz)$",
        r"^[\d\.,]+\s*(kg|g|lb|oz)$"
    ],
    "Discontinued": [
        r"^(yes|no|y|n|true|false|t|f|0|1)$"
    ],
    "Release Date": [
        r"^\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}$",  # DD/MM/YYYY or variants
        r"^\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}$"   # YYYY/MM/DD or variants
    ]
}

# Common field relationships for context-aware mapping
FIELD_RELATIONSHIPS = {
    "MSRP": ["Buy Cost", "Trade Price"],  # These fields often appear together
    "SKU": ["Manufacturer SKU"],  # Often adjacent or nearby
    "Short Description": ["Long Description"],  # Often adjacent
    "Dimensions": ["Weight"],  # Often grouped together
    "Image URL": ["Document URL"]  # Media fields often grouped
}

# Common units for different measurement fields
FIELD_UNITS = {
    "Dimensions": ["mm", "cm", "m", "in", "inches", "feet", "ft"],
    "Weight": ["kg", "g", "lb", "lbs", "oz", "grams", "kilograms", "pounds", "ounces"],
    "Power": ["W", "kW", "mW", "watts", "kilowatts", "milliwatts"],
    "Frequency Response": ["Hz", "kHz", "Hz-kHz", "hertz", "kilohertz"]
}