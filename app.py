import os
import json
from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

app = Flask(__name__)

# Imposta la chiave segreta per la verifica del webhook
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "Simone260889")

# Carica il modello e il tokenizer
MODEL_NAME = "microsoft/DialoGPT-medium"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.add_special_tokens({'pad_token': '[PAD]'})  # 🔥 Fix definitivo
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

@app.route("/", methods=["GET"])
def verify():
    """Verifica il webhook di Messenger."""
    token_sent = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token_sent == VERIFY_TOKEN:
        return challenge
    return "Token di verifica non valido", 403

@app.route("/", methods=["POST"])
def webhook():
    """Riceve i messaggi da Messenger e risponde."""
    try:
        data = request.get_json()
        if data and "entry" in data:
            for entry in data["entry"]:
                for message in entry["messaging"]:
                    if "message" in message:
                        sender_id = message["sender"]["id"]
                        user_message = message["message"]["text"]
                        
                        # Tokenizzazione del messaggio
                        inputs = tokenizer(user_message, return_tensors="pt", padding=True, truncation=True)
                        
                        # Generazione della risposta
                        response_ids = model.generate(**inputs, max_length=1000)
                        bot_response = tokenizer.decode(response_ids[0], skip_special_tokens=True)

                        # Simulazione invio risposta (da implementare con API Messenger)
                        print(f"Risposta per {sender_id}: {bot_response}")

                        return jsonify({"recipient_id": sender_id, "message": bot_response}), 200
        return "Nessun messaggio valido", 400
    except Exception as e:
        print(f"Errore: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Usa la porta specificata da Render
    app.run(host="0.0.0.0", port=port)
