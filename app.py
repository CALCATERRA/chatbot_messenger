from flask import Flask, request
import openai
import requests
import os

app = Flask(__name__)

# Carica le chiavi API dalle variabili d'ambiente
openai.api_key = os.getenv('OPENAI_API_KEY')  # Chiave OpenAI
PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')  # Chiave di accesso di Facebook
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')  # Token di verifica di Meta

@app.route('/', methods=['GET'])
def verify():
    # Verifica del webhook
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        return challenge, 200
    return 'Verification failed', 403

@app.route('/', methods=['POST'])
def webhook():
    # Ricezione dei messaggi dal webhook
    data = request.json
    if 'entry' in data:
        for entry in data['entry']:
            messaging = entry.get('messaging', [])
            for message in messaging:
                if 'message' in message:
                    user_message = message['message']['text']
                    sender_id = message['sender']['id']

                    # Risposta generata da ChatGPT
                    response = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "Rispondi come [il tuo nome]."},
                            {"role": "user", "content": user_message}
                        ]
                    )
                    reply = response['choices'][0]['message']['content']

                    # Invia la risposta a Messenger
                    send_message(sender_id, reply)
    return 'Event received', 200

def send_message(recipient_id, text):
    # Invia il messaggio di risposta a Messenger
    url = f'https://graph.facebook.com/v16.0/me/messages?access_token={PAGE_ACCESS_TOKEN}'
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    headers = {"Content-Type": "application/json"}
    requests.post(url, json=payload, headers=headers)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

