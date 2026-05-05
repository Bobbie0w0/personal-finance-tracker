# personal-finance-tracker

## Objective
This project automates the extraction of transaction data from bank statement PDFs and transforms it into a structured dataset for financial analysis and reporting.

## Tools
- Python (pypdf, regex, datetime, csv)
- Microsoft Excel (data analysis, pivot tables)

##  Data Source
- Bank statement PDFs from:
  - RBC (Visa statements)
  - TD (credit card statements)
- Data includes transaction dates, posting dates, descriptions, and amounts

## Workflow
### 1. Data Extraction (Python)
- Parsed PDF statements using pypdf
- Applied custom regex patterns to extract transaction data for different banks (RBC, TD)
- Handled variations in statement formats across institutions

### 2. Data Transformation
- Standardized transaction fields:
  - Transaction date  
  - Posting date  
  - Description  
  - Amount  
- Resolved year ambiguities for statements spanning multiple calendar years  
- Converted extracted data into structured rows

### 3. Data Output
- Exported all transactions into a unified CSV file: all-transaction.csv
- Combined data across multiple PDF statements automatically

### 4. Data Analysis (Excel)
- Imported CSV into Excel for further analysis  
- Used PivotTables to:
  - Aggregate spending by category and month  
  - Identify high-spending areas  
  - Analyzed trends in transaction data to support budgeting and tax preparation  

## Key Features
- Multi-bank support (RBC and TD)
- Automated parsing of multiple PDF files using batch processing
- Handles different statement formats with custom regex logic
- Generates a clean, analysis-ready dataset

## Files
parser.py -> Main parsing script
all_transactions.csv #Output dataset

