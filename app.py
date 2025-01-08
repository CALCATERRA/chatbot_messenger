from flask import Flask, request
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch  # Necessario per gestire i tensori
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
    # Gestione delle richieste HEAD
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
    # Ricezione dei messaggi dal webhook
    data = request.json
    if 'entry' in data:
        for entry in data['entry']:
            messaging = entry.get('messaging', [])
            for message in messaging:
                if 'message' in message:
                    user_message = message['message']['text']
                    sender_id = message['sender']['id']

                    # Risposta generata dal modello Hugging Face
                    inputs = tokenizer.encode(user_message, return_tensors="pt")
                    
                    # Creazione del `attention_mask` per evitare avvertimenti
                    inputs_with_mask = {
                        "input_ids": inputs,
                        "attention_mask": torch.ones_like(inputs)  # Genera una maschera basata sugli input
                    }
                    
                    # Generazione della risposta
                    outputs = model.generate(
                        **inputs_with_mask, 
                        max_length=50, 
                        num_return_sequences=1, 
                        pad_token_id=tokenizer.eos_token_id  # Aggiunta per evitare avvisi su `pad_token_id`
                    )
                    
                    reply = tokenizer.decode(outputs[0], skip_special_tokens=True)

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
    import os
    port = int(os.environ.get('PORT', 5000))  # Usa la porta definita da Render, altrimenti 5000
    app.run(host='0.0.0.0', port=port)
