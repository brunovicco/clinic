#!/bin/bash

echo "🚀 Iniciando ambiente de desenvolvimento..."

# Configura o ngrok
if [ ! -z "$NGROK_AUTHTOKEN" ]; then
    echo "🔑 Configurando token do ngrok..."
    ngrok config add-authtoken $NGROK_AUTHTOKEN
fi

# Inicia ngrok em background
echo "🌐 Iniciando ngrok..."
ngrok http --log=stdout 8000 &
NGROK_PID=$!

# Aguarda ngrok inicializar
echo "⏳ Aguardando ngrok inicializar..."
sleep 10

# Inicia aplicação
echo "🚀 Iniciando aplicação..."
python src/main.py

# Limpa ao sair
trap 'kill $NGROK_PID' EXIT