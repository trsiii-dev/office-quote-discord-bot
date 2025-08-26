# post_quote.py
import os, requests, datetime
from pathlib import Path

WEBHOOK_URL = os.environ["https://discord.com/api/webhooks/1409869968341729430/NSYdwW-INK4ueMS-XMzqiHuzyfxoLy2FqO6DIJb-XC77AWRsNuMDoe2PC1-IE7Lzsg5F"]
QUOTES_FILE = Path("D:\Code\Github Repos\office-quote-discord-bot\quotes.txt")
PREFIX = "📺 The Office — Daily quote:"
MAX_LEN = 500

def load_quotes(p: Path):
    lines = [ln.strip() for ln in p.read_text(encoding="utf-8-sig").splitlines()]
    return [ln for ln in lines if ln and not ln.lstrip().startswith("#")]

def pick_quote(quotes):
    # Deterministic: same quote for same day, rotates across the list
    # Uses UTC date (matches GitHub Actions scheduler)
    today = datetime.datetime.utcnow().date().toordinal()
    return quotes[today % len(quotes)]

def post(content: str):
    r = requests.post(WEBHOOK_URL, json={"content": content[:MAX_LEN]}, timeout=20)
    r.raise_for_status()

def main():
    quotes = load_quotes(QUOTES_FILE)
    if not quotes:
        raise SystemExit("No quotes found in quotes.txt")
    q = pick_quote(quotes)
    if " | " in q:
        text, by = q.split(" | ", 1)
        content = f"{PREFIX}\n> {text}\n- {by}"
    else:
        content = f"{PREFIX}\n> {q}"
    post(content)

    if __name__ == "__main__":
        main()