#!/bin/bash

echo "🚀 Iniciando ambiente de desenvolvimento..."

# Mata processos existentes
echo "🧹 Limpando processos anteriores..."
pkill -f ngrok
pkill -f uvicorn
pkill -f python
sleep 2

# Ativa ambiente virtual
source venv/bin/activate

# Inicia ngrok
echo "🌐 Iniciando ngrok..."
python src/utils/setup_ngrok.py &
NGROK_PID=$!

# Aguarda ngrok inicializar
echo "⏳ Aguardando ngrok inicializar..."
sleep 10

# Verifica se ngrok está rodando
if ! curl -s http://localhost:4040/api/tunnels > /dev/null; then
    echo "❌ Falha ao iniciar ngrok"
    exit 1
fi

# Inicia aplicação
echo "🚀 Iniciando aplicação..."
python src/main.py

# Limpa ao sair
trap 'echo "⏹️ Encerrando processos..."; kill $NGROK_PID' EXIT