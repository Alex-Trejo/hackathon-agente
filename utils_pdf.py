import PyPDF2

def extraer_texto_pdf(archivo_pdf, max_chars=2000):
    """
    Extrae texto de un archivo PDF subido a memoria (UploadedFile).
    Limita la cantidad de caracteres para optimizar uso de tokens en OpenAI.
    """
    try:
        lector_pdf = PyPDF2.PdfReader(archivo_pdf)
        texto_completo = ""
        
        for pagina in lector_pdf.pages:
            texto_extraido = pagina.extract_text()
            if texto_extraido:
                texto_completo += texto_extraido + "\n"
                
        # Retornamos texto limpio con un límite de caracteres
        return texto_completo.strip()[:max_chars]
        
    except Exception as e:
        raise ValueError(f"Error al procesar el documento PDF: {str(e)}")