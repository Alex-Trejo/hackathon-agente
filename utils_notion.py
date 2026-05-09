import os
import requests
from dotenv import load_dotenv

load_dotenv()
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("DATABASE_ID")

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2026-03-11"
}

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
        data = response.json()
        
        if not data.get("results"):
            return None 
            
        propiedades = data["results"][0]["properties"]
        nombre = propiedades.get("Nombre", {}).get("rich_text",[{}])[0].get("text", {}).get("content", "Desconocido") if propiedades.get("Nombre", {}).get("rich_text") else "Desconocido"
        plan = propiedades.get("Plan", {}).get("select", {}).get("name", "Sin plan") if propiedades.get("Plan", {}).get("select") else "Sin plan"
        carencia = propiedades.get("Carencia Cumplida", {}).get("number", 0)
        procedimientos = propiedades["Procedimientos Cubiertos"]["rich_text"][0]["text"]["content"] if propiedades.get("Procedimientos Cubiertos", {}).get("rich_text") else "Ninguno"
            
        return {
            "Cédula": cedula, "Paciente": nombre, "Plan Médico": plan,
            "Meses de Carencia": carencia, "Procedimientos Cubiertos": procedimientos
        }
    except Exception as e:
        raise Exception(f"Error leyendo CRM Notion: {str(e)}")

def listar_pacientes():
    """Obtiene TODOS los pacientes de la base de datos de Notion"""
    try:
        data_source_id = _get_data_source_id()
        query_url = f"https://api.notion.com/v1/data_sources/{data_source_id}/query"
        
        response = requests.post(query_url, headers=HEADERS, json={})
        data = response.json()
        
        pacientes =[]
        for row in data.get("results", []):
            propiedades = row["properties"]
            
            cedula = propiedades.get("Cédula", {}).get("title", [{}])[0].get("text", {}).get("content", "") if propiedades.get("Cédula", {}).get("title") else ""
            nombre = propiedades.get("Nombre", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "Sin nombre") if propiedades.get("Nombre", {}).get("rich_text") else "Sin nombre"
            plan = propiedades.get("Plan", {}).get("select", {}).get("name", "Sin plan") if propiedades.get("Plan", {}).get("select") else "Sin plan"
            carencia = propiedades.get("Carencia Cumplida", {}).get("number", 0)
            procedimientos = propiedades["Procedimientos Cubiertos"]["rich_text"][0]["text"]["content"] if propiedades.get("Procedimientos Cubiertos", {}).get("rich_text") else "Ninguno"
            
            if cedula:
                pacientes.append({
                    "Cédula": cedula, "Nombre": nombre, "Plan": plan, 
                    "Carencia (Meses)": carencia, "Cobertura": procedimientos
                })
        return pacientes
    except Exception as e:
        return[]

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