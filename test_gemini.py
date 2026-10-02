from openai import OpenAI
from config import GEMINI_API_KEY, GEMINI_MODEL

client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

res = client.chat.completions.create(
    model=GEMINI_MODEL,
    messages=[{"role": "user", "content": "안녕! 한 문장으로 자기소개 해줘."}],
    max_tokens=200,
)
print(res.choices[0].message.content)
