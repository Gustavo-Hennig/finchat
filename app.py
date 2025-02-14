from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from nlp import process_message  # Sua função para processar as mensagens

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def whatsapp_webhook():
    # Os dados enviados pelo Twilio são enviados via form-data
    data = request.form  
    message = data.get('Body')  # Conteúdo da mensagem
    sender = data.get('From')   # Número do remetente (ex.: "whatsapp:+5511999999999")
    
    # Processa a mensagem com sua função NLP
    response_text = process_message(message, sender)
    
    # Cria uma resposta TwiML para enviar a mensagem de volta via WhatsApp
    resp = MessagingResponse()
    resp.message(response_text)
    
    # Retorne a resposta TwiML com o mimetype apropriado
    return Response(str(resp), mimetype='text/xml')

if __name__ == '__main__':
    app.run(debug=True)
