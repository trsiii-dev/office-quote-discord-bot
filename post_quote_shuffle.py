# post_quote_shuffle.py
import os, sys, json, hashlib, random, requests
from pathlib import Path

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
QUOTES_FILE = Path("quotes.txt")
STATE_DIR = Path(".state")
STATE_FILE = STATE_DIR / "queue.json"   # persisted in repo
PREFIX = "📺 The Office — Daily quote:"
MAX_LEN = 500

def die(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)

def load_quotes(p: Path):
    try:
        lines = p.read_text(encoding="utf-8-sig").splitlines()
    except FileNotFoundError:
        die(f"ERROR: {p} not found. Commit quotes.txt at repo root.")
    quotes = [ln.strip() for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]
    if not quotes:
        die("ERROR: quotes.txt is empty or only comments (#...).")
    return quotes

def quotes_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def ensure_queue(quotes_len: int, qhash: str):
    STATE_DIR.mkdir(exist_ok=True)
    if STATE_FILE.exists():
        try:
            st = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            if st.get("quotes_hash") == qhash and st.get("queue"):
                return st
        except Exception:
            pass
    # Build a fresh shuffled queue of indices 0..n-1
    idxs = list(range(quotes_len))
    random.shuffle(idxs)
    st = {"quotes_hash": qhash, "queue": idxs}
    STATE_FILE.write_text(json.dumps(st, indent=2), encoding="utf-8")
    return st

def next_index_and_update(st: dict, quotes_len: int, qhash: str):
    q = st.get("queue", [])
    if not q:
        # reshuffle when empty
        q = list(range(quotes_len))
        random.shuffle(q)
    idx = q.pop(0)
    st = {"quotes_hash": qhash, "queue": q}
    STATE_FILE.write_text(json.dumps(st, indent=2), encoding="utf-8")
    return idx

def post(content: str):
    if not WEBHOOK_URL or "discord.com/api/webhooks/" not in WEBHOOK_URL:
        die("ERROR: DISCORD_WEBHOOK_URL missing/malformed. Add repo secret named DISCORD_WEBHOOK_URL.")
    r = requests.post(WEBHOOK_URL, json={"content": content[:MAX_LEN]}, timeout=30)
    try:
        r.raise_for_status()
    except requests.HTTPError:
        die(f"ERROR: Discord POST failed: {r.status_code} {r.reason}\nResponse: {r.text[:300]}")

def main():
    quotes = load_quotes(QUOTES_FILE)
    raw = QUOTES_FILE.read_bytes()
    qhash = quotes_hash(raw)

    st = ensure_queue(len(quotes), qhash)
    idx = next_index_and_update(st, len(quotes), qhash)
    q = quotes[idx]

    if " | " in q:
        text, by = q.split(" | ", 1)
        content = f"{PREFIX}\n> {text}\n— {by}"
    else:
        content = f"{PREFIX}\n> {q}"

    print("INFO: Posting:\n", content)
    post(content)
    print(f"SUCCESS: Posted index {idx}.")

if __name__ == "__main__":
    main()
