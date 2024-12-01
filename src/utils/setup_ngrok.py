# src/utils/setup_ngrok.py

import subprocess
import json
import logging
import os
from pathlib import Path
import requests
import time
import sys


def setup_ngrok():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    try:
        # Mata qualquer processo ngrok existente
        try:
            subprocess.run(['pkill', 'ngrok'], capture_output=True)
            time.sleep(2)
        except:
            pass

        # Inicia o ngrok
        logger.info("Iniciando ngrok...")
        ngrok = subprocess.Popen(
            ['ngrok', 'http', '8000'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Aguarda o ngrok iniciar
        logger.info("Aguardando ngrok inicializar...")
        time.sleep(5)

        # Obtém a URL
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = requests.get('http://localhost:4040/api/tunnels')
                tunnels = response.json()['tunnels']
                ngrok_url = next(
                    (t['public_url']
                     for t in tunnels if t['proto'] == 'https'),
                    None
                )

                if ngrok_url:
                    logger.info(f"\nURL do ngrok: {ngrok_url}")
                    return ngrok_url
            except Exception as e:
                logger.warning(f"Tentativa {attempt + 1} falhou: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(3)

        raise Exception("Não foi possível obter URL do ngrok")

    except Exception as e:
        logger.error(f"Erro fatal: {str(e)}")
        if 'ngrok' in locals():
            ngrok.terminate()
        raise


if __name__ == "__main__":
    setup_ngrok()
