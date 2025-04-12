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
        r"(?i)^(inventory\s*(?:number|code|id))$"
    ],
    
    "Short Description": [
        r"(?i)^(short\s*desc|brief\s*desc|title|product\s*name|item\s*name|name|description\s*\(short\))$",
        r"(?i)^(product\s*title|item\s*title|short\s*title|short\s*text|headline)$"
    ],
    
    "Long Description": [
        r"(?i)^(long\s*desc|detailed\s*desc|full\s*desc|product\s*desc|item\s*desc|description|product\s*description|item\s*description|desc|details|full\s*description)$",
        r"(?i)^(features|specifications|product\s*details|extended\s*description|product\s*information)$",
        r"(?i)^(tech\s*specs|technical\s*description|full\s*text|product\s*specs)$"
    ],
    
    "Model": [
        r"(?i)^(model|model\s*(?:code|number|#|no))$",
        r"(?i)^(version|product\s*model|device\s*model)$"
    ],
    
    "Category Group": [
        r"(?i)^(category\s*group|main\s*category|top\s*category|product\s*group|dept|department|division)$",
        r"(?i)^(product\s*line|major\s*category|product\s*class|primary\s*category)$"
    ],
    
    "Category": [
        r"(?i)^(category|sub\s*category|product\s*category|product\s*type|group|family)$",
        r"(?i)^(class|classification|segment|product\s*segment|section)$"
    ],
    
    "Manufacturer": [
        r"(?i)^(manufacturer|brand|maker|vendor|supplier|producer|company)$",
        r"(?i)^(oem|original\s*manufacturer|provider|source|origin)$"
    ],
    
    "Manufacturer SKU": [
        r"(?i)^(mfr\s*(?:part|#|number|code|sku)|manufacturer\s*(?:part|#|number|code|sku)|vendor\s*(?:part|#|number|code|sku)|oem\s*(?:part|#|number|code))$",
        r"(?i)^(brand\s*(?:sku|number|code)|maker\s*(?:part|#|number|code)|external\s*(?:sku|id))$"
    ],
    
    "Image URL": [
        r"(?i)^(image\s*(?:url|link|path)|photo\s*(?:url|link|path)|picture\s*(?:url|link|path)|img\s*(?:url|link|path)|product\s*(?:image|photo|picture))$",
        r"(?i)^(image|photo|picture|img|thumbnail|main\s*image)$"
    ],
    
    "Document Name": [
        r"(?i)^(document\s*name|doc\s*name|file\s*name|manual\s*name|spec\s*sheet\s*name)$",
        r"(?i)^(pdf\s*name|attachment\s*name|documentation\s*name)$"
    ],
    
    "Document URL": [
        r"(?i)^(document\s*(?:url|link|path)|doc\s*(?:url|link|path)|manual\s*(?:url|link|path)|spec\s*(?:url|link|path)|pdf\s*(?:url|link|path))$",
        r"(?i)^(documentation\s*(?:url|link)|attachment\s*(?:url|link)|data\s*sheet\s*(?:url|link))$"
    ],
    
    "Unit Of Measure": [
        r"(?i)^(uom|unit\s*(?:of\s*measure|measure|type)|sell\s*unit|packaging|pack\s*size|quantity\s*unit)$",
        r"(?i)^(measurement\s*unit|sales\s*unit|unit\s*size|package\s*type|qty\s*unit)$"
    ],
    
    # Price field patterns - critical for accurate price detection
    "Buy Cost": [
        r"(?i)^((?:buy|cost|wholesale|net|dealer|base)\s*(?:cost|price)|(?:cost|price)\s*(?:to|for)\s*(?:buy|dealer|distributor|reseller)|cost|price|unit\s*cost)$",
        r"(?i)^(landed\s*cost|purchase\s*price|acquisition\s*cost|inventory\s*cost|stock\s*cost)$",
        r"(?i)^(direct\s*cost|factory\s*price|ex-works\s*price|supply\s*price)$"
    ],
    
    "Trade Price": [
        r"(?i)^((?:trade|dealer|distributor|reseller)\s*(?:cost|price)|price\s*(?:to|for)\s*(?:trade|dealer|distributor|reseller))$",
        r"(?i)^(wholesale\s*price|b2b\s*price|commercial\s*price|partner\s*price|channel\s*price)$",
        r"(?i)^(net\s*price|discount\s*price|special\s*price|contractor\s*price)$"
    ],
    
    # Currency-specific MSRP patterns
    "MSRP GBP": [
        r"(?i)^((?:msrp|srp|rrp|list|retail|resale|recommended|suggested)\s*(?:price|cost)\s*(?:\(gbp\)|gbp|£|pounds?))$",
        r"(?i)^((?:price|cost)\s*(?:gbp|£|pounds?))$",
        r"(?i)^(uk\s*(?:price|retail|msrp|rrp))$",
        r"(?i)^(gbp|£|pounds?)$"
    ],
    
    "MSRP USD": [
        r"(?i)^((?:msrp|srp|rrp|list|retail|resale|recommended|suggested)\s*(?:price|cost)\s*(?:\(usd\)|usd|\$|dollars?))$",
        r"(?i)^((?:price|cost)\s*(?:usd|\$|dollars?))$",
        r"(?i)^(us\s*(?:price|retail|msrp|rrp))$",
        r"(?i)^(usd|\$|dollars?)$"
    ],
    
    "MSRP EUR": [
        r"(?i)^((?:msrp|srp|rrp|list|retail|resale|recommended|suggested)\s*(?:price|cost)\s*(?:\(eur\)|eur|€|euros?))$",
        r"(?i)^((?:price|cost)\s*(?:eur|€|euros?))$",
        r"(?i)^(eu\s*(?:price|retail|msrp|rrp))$",
        r"(?i)^(eur|€|euros?)$"
    ],
    
    "Discontinued": [
        r"(?i)^(discontinued|obsolete|eol|end\s*of\s*life|inactive|status)$",
        r"(?i)^(available|in\s*stock|active|discontinued\s*(?:flag|indicator))$"
    ]
}

# Generic MSRP pattern - used when currency is unclear
GENERIC_MSRP_PATTERNS = [
    r"(?i)^(msrp|srp|rrp|list\s*price|retail\s*price|resale\s*price|recommended\s*price|suggested\s*price)$",
    r"(?i)^(public\s*price|consumer\s*price|end\s*user\s*price|advertised\s*price|catalog\s*price)$"
]

# Special patterns for price hints in row-based format (when prices are in rows instead of columns)
ROW_PRICE_PATTERNS = {
    "Buy Cost": [
        r"(?i)(buy|cost|wholesale|net|dealer|base)(?:\s|-)(?:cost|price)",
        r"(?i)(cost|price)(?:\s|-)(?:to|for)(?:\s|-)(?:buy|dealer|distributor|reseller)",
        r"(?i)\b(cost|landed\s*cost|purchase\s*price)\b"
    ],
    "Trade Price": [
        r"(?i)(trade|dealer|distributor|reseller)(?:\s|-)(?:cost|price)",
        r"(?i)(price)(?:\s|-)(?:to|for)(?:\s|-)(?:trade|dealer|distributor|reseller)",
        r"(?i)\b(wholesale\s*price|b2b\s*price)\b"
    ],
    "MSRP": [
        r"(?i)(msrp|srp|rrp|list|retail|resale|recommended|suggested)(?:\s|-)(?:price|cost)",
        r"(?i)\b(public\s*price|consumer\s*price|retail)\b"
    ]
}

# Currency symbols and abbreviations for detection
CURRENCY_INDICATORS = {
    "GBP": ["£", "GBP", "pounds", "pound", "uk", "british"],
    "USD": ["$", "USD", "dollars", "dollar", "us", "american"],
    "EUR": ["€", "EUR", "euros", "euro", "eu", "european"]
}