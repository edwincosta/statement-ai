import logging
import os
from json import JSONDecodeError
from fastapi import Depends, FastAPI, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from openai import OpenAI
from pathlib import Path
from .parsers import file_to_text
from .rag import split_text
from .extractor import extract_json

app = FastAPI()
security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads"
Path(UPLOAD_DIR).mkdir(exist_ok=True)

@app.post("/process-statement")
async def process_statement(
    file: UploadFile,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    if credentials is None:
        logger.warning("Authorization header missing")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header missing")

    if credentials.scheme.lower() != "bearer" or not credentials.credentials:
        logger.warning("Invalid authorization scheme: %s", credentials.scheme)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization scheme")

    client = OpenAI(api_key=credentials.credentials)
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    ext = Path(file.filename).suffix
    text = file_to_text(file_path, ext)
    chunks = split_text(text)
    try:
        data = extract_json(chunks, client)
    except JSONDecodeError as exc:
        logger.error("OpenAI response is not valid JSON", exc_info=exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Invalid JSON returned from model")
    except Exception as exc:
        logger.error("Failed to extract statement data", exc_info=exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Extraction failed")

    return data