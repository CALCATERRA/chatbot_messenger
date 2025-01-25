from flask import Flask, request
from transformers import AutoModelForCausalLM, AutoTokenizer
import requests
import os

app = Flask(__name__)

# Carica il modello Hugging Face
MODEL_NAME = "distilgpt2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

# Variabili d'ambiente
PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')

@app.route('/', methods=['GET', 'HEAD'])
def verify():
    if request.method == 'HEAD':
        return '', 200  # Risponde con uno stato HTTP 200 OK e nessun contenuto

    # Verifica del webhook
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        return challenge, 200
    return 'Verification failed', 403

@app.route('/', methods=['POST'])
def webhook():
    data = request.json
    if 'entry' in data:
        for entry in data['entry']:
            messaging = entry.get('messaging', [])
            for message in messaging:
                if 'message' in message:
                    user_message = message['message']['text']
                    sender_id = message['sender']['id']

                    # Risposta generata dal modello Hugging Face
                    inputs = tokenizer(user_message, return_tensors="pt", padding=True, truncation=True)
                    outputs = model.generate(
                        inputs["input_ids"],
                        attention_mask=inputs["attention_mask"],
                        max_length=50,
                        num_return_sequences=1,
                        pad_token_id=tokenizer.eos_token_id  # Imposta pad_token_id correttamente
                    )
                    reply = tokenizer.decode(outputs[0], skip_special_tokens=True)

                    # Invia la risposta a Messenger
                    send_message(sender_id, reply)
    return 'Event received', 200

def send_message(recipient_id, text):
    url = f'https://graph.facebook.com/v16.0/me/messages?access_token={PAGE_ACCESS_TOKEN}'
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    headers = {"Content-Type": "application/json"}
    requests.post(url, json=payload, headers=headers)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
