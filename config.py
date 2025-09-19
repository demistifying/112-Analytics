# config.py
# Project-wide constants and expected column names

REQUIRED_COLUMNS = [
    "call_id",
    "call_ts",        # timestamp string: YYYY-MM-DD HH:MM:SS
    "caller_lat",
    "caller_lon",
    "category",
    "jurisdiction"
]

DATE_COL = "call_ts"
CATEGORY_COL = "category"
JURISDICTION_COL = "jurisdiction"