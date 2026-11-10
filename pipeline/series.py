"""Series fetched from the Bank of Canada Valet API.

Names were confirmed against https://www.bankofcanada.ca/valet/lists/series/json.
"""

# (series id, label, kind, tenor in years for bond yields)
SERIES = [
    ("V39079", "Policy interest rate", "rate", None),
    ("AVG.INTWO", "CORRA", "rate", None),
    ("BD.CDN.2YR.DQ.YLD", "2Y GoC yield", "rate", 2),
    ("BD.CDN.5YR.DQ.YLD", "5Y GoC yield", "rate", 5),
    ("BD.CDN.10YR.DQ.YLD", "10Y GoC yield", "rate", 10),
    ("FXUSDCAD", "USD/CAD", "fx", None),
    ("FXEURCAD", "EUR/CAD", "fx", None),
    ("FXGBPCAD", "GBP/CAD", "fx", None),
]

SERIES_IDS = [s[0] for s in SERIES]

# Derived series computed in SQL (see sql/schema.sql).
SPREAD_ID = "SPREAD_10Y_2Y"
SPREAD_ROW = (SPREAD_ID, "10Y minus 2Y spread", "rate", None)

# Series shown on the four summary cards, in display order.
CARD_IDS = ["V39079", "BD.CDN.2YR.DQ.YLD", "BD.CDN.10YR.DQ.YLD", "FXUSDCAD"]
