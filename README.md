# Clinic WhatsApp AI

Sistema de atendimento automatizado via WhatsApp para clínicas médicas.

## Requisitos

- Python 3.11+
- WhatsApp Business API Token
- Anthropic API Key (Claude)

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/brunovicco/clinic.git
cd clinic
```

2. Execute o script de setup:
```bash
chmod +x setup.sh
./setup.sh
```

3. Configure as variáveis de ambiente no arquivo .env:
```
WHATSAPP_TOKEN=seu_token_aqui
ANTHROPIC_API_KEY=seu_token_aqui
WEBHOOK_VERIFY_TOKEN=token_verificacao_webhook
```

## Executando o projeto

1. Ative o ambiente virtual:
```bash
source venv/bin/activate
```

2. Execute o servidor:
```bash
python src/main.py
```

## Testes

Para executar os testes:
```bash
pytest
```

## Estrutura do Projeto

```
clinic/
├── src/
│   ├── api/
│   ├── services/
│   ├── utils/
│   ├── config/
│   └── main.py
├── tests/
├── docs/
├── logs/
├── venv/
├── .env
├── .gitignore
├── requirements.txt
├── setup.sh
└── README.md
```
