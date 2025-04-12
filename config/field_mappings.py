#!/usr/bin/env python3
"""
Enhanced configuration file containing pattern definitions for mapping source columns to target fields.
This version focuses on reducing false positives and false negatives with improved pattern specificity,
handling of ambiguous terms, and prioritization rules.
"""

# Regular expression patterns for field detection
# Each target field has multiple possible patterns to match different naming conventions
FIELD_PATTERNS = {
    "SKU": [
        r"(?i)^(sku|item\s*(?:code|number|#|no)|product\s*(?:code|number|#|no)|part\s*(?:code|number|#|no)|stock\s*(?:code|number))$",
        r"(?i)^(article\s*(?:number|code|#|no)|catalog\s*(?:number|code|#|no)|reference\s*(?:number|code))$",
        r"(?i)^(inventory\s*(?:number|code|id)|reference|model\s*number|part\s*id)$",
        r"(?i)^(mpn|mfr\s*#|ean|upc|gtin|isbn)$",
        r"(?i)^((?:^product|^item|^part)$)$"  # Standalone product/item/part but with stricter boundary conditions
    ],
    
    "Short Description": [
        r"(?i)^(short\s*desc(?:ription)?|brief\s*desc(?:ription)?|title|product\s*name|item\s*name|name|description\s*\(short\))$",
        r"(?i)^(product\s*title|item\s*title|short\s*title|short\s*text|headline|caption|summary)$",
        r"(?i)^(label|display\s*name|listing\s*title|short\s*name|brief\s*name)$",
        r"(?i)^((?<!long\s)(?<!full\s)(?<!detailed\s)description(?!\s*(?:long|full|detailed)))$"  # description but not long/full/detailed description
    ],
    
    "Long Description": [
        r"(?i)^(long\s*desc(?:ription)?|detailed\s*desc(?:ription)?|full\s*desc(?:ription)?|product\s*desc(?:ription)?|item\s*desc(?:ription)?)$",
        r"(?i)^(description\s*(?:long|full|detailed)|full\s*description|extended\s*description|complete\s*description)$",
        r"(?i)^(features|specifications|spec(?:s)?|product\s*details|item\s*details|product\s*information|technical\s*details)$",
        r"(?i)^(tech\s*specs|technical\s*description|full\s*text|product\s*specs|feature\s*list|specification(?:s)?)$",
        r"(?i)^(product\s*overview|detailed\s*information|details|product\s*features|comprehensive\s*description)$"
    ],
    
    "Model": [
        r"(?i)^(model|model\s*(?:code|number|#|no)|model\s*name|model\s*id)$",
        r"(?i)^(version|product\s*model|device\s*model|model\s*identifier|model\s*designation)$",
        r"(?i)^(variant|style\s*number|style\s*code|design\s*number|type\s*number)$"
    ],
    
    "Category Group": [
        r"(?i)^(category\s*group|main\s*category|top\s*category|product\s*group|dept|department|division)$",
        r"(?i)^(product\s*line|major\s*category|product\s*class|primary\s*category|category\s*level\s*1)$",
        r"(?i)^(top\s*level\s*category|parent\s*category|category\s*parent|main\s*group|product\s*area)$",
        r"(?i)^(group(?!\s*(?:product|sub|category)))$"  # Group alone, but not followed by product/sub/category
    ],
    
    "Category": [
        r"(?i)^(category(?!\s*group)|sub\s*category|product\s*category|product\s*type|sub\s*group|family)$",
        r"(?i)^(class|classification|segment|product\s*segment|section|category\s*level\s*2)$",
        r"(?i)^(subcategory|sub\s*classification|product\s*family|product\s*subdivision|product\s*class)$",
        r"(?i)^(type|level|tier|grouping|product\s*sector)$"
    ],
    
    "Manufacturer": [
        r"(?i)^(manufacturer|brand|maker|vendor|supplier|producer|company)$",
        r"(?i)^(oem|original\s*manufacturer|provider|source|origin|brand\s*name)$",
        r"(?i)^(made\s*by|manufactured\s*by|created\s*by|built\s*by|developer)$"
    ],
    
    "Manufacturer SKU": [
        r"(?i)^(mfr\s*(?:part|#|number|code|sku)|manufacturer\s*(?:part|#|number|code|sku)|vendor\s*(?:part|#|number|code|sku)|oem\s*(?:part|#|number|code))$",
        r"(?i)^(brand\s*(?:sku|number|code)|maker\s*(?:part|#|number|code)|external\s*(?:sku|id))$",
        r"(?i)^(supplier\s*(?:code|number|id|reference)|factory\s*(?:code|number|id|reference)|original\s*(?:code|number))$",
        r"(?i)^(manufacturer\s*reference|oem\s*ref|vendor\s*reference|producer\s*code|mpn)$"
    ],
    
    "Barcode": [
        r"(?i)^(barcode|ean|upc|ean\s*(?:13|8)|upc\s*(?:a|e)|gtin|isbn)$",
        r"(?i)^(scan\s*code|scanner\s*code|universal\s*product\s*code|european\s*article\s*number)$",
        r"(?i)^(international\s*standard\s*book\s*number|global\s*trade\s*item\s*number)$"
    ],
    
    "Image URL": [
        r"(?i)^(image\s*(?:url|link|path|src|source)|photo\s*(?:url|link|path|src|source)|picture\s*(?:url|link|path|src|source))$",
        r"(?i)^(img\s*(?:url|link|path|src|source)|product\s*(?:image|photo|picture)\s*(?:url|link|path)?)$",
        r"(?i)^(image|photo|picture|img|thumbnail|main\s*image|product\s*image|primary\s*image)$",
        r"(?i)^(image\s*location|photo\s*location|image\s*address|main\s*photo|gallery|image\s*file)$"
    ],
    
    "Document Name": [
        r"(?i)^(document\s*name|doc\s*name|file\s*name|manual\s*name|spec\s*sheet\s*name|document\s*title)$",
        r"(?i)^(pdf\s*name|attachment\s*name|documentation\s*name|document|manual\s*title|guide\s*name)$",
        r"(?i)^(technical\s*document\s*name|spec\s*name|whitepaper\s*name|brochure\s*name)$"
    ],
    
    "Document URL": [
        r"(?i)^(document\s*(?:url|link|path)|doc\s*(?:url|link|path)|manual\s*(?:url|link|path)|spec\s*(?:url|link|path)|pdf\s*(?:url|link|path))$",
        r"(?i)^(documentation\s*(?:url|link)|attachment\s*(?:url|link)|data\s*sheet\s*(?:url|link)|document\s*url)$",
        r"(?i)^(technical\s*(?:doc|document|manual)\s*(?:url|link)|guide\s*(?:url|link)|instruction\s*(?:url|link))$",
        r"(?i)^(brochure\s*(?:url|link)|whitepaper\s*(?:url|link)|catalog\s*(?:url|link)|literature\s*(?:url|link))$"
    ],
    
    "Unit Of Measure": [
        r"(?i)^(uom|unit\s*(?:of\s*measure|measure|type)|sell\s*unit|packaging|pack\s*size|quantity\s*unit)$",
        r"(?i)^(measurement\s*unit|sales\s*unit|unit\s*size|package\s*type|qty\s*unit|order\s*unit)$",
        r"(?i)^(unit|quantity\s*type|base\s*unit|stock\s*unit|inventory\s*unit|sales\s*unit\s*of\s*measure)$",
        r"(?i)^(each|package|piece|set|case|bottle|box|pallet|container)$"
    ],
    
    # Price field patterns - critical for accurate price detection
    "Buy Cost": [
        r"(?i)^((?:buy|cost|wholesale|net|dealer|base)\s*(?:cost|price)|(?:cost|price)\s*(?:to|for)\s*(?:buy|dealer|distributor|reseller))$",
        r"(?i)^(cost(?!\s*(?:retail|public|msrp|srp|rrp))|purchase\s*price|unit\s*cost|dealer\s*cost)$",
        r"(?i)^(landed\s*cost|acquisition\s*cost|inventory\s*cost|stock\s*cost|internal\s*price)$",
        r"(?i)^(direct\s*cost|factory\s*price|ex-works\s*price|supply\s*price|inventory\s*value)$",
        r"(?i)^(procurement\s*(?:cost|price)|supplier\s*(?:cost|price)|manufacturer\s*(?:cost|price))$"
    ],
    
    "Trade Price": [
        r"(?i)^((?:trade|dealer|distributor|reseller|wholesale)\s*(?:cost|price)|price\s*(?:to|for)\s*(?:trade|dealer|distributor|reseller))$",
        r"(?i)^(wholesale\s*price|b2b\s*price|commercial\s*price|partner\s*price|channel\s*price|business\s*price)$",
        r"(?i)^(net\s*price|discount\s*price|special\s*price|contractor\s*price|pro\s*price|trade\s*discount)$",
        r"(?i)^(professional\s*price|bulk\s*price|volume\s*price|non-retail\s*price|trade\s*only\s*price)$"
    ],
    
    # Generic MSRP pattern - used when currency is unclear
    "MSRP": [
        r"(?i)^(msrp|srp|rrp|list\s*price|retail\s*price|resale\s*price|recommended\s*price|suggested\s*price)$",
        r"(?i)^(public\s*price|consumer\s*price|end\s*user\s*price|advertised\s*price|catalog\s*price)$",
        r"(?i)^(selling\s*price|retail(?!\s*(?:gbp|usd|eur|£|\$|€)))$",  # Retail not followed by currency indicator
        r"(?i)^(customer\s*price|market\s*price|price\s*list|published\s*price|sticker\s*price)$",
        r"(?i)^(advertised\s*retail\s*price|recommended\s*retail\s*price|regular\s*price)$"
    ],
    
    # Currency-specific MSRP patterns
    "MSRP GBP": [
        r"(?i)^((?:msrp|srp|rrp|list|retail|resale|recommended|suggested)\s*(?:price|cost)\s*(?:\(gbp\)|gbp|£|pounds?))$",
        r"(?i)^((?:price|cost)\s*(?:gbp|£|pounds?)|retail\s*gbp|retail\s*£)$",
        r"(?i)^(uk\s*(?:price|retail|msrp|rrp)|price\s*uk|british\s*pounds?)$",
        r"(?i)^(gbp|£|pounds?|price\s*gbp|sterling)$",
        r"(?i)^((?:price|cost)\s*(?:in\s*gbp|in\s*pounds?)|uk\s*retail\s*price)$"
    ],
    
    "MSRP USD": [
        r"(?i)^((?:msrp|srp|rrp|list|retail|resale|recommended|suggested)\s*(?:price|cost)\s*(?:\(usd\)|usd|\$|dollars?))$",
        r"(?i)^((?:price|cost)\s*(?:usd|\$|dollars?)|retail\s*usd|retail\s*\$)$",
        r"(?i)^(us\s*(?:price|retail|msrp|rrp)|price\s*us|american\s*dollars?)$",
        r"(?i)^(usd|\$|dollars?|price\s*usd)$",
        r"(?i)^((?:price|cost)\s*(?:in\s*usd|in\s*dollars?)|us\s*retail\s*price)$"
    ],
    
    "MSRP EUR": [
        r"(?i)^((?:msrp|srp|rrp|list|retail|resale|recommended|suggested)\s*(?:price|cost)\s*(?:\(eur\)|eur|€|euros?))$",
        r"(?i)^((?:price|cost)\s*(?:eur|€|euros?)|retail\s*eur|retail\s*€)$",
        r"(?i)^(eu\s*(?:price|retail|msrp|rrp)|price\s*eu|european\s*euros?)$",
        r"(?i)^(eur|€|euros?|price\s*eur)$",
        r"(?i)^((?:price|cost)\s*(?:in\s*eur|in\s*euros?)|eu\s*retail\s*price)$"
    ],
    
    "MSRP CAD": [
        r"(?i)^((?:msrp|srp|rrp|list|retail|resale|recommended|suggested)\s*(?:price|cost)\s*(?:\(cad\)|cad|c\$|canadian\s*dollars?))$",
        r"(?i)^((?:price|cost)\s*(?:cad|c\$|canadian\s*dollars?)|retail\s*cad|retail\s*c\$)$",
        r"(?i)^(canada\s*(?:price|retail|msrp|rrp)|price\s*canada|canadian\s*dollars?)$",
        r"(?i)^(cad|c\$|canadian\s*dollars?|price\s*cad)$"
    ],
    
    "MSRP AUD": [
        r"(?i)^((?:msrp|srp|rrp|list|retail|resale|recommended|suggested)\s*(?:price|cost)\s*(?:\(aud\)|aud|a\$|australian\s*dollars?))$",
        r"(?i)^((?:price|cost)\s*(?:aud|a\$|australian\s*dollars?)|retail\s*aud|retail\s*a\$)$",
        r"(?i)^(australia\s*(?:price|retail|msrp|rrp)|price\s*australia|australian\s*dollars?)$",
        r"(?i)^(aud|a\$|australian\s*dollars?|price\s*aud)$"
    ],
    
    "Retail GBP": [
        r"(?i)^(retail\s*(?:gbp|£|pounds?)|retail\s*price\s*(?:gbp|£|pounds?))$",
        r"(?i)^(gbp|£|pounds?|price\s*gbp|uk\s*price|retail\s*price\s*uk)$",
        r"(?i)^((?:price|cost)\s*(?:gbp|£|pounds?)|retail\s*price\s*in\s*pounds?)$"
    ],
    
    "Discontinued": [
        r"(?i)^(discontinued|obsolete|eol|end\s*of\s*life|inactive|status|discontinued\s*flag)$",
        r"(?i)^(discontinued\s*(?:status|indicator|product)|product\s*status|availability\s*status)$",
        r"(?i)^(availability|in\s*stock|active|out\s*of\s*stock|stock\s*status|inventory\s*status)$",
        r"(?i)^(available|obtainable|procurable|purchasable|orderable|in\s*production)$"
    ],
    
    # Additional fields observed in sample data
    "Warranty": [
        r"(?i)^(warranty(?!\s*(?:void|null|exclude))|guarantee|warranty\s*(?:period|terms|length|duration|coverage|info))$",
        r"(?i)^(product\s*warranty|included\s*warranty|standard\s*warranty|manufacturer\s*warranty)$",
        r"(?i)^(coverage\s*(?:term|period|length)|included\s*coverage|support\s*(?:duration|period|term))$",
        r"(?i)^(warranty\s*information|guarantee\s*(?:period|terms)|service\s*plan)$"
    ],
    
    "Release Date": [
        r"(?i)^(release\s*date|launch\s*date|availability\s*date|available\s*date|intro\s*date)$",
        r"(?i)^(market\s*date|first\s*available|introduction\s*date|rollout\s*date)$",
        r"(?i)^(debut\s*date|start\s*date|release|launch|availability|release\s*year)$",
        r"(?i)^(date\s*(?:released|launched|available)|product\s*launch\s*date)$"
    ],
    
    "Color": [
        r"(?i)^(colou?r(?!\s*(?:temperature|depth|gamut))|hue|shade|tint|paint|finish)$",
        r"(?i)^(housing\s*colou?r|enclosure\s*(?:colou?r|finish)|product\s*colou?r|case\s*colou?r)$",
        r"(?i)^(exterior\s*(?:colou?r|finish)|available\s*colou?rs|colou?r\s*options|body\s*colou?r)$",
        r"(?i)^(surface\s*(?:colou?r|finish|treatment)|appearance|aesthetic|style\s*colou?r)$"
    ],
    
    "Dimensions": [
        r"(?i)^(dimensions?(?!\s*(?:tolerance|variance))|size|measurements?|product\s*(?:size|dimensions))$",
        r"(?i)^(height|width|depth|length|diameter|radius|overall\s*dimensions)$",
        r"(?i)^(product\s*measurements?|physical\s*(?:size|dimensions)|h\s*x\s*w\s*x\s*d)$",
        r"(?i)^(dims?|hwd|lwh|external\s*dimensions|outer\s*dimensions|footprint)$",
        r"(?i)^(unit\s*(?:dimensions?|size)|product\s*dimensions?|physical\s*specs)$"
    ],
    
    "Weight": [
        r"(?i)^(weight(?!\s*(?:tolerance|variance|limit|capacity))|product\s*weight|unit\s*weight)$",
        r"(?i)^(net\s*weight|gross\s*weight|shipping\s*weight|item\s*weight|mass)$",
        r"(?i)^(weight\s*(?:net|gross|shipping|product)|packed\s*weight|unpacked\s*weight)$",
        r"(?i)^(weight\s*(?:kg|g|lb|oz|pounds|ounces)|kg|lbs|pounds)$"
    ],
    
    "Power": [
        r"(?i)^(power(?!\s*(?:supply|input|source|cord|cable|consumption|requirement|adapter))|wattage|power\s*rating|output\s*power)$",
        r"(?i)^(power\s*output|power\s*handling|power\s*capacity|continuous\s*power)$",
        r"(?i)^(max\s*power|peak\s*power|program\s*power|power\s*capabilities|watts)$",
        r"(?i)^(w\s*rms|watt|power\s*specs|power\s*specifications|amplifier\s*power)$"
    ],
    
    "Power Requirements": [
        r"(?i)^(power\s*(?:supply|input|source|requirements?|needs?|specs?))$",
        r"(?i)^(input\s*voltage|voltage\s*requirements?|electrical\s*requirements?)$",
        r"(?i)^(power\s*(?:consumption|draw|usage)|energy\s*consumption|electrical\s*specs)$",
        r"(?i)^(current\s*draw|amperage|voltage\s*range|ac\s*requirements|dc\s*requirements)$"
    ],
    
    "Frequency Response": [
        r"(?i)^(frequency\s*(?:response|range|spectrum|bandwidth)|freq\s*resp|audio\s*range)$",
        r"(?i)^(acoustic\s*(?:frequency|range)|frequency\s*(?:band|sensitivity))$",
        r"(?i)^(freq\s*range|bandwidth|Hz\s*range|audio\s*frequency\s*range)$",
        r"(?i)^(frequency|speaker\s*range|operational\s*frequency|response\s*curve)$"
    ],
    
    "Coverage": [
        r"(?i)^(coverage(?!\s*(?:area|plan|map|warranty|insurance))|coverage\s*(?:angle|pattern)|dispersion)$",
        r"(?i)^(sound\s*coverage|audio\s*coverage|horizontal\s*coverage|vertical\s*coverage)$",
        r"(?i)^(coverage\s*(?:horizontal|vertical)|dispersion\s*(?:angle|pattern))$",
        r"(?i)^(beam\s*width|radiation\s*pattern|directivity|throw\s*pattern)$"
    ],
    
    "Max SPL": [
        r"(?i)^(max\s*(?:spl|sound\s*pressure\s*level)|maximum\s*(?:spl|sound\s*pressure\s*level))$",
        r"(?i)^(max\s*output|max\s*volume|peak\s*spl|output\s*level|sound\s*pressure)$",
        r"(?i)^(maximum\s*output|loudness|peak\s*output|acoustic\s*output|max\s*db)$",
        r"(?i)^(spl|sound\s*pressure\s*level|db\s*spl|sound\s*level)$"
    ],
    
    "Channels": [
        r"(?i)^(channels|audio\s*channels|i\/o|inputs\s*outputs|channel\s*count)$",
        r"(?i)^(input\s*channels|output\s*channels|number\s*of\s*channels)$",
        r"(?i)^(mic\s*channels|line\s*channels|channel\s*configuration)$",
        r"(?i)^(mono\/stereo|channel\s*inputs|connectivity|io\s*configuration)$"
    ],
    
    "Connectors": [
        r"(?i)^(connectors?|connections?|connector\s*types?|connection\s*types?)$",
        r"(?i)^(ports?|inputs?|outputs?|io\s*(?:ports?|connections?))$",
        r"(?i)^(audio\s*(?:connections?|connectors?)|video\s*(?:connections?|connectors?))$",
        r"(?i)^(interfaces?|terminals?|jacks?|plugs?|sockets?|connectivity)$"
    ],
    
    "Material": [
        r"(?i)^(materials?|construction|composition|made\s*(?:of|from)|build\s*material)$",
        r"(?i)^(housing\s*material|enclosure\s*material|body\s*material|shell\s*material)$",
        r"(?i)^(fabric|wood|metal|plastic|glass|composite|material\s*type)$",
        r"(?i)^(cabinet\s*material|structure|chassis\s*material|casing\s*material)$"
    ],
    
    # Additional fields for training/services catalog
    "Group": [
        r"(?i)^(group$)$",  # Only exact match for 'group'
        r"(?i)^(product\s*group|item\s*group|service\s*group|offering\s*group)$",
        r"(?i)^(product\s*grouping|item\s*grouping|high\s*level\s*group|main\s*group)$",
        r"(?i)^(product\s*collection|collection|product\s*range|range|group\s*name)$"
    ],
    
    "Series": [
        r"(?i)^(series|product\s*series|model\s*series|family|product\s*family)$",
        r"(?i)^(product\s*line|model\s*line|product\s*range|model\s*range|lineup)$",
        r"(?i)^(collection|generation|iteration|version\s*family|model\s*group)$",
        r"(?i)^(related\s*products|product\s*set|sibling\s*products|series\s*name)$"
    ],
    
    "System": [
        r"(?i)^(system$)$",  # Exact match for system
        r"(?i)^(product\s*system|equipment\s*system|audio\s*system|sound\s*system)$",
        r"(?i)^(solution|system\s*solution|complete\s*system|system\s*type)$",
        r"(?i)^(configuration|setup|ecosystem|platform|system\s*name|product\s*ecosystem)$"
    ],
    
    "Product": [
        r"(?i)^(product$)$",  # Exact match for product
        r"(?i)^(product\s*name|product\s*identifier|product\s*designation|product\s*id)$",
        r"(?i)^(item$|item\s*name|item\s*designation|item\s*identifier|item\s*id)$",
        r"(?i)^(part$|part\s*name|part\s*designation|specific\s*product|specific\s*item)$"
    ],
    
    "Retail GBP": [
        r"(?i)^(retail\s*(?:gbp|£|pounds?)|retail\s*price\s*(?:gbp|£|pounds?))$",
        r"(?i)^(gbp|£|pounds?|price\s*gbp|uk\s*price|retail\s*price\s*uk)$",
        r"(?i)^((?:price|cost)\s*(?:gbp|£|pounds?)|retail\s*price\s*in\s*pounds?)$"
    ]
}

# Special patterns for price hints in row-based format (when prices are in rows instead of columns)
ROW_PRICE_PATTERNS = {
    "Buy Cost": [
        r"(?i)(buy|cost|wholesale|net|dealer|base)(?:\s|-)(?:cost|price)",
        r"(?i)(cost|price)(?:\s|-)(?:to|for)(?:\s|-)(?:buy|dealer|distributor|reseller)",
        r"(?i)\b(cost|landed\s*cost|purchase\s*price|dealer\s*cost)\b",
        r"(?i)\b(inventory\s*(?:cost|price)|procurement\s*(?:cost|price)|factory\s*price)\b",
        r"(?i)\b(supplier\s*(?:cost|price)|manufacturer\s*(?:cost|price)|acquisition\s*cost)\b"
    ],
    "Trade Price": [
        r"(?i)(trade|dealer|distributor|reseller|wholesale)(?:\s|-)(?:cost|price)",
        r"(?i)(price)(?:\s|-)(?:to|for)(?:\s|-)(?:trade|dealer|distributor|reseller)",
        r"(?i)\b(wholesale\s*price|b2b\s*price|commercial\s*price|partner\s*price)\b",
        r"(?i)\b(channel\s*price|net\s*price|discount\s*price|special\s*price)\b",
        r"(?i)\b(contractor\s*price|pro\s*price|trade\s*discount|professional\s*price)\b"
    ],
    "MSRP": [
        r"(?i)(msrp|srp|rrp|list|retail|resale|recommended|suggested)(?:\s|-)(?:price|cost)",
        r"(?i)\b(public\s*price|consumer\s*price|retail\s*price|end\s*user\s*price)\b",
        r"(?i)\b(advertised\s*price|catalog\s*price|selling\s*price|customer\s*price)\b",
        r"(?i)\b(market\s*price|published\s*price|sticker\s*price)\b"
    ],
    "MSRP GBP": [
        r"(?i)(msrp|srp|rrp|list|retail|resale|recommended|suggested)(?:\s|-)(?:price|cost)(?:\s|-)(?:gbp|£|pounds)",
        r"(?i)(gbp|£|pounds?)(?:\s|-)(?:price|cost|retail)",
        r"(?i)(uk)(?:\s|-)(?:price|retail|msrp|rrp)"
    ],
    "MSRP USD": [
        r"(?i)(msrp|srp|rrp|list|retail|resale|recommended|suggested)(?:\s|-)(?:price|cost)(?:\s|-)(?:usd|\$|dollars?)",
        r"(?i)(usd|\$|dollars?)(?:\s|-)(?:price|cost|retail)",
        r"(?i)(us)(?:\s|-)(?:price|retail|msrp|rrp)"
    ],
    "MSRP EUR": [
        r"(?i)(msrp|srp|rrp|list|retail|resale|recommended|suggested)(?:\s|-)(?:price|cost)(?:\s|-)(?:eur|€|euros?)",
        r"(?i)(eur|€|euros?)(?:\s|-)(?:price|cost|retail)",
        r"(?i)(eu)(?:\s|-)(?:price|retail|msrp|rrp)"
    ]
}