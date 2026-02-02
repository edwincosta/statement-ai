import pandas as pd
from pypdf import PdfReader
from ofxparse import OfxParser
from .ocr import image_to_text

def pdf_to_text(path: str) -> str:
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def csv_to_text(path: str) -> str:
    df = pd.read_csv(path)
    return df.to_string()

def xlsx_to_text(path: str) -> str:
    df = pd.read_excel(path)
    return df.to_string()

def ofx_to_text(path: str) -> str:
    with open(path) as f:
        ofx = OfxParser.parse(f)
    text = ""
    for txn in ofx.account.statement.transactions:
        text += f"{txn.date} {txn.memo} {txn.amount}\n"
    return text

def file_to_text(path: str, ext: str) -> str:
    ext = ext.lower()
    if ext == ".pdf":
        return pdf_to_text(path)
    if ext == ".csv":
        return csv_to_text(path)
    if ext in [".xls", ".xlsx"]:
        return xlsx_to_text(path)
    if ext == ".ofx":
        return ofx_to_text(path)
    if ext in [".png", ".jpg", ".jpeg"]:
        return image_to_text(path)
    raise ValueError("Unsupported file type")