import os
from fastapi import FastAPI, UploadFile
from pathlib import Path
from .parsers import file_to_text
from .rag import split_text
from .extractor import extract_json

app = FastAPI()

UPLOAD_DIR = "uploads"
Path(UPLOAD_DIR).mkdir(exist_ok=True)

@app.post("/process-statement")
async def process_statement(file: UploadFile):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    ext = Path(file.filename).suffix
    text = file_to_text(file_path, ext)
    chunks = split_text(text)
    data = extract_json(chunks)

    return data