import requests

BASE = "http://localhost:8000"

def post_form(url, data):
    return requests.post(url, files={k: (None, str(v)) for k, v in data.items()})

# ── Search ────────────────────────────────────────────────────────────────────
r = requests.post(f"{BASE}/search", json={"query": "BERT language model", "top_k": 3})
print("Search status:", r.status_code)
if r.status_code != 200:
    print("Error:", r.text)
    exit()

result = r.json()
print(f"Total results: {result['total']}")
for item in result["results"]:
    print(f"  [{item['score']:.3f}] (rank {item['rank']}) {item['paper']['title']}")

print("\n\nTesting paper-specific chatbot\n\n")

# ── Use the first paper from results ──────────────────────────────────────────
test_paper    = result["results"][0]["paper"]
test_entry_id = test_paper["id"]
print(f"Testing paper chat for: {test_paper['title']}")
print(f"Paper ID: {test_entry_id}")

# ── Start paper session ───────────────────────────────────────────────────────
r = post_form(f"{BASE}/paper/start", {"entry_id": test_entry_id})
print("\nPaper start status:", r.status_code)
if r.status_code != 200:
    print("Error:", r.text)
    exit()

paper_data = r.json()
paper_sid  = paper_data["session_id"]
print(f"Opening message:\n{paper_data['opening_message']}")

# ── Turn 1 ────────────────────────────────────────────────────────────────────
r = post_form(f"{BASE}/paper/chat", {
    "session_id": paper_sid,
    "message"   : "What is the main contribution of this paper?",
})
print("\nTurn 1 status:", r.status_code)
if r.status_code != 200:
    print("Error:", r.text)
    exit()
print("Bot:", r.json()["answer"])

# ── Turn 2 — tests session memory ─────────────────────────────────────────────
r = post_form(f"{BASE}/paper/chat", {
    "session_id": paper_sid,
    "message"   : "How does this compare to previous approaches?",
})
print("\nTurn 2 status:", r.status_code)
if r.status_code != 200:
    print("Error:", r.text)
    exit()
print("Bot:", r.json()["answer"])

# ── Turn 3 — grounding check ──────────────────────────────────────────────────
r = post_form(f"{BASE}/paper/chat", {
    "session_id": paper_sid,
    "message"   : "What were the exact hyperparameters used in the experiments?",
})
print("\nTurn 3 status:", r.status_code)
if r.status_code != 200:
    print("Error:", r.text)
    exit()
print("Bot:", r.json()["answer"])

# ── Clear session ─────────────────────────────────────────────────────────────
r = requests.delete(f"{BASE}/paper/chat/{paper_sid}")
print("\nClear session status:", r.status_code)
print(r.json())