from openai import OpenAI
from .schema import statement_schema

client = OpenAI()

def extract_json(chunks: list[str]) -> dict:
    content = "\n\n".join(chunks[:8])

    prompt = f"""
{statement_schema}

Extract the data from this statement text:

{content}
"""

    response = client.chat.completions.create(
        model="gpt-5.2",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    return response.choices[0].message.content