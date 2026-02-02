import logging
import os
from json import JSONDecodeError
from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from openai import OpenAI
from openai import APIError, AuthenticationError, RateLimitError
from pathlib import Path
from .parsers import file_to_text
from .rag import split_text
from .extractor import extract_json

app = FastAPI()
security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))

UPLOAD_DIR = "uploads"
Path(UPLOAD_DIR).mkdir(exist_ok=True)

@app.post("/process-statement")
async def process_statement(
    request: Request,
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

    try:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_UPLOAD_BYTES:
            logger.warning("Content-Length exceeds limit", extra={"content_length": content_length})
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")

        file_size = os.path.getsize(file_path)
        if file_size > MAX_UPLOAD_BYTES:
            logger.warning("Uploaded file exceeds limit", extra={"file_size": file_size})
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")

        ext = Path(file.filename).suffix
        text = file_to_text(file_path, ext)
        chunks = split_text(text)
        data = extract_json(chunks, client)
    except AuthenticationError as exc:
        logger.error("OpenAI authentication failed", exc_info=exc)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing OpenAI API key")
    except RateLimitError as exc:
        logger.error("OpenAI rate limit or quota exceeded", exc_info=exc)
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="OpenAI rate limit or quota exceeded")
    except APIError as exc:
        logger.error("OpenAI API error", exc_info=exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Upstream model error")
    except JSONDecodeError as exc:
        logger.error("OpenAI response is not valid JSON", exc_info=exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Invalid JSON returned from model")
    except Exception as exc:
        logger.error("Failed to extract statement data", exc_info=exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Extraction failed")
    finally:
        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass
        except Exception as cleanup_exc:
            logger.warning("Failed to delete uploaded file", exc_info=cleanup_exc)

    return data