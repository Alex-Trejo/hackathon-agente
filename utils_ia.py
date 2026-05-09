import os
import re
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

def _get_client() -> OpenAI:
    """Inicialización lazy del cliente OpenAI para evitar errores en el import."""
    load_dotenv(Path(__file__).resolve().parent / ".env")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception("Falta la variable OPENAI_API_KEY en el archivo .env")
    return OpenAI(api_key=api_key)

def extraer_datos_paciente(texto_pdf: str) -> dict:
    """Extrae Cédula y Procedimiento del PDF devolviendo un JSON puro con nivel de confianza."""
    prompt = f"""
    Lee este informe médico y extrae la información solicitada.
    Devuelve ÚNICAMENTE un JSON válido con estas claves:
    - "cedula": Número de cédula del paciente (solo dígitos numéricos, sin guiones ni espacios).
    - "procedimiento": Nombre exacto de la cirugía o procedimiento médico solicitado.
    - "nombre_paciente": Nombre completo del paciente tal como aparece en el documento.
    - "confianza": Un número entero de 0 a 100 que indica qué tan seguro estás de haber extraído correctamente los datos. 100 = certeza total, 0 = no se encontró nada.

    REGLAS:
    - Si no encuentras la cédula, pon "cedula": null.
    - Si no encuentras el procedimiento, pon "procedimiento": null.
    - Si el texto parece no ser un informe médico, pon confianza en 0.

    INFORME:
    {texto_pdf}
    """
    try:
        response = _get_client().chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Eres un sistema de extracción de datos médicos. Tu trabajo es leer informes clínicos y extraer variables clave con precisión. Responde exclusivamente en JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0 # Temperatura cero = Respuestas exactas
        )
        resultado = json.loads(response.choices[0].message.content)
        
        # Validación post-IA: limpiar la cédula
        cedula = resultado.get("cedula")
        if cedula:
            cedula_limpia = re.sub(r'\D', '', str(cedula))  # Eliminar todo lo que no sea dígito
            resultado["cedula"] = cedula_limpia if cedula_limpia else None
        
        return resultado
    except Exception as e:
        raise Exception(f"Error de IA (Extracción): {str(e)}")

def evaluar_auditoria(datos_paciente: dict, datos_poliza: dict) -> dict:
    """Audita reglas de negocio: cruza lo solicitado vs lo cubierto."""
    procedimiento = datos_paciente.get("procedimiento", "")
    
    prompt = f"""
    Eres un estricto auditor médico de una aseguradora de salud.
    Tu trabajo es evaluar si una solicitud de procedimiento médico cumple con las reglas de la póliza del paciente.

    SOLICITUD DEL HOSPITAL:
    - Procedimiento solicitado: "{procedimiento}"
    
    DATOS DE LA PÓLIZA DEL PACIENTE (del CRM de la aseguradora):
    - Procedimientos cubiertos: {datos_poliza['Procedimientos Cubiertos']}
    - Carencia cumplida: {datos_poliza['Meses de Carencia']} meses
    - Plan médico: {datos_poliza['Plan Médico']}
    
    REGLAS ESTRICTAS PARA APROBAR (deben cumplirse AMBAS):
    1. COBERTURA: El procedimiento solicitado DEBE estar explícitamente incluido (o ser un sinónimo médico directo) en la lista de procedimientos cubiertos.
    2. CARENCIA: El paciente debe tener 3 o más meses de carencia cumplida.
    
    Si AMBAS reglas se cumplen → APROBADO.
    Si CUALQUIERA falla → RECHAZADO.
    
    Devuelve ÚNICAMENTE un JSON con:
    - "estado": "APROBADO" o "RECHAZADO"
    - "motivo": Explicación técnica corta y precisa del resultado.
    - "detalle_reglas": Un array con exactamente 2 objetos:
        - {{"regla": "Cobertura", "cumple": true/false, "explicacion": "..."}}
        - {{"regla": "Carencia", "cumple": true/false, "explicacion": "..."}}
    - "carta": Mensaje formal y breve dirigido a la clínica informando el resultado de la pre-autorización.
    """
    try:
        response = _get_client().chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Eres el sistema automatizado de auditoría médica de una aseguradora. Evalúas reglas de negocio con rigor absoluto. Responde exclusivamente en JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        raise Exception(f"Error de IA (Auditoría): {str(e)}")