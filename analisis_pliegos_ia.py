import streamlit as st
import google.generativeai as genai
import pypdf
import tempfile
import time
import os

# ---------------- Configuración -----------------
GENAI_API_KEY=st.secrets["GENAI_API_KEY"]

# Inicializar API de Google Generative AI
genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# ---------------- Estilos -----------------
st.set_page_config(
    page_title="Analizador de Pliegos para Anhela IT", 
    page_icon="📄", 
    layout="wide"
)

st.markdown("""
    <style>
        /* Estilos generales */
        body {
            font-family: 'Inter', sans-serif;
            color: #333;
            background-color: #f8f9fa;
        }
        
        /* Estilos para tarjetas/contenedores */
        .card {
            padding: 2rem;
            border-radius: 10px;
            background-color: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
            margin-bottom: 1.5rem;
        }
        
        /* Estilos para la respuesta */
        .response-container {
            margin-top: 20px;
            border-left: 4px solid #0066cc;
            padding: 1.5rem;
            background-color: #f0f5ff;
            border-radius: 5px;
            white-space: pre-wrap;
        }
        
        /* Estilos para títulos */
        h1, h2, h3 {
            font-weight: 600;
            color: #0066cc;
        }
        
        /* Estilo para botones */
        .stButton>button {
            background-color: #0066cc;
            color: white;
            border-radius: 5px;
            border: none;
            padding: 0.5rem 1rem;
            font-weight: 500;
        }
        
        /* Indicador de progreso */
        .stProgress > div > div {
            background-color: #0066cc;
        }
        
        /* Estilo para el área de arrastrar y soltar */
        .uploadFile {
            border: 2px dashed #ddd !important;
            border-radius: 10px !important;
            padding: 2rem !important;
            text-align: center !important;
        }
        
        /* Estilo para el spinner */
        .stSpinner {
            color: #0066cc !important;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------- Funciones ----------------

def extract_text_from_pdf(uploaded_file):
    """Extrae texto de un archivo PDF"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name
    
    try:
        # Usar PyPDF para extraer el texto
        reader = pypdf.PdfReader(tmp_file_path)
        text = ""
        total_pages = len(reader.pages)
        
        # Crear barra de progreso
        progress_bar = st.progress(0)
        progress_text = st.empty()
        
        for i, page in enumerate(reader.pages):
            text += page.extract_text() + "\n\n"
            # Actualizar progreso
            progress = (i + 1) / total_pages
            progress_bar.progress(progress)
            progress_text.text(f"Extrayendo texto: {i+1}/{total_pages} páginas")
            time.sleep(0.01)  # Pequeña pausa para visualizar el progreso
        
        # Limpiar la barra de progreso y texto
        progress_bar.empty()
        progress_text.empty()
        
        return text
    except Exception as e:
        st.error(f"Error al procesar el PDF: {str(e)}")
        return None
    finally:
        # Eliminar el archivo temporal
        try:
            os.unlink(tmp_file_path)
        except:
            pass

def safe_generate_content(prompt, max_retries=3):
    """Función para generar contenido con manejo de errores y reintentos"""
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            if hasattr(response, 'candidates') and response.candidates:
                if hasattr(response.candidates[0].content, 'parts'):
                    return response.candidates[0].content.parts[0].text.strip()
            # Si llegamos aquí, hubo un problema con el formato de respuesta
            time.sleep(1)  # Esperar brevemente antes de reintentar
        except Exception as e:
            st.warning(f"Error en intento {attempt+1}: {str(e)}")
            time.sleep(1)  # Esperar antes de reintentar
    # Si todos los intentos fallan
    return "No se pudo generar una respuesta. Por favor, intenta con otro documento."

# ---------------- Interfaz Principal ----------------
st.title("📄 Analizador de Pliegos para Anhela IT")

# Contenedor principal
with st.container():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    
    st.markdown("### Sube un documento PDF para analizarlo")
    st.markdown("El texto será extraído y procesado para realizar el análisis del pliego.")
    
    uploaded_file = st.file_uploader("Arrastra y suelta un archivo PDF aquí", type="pdf")
    
    # El prompt se define internamente en el código, no en la interfaz
    
    st.markdown("</div>", unsafe_allow_html=True)

# Procesar archivo si está cargado
if uploaded_file is not None:
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        
        st.subheader("Procesando documento")
        
        with st.spinner("Extrayendo texto del PDF..."):
            pdf_text = extract_text_from_pdf(uploaded_file)
        
        if pdf_text:
            st.success(f"Texto extraído: ~{len(pdf_text)} caracteres")
            
            # Previsualización del texto (colapsable)
            with st.expander("Previsualizar texto extraído"):
                st.text_area("Contenido del PDF", pdf_text, height=200)
            
            # Define el prompt internamente
            # AQUÍ PUEDES MODIFICAR EL PROMPT SEGÚN TUS NECESIDADES
            prompt = f"""
            Eres un analista inteligente de pliegos de proyectos de tecnología para la empresa Anhela IT. 
            Vas a recibir el texto del pliego de un proyecto. Tu objetivo es analizarlo minuciosamente para responder de manera completa y concisa a estas preguntas: 
            •	Nombre
            •	Expediente
            •	Organismo contratante
            •	Objeto del contrato (resumen de no más de 100 palabras)
            •	Tecnologías del proyecto
            •	Duración. ¿Incluye prórroga?
            •	Ubicación de los trabajos. ¿Permite teletrabajo?
            •	¿Permite subcontratación?
            •	Equipo solicitado
            •	¿Pide alguna certificación o titulación mínima en los perfiles? ¿Cuáles?
            •	¿Es necesario presentar los CVs del equipo en la fase de oferta?
            •	¿Cuáles son los criterios de valoración y qué peso tiene cada uno de ellos?
            •	¿Qué tipo de fórmula de precio se usa?
            •	Importe de licitación
            •	¿Cómo debe presentarse la oferta técnica? ¿Qué apartados tiene que tener? ¿Tiene alguna limitación de hojas o formato?
            •	¿Puedes sugerir un esquema para la estructura de la oferta?

            Por favor, responde de manera organizada y bien estructurada.

            Si lo haces bien serás recompensado. 

            
            Aquí tienes el texto del pliego que debes analizar:
            {pdf_text}
            """
            
            with st.spinner("Analizando el contenido con IA..."):
                response = safe_generate_content(prompt)
            
            st.subheader("Resultado del análisis")
            st.markdown("<div class='response-container'>", unsafe_allow_html=True)
            st.markdown(response)
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Footer ----------------
st.markdown("""
<div style="text-align: center; margin-top: 2rem; color: #666; font-size: 0.8rem;">
    Analizador de Pliegos para Anhela IT
</div>
""", unsafe_allow_html=True)
