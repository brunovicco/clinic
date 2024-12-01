# Dockerfile
FROM python:3.11-slim

# Configurar variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Instalar ngrok e atualizar pip
RUN apt-get update && apt-get install -y wget && \
    wget -q https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz && \
    tar xvf ngrok-v3-stable-linux-amd64.tgz -C /usr/local/bin && \
    rm ngrok-v3-stable-linux-amd64.tgz && \
    pip install --upgrade pip

# Criar diretório da aplicação
WORKDIR /app

# Copiar arquivos do projeto
COPY requirements.txt .
COPY src/ src/
COPY start_dev.sh .

# Instalar dependências
RUN pip install --no-cache-dir -r requirements.txt

# Dar permissão de execução ao script
RUN chmod +x start_dev.sh

# Expor portas
EXPOSE 8000
EXPOSE 4040

# Comando para iniciar
CMD ["./start_dev.sh"]