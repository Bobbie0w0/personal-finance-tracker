from pypdf import PdfReader
import re
from datetime import date
import csv
import glob

MONTH_NUMS = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12
}

# RBC transaction pattern: "MMM DD MMM DD DESCRIPTION\n<reference number>\n[-]$AMOUNT"
rbc_pattern = re.compile(
    r"([A-Z]{3}) (\d{1,2})\s+([A-Z]{3}) (\d{1,2})\s+(.+?)\n[\d ]+\n(-?\$[\d,]+\.\d{2})",
    re.DOTALL
)

# TD transaction pattern: "MMM DD MMM DD [-]$AMOUNTDESCRIPTION"
td_pattern = re.compile(
    r"([A-Z]{3}) (\d{1,2})\s+([A-Z]{3}) (\d{1,2})\s+(-?\$?[\d,]+\.\d{2})(.+?)$",
    re.MULTILINE
)

def get_rbc_period(text):
    # Two years example: "STATEMENT FROM DEC 12, 2024 TO JAN 13, 2025"
    m = re.search(r"STATEMENT FROM (\w+) (\d+), (\d{4}) TO (\w+) (\d+), (\d{4})", text)
    if m:
        start_month, start_day, start_year, end_month, end_day, end_year = m.groups()
        return start_month, int(start_year), end_month, int(end_year)
    
    # Single year example: "STATEMENT FROM MAY 08 TO JUN 9, 2025"
    m = re.search(r"STATEMENT FROM (\w+) \d+ TO (\w+) \d+, (\d{4})", text)
    if m:
        start_month, end_month, year = m.groups()
        return start_month, int(year), end_month, int(year)
    
    raise ValueError("Could not find statement period in PDF")

def get_td_period(text):
    # example: "STATEMENT PERIOD: March 12, 2025 to April 11, 2025"
    m = re.search(r"STATEMENT PERIOD: (\w+) \d+, (\d{4}) to (\w+) \d+, (\d{4})", text)
    start_month, start_year, end_month, end_year = m.groups()
    if not m:
        raise ValueError("Could not find TD statement period")
    return start_month.upper()[:3], int(start_year), end_month.upper()[:3], int(end_year)

def figure_out_year(txn_month_name, start_month_name, start_year, end_year):
    if start_year == end_year:
        # Same-year statement
        return start_year
    
    # Year is crossing over
    if MONTH_NUMS[txn_month_name] >= MONTH_NUMS[start_month_name]: 
        return start_year  
    else:
        return end_year    

def _build_row(bank, txn_month, txn_day, post_month, post_day, desc, amt,
               start_month, start_yr, end_yr):
    """Convert raw regex captures into a transaction row."""
    txn_year = figure_out_year(txn_month, start_month, start_yr, end_yr)
    post_year = figure_out_year(post_month, start_month, start_yr, end_yr)
    amount = float(amt.replace("$", "").replace(",", ""))
    return [
        bank,
        date(txn_year, MONTH_NUMS[txn_month], int(txn_day)).isoformat(),
        date(post_year, MONTH_NUMS[post_month], int(post_day)).isoformat(),
        desc.strip(),
        amount,
    ]

def parse_any(path):
    """Pick the right parser based on filename."""

    reader = PdfReader(path)
    if reader.is_encrypted:
        reader.decrypt("")
    text = "\n".join(p.extract_text() for p in reader.pages)

     # Normalize the inline annual-fee form
    text = re.sub(
        r"([A-Z]{3} \d{1,2} [A-Z]{3} \d{1,2}) (ANNUAL FEE) \$?([\d,]+\.\d{2})",
        r"\1 \2\n0\n$\3",
        text
    )

    rows = []
    bank = ""
    filename = path.lower()
    if "td_first_class" in filename or "td_" in filename:
        start_month, start_yr, end_month, end_yr = get_td_period(text)
        bank = "TD"
        for m in td_pattern.finditer(text):
            txn_month, txn_day, post_month, post_day, amt, desc = m.groups()
            rows.append(_build_row(bank, txn_month, txn_day, post_month, post_day,
                                   desc, amt, start_month, start_yr, end_yr))
    elif "visa statement" in filename:   # RBC's filename pattern
        start_month, start_yr, end_month, end_yr = get_rbc_period(text)
        bank = "RBC"
        for m in rbc_pattern.finditer(text):
            txn_month, txn_day, post_month, post_day, desc, amt = m.groups()
            rows.append(_build_row(bank, txn_month, txn_day, post_month, post_day,
                                   desc, amt, start_month, start_yr, end_yr))
        
    else:
        print(f"⚠ Unknown bank for: {path}")
        return []
    return rows  

all_transactions = []
for pdf_path in glob.glob("statements/*.pdf"):
    print(f"Parsing {pdf_path}...")
    rows = parse_any(pdf_path)
    print(f"  -> {len(rows)} transactions")
    all_transactions.extend(rows)

with open("all_transactions.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Bank", "Transaction Date", "Posting Date", "Description", "Amount"])
    w.writerows(all_transactions)


print(f"Wrote {len(all_transactions)} transactions to all_transactions.csv")    