"""Setup check: one call to the Claude API, to prove the key and the library work.

Prints the answer, the token counts and the cost of the call.

Run with: uv run --env-file .env scripts/check_LLM_api.py
"""

import anthropic

MODEL = "claude-haiku-5-5"

# US dollars per million tokens, for prompts up to 100,000 tokens
INPUT_PRICE_PER_MTOK = 0.10
OUTPUT_PRICE_PER_MTOK = 0.50

client = anthropic.Anthropic()

response = client.messages.create(
    model=MODEL,
    max_tokens=300,
    messages=[
        {
            "role": "user",
            "content": "In one sentence, what does an on-call engineer do?",
        }
    ],
)

for block in response.content:
    if block.type == "text":
        print(block.text)

usage = response.usage
cost = (
    usage.input_tokens * INPUT_PRICE_PER_MTOK
    + usage.output_tokens * OUTPUT_PRICE_PER_MTOK
) / 1_000_000

print()
print(f"Model:         {response.model}")
print(f"Stop reason:   {response.stop_reason}")
print(f"Input tokens:  {usage.input_tokens}")
print(f"Output tokens: {usage.output_tokens}")
print(f"Cost:          ${cost:.6f}")
