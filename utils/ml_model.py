from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

def get_fallback_model():
    headers = [
        "Product Name", "Retail GBP", "Dealer Price", "SKU",
        "MFR Part Number", "Short Description", "Buy Cost", "MSRP",
        "Item Title", "Cost to Dealer", "Trade Cost", "Retail Price USD"
    ]
    labels = [
        "Short Description", "MSRP GBP", "Trade Price", "SKU",
        "Manufacturer SKU", "Short Description", "Buy Cost", "MSRP USD",
        "Short Description", "Buy Cost", "Trade Price", "MSRP USD"
    ]

    model = make_pipeline(TfidfVectorizer(), LogisticRegression(max_iter=1000))
    model.fit(headers, labels)
    return model

ml_fallback_model = get_fallback_model()
