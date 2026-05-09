import re
import PyPDF2
from fpdf import FPDF

def extraer_texto_pdf(archivo_pdf, max_chars=3000):
    """
    Extrae texto de un archivo PDF subido a memoria (UploadedFile).
    Limita la cantidad de caracteres para optimizar uso de tokens en OpenAI.
    Retorna un diccionario con el texto, metadata y estado de truncamiento.
    """
    try:
        lector_pdf = PyPDF2.PdfReader(archivo_pdf)
        texto_completo = ""
        paginas_procesadas = 0
        
        for pagina in lector_pdf.pages:
            texto_extraido = pagina.extract_text()
            if texto_extraido:
                texto_completo += texto_extraido + "\n"
                paginas_procesadas += 1
        
        # Limpiar múltiples saltos de línea y espacios redundantes
        texto_limpio = re.sub(r'\n{3,}', '\n\n', texto_completo)
        texto_limpio = re.sub(r' {2,}', ' ', texto_limpio).strip()
        
        # Verificar truncamiento
        fue_truncado = len(texto_limpio) > max_chars
        texto_final = texto_limpio[:max_chars]
        
        return {
            "texto": texto_final,
            "paginas": paginas_procesadas,
            "total_paginas": len(lector_pdf.pages),
            "truncado": fue_truncado,
            "caracteres": len(texto_final)
        }
        
    except Exception as e:
        raise ValueError(f"Error al procesar el documento PDF: {str(e)}")


def generar_pdf_plantilla(titulo: str, texto: str) -> bytes:
    """
    Genera un PDF descargable a partir de un texto de plantilla.
    Retorna los bytes del PDF listos para usar en st.download_button().
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(left=20, top=20, right=20)

    # Título
    pdf.set_font("Helvetica", style="B", size=14)
    pdf.cell(0, 10, titulo, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)

    # Línea separadora
    pdf.set_draw_color(180, 180, 180)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(6)

    # Cuerpo del texto
    pdf.set_font("Helvetica", size=11)
    for linea in texto.split("\n"):
        # Codificar caracteres especiales (fpdf2 con fuentes core usa latin-1)
        linea_safe = linea.encode("latin-1", errors="replace").decode("latin-1")
        pdf.multi_cell(0, 7, linea_safe, new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())