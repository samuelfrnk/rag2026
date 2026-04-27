import requests

BASE = "http://localhost:8000"

# ── Health check ──────────────────────────────────────────────────────────────
r = requests.get(f"{BASE}/health")
print("Health:", r.json())

# ── Search ────────────────────────────────────────────────────────────────────
r = requests.post(f"{BASE}/search", data={"keywords": "BERT language model", "top_k": 3})
print("\nSearch status:", r.status_code)
if r.status_code != 200:
    print("Error:", r.text)
    exit()

result = r.json()
print("Answer:", result["answer"][:300])
for p in result["papers"]:
    print(f"  [{p['score']:.3f}] {p['title']}")

# Chat turn 1
r = requests.post(
    f"{BASE}/chat",
    data={"message": "What is a transformer?", "top_k": 3}
)
print("\nChat status:", r.status_code)
if r.status_code != 200:
    print("Error:", r.text)
    exit()

data = r.json()
sid  = data["session_id"]
print("Bot:", data["answer"][:300])

# Chat turn 2
r = requests.post(
    f"{BASE}/chat",
    data={"session_id": sid, "message": "How does it differ from BERT?", "top_k": 3}
)
print("\nChat turn 2 status:", r.status_code)
if r.status_code != 200:
    print("Error:", r.text)
    exit()

print("Bot:", r.json()["answer"][:300])