# app.py

from flask import Flask, request
import requests
import threading
import subprocess
import re

app = Flask(__name__)

# ─── CONFIG ──────────────────────────────────────────────────────────────────
VERIFY_TOKEN    = 'selma'
ACCESS_TOKEN    = 'EAAUQxoYZBH6kBPKr9xGk454LrzTIaCHzT2mdQQlmC4wm1TxtM1JQf09yFrryHSUejwDgZBfBz8PskbIbMmnKJNHKExxIfAoZBkVdLNRJzA6L4SDpByu7PSxSl2UvRKkB7CGsj2KHhqQQCxG4vImaX7WnUnw6MyoZAYnTw98icn8kwk0q8BNrFRtPg5MnUQtNG3KuSQZDZD'
OLLAMA_MODEL    = 'gemma3:4b'   # fits in ~3–4 GB RAM
OLLAMA_TIMEOUT  = 60
# ──────────────────────────────────────────────────────────────────────────────

# Regex for arithmetic expressions
ARITH = re.compile(r'([-+]?\d+(?:\.\d+)?\s*[-+*/]\s*[-+]?\d+(?:\.\d+)?)+')

def translate_to_arabic(text: str) -> str:
    """Use the free Google Translate web API endpoint."""
    params = {
        'client': 'gtx',
        'sl': 'en',
        'tl': 'ar',
        'dt': 't',
        'q': text
    }
    try:
        resp = requests.get('https://translate.googleapis.com/translate_a/single', params=params, timeout=10)
        resp.raise_for_status()
        # The response is a nested array: [[[translation, original,...],...],...]
        data = resp.json()
        return ''.join(segment[0] for segment in data[0])
    except Exception as e:
        app.logger.error("Translation error: %s", e)
        return "❌ Translation failed."

def ask_ollama(prompt: str) -> str:
    """
    1) If prompt starts with "translate to arabic", translate instantly.
    2) If it’s simple arithmetic, evaluate.
    3) Otherwise, run Ollama in a subprocess.
    """
    lower = prompt.lower()

    # 1) Translation
    if lower.startswith("translate to arabic"):
        # Expect: "translate to arabic this : TEXT" or "translate to arabic : TEXT"
        parts = prompt.split(":", 1)
        if len(parts) == 2:
            return translate_to_arabic(parts[1].strip())
        return "❌ Format: translate to arabic : <text>"

    # 2) Arithmetic
    m = ARITH.search(prompt.replace('=', ''))
    if m:
        expr = m.group(0)
        try:
            res = eval(expr)
            return str(int(res)) if isinstance(res, float) and res.is_integer() else str(res)
        except Exception:
            pass

    # 3) Ollama fallback
    try:
        proc = subprocess.run(
            ['ollama', 'run', OLLAMA_MODEL, prompt],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=OLLAMA_TIMEOUT
        )
        out = proc.stdout.decode('utf-8', errors='ignore').strip()
        if proc.returncode == 0 and out:
            return out
        err = proc.stderr.decode('utf-8', errors='ignore').strip()
        app.logger.error("Ollama error: %s", err)
        if 'model not found' in err.lower():
            return f"❌ Model not found. Run: ollama pull {OLLAMA_MODEL}"
        return f"❌ AI error: {err or 'unknown'}"
    except subprocess.TimeoutExpired:
        return "🤖 Sorry, I'm taking too long—please try again."
    except Exception as e:
        app.logger.exception("Unexpected error calling Ollama")
        return f"❌ Unexpected error: {e}"

def send_typing(recipient_id: str):
    """Show typing indicator in Messenger."""
    requests.post(
        'https://graph.facebook.com/v17.0/me/messages',
        params={'access_token': ACCESS_TOKEN},
        json={'recipient': {'id': recipient_id}, 'sender_action': 'typing_on'}
    )

def send_message(recipient_id: str, text: str):
    """Send a text message via the Graph API."""
    requests.post(
        'https://graph.facebook.com/v17.0/me/messages',
        params={'access_token': ACCESS_TOKEN},
        json={'recipient': {'id': recipient_id}, 'message': {'text': text}}
    )

def handle_event(evt):
    sender = evt['sender']['id']
    msg = evt['message'].get('text', '').strip()
    if not msg:
        return

    send_typing(sender)
    reply = ask_ollama(msg)
    send_message(sender, reply)

@app.route('/', methods=['GET'])
def verify():
    token = request.args.get('hub.verify_token')
    if token == VERIFY_TOKEN:
        return request.args.get('hub.challenge'), 200
    return 'Invalid verification token', 403

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    if data.get('object') == 'page':
        for entry in data['entry']:
            for evt in entry.get('messaging', []):
                if evt.get('message', {}).get('is_echo'):
                    continue
                if 'text' in evt.get('message', {}):
                    threading.Thread(target=handle_event, args=(evt,)).start()
    return 'EVENT_RECEIVED', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)