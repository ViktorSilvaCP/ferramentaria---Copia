from datetime import datetime
import pytz
import requests
import time
import logging

# URL da API WorldTimeAPI para São Paulo
TIME_SERVER_URL = "http://worldtimeapi.org/api/timezone/America/Sao_Paulo"

# Cache simples para evitar chamadas excessivas à API
_cached_time = None
_cache_expiry = 0
CACHE_DURATION_SECONDS = 5  # Atualiza a cada 5 segundos

def _get_time_from_server():
    """Função interna para buscar o tempo da API WorldTimeAPI com cache."""
    global _cached_time, _cache_expiry

    # Retorna cache se ainda válido
    if time.time() < _cache_expiry and _cached_time:
        return _cached_time

    try:
        response = requests.get(TIME_SERVER_URL, timeout=3)
        response.raise_for_status()
        
        # Parse da resposta JSON
        data = response.json()
        datetime_str = data['datetime']
        
        # Converte a string ISO para datetime
        _cached_time = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        
        # Converte para São Paulo timezone
        sp_tz = pytz.timezone('America/Sao_Paulo')
        _cached_time = _cached_time.astimezone(sp_tz)
        
        _cache_expiry = time.time() + CACHE_DURATION_SECONDS
        
        logging.debug(f"[TIME] Horário obtido da API WorldTimeAPI: {_cached_time}")
        return _cached_time
        
    except requests.RequestException as e:
        logging.warning(f"[TIME] Falha ao conectar com WorldTimeAPI: {e}. Usando horário local como fallback.")
        # Fallback para o horário local se a API falhar
        tz = pytz.timezone('America/Sao_Paulo')
        _cached_time = datetime.now(tz)
        _cache_expiry = time.time() + CACHE_DURATION_SECONDS
        return _cached_time
    except (ValueError, KeyError) as e:
        logging.warning(f"[TIME] Erro ao parsear resposta da API: {e}. Usando horário local como fallback.")
        tz = pytz.timezone('America/Sao_Paulo')
        _cached_time = datetime.now(tz)
        _cache_expiry = time.time() + CACHE_DURATION_SECONDS
        return _cached_time

def get_current_datetime():
    """
    Retorna a data e hora atual consultando a API de tempo WorldTimeAPI.
    """
    return _get_time_from_server()

def get_current_date():
    """
    Retorna a data atual consultando a API de tempo WorldTimeAPI.
    """
    return _get_time_from_server().date()

def format_datetime(dt, format='%d/%m/%Y %H:%M'):
    """
    Formata um objeto datetime para o formato especificado, garantindo fuso horário correto.
    """
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        tz = pytz.timezone('America/Sao_Paulo')
        dt = tz.localize(dt)
    return dt.strftime(format)

def parse_datetime(date_str, format='%Y-%m-%d %H:%M:%S'):
    """
    Converte uma string de data/hora para um objeto datetime com fuso horário.
    """
    if not date_str:
        return None
    
    tz = pytz.timezone('America/Sao_Paulo')
    try:
        dt = datetime.strptime(date_str, format)
        return tz.localize(dt)
    except ValueError:
        return None
