import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_recommendation(cars):
    prompt = f"""
You are an automotive expert helping a buyer choose between used cars.

Given this data:
{cars}

For each car:
- List pros and cons
- Comment on reliability & depreciation
- Give a final recommendation
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content
