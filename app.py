from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = 'selma'

@app.route('/', methods=['GET'])
def verify():
    # Facebook webhook verification
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Verification token mismatch", 403

@app.route('/', methods=['POST'])
def webhook():
    # Facebook webhook event handler
    data = request.get_json()
    print("Received webhook event:", data)
    return "EVENT_RECEIVED", 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
