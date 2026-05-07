from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

response = client.chat.completions.create(
    model="qwen2.5-coder",
    messages=[
        {
            "role": "system",
            "content": "You are a senior Kubernetes SRE engineer."
        },
        {
            "role": "user",
            "content": "Explain CrashLoopBackOff"
        }
    ]
)

print(response.choices[0].message.content)