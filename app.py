from flask import Flask, request
import requests
import os
import re
import subprocess
import threading

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

@app.route('/', methods=['GET'])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == VERIFY_TOKEN:
        return challenge
    return "Verification token mismatch", 403

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                if "message" in messaging_event and "text" in messaging_event["message"]:
                    sender_id = messaging_event["sender"]["id"]
                    message_text = messaging_event["message"]["text"]

                    # Handle user input
                    if message_text.startswith("ask:"):
                        user_prompt = message_text[4:].strip()
                        response = query_ollama(user_prompt)
                        send_message(sender_id, response)

                    elif message_text.startswith("math:"):
                        math_expr = message_text[5:].strip()
                        result = evaluate_math_expression(math_expr)
                        send_message(sender_id, result)

                    elif message_text.startswith("translate:"):
                        sentence = message_text[9:].strip()
                        translated = translate(sentence)
                        send_message(sender_id, translated)

                    else:
                        send_message(sender_id, "Hi! Send 'ask:', 'math:', or 'translate:' to try features.")

    return "ok", 200

def send_message(recipient_id, message_text):
    params = {
        "access_token": ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    requests.post("https://graph.facebook.com/v17.0/me/messages", params=params, headers=headers, json=data)

def query_ollama(prompt):
    try:
        result = subprocess.run(
            ["ollama", "run", "llama3", prompt],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            text=True
        )
        return result.stdout.strip() if result.stdout else "No response from AI."
    except Exception as e:
        return f"Error: {e}"

def evaluate_math_expression(expr):
    try:
        # Only allow safe characters
        if not re.match(r'^[0-9+\-*/(). ]+$', expr):
            return "Invalid characters in expression"
        result = eval(expr, {"__builtins__": None}, {})
        return f"Result: {result}"
    except Exception:
        return "Error in expression"

def translate(sentence):
    try:
        import googletrans
        from googletrans import Translator
        translator = Translator()
        detected = translator.detect(sentence)
        if detected.lang == 'en':
            translated = translator.translate(sentence, dest='ar')
        else:
            translated = translator.translate(sentence, dest='en')
        return translated.text
    except Exception:
        return "Translation failed. Please try again."

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
