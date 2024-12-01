# src/utils/token_generator.py
import secrets
import base64
import hashlib
import os
from pathlib import Path


def generate_webhook_token(length=32):
    """
    Gera um token seguro para verificação do webhook
    Args:
        length: Comprimento do token em bytes
    Returns:
        tuple: (token original, token hash)
    """
    # Gera bytes aleatórios seguros
    token_bytes = secrets.token_bytes(length)

    # Converte para base64 para ter um token legível
    token = base64.urlsafe_b64encode(token_bytes).decode('utf-8').rstrip('=')

    # Gera um hash do token para armazenamento seguro
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    return token, token_hash


def save_token_to_env(token):
    """
    Salva o token no arquivo .env
    Args:
        token: Token a ser salvo
    """
    env_path = Path('.env')

    # Lê o arquivo .env existente
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()

        # Procura por uma linha existente com WEBHOOK_VERIFY_TOKEN
        token_line_index = None
        for i, line in enumerate(lines):
            if line.startswith('WEBHOOK_VERIFY_TOKEN='):
                token_line_index = i
                break

        # Atualiza ou adiciona o token
        new_line = f'WEBHOOK_VERIFY_TOKEN={token}\n'
        if token_line_index is not None:
            lines[token_line_index] = new_line
        else:
            lines.append(new_line)

        # Escreve de volta no arquivo
        with open(env_path, 'w') as f:
            f.writelines(lines)
    else:
        # Cria novo arquivo .env se não existir
        with open(env_path, 'w') as f:
            f.write(f'WEBHOOK_VERIFY_TOKEN={token}\n')


if __name__ == "__main__":
    # Gera o token
    token, token_hash = generate_webhook_token()

    # Salva no .env
    save_token_to_env(token)

    print("\n=== Webhook Token Generator ===")
    print("\nToken gerado com sucesso!")
    print("\nToken para configuração no WhatsApp Business API:")
    print(f"\n{token}")
    print("\nHash do token (para verificação):")
    print(f"\n{token_hash}")
    print("\nO token foi salvo automaticamente no arquivo .env")
    print("\nGuarde este token em um local seguro!")
