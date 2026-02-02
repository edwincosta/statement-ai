import json
from openai import OpenAI
from .schema import statement_schema


def extract_json(chunks: list[str], client: OpenAI) -> dict:
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

    message_content = response.choices[0].message.content
    return json.loads(message_content)