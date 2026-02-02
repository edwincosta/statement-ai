# statement-ai

FastAPI service that parses uploaded bank/credit-card statements, forwards extracted text to OpenAI for structured extraction, and returns JSON according to a fixed schema.

## Features
- Single endpoint: POST `/process-statement` (multipart upload)
- Authorization: `Authorization: Bearer <openai_api_key>` required per request
- File support: PDF, CSV, XLS/XLSX, OFX, images (OCR via Tesseract)
- Text chunking with LangChain, extraction via OpenAI `chat.completions` with JSON mode

## Prerequisites
- Python 3.10+
- Tesseract installed for image OCR (macOS: `brew install tesseract`)

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
uvicorn app.main:app --reload
```

## Usage
Send a file with a bearer token (your OpenAI API key):
```bash
curl -X POST \
  -H "Authorization: Bearer sk-..." \
  -F "file=@/path/to/statement.pdf" \
  http://localhost:8000/process-statement
```

### Response
A JSON object matching the schema in `app/schema.py`, for example:
```json
{
  "institution": "Bank Name",
  "document_type": "bank_statement",
  "account_holder": "Jane Doe",
  "period": "2025-01-01 to 2025-01-31",
  "transactions": [
    {
      "date": "2025-01-15",
      "description": "Grocery Store",
      "amount": -54.23,
      "currency": "BRL",
      "category": "groceries",
      "source_page": 1
    }
  ]
}
```

## Errors
- 401 if the `Authorization` header is missing or not `Bearer`
- 502 if the OpenAI response cannot be parsed as JSON or extraction fails
- 413 if the uploaded file exceeds the size limit (default 10 MB via `MAX_UPLOAD_BYTES`)
- 429 if the upstream OpenAI key is rate-limited or out of quota

## Notes
- Uploaded files are saved under `uploads/`; ensure you manage retention if needed.
- The OpenAI key is taken from the request header, not the environment.
- Uploads are deleted after processing. Override the size limit with `MAX_UPLOAD_BYTES` if needed.
- Logs go to stdout/stderr. On Render, configure a log drain (Settings → Log streams) to forward to your sink.

## Deploy (Render free tier)
1. Ensure the included `Dockerfile` is in the repo root (installs Tesseract, requirements, and runs uvicorn).
2. Push to GitHub/GitLab.
3. In Render, create a new Web Service → connect the repo → select Dockerfile as the blueprint.
4. Use the default command from the Dockerfile: uvicorn `app.main:app` on port 8000; Render will map it.
5. No OpenAI key env var is needed; clients send `Authorization: Bearer <key>` per request.
6. Deploy; call `https://<service>.onrender.com/process-statement` with the curl example above.
