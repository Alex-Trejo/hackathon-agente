# 🛡️ Sistema Agéntico de Pre-Autorizaciones Médicas (IA)

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://hackathon-agente-8dijxcojc8haf4sdobmvs2.streamlit.app)

Este proyecto fue desarrollado para el **hackIAthon (Ecuador)**. Resuelve el cuello de botella de las pre-autorizaciones médicas, reduciendo el tiempo de espera de días a **milisegundos** mediante el uso de Inteligencia Artificial y un enfoque "Headless CRM" con Notion.

## 👥 Equipo: KINEX
* **JUAN PABLO PINZA ARMIJOS**
* **ALEX FERNANDO TREJO DUQUE**

## 🚀 Demo en Vivo
**[Haz clic aquí para probar el Agente Funcional en Vivo](https://hackathon-agente-8dijxcojc8haf4sdobmvs2.streamlit.app)**

## 🏗️ Arquitectura del Sistema
El sistema consta de 3 capas principales:
1. **Frontend (Streamlit):** Interfaz amigable para el Hospital y el panel de administración del CRM.
2. **Base de Datos (Notion API):** Actúa como el sistema de gestión de pólizas de la Aseguradora, permitiendo lectura y escritura en tiempo real.
3. **Cerebro Agéntico (LLM):** Extrae información de PDFs médicos no estructurados y audita las reglas de negocio (Cobertura y Carencia) usando `temperature=0.0` para garantizar respuestas deterministas y exactas.

## ⚙️ Tecnologías Utilizadas
* **Python 3**
* **Streamlit** (Interfaz y Deploy automatizado)
* **OpenAI API (gpt-4o-mini)** (Procesamiento de Lenguaje Natural y Toma de Decisiones)
* **Notion API** (Gestión de Base de Datos de Asegurados)
* **PyPDF2** (Extracción de texto en memoria)

## 📋 ¿Cómo probarlo?
1. Ingresa a la aplicación web.
2. Ve a la pestaña **"Reglas y Plantillas"** y descarga el informe médico de prueba.
3. Regresa a **"Auditoría IA"**, sube el PDF y observa cómo el agente orquesta el flujo completo de validación.
4. *Opcional:* Ve a la pestaña **"Alta de Asegurado"**, registra un paciente, y sube un PDF modificado con esos nuevos datos.