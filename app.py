import os
import json
from flask import Flask, request, jsonify
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

app = Flask(__name__)

# Modello più leggero
MODEL_NAME = "facebook/blenderbot-400M-distill"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

# Configura la route per Webhook
@app.route("/", methods=["GET"])
def verify():
    verify_token = os.getenv("VERIFY_TOKEN")
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == verify_token:
        return challenge, 200
    else:
        return "Forbidden", 403

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    if data and "message" in data:
        user_message = data["message"]
        inputs = tokenizer(user_message, return_tensors="pt")
        outputs = model.generate(**inputs)
        bot_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return jsonify({"response": bot_response})
    return "Invalid Request", 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)