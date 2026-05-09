import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extraer_datos_paciente(texto_pdf: str) -> dict:
    """Extrae Cédula y Procedimiento del PDF devolviendo un JSON puro."""
    prompt = f"""
    Lee este informe médico y extrae la información.
    Devuelve ÚNICAMENTE un JSON válido con estas claves:
    - "cedula": Número de cédula del paciente (solo números).
    - "procedimiento": Cirugía solicitada.

    INFORME:
    {texto_pdf}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0 # Temperatura cero = Respuestas exactas
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        raise Exception(f"Error de IA (Extracción): {str(e)}")

def evaluar_auditoria(datos_paciente: dict, datos_poliza: dict) -> dict:
    """Audita reglas de negocio: cruza lo solicitado vs lo cubierto."""
    procedimiento = datos_paciente.get("procedimiento", "")
    
    prompt = f"""
    Eres un estricto auditor médico de aseguradora.
    SOLICITUD: Procedimiento: {procedimiento}
    
    PÓLIZA DEL PACIENTE:
    - Cubre: {datos_poliza['Procedimientos Cubiertos']}
    - Carencia cumplida: {datos_poliza['Meses de Carencia']} meses.
    
    REGLAS PARA APROBAR:
    1. El procedimiento solicitado DEBE estar dentro de los cubiertos.
    2. Debe tener 3 o más meses de carencia cumplida.
    
    Devuelve ÚNICAMENTE un JSON con:
    - "estado": "APROBADO" o "RECHAZADO"
    - "motivo": Explicación corta técnica.
    - "carta": Mensaje formal dirigido a la clínica informando el resultado.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Sistema automatizado de auditoría en JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        raise Exception(f"Error de IA (Auditoría): {str(e)}")