import json


def parse_llm_json(response: str):

    text = response.strip()

    text = text.replace("```json", "")
    text = text.replace("```", "")

    text = text.strip()

    return json.loads(text)