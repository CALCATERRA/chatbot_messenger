import os
import requests
import json
from flask import Flask, request
from transformers import AutoModelForCausalLM, AutoTokenizer

app = Flask(__name__)

# Caricamento delle variabili d'ambiente
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "Simone260889")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")

# Caricamento del modello e del tokenizer
MODEL_NAME = "facebook/opt-1.3b"  # Modello di Facebook AI
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token  # Imposta il padding token

@app.route("/", methods=["GET"])
def webhook_verify():
    """Verifica della connessione con il Webhook di Facebook."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Verifica fallita", 403

@app.route("/", methods=["POST"])
def webhook():
    """Gestisce i messaggi ricevuti da Facebook Messenger."""
    data = request.get_json()
    
    if "entry" in data:
        for entry in data["entry"]:
            for messaging in entry.get("messaging", []):
                sender_id = messaging["sender"]["id"]
                if "message" in messaging:
                    user_message = messaging["message"]["text"]
                    
                    # Generazione della risposta
                    inputs = tokenizer(user_message, return_tensors="pt", padding=True, truncation=True)
                    response_ids = model.generate(**inputs, max_length=150)
                    bot_response = tokenizer.decode(response_ids[0], skip_special_tokens=True)
                    
                    send_message(sender_id, bot_response)
    return "EVENT_RECEIVED", 200

def send_message(recipient_id, text):
    """Invia un messaggio di risposta a Facebook Messenger."""
    url = "https://graph.facebook.com/v18.0/me/messages"
    headers = {"Content-Type": "application/json"}
    params = {"access_token": PAGE_ACCESS_TOKEN}
    
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    
    response = requests.post(url, headers=headers, params=params, json=payload)
    return response.json()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)