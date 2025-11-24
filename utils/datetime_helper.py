from datetime import datetime
import pytz

def get_current_datetime():
    """
    Retorna a data e hora atual no fuso horário de São Paulo.
    """
    tz = pytz.timezone('America/Sao_Paulo')
    return datetime.now(tz)

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
