import os
import requests
import json
from flask import Flask, request

app = Flask(__name__)

# Variabili d'ambiente
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "Simone260889")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def generate_response(prompt):
    """Genera una risposta usando OpenAI GPT-3.5."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"].strip()

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
                    
                    # Genera risposta con GPT-3.5
                    bot_response = generate_response(user_message)
                    
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
