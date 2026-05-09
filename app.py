import streamlit as st
from utils_pdf import extraer_texto_pdf
from utils_ia import extraer_datos_paciente, evaluar_auditoria
from utils_notion import obtener_datos_poliza, listar_pacientes

st.set_page_config(page_title="Agente IA Aseguradora", page_icon="🛡️", layout="wide")

# --- ESTILOS CSS ---
st.markdown("""
<style>
.aprobado { color: #0f5132; background-color: #d1e7dd; padding: 15px; border-radius: 8px; border: 1px solid #badbcc; }
.rechazado { color: #842029; background-color: #f8d7da; padding: 15px; border-radius: 8px; border: 1px solid #f5c2c7; }
</style>
""", unsafe_allow_html=True)

# --- CABECERA ---
st.title("🛡️ Sistema Agéntico de Pre-Autorizaciones")
st.write("Agente automatizado que audita informes médicos, cruza datos con el CRM en Notion y dictamina coberturas.")

# --- PESTAÑAS DEL DASHBOARD ---
tab1, tab2, tab3 = st.tabs(["🩺 Auditoría IA", "📊 CRM de Pacientes (Notion)", "ℹ️ Reglas y Plantillas"])

# ==========================================
# PESTAÑA 1: AUDITORÍA (SISTEMA PRINCIPAL)
# ==========================================
with tab1:
    col_izq, col_der = st.columns([1, 1.5])
    
    with col_izq:
        st.subheader("📥 Subir Informe Médico")
        archivo_subido = st.file_uploader("Adjunta el PDF enviado por el Hospital:", type=["pdf"])
        
        if archivo_subido:
            st.success("✅ Archivo PDF cargado correctamente en memoria.")
            iniciar = st.button("🚀 Procesar con Inteligencia Artificial", type="primary", use_container_width=True)
            
    with col_der:
        if archivo_subido and iniciar:
            st.subheader("⚙️ Consola de Razonamiento del Agente")
            try:
                with st.status("Ejecutando orquestación...", expanded=True) as status:
                    
                    st.write("📄 **1. Extrayendo texto del PDF...**")
                    texto_pdf = extraer_texto_pdf(archivo_subido)
                    if not texto_pdf:
                        raise ValueError("El PDF está vacío o es una imagen escaneada sin texto.")
                        
                    st.write("🧠 **2. IA reconociendo variables clave...**")
                    datos_paciente = extraer_datos_paciente(texto_pdf)
                    cedula = datos_paciente.get("cedula")
                    procedimiento = datos_paciente.get("procedimiento")
                    st.code(f"Detectado -> Cédula: {cedula} | Solicitud: {procedimiento}")
                    
                    st.write("🏢 **3. Conectando con API de Notion (Aseguradora)...**")
                    if not cedula:
                        raise ValueError("No se pudo detectar una cédula válida en el PDF.")
                        
                    datos_poliza = obtener_datos_poliza(cedula)
                    if not datos_poliza:
                        raise ValueError(f"El paciente con cédula {cedula} NO está registrado en la póliza.")
                    
                    st.write("⚖️ **4. IA auditando reglas de negocio...**")
                    dictamen = evaluar_auditoria(datos_paciente, datos_poliza)
                    
                    status.update(label="✅ Orquestación finalizada exitosamente.", state="complete", expanded=False)

                # RENDERIZAR RESULTADO FINAL
                st.divider()
                st.subheader("⚖️ Dictamen Oficial")
                estado = dictamen.get("estado", "INDEFINIDO")
                motivo = dictamen.get("motivo", "")
                carta = dictamen.get("carta", "")
                
                if estado == "APROBADO":
                    st.markdown(f"<div class='aprobado'><h3>✅ APROBADO</h3><p><b>Razón técnica:</b> {motivo}</p></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='rechazado'><h3>❌ {estado}</h3><p><b>Razón técnica:</b> {motivo}</p></div>", unsafe_allow_html=True)
                
                st.markdown("#### ✉️ Respuesta Automatizada al Hospital:")
                st.info(carta)

            except Exception as e:
                st.error(f"⚠️ **Error en el flujo:** {str(e)}")

# ==========================================
# PESTAÑA 2: CRM NOTION (LISTA EN VIVO)
# ==========================================
with tab2:
    st.subheader("📊 Base de Datos de Asegurados (Live from Notion)")
    st.write("Esta tabla consulta en tiempo real la API de Notion para mostrar los pacientes vigentes.")
    
    if st.button("🔄 Actualizar Datos desde Notion"):
        pass # Streamlit recarga la página automáticamente
        
    pacientes_db = listar_pacientes()
    if pacientes_db:
        st.dataframe(pacientes_db, use_container_width=True)
    else:
        st.warning("No se encontraron pacientes o hay un problema de conexión con Notion.")

# ==========================================
# PESTAÑA 3: REGLAS Y PLANTILLAS (UX/UI)
# ==========================================
with tab3:
    st.subheader("ℹ️ ¿Cómo funciona el Agente de Auditoría?")
    
    st.markdown("""
    Este sistema fue diseñado para agilizar la pre-autorización de cirugías. El flujo es el siguiente:
    1. **Extracción:** La IA usa procesamiento de lenguaje natural (NLP) para leer el PDF del hospital y extraer la **Cédula** y el **Procedimiento**.
    2. **Validación:** El sistema entra al CRM (Notion) de la aseguradora y consulta la póliza vinculada a esa Cédula.
    3. **Evaluación Estricta:** La IA evalúa dos reglas fundamentales:
        * 🔍 **Cobertura:** ¿El procedimiento solicitado está incluido en la columna 'Procedimientos Cubiertos'?
        * ⏳ **Carencia:** ¿El paciente tiene `3 meses o más` registrados en la columna 'Carencia Cumplida'?
    4. **Emisión:** Si cumple ambas, aprueba. Si falta una, rechaza.
    """)
    
    st.divider()
    st.subheader("📄 Plantilla de Prueba")
    st.write("Puedes copiar este texto, pegarlo en Word y guardarlo como PDF para probar el sistema:")
    
    plantilla_texto = """HOSPITAL METROPOLITANO
INFORME MÉDICO DE EMERGENCIA

Datos del Paciente:
Nombre: ALEX TREJO
Cédula: 1752939783

Diagnóstico Clínico:
El paciente ingresó por emergencia presentando dolor abdominal agudo en la fosa ilíaca derecha, acompañado de fiebre y náuseas. Tras los exámenes de laboratorio y ecografía, se confirma el diagnóstico de apendicitis aguda.

Procedimiento Solicitado:
Se requiere autorización urgente de la aseguradora para proceder con la cirugía de: Apendicectomía."""

    st.code(plantilla_texto, language="markdown")
    st.download_button(
        label="⬇️ Descargar Plantilla en .txt",
        data=plantilla_texto,
        file_name="plantilla_informe_medico.txt",
        mime="text/plain"
    )