from flask import Flask, jsonify
from datetime import datetime
import pytz
import logging

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

@app.route('/time')
def get_time():
    """
    Endpoint que retorna a data e hora atual no fuso horário de São Paulo.
    """
    try:
        sao_paulo_tz = pytz.timezone('America/Sao_Paulo')
        now_sp = datetime.now(sao_paulo_tz)
        
        return jsonify({
            "current_time_iso": now_sp.isoformat()
        })
    except Exception as e:
        logging.error(f"Erro ao obter o horário: {e}")
        return jsonify({"error": "Não foi possível obter o horário"}), 500

if __name__ == '__main__':
    logging.info("Iniciando servidor de tempo na porta 5001...")
    app.run(host='0.0.0.0', port=5001)