from decimal import Decimal
import json as _json

def dict_format(conn, rows):
    """Trasforma le righe in dizionari e pulisce i tipi di dati (Date, Time, Decimal)"""
    if not rows:
        return []
    
    # 1. Prendi i nomi delle colonne
    cols = [c['name'] for c in conn.columns]
    
    formatted_results = []
    for row in rows:
        # 2. Crea il dizionario accoppiando nome colonna e valore
        row_dict = dict(zip(cols, row))
        
        # 3. Pulisci ogni valore nel dizionario (Decimal, Date, Time)
        for key, value in row_dict.items():
            row_dict[key] = _clean_value(value)
            
        formatted_results.append(row_dict)
    
    return formatted_results

def dict_format_single(conn, rows):
    """Versione per un singolo risultato"""
    results = dict_format(conn, rows)
    return results[0] if results else None

def _clean_value(value):
    if value is None:
        return None

    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)

    # Stringhe JSON restituite da pg8000 per colonne json/jsonb (es. json_agg)
    if isinstance(value, str) and len(value) > 1 and value[0] in ('[', '{'):
        try:
            return _json.loads(value)
        except Exception:
            pass

    # Tipi time (ha strftime ma non isoformat)
    if hasattr(value, 'strftime') and not hasattr(value, 'isoformat'):
        return value.strftime("%H:%M")

    # Tipi date/datetime
    if hasattr(value, 'isoformat'):
        return value.isoformat()

    return value