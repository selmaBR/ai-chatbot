from flask import Flask, request
import requests

app = Flask(__name__)

VERIFY_TOKEN = 'selma'  # This should match the verify_token in your Facebook webhook URL
PAGE_ACCESS_TOKEN = 'EAAUQxoYZBH6kBPOgOt11CZBw0M1BCdxjwLqsXgj3oKpb9j3AoWx2ZBJUwEi2dTHZCZAxq1C6N5i2VYNRPp77lZC5ZBwTrEeBFk7EUWLoQoD0oRPVxNGyYdDjCZAidwVa3zF3R6sHztusjZCHunREhAaZAMjbPPdiq1RcP4qbCwckFupMLFxQmerKBSJ1T39JkhpLzI5yjJggZDZD'  # Replace this with your real token

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Facebook Webhook verification
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if token == VERIFY_TOKEN:
            return challenge, 200
        return 'Invalid verification token', 403

    elif request.method == 'POST':
        # Incoming messages
        data = request.get_json()
        if data.get('object') == 'page':
            for entry in data['entry']:
                messaging = entry.get('messaging', [])
                for message_event in messaging:
                    sender_id = message_event['sender']['id']
                    if 'message' in message_event:
                        message_text = message_event['message'].get('text', '')
                        send_message(sender_id, f"You said: {message_text}")
        return 'ok', 200

def send_message(recipient_id, message_text):
    url = 'https://graph.facebook.com/v18.0/me/messages'
    params = {
        'access_token': PAGE_ACCESS_TOKEN
    }
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'recipient': {'id': recipient_id},
        'message': {'text': message_text}
    }
    response = requests.post(url, params=params, headers=headers, json=data)
    print(f"Sent message to {recipient_id}: {message_text}")
    print("Facebook response:", response.text)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
