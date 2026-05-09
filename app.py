import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")  # Ruta absoluta al .env junto a app.py

import streamlit as st
from utils_pdf import extraer_texto_pdf, generar_pdf_plantilla
from utils_ia import extraer_datos_paciente, evaluar_auditoria
from utils_notion import obtener_datos_poliza, listar_pacientes, agregar_paciente

st.set_page_config(page_title="Agente IA Aseguradora", page_icon="🛡️", layout="wide")

# --- ESTILOS CSS PREMIUM ---
st.markdown("""
<style>
/* ===== TIPOGRAFÍA ===== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ===== RESULTADO APROBADO ===== */
.aprobado {
    color: #0f5132;
    background: linear-gradient(135deg, #d1e7dd 0%, #badbcc 100%);
    padding: 20px 24px;
    border-radius: 12px;
    border-left: 5px solid #198754;
    box-shadow: 0 4px 15px rgba(25, 135, 84, 0.15);
    animation: fadeSlideIn 0.5s ease-out;
}

/* ===== RESULTADO RECHAZADO ===== */
.rechazado {
    color: #842029;
    background: linear-gradient(135deg, #f8d7da 0%, #f5c2c7 100%);
    padding: 20px 24px;
    border-radius: 12px;
    border-left: 5px solid #dc3545;
    box-shadow: 0 4px 15px rgba(220, 53, 69, 0.15);
    animation: fadeSlideIn 0.5s ease-out;
}

/* ===== TARJETA DE REGLA ===== */
.regla-card {
    padding: 14px 18px;
    border-radius: 10px;
    margin-bottom: 10px;
    font-size: 0.92em;
    line-height: 1.5;
    animation: fadeSlideIn 0.4s ease-out;
}
.regla-cumple {
    background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
    border-left: 4px solid #4caf50;
    color: #1b5e20;
}
.regla-falla {
    background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
    border-left: 4px solid #f44336;
    color: #b71c1c;
}

/* ===== BADGE DE CONFIANZA ===== */
.badge-confianza {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.85em;
    letter-spacing: 0.5px;
}
.badge-alta { background: #d1e7dd; color: #0f5132; }
.badge-media { background: #fff3cd; color: #664d03; }
.badge-baja { background: #f8d7da; color: #842029; }

/* ===== SECCIÓN DE ARQUITECTURA ===== */
.arq-card {
    background: linear-gradient(135deg, #1e2330 0%, #252d40 100%);
    border: 1px solid rgba(99, 130, 255, 0.2);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    height: 100%;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}
.arq-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 24px rgba(99, 130, 255, 0.15);
    border-color: rgba(99, 130, 255, 0.5);
}
.arq-card h4 { margin: 10px 0 8px; color: #e2e8f0; }
.arq-card p { color: #94a3b8; font-size: 0.88em; margin: 0; }
.arq-icon { font-size: 2.2em; }

/* ===== ANIMACIONES ===== */
@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ===== FOOTER ===== */
.footer {
    text-align: center;
    padding: 20px 0 10px;
    color: #6c757d;
    font-size: 0.82em;
    border-top: 1px solid #dee2e6;
    margin-top: 40px;
}
</style>
""", unsafe_allow_html=True)

# --- BARRA LATERAL (INFORMACIÓN DEL EQUIPO) ---
with st.sidebar:
    st.header("🇪🇨 hackIAthon Ecuador")
    st.subheader("🚀 Grupo: KINEX")
    st.markdown("**Integrantes:**")
    st.markdown("- JUAN PABLO PINZA ARMIJOS\n- ALEX FERNANDO TREJO DUQUE")
    st.divider()
    st.info("📍 **Reto 1:** Agente de Pre-Autorización Quirúrgica en Tiempo Real")
    st.success("Herramientas: Notion API, OpenAI & Streamlit")
    st.divider()
    st.caption("🔧 **Stack Tecnológico**")
    st.markdown("""
    | Componente | Tecnología |
    |---|---|
    | 🖥️ Frontend | Streamlit |
    | 🧠 IA | GPT-4o-mini |
    | 🏢 CRM | Notion API |
    | 📄 PDF | PyPDF2 |
    """)
    
# --- CABECERA ---
st.title("🛡️ Sistema Agéntico de Pre-Autorizaciones")
st.write("Agente automatizado que audita informes médicos, cruza datos con el CRM en Notion y dictamina coberturas.")

# --- PESTAÑAS DEL DASHBOARD ---
tab1, tab2, tab3, tab4 = st.tabs(["🩺 Auditoría IA", "📊 CRM de Pacientes (Notion)", "➕ Alta de Asegurado", "ℹ️ Reglas y Plantillas"])

# ==========================================
# PESTAÑA 1: AUDITORÍA (SISTEMA PRINCIPAL)
# ==========================================
with tab1:
    col_izq, col_der = st.columns([1, 1.5])
    
    with col_izq:
        st.subheader("📥 Ingresar Informe Médico")
        
        modo = st.radio(
            "¿Cómo deseas ingresar el informe?",
            ["📄 Subir PDF", "📋 Pegar texto directamente"],
            horizontal=True,
            key="modo_entrada"
        )
        
        listo_para_procesar = False
        texto_entrada = None
        metadata_pdf = None

        if modo == "📄 Subir PDF":
            archivo_subido = st.file_uploader("Adjunta el PDF enviado por el Hospital:", type=["pdf"])
            if archivo_subido:
                st.success("✅ Archivo PDF cargado correctamente en memoria.")
                listo_para_procesar = True
        else:
            texto_entrada = st.text_area(
                "Pega aquí el texto del informe médico:",
                height=280,
                placeholder="HOSPITAL METROPOLITANO\nNombre: ALEX TREJO\nCédula: 1752939783\nProcedimiento: Apendicectomía..."
            )
            if texto_entrada and texto_entrada.strip():
                st.success(f"✅ Texto recibido ({len(texto_entrada)} caracteres).")
                listo_para_procesar = True
            else:
                st.caption("💡 Puedes copiar el texto de una plantilla en la pestaña **Reglas y Plantillas**.")
                archivo_subido = None

        if listo_para_procesar:
            iniciar = st.button("🚀 Procesar con Inteligencia Artificial", type="primary", width="stretch")
        else:
            iniciar = False

    with col_der:
        if listo_para_procesar and iniciar:
            st.subheader("⚙️ Consola de Razonamiento del Agente")
            try:
                with st.status("Ejecutando orquestación...", expanded=True) as status:

                    # === PASO 1: OBTENCIÓN DEL TEXTO ===
                    if modo == "📄 Subir PDF":
                        st.write("📄 **1. Extrayendo texto del PDF...**")
                        resultado_pdf = extraer_texto_pdf(archivo_subido)
                        texto_pdf = resultado_pdf["texto"]
                        if not texto_pdf:
                            raise ValueError("El PDF está vacío o es una imagen escaneada sin texto.")
                        st.caption(f"ℹ️ {resultado_pdf['paginas']}/{resultado_pdf['total_paginas']} páginas procesadas · {resultado_pdf['caracteres']} caracteres extraídos" + (" · ⚠️ Texto truncado" if resultado_pdf['truncado'] else ""))
                    else:
                        st.write("📋 **1. Usando texto ingresado directamente...**")
                        texto_pdf = texto_entrada.strip()
                        st.caption(f"ℹ️ {len(texto_pdf)} caracteres recibidos (modo texto directo)")

                    # === PASO 2: IA EXTRAE VARIABLES ===
                    st.write("🧠 **2. IA reconociendo variables clave...**")
                    datos_paciente = extraer_datos_paciente(texto_pdf)
                    cedula = datos_paciente.get("cedula")
                    procedimiento = datos_paciente.get("procedimiento")
                    nombre_ia = datos_paciente.get("nombre_paciente", "—")
                    confianza = datos_paciente.get("confianza", 0)
                    
                    if confianza >= 80:
                        badge_class = "badge-alta"
                    elif confianza >= 50:
                        badge_class = "badge-media"
                    else:
                        badge_class = "badge-baja"
                    
                    st.code(f"Detectado -> Cédula: {cedula} | Solicitud: {procedimiento} | Paciente: {nombre_ia}")
                    st.markdown(f"<span class='badge-confianza {badge_class}'>🎯 Confianza IA: {confianza}%</span>", unsafe_allow_html=True)
                    
                    # === PASO 3: CONSULTA A NOTION ===
                    st.write("🏢 **3. Conectando con API de Notion (Aseguradora)...**")
                    if not cedula:
                        raise ValueError("No se pudo detectar una cédula válida en el informe.")
                        
                    datos_poliza = obtener_datos_poliza(cedula)
                    if not datos_poliza:
                        raise ValueError(f"El paciente con cédula {cedula} NO está registrado en la póliza.")
                    
                    st.code(f"Póliza encontrada -> {datos_poliza['Paciente']} | Plan: {datos_poliza['Plan Médico']} | Carencia: {datos_poliza['Meses de Carencia']} meses")
                    
                    # === PASO 4: AUDITORÍA IA ===
                    st.write("⚖️ **4. IA auditando reglas de negocio...**")
                    dictamen = evaluar_auditoria(datos_paciente, datos_poliza)
                    
                    status.update(label="✅ Orquestación finalizada exitosamente.", state="complete", expanded=False)

                # ==========================================
                # RENDERIZAR RESULTADO FINAL
                # ==========================================
                st.divider()
                st.subheader("⚖️ Dictamen Oficial")
                
                estado = dictamen.get("estado", "INDEFINIDO")
                motivo = dictamen.get("motivo", "")
                carta = dictamen.get("carta", "")
                detalle_reglas = dictamen.get("detalle_reglas", [])
                
                if estado == "APROBADO":
                    st.markdown(f"<div class='aprobado'><h3>✅ APROBADO</h3><p><b>Razón técnica:</b> {motivo}</p></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='rechazado'><h3>❌ {estado}</h3><p><b>Razón técnica:</b> {motivo}</p></div>", unsafe_allow_html=True)
                
                st.markdown("####")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("👤 Paciente", datos_poliza.get("Paciente", "—"))
                m2.metric("📋 Plan", datos_poliza.get("Plan Médico", "—"))
                m3.metric("⏳ Carencia", f"{datos_poliza.get('Meses de Carencia', 0)} meses")
                m4.metric("🔬 Procedimiento", procedimiento or "—")
                
                if detalle_reglas:
                    st.markdown("#### 📐 Evaluación Regla por Regla")
                    for regla in detalle_reglas:
                        nombre_regla = regla.get("regla", "")
                        cumple = regla.get("cumple", False)
                        explicacion = regla.get("explicacion", "")
                        icono = "✅" if cumple else "❌"
                        css_class = "regla-cumple" if cumple else "regla-falla"
                        st.markdown(
                            f"<div class='regla-card {css_class}'>"
                            f"<strong>{icono} {nombre_regla}:</strong> {explicacion}"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                
                st.markdown("#### ✉️ Respuesta Automatizada al Hospital:")
                st.info(carta)
                
                with st.expander("📋 Ver datos crudos de la Póliza (Notion)"):
                    st.json(datos_poliza)
                with st.expander("🧠 Ver respuesta completa de la IA (Auditoría)"):
                    st.json(dictamen)

            except Exception as e:
                st.error(f"⚠️ **Error en el flujo:** {str(e)}")

# ==========================================
# PESTAÑA 2: CRM NOTION (LISTA EN VIVO)
# ==========================================
with tab2:
    st.subheader("📊 Base de Datos de Asegurados (Live from Notion)")
    st.write("Esta tabla consulta en tiempo real la API de Notion para mostrar los pacientes vigentes.")
    
    if st.button("🔄 Actualizar Tabla"):
        pass 
        
    pacientes_db = listar_pacientes()
    if pacientes_db:
        st.dataframe(pacientes_db, use_container_width=True)
    else:
        st.warning("No se encontraron pacientes o hay un problema de conexión con Notion.")

# ==========================================
# PESTAÑA 3: FORMULARIO ALTA PACIENTE 
# ==========================================
with tab3:
    st.subheader("➕ Registrar Nuevo Asegurado")
    st.write("Agrega un paciente a la base de datos de Notion directamente desde este formulario.")
    
    # Inicializar el contador de formulario (permite reiniciarlo limpiando todos los campos)
    if "form_counter" not in st.session_state:
        st.session_state["form_counter"] = 0

    # Mostrar mensaje de éxito si fue guardado exitosamente
    if st.session_state.get("exito_guardado", False):
        st.success("✅ ¡Paciente agregado con éxito! Ve a la pestaña 'CRM de Pacientes' para confirmarlo.")
        st.session_state["exito_guardado"] = False

    # La clave del formulario cambia con el contador → Streamlit lo re-crea desde cero (campos vacíos)
    form_key = f"form_nuevo_paciente_{st.session_state['form_counter']}"
    
    with st.form(form_key, clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            new_cedula = st.text_input("Número de Cédula (10 dígitos)", max_chars=10)
            new_nombre = st.text_input("Nombre Completo (Sin números)")
        with col2:
            new_plan = st.selectbox("Plan Médico", ["Básico", "Premium", "VIP"])
            new_carencia = st.number_input("Meses de Carencia Cumplidos", min_value=0, step=1)
        
        new_procedimientos = st.text_area("Procedimientos Cubiertos (separados por coma)")
        
        submit_btn = st.form_submit_button("💾 Guardar Paciente en Notion")
        
        if submit_btn:
            # --- VALIDACIONES ---
            errores = []
            
            if not new_cedula.isdigit():
                errores.append("⚠️ La Cédula debe contener SOLO números (sin guiones ni espacios).")
            elif len(new_cedula) != 10:
                errores.append("⚠️ La Cédula debe tener exactamente 10 dígitos.")
                
            nombre_limpio = new_nombre.replace(" ", "")
            if not new_nombre.strip():
                errores.append("⚠️ El Nombre no puede estar vacío.")
            elif not nombre_limpio.isalpha():
                errores.append("⚠️ El Nombre solo debe contener letras.")
                
            if not new_procedimientos.strip():
                errores.append("⚠️ Debes ingresar al menos un procedimiento cubierto.")
                
            # --- EJECUCIÓN O MUESTRA DE ERRORES ---
            if errores:
                for error in errores:
                    st.error(error)
            else:
                with st.spinner("Escribiendo en la base de datos de Notion..."):
                    try:
                        agregar_paciente(new_cedula, new_nombre.upper(), new_plan, int(new_carencia), new_procedimientos)
                        
                        # Incrementar el contador reinicia el formulario sin tocar los keys de los widgets
                        st.session_state["form_counter"] += 1
                        st.session_state["exito_guardado"] = True
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Ocurrió un error al guardar: {str(e)}")

# ==========================================
# PESTAÑA 4: REGLAS Y PLANTILLAS (UX/UI)
# ==========================================
with tab4:
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
    
    # --- ARQUITECTURA VISUAL ---
    st.divider()
    st.subheader("🏗️ Arquitectura del Sistema")
    
    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown("""
        <div class='arq-card'>
            <div class='arq-icon'>🖥️</div>
            <h4>Frontend</h4>
            <p>Streamlit<br>Interfaz interactiva para el Hospital y Admin de la Aseguradora</p>
        </div>
        """, unsafe_allow_html=True)
    with a2:
        st.markdown("""
        <div class='arq-card'>
            <div class='arq-icon'>🧠</div>
            <h4>Cerebro Agéntico</h4>
            <p>GPT-4o-mini<br>Extracción NLP + Auditoría con temperature=0.0</p>
        </div>
        """, unsafe_allow_html=True)
    with a3:
        st.markdown("""
        <div class='arq-card'>
            <div class='arq-icon'>🏢</div>
            <h4>CRM / Base de Datos</h4>
            <p>Notion API<br>Gestión de pólizas en tiempo real (Lectura + Escritura)</p>
        </div>
        """, unsafe_allow_html=True)
    
    # --- PLANTILLAS DE PRUEBA ---
    st.divider()
    st.subheader("📄 Plantillas de Prueba")
    st.write("Descarga directamente como **PDF** o **TXT**, o copia el texto para pegarlo en la pestaña **Auditoría IA**:")
    
    plantilla_aprobado = """HOSPITAL METROPOLITANO
INFORME MEDICO DE EMERGENCIA

Datos del Paciente:
Nombre: ALEX TREJO
Cedula: 1752939783

Diagnostico Clinico:
El paciente ingreso por emergencia presentando dolor abdominal agudo en la fosa
iliaca derecha, acompanado de fiebre y nauseas. Tras los examenes de laboratorio
y ecografia, se confirma el diagnostico de apendicitis aguda.

Procedimiento Solicitado:
Se requiere autorizacion urgente de la aseguradora para proceder con la
cirugia de: Apendicectomia."""

    plantilla_rechazado = """HOSPITAL METROPOLITANO
INFORME MEDICO DE CONSULTA EXTERNA

Datos del Paciente:
Nombre: ALEX TREJO
Cedula: 1752939783

Diagnostico Clinico:
El paciente acude a consulta programada por molestias esteticas en la region
nasal. Tras la evaluacion del otorrinolaringologo, se determina la necesidad
de una rinoplastia correctiva con fines esteticos.

Procedimiento Solicitado:
Se requiere autorizacion de la aseguradora para proceder con: Rinoplastia Estetica."""

    col_aprobado, col_rechazado = st.columns(2)
    
    with col_aprobado:
        st.markdown("##### ✅ Caso que DEBERÍA ser APROBADO")
        st.caption("Paciente registrado, procedimiento cubierto, carencia cumplida.")
        st.code(plantilla_aprobado, language="markdown")
        b1, b2 = st.columns(2)
        b1.download_button(
            label="⬇️ Descargar .txt",
            data=plantilla_aprobado,
            file_name="caso_aprobado.txt",
            mime="text/plain",
            use_container_width=True
        )
        b2.download_button(
            label="⬇️ Descargar .pdf",
            data=generar_pdf_plantilla("Informe Medico - Caso APROBADO", plantilla_aprobado),
            file_name="caso_aprobado.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    
    with col_rechazado:
        st.markdown("##### ❌ Caso que DEBERÍA ser RECHAZADO")
        st.caption("El procedimiento no está dentro de la cobertura del paciente.")
        st.code(plantilla_rechazado, language="markdown")
        b3, b4 = st.columns(2)
        b3.download_button(
            label="⬇️ Descargar .txt",
            data=plantilla_rechazado,
            file_name="caso_rechazado.txt",
            mime="text/plain",
            use_container_width=True
        )
        b4.download_button(
            label="⬇️ Descargar .pdf",
            data=generar_pdf_plantilla("Informe Medico - Caso RECHAZADO", plantilla_rechazado),
            file_name="caso_rechazado.pdf",
            mime="application/pdf",
            use_container_width=True
        )

# --- FOOTER ---
st.markdown("""
<div class='footer'>
    🛡️ Sistema Agéntico de Pre-Autorizaciones · Equipo <strong>KINEX</strong> · hackIAthon Ecuador 2026<br>
    Desarrollado con Streamlit · OpenAI · Notion API
</div>
""", unsafe_allow_html=True)