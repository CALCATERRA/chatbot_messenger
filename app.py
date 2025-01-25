from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer
import requests
import os

app = Flask(__name__)

# Carica il modello Hugging Face
MODEL_NAME = "distilgpt2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

# Configura il pad token se non è presente
if tokenizer.pad_token is None:
    tokenizer.add_special_tokens({'pad_token': tokenizer.eos_token})
    model.resize_token_embeddings(len(tokenizer))

# Variabili d'ambiente
PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')

@app.route('/', methods=['GET', 'HEAD'])
def verify():
    try:
        if request.method == 'HEAD':
            return '', 200

        # Verifica del webhook
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        return 'Verification failed', 403
    except Exception as e:
        app.logger.error(f"Errore nella verifica: {str(e)}")
        return 'Internal Server Error', 500

@app.route('/', methods=['POST'])
def webhook():
    try:
        data = request.json
        if not data:
            return 'Invalid request', 400

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
                            pad_token_id=tokenizer.eos_token_id
                        )
                        reply = tokenizer.decode(outputs[0], skip_special_tokens=True)

                        # Invia la risposta a Messenger
                        send_message(sender_id, reply)
        return 'Event received', 200
    except Exception as e:
        app.logger.error(f"Errore nel webhook: {str(e)}")
        return jsonify({"error": str(e)}), 500

def send_message(recipient_id, text):
    try:
        url = f'https://graph.facebook.com/v16.0/me/messages?access_token={PAGE_ACCESS_TOKEN}'
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": text}
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Solleva un'eccezione per errori HTTP
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Errore nell'invio del messaggio: {str(e)}")

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
