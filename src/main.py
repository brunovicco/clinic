import os
import traceback
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from anthropic import Anthropic
import json
import logging
import sys
from pathlib import Path
import httpx
from datetime import datetime

# Configurar logging primeiro
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Verificar token do webhook
token = os.getenv("WEBHOOK_VERIFY_TOKEN")
if not token:
    logger.error("WEBHOOK_VERIFY_TOKEN não encontrado no .env")
    sys.exit(1)
else:
    logger.info(f"WEBHOOK_VERIFY_TOKEN carregado: {token}")

# Inicializar e testar Claude
# No início do arquivo, após load_dotenv()
try:
    anthropic = Anthropic()
    client = anthropic.beta.messages
    # Teste simples
    response = client.create(
        model="claude-3-sonnet-20240229",
        max_tokens=50,
        messages=[{"role": "user", "content": "Teste"}]
    )
    logger.info("Claude inicializado com sucesso")
except Exception as e:
    logger.error(f"Erro inicializando Claude: {str(e)}")
    sys.exit(1)

# Constantes
WHATSAPP_MESSAGE_TYPES = {
    "TEMPLATE": "template",
    "TEXT": "text"
}

WHATSAPP_API_URL = "https://graph.facebook.com/v21.0"
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

# Inicializar aplicação
app = FastAPI(title="Clinic WhatsApp AI")

# Gerenciamento de contexto
CONTEXTS = {}

INITIAL_PROMPT = """Você é uma recepcionista virtual de uma clínica médica.
Seja sempre cordial e profissional. Identifique-se como Ana, a assistente virtual.
Suas principais funções são:
1. Dar boas vindas
2. Coletar nome do paciente
3. Entender qual serviço procura
4. Verificar disponibilidade de horários
5. Agendar consultas

Mantenha as respostas curtas e objetivas. Não ultrapasse 200 caracteres por mensagem.
"""

@app.get("/health")
async def health_check():
    """Endpoint para verificar a saúde da aplicação"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/webhook")
async def verify_webhook(request: Request):
    """Endpoint para verificação do webhook do WhatsApp"""
    try:
        params = dict(request.query_params)
        verify_token = os.getenv("WEBHOOK_VERIFY_TOKEN")
        
        mode = params.get("hub.mode")
        token = params.get("hub.verify_token")
        challenge = params.get("hub.challenge")

        logger.info(f"Webhook verification params: {params}")
        logger.info(f"Received token: {token}")
        logger.info(f"Expected token: {verify_token}")

        if not mode or not token:
            logger.error("Missing mode or token")
            raise HTTPException(status_code=400, detail="Missing parameters")
            
        if mode == "subscribe" and token == verify_token:
            if not challenge:
                logger.error("Missing challenge")
                raise HTTPException(status_code=400, detail="Missing challenge")
                
            logger.info(f"Webhook verified! Challenge: {challenge}")
            return int(challenge)
            
        logger.error(f"Invalid mode or token. Mode: {mode}, Token match: {token == verify_token}")
        raise HTTPException(status_code=403, detail="Verification failed")

    except Exception as e:
        logger.error(f"Error in webhook verification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook")
async def webhook(request: Request):
    """Endpoint para receber mensagens do WhatsApp"""
    try:
        body = await request.json()
        logger.info(f"Webhook POST recebido: {json.dumps(body, indent=2)}")

        if "object" not in body or body["object"] != "whatsapp_business_account":
            logger.info("Ignorando evento não-WhatsApp")
            return {"status": "ignored"}

        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        # Log detalhado da estrutura
        logger.info(f"Entry: {json.dumps(entry, indent=2)}")
        logger.info(f"Value: {json.dumps(value, indent=2)}")

        if "messages" in value:
            messages = value["messages"]
            logger.info(f"Mensagens recebidas: {json.dumps(messages, indent=2)}")

            for message in messages:
                if message.get("type") == "text":
                    phone = message["from"]
                    text = message["text"]["body"]
                    logger.info(f"Processando mensagem de {phone}: {text}")

                    # Gera resposta
                    context = CONTEXTS.get(phone, {"history": [], "stage": "initial"})
                    response = await generate_response(text, context)
                    logger.info(f"Resposta gerada: {response}")

                    # Atualiza contexto
                    context["history"].append({"role": "user", "content": text})
                    context["history"].append({"role": "assistant", "content": response})
                    CONTEXTS[phone] = context

                    # Envia resposta
                    logger.info(f"Enviando resposta para {phone}")
                    await send_message(phone, response)
                    return {"status": "processed"}

        logger.info("Nenhuma mensagem de texto para processar")
        return {"status": "no_message"}

    except Exception as e:
        logger.error(f"Erro processando webhook: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"status": "error", "message": str(e)}

async def generate_response(message: str, context: dict) -> str:
    """Gera resposta usando o Claude"""
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY não encontrada no .env")
            return "Desculpe, estou com problemas técnicos de configuração. Por favor, tente mais tarde."

        logger.info(f"Gerando resposta para mensagem: {message}")
        logger.info(f"Contexto atual: {json.dumps(context, indent=2)}")

        messages = [
            {"role": "system", "content": INITIAL_PROMPT},
            *context["history"][-4:],
            {"role": "user", "content": message}
        ]

        logger.info(f"Enviando mensagem para Claude: {json.dumps(messages, indent=2)}")
        
        response = client.create(
            model="claude-3-sonnet-20240229",
            max_tokens=150,
            messages=messages
        )
        
        response_text = response.content[0].text
        logger.info(f"Resposta do Claude: {response_text}")
        
        return response_text

    except Exception as e:
        logger.error(f"Erro gerando resposta: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return "Olá! No momento estou em manutenção. Por favor, tente novamente em alguns minutos."
    
async def send_message(to: str, message: str, message_type="text"):
    """
    Envia mensagem via WhatsApp API
    Args:
        to: número do destinatário
        message: mensagem ou nome do template
        message_type: "text" ou "template"
    """
    try:
        # Formata o número
        to = to.replace("(", "").replace(")", "").replace(" ", "").replace("-", "")
        if not to.startswith("+"):
            to = f"+{to}"

        url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }

        # Base do payload
        payload = {
            "messaging_product": "whatsapp",
            "to": to
        }

        # Adiciona conteúdo específico baseado no tipo
        if message_type == WHATSAPP_MESSAGE_TYPES["TEMPLATE"]:
            payload.update({
                "type": "template",
                "template": {
                    "name": message,
                    "language": {
                        "code": "en_US"
                    }
                }
            })
        else:
            payload.update({
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": message
                }
            })

        logger.info(f"Enviando mensagem:")
        logger.info(f"URL: {url}")
        logger.info(f"Payload: {json.dumps(payload, indent=2)}")

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Response Status: {response.status_code}")
                logger.error(f"Response Body: {response.text}")
            else:
                logger.info(f"Mensagem enviada com sucesso: {response.json()}")
            
            response.raise_for_status()
            return response.json()

    except Exception as e:
        logger.error(f"Erro enviando mensagem: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        if isinstance(e, httpx.HTTPError) and hasattr(e, 'response'):
            logger.error(f"Response Status: {e.response.status_code}")
            logger.error(f"Response Body: {e.response.text}")
        raise

@app.post("/test/send-text")
async def test_send_text(phone: str, message: str):
    """Endpoint para testar envio de mensagem de texto"""
    try:
        result = await send_message(phone, message, WHATSAPP_MESSAGE_TYPES["TEXT"])
        return {
            "status": "success",
            "request": {
                "to": phone,
                "message": message,
                "type": "text"
            },
            "response": result
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/test/send-template")
async def test_send_template(phone: str, template_name: str = "hello_world"):
    """Endpoint para testar envio de template"""
    try:
        result = await send_message(
            phone, 
            template_name, 
            WHATSAPP_MESSAGE_TYPES["TEMPLATE"]
        )
        return {
            "status": "success",
            "request": {
                "to": phone,
                "template": template_name
            },
            "response": result
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Clinic WhatsApp AI...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("ENVIRONMENT") == "development"
    )