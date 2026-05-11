import requests

BASE = "http://localhost:8000"

r = requests.post(f"{BASE}/search", data={"keywords": "BERT language model", "top_k": 3})
print("\nSearch status:", r.status_code)
if r.status_code != 200:
    print("Error:", r.text)
    exit()

result = r.json()
print("Answer:", result["answer"])
for p in result["papers"]:
    print(f"  [{p['score']:.3f}] {p['title']}")

print("\n\nTesting paper-specific chatbot\n\n")

# ── Use the first paper from the search result above as the test subject ───────
test_paper = result["papers"][0]
test_entry_id = test_paper["entry_id"]
print(f"Testing paper chat for: {test_paper['title']}")
print(f"Entry ID: {test_entry_id}")

# ── Start a paper session (auto-generates opening message) ────────────────────
r = requests.post(f"{BASE}/paper/start", data={"entry_id": test_entry_id})
print("\nPaper start status:", r.status_code)
if r.status_code != 200:
    print("Error:", r.text)
    exit()

paper_data = r.json()
paper_sid  = paper_data["session_id"]
print(f"Session ID: {paper_sid}")
print(f"Opening message:\n{paper_data['opening_message']}")

# ── Turn 1 — specific question about the paper ────────────────────────────────
r = requests.post(f"{BASE}/paper/chat", data={
    "session_id": paper_sid,
    "message"   : "What is the main contribution of this paper?",
})
print("\nPaper chat turn 1 status:", r.status_code)
if r.status_code != 200:
    print("Error:", r.text)
    exit()
print("Bot:", r.json()["answer"])

# ── Turn 2 — follow-up that tests session memory ──────────────────────────────
r = requests.post(f"{BASE}/paper/chat", data={
    "session_id": paper_sid,
    "message"   : "How does the method you just described compare to previous approaches?",
})
print("\nPaper chat turn 2 status:", r.status_code)
if r.status_code != 200:
    print("Error:", r.text)
    exit()
print("Bot:", r.json()["answer"])

# ── Turn 3 — test grounding (ask something outside the abstract) ──────────────
r = requests.post(f"{BASE}/paper/chat", data={
    "session_id": paper_sid,
    "message"   : "What were the exact hyperparameters used in the experiments?",
})
print("\nPaper chat turn 3 status:", r.status_code)
if r.status_code != 200:
    print("Error:", r.text)
    exit()
print("Bot:", r.json()["answer"])

# ── Clear the paper session ───────────────────────────────────────────────────
r = requests.delete(f"{BASE}/paper/chat/{paper_sid}")
print("\nClear paper session status:", r.status_code)
print(r.json())