import requests

BASE = "http://localhost:8000"

# ── Health check ──────────────────────────────────────────────────────────────
r = requests.get(f"{BASE}/health")
print("Health:", r.json())

print("\n\nTesting query\n\n")

# ── Search ────────────────────────────────────────────────────────────────────
r = requests.post(f"{BASE}/search", data={"keywords": "BERT language model", "top_k": 3})
print("\nSearch status:", r.status_code)
if r.status_code != 200:
    print("Error:", r.text)
    exit()

result = r.json()
print("Answer:", result["answer"])
for p in result["papers"]:
    print(f"  [{p['score']:.3f}] {p['title']}")

print("\n\nTesting turn based chatbot\n\n")

# Chat turn 1
r = requests.post(
    f"{BASE}/chat",
    data={"message": "Which papers show the combination of Transformer architecture with GNN? Also cite papers that mention it", "top_k": 3}
)
print("\nChat status:", r.status_code)
if r.status_code != 200:
    print("Error:", r.text)
    exit()

data = r.json()
sid  = data["session_id"]
print("Bot:", data["answer"])

# Chat turn 2
r = requests.post(
    f"{BASE}/chat",
    data={"session_id": sid, "message": "What is the core mechanism of the first paper you cited?", "top_k": 3}
)
print("\nChat turn 2 status:", r.status_code)
if r.status_code != 200:
    print("Error:", r.text)
    exit()

print("Bot:", r.json()["answer"])