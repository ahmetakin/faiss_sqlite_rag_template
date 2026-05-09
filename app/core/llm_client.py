from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="local-llama-cpp"
)

def ask_llm(messages, temperature=0.2, max_tokens=1024):
    response = client.chat.completions.create(
        model="local-model",
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content