import os
import requests
from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")

def send_message(recipient_id, message_text):
    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={ACCESS_TOKEN}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    response = requests.post(url, headers=headers, json=payload)
    print("SEND RESPONSE:", response.status_code, response.text)

@app.route("/", methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("WEBHOOK VERIFIED")
            return challenge, 200
        else:
            return "Verification token mismatch", 403

    if request.method == 'POST':
        data = request.get_json()
        print("RECEIVED DATA:", data)

        if data["object"] == "page":
            for entry in data["entry"]:
                messaging = entry.get("messaging", [])
                for event in messaging:
                    sender_id = event["sender"]["id"]
                    if "message" in event and "text" in event["message"]:
                        message_text = event["message"]["text"]
                        send_message(sender_id, f"You said: {message_text}")
        return "EVENT_RECEIVED", 200

    return "404 Not Found", 404

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
