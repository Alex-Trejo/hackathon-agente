import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("DATABASE_ID")

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2026-03-11"
}

# ==============================
# HELPERS DEFENSIVOS
# ==============================

def _safe_get_title(propiedades: dict, campo: str, default: str = "") -> str:
    """Extrae texto de una propiedad tipo 'title' de forma segura."""
    try:
        items = propiedades.get(campo, {}).get("title", [])
        if items and len(items) > 0:
            return items[0].get("text", {}).get("content", default)
    except (IndexError, KeyError, TypeError):
        pass
    return default

def _safe_get_rich_text(propiedades: dict, campo: str, default: str = "Sin dato") -> str:
    """Extrae texto de una propiedad tipo 'rich_text' de forma segura."""
    try:
        items = propiedades.get(campo, {}).get("rich_text", [])
        if items and len(items) > 0:
            return items[0].get("text", {}).get("content", default)
    except (IndexError, KeyError, TypeError):
        pass
    return default

def _safe_get_select(propiedades: dict, campo: str, default: str = "Sin plan") -> str:
    """Extrae texto de una propiedad tipo 'select' de forma segura."""
    try:
        select = propiedades.get(campo, {}).get("select")
        if select:
            return select.get("name", default)
    except (KeyError, TypeError):
        pass
    return default

def _safe_get_number(propiedades: dict, campo: str, default: int = 0) -> int:
    """Extrae valor de una propiedad tipo 'number' de forma segura."""
    try:
        valor = propiedades.get(campo, {}).get("number")
        return valor if valor is not None else default
    except (KeyError, TypeError):
        return default


# ==============================
# FUNCIONES PRINCIPALES
# ==============================

def _get_data_source_id():
    """Función auxiliar para obtener el Data Source ID de la Base de Datos"""
    db_url = f"https://api.notion.com/v1/databases/{DATABASE_ID}"
    response = requests.get(db_url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"Fallo conexión a BBDD: {response.text}")
    return response.json()["data_sources"][0]["id"]

def obtener_datos_poliza(cedula: str):
    """Consulta la API de Notion usando la cédula. Retorna diccionario o None."""
    try:
        data_source_id = _get_data_source_id()
        query_url = f"https://api.notion.com/v1/data_sources/{data_source_id}/query"
        payload = {"filter": {"property": "Cédula", "title": {"equals": cedula}}}
        
        response = requests.post(query_url, headers=HEADERS, json=payload)
        if response.status_code != 200:
            raise Exception(f"Error HTTP {response.status_code} consultando póliza: {response.text}")
        
        data = response.json()
        
        if not data.get("results"):
            return None 
            
        propiedades = data["results"][0]["properties"]
        
        return {
            "Cédula": cedula,
            "Paciente": _safe_get_rich_text(propiedades, "Nombre", "Desconocido"),
            "Plan Médico": _safe_get_select(propiedades, "Plan", "Sin plan"),
            "Meses de Carencia": _safe_get_number(propiedades, "Carencia Cumplida", 0),
            "Procedimientos Cubiertos": _safe_get_rich_text(propiedades, "Procedimientos Cubiertos", "Ninguno")
        }
    except Exception as e:
        raise Exception(f"Error leyendo CRM Notion: {str(e)}")

def listar_pacientes():
    """Obtiene TODOS los pacientes de la base de datos de Notion"""
    try:
        data_source_id = _get_data_source_id()
        query_url = f"https://api.notion.com/v1/data_sources/{data_source_id}/query"
        
        response = requests.post(query_url, headers=HEADERS, json={})
        if response.status_code != 200:
            raise Exception(f"Error HTTP {response.status_code} listando pacientes: {response.text}")
        
        data = response.json()
        
        pacientes = []
        for row in data.get("results", []):
            propiedades = row["properties"]
            
            cedula = _safe_get_title(propiedades, "Cédula")
            if cedula:
                pacientes.append({
                    "Cédula": cedula,
                    "Nombre": _safe_get_rich_text(propiedades, "Nombre", "Sin nombre"),
                    "Plan": _safe_get_select(propiedades, "Plan", "Sin plan"),
                    "Carencia (Meses)": _safe_get_number(propiedades, "Carencia Cumplida", 0),
                    "Cobertura": _safe_get_rich_text(propiedades, "Procedimientos Cubiertos", "Ninguno")
                })
        return pacientes
    except Exception as e:
        return []

def agregar_paciente(cedula: str, nombre: str, plan: str, carencia: int, procedimientos: str):
    """Escribe un nuevo paciente en la tabla de Notion"""
    try:
        data_source_id = _get_data_source_id()
        url = "https://api.notion.com/v1/pages"
        
        # Estructura estricta que exige Notion para crear páginas en un Data Source
        payload = {
            "parent": { "type": "data_source_id", "data_source_id": data_source_id },
            "properties": {
                "Cédula": {"title":[{"text": {"content": cedula}}]},
                "Nombre": {"rich_text": [{"text": {"content": nombre}}]},
                "Plan": {"select": {"name": plan}},
                "Carencia Cumplida": {"number": carencia},
                "Procedimientos Cubiertos": {"rich_text": [{"text": {"content": procedimientos}}]}
            }
        }
        
        response = requests.post(url, headers=HEADERS, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Fallo al agregar a Notion: {response.text}")
        return True
    except Exception as e:
        raise Exception(f"Error creando registro en Notion: {str(e)}")