from flask import Flask, request
from transformers import AutoModelForCausalLM, AutoTokenizer
import requests
import os

app = Flask(__name__)

# Configurazione Modello ChatGPT
MODEL_NAME = "distilgpt2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
model.config.pad_token_id = model.config.eos_token_id  # Correzione per il pad_token

# Token di Meta (presi dalle variabili d'ambiente su Render)
PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')  # Token della Pagina Facebook/Instagram
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'Simone260889')  # Usa il token impostato su Render

@app.route('/', methods=['GET'])
def verify():
    """Verifica Webhook di Meta"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification failed", 403

@app.route('/', methods=['POST'])
def webhook():
    """Riceve e risponde ai messaggi"""
    data = request.json
    if 'entry' in data:
        for entry in data['entry']:
            messaging = entry.get('messaging', [])
            for message in messaging:
                if 'message' in message:
                    user_message = message['message']['text']
                    sender_id = message['sender']['id']

                    # Genera risposta ChatGPT
                    inputs = tokenizer(user_message, return_tensors="pt", padding=True, truncation=True)
                    outputs = model.generate(inputs.input_ids, max_length=50)
                    reply = tokenizer.decode(outputs[0], skip_special_tokens=True)

                    # Invia risposta a Instagram
                    send_message(sender_id, reply)
    return "Event received", 200

def send_message(recipient_id, text):
    """Invia messaggi a Instagram"""
    url = f"https://graph.facebook.com/v16.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    headers = {"Content-Type": "application/json"}
    requests.post(url, json=payload, headers=headers)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
