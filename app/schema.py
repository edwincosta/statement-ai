statement_schema = """
You must extract the bank/credit card statement into JSON:
- Always follow this schema exactly (no extra fields):
{
  "institution": "string",
  "document_type": "bank_statement | credit_card_statement",
  "account_holder": "string",
  "period": "string",
  "transactions": [
    {
      "date": "YYYY-MM-DD",
      "description": "string",
      "amount": "float (negative for debit, positive for credit)",
      "currency": "string (BRL, USD, EUR, etc.)",
      "category": "string",
      "source_page": "int"
    }
  ]
}

- If a field is not present in the source, set it to null rather than guessing.
- Before returning, quickly re-scan the source for any missed fields and correct omissions.
"""