import json
import tempfile
import io
import asyncio
import os
import requests
import streamlit as st
from audio_recorder_streamlit import audio_recorder
from google import genai
import edge_tts
from streamlit_lottie import st_lottie

# 1. Configuración de la página
st.set_page_config(page_title="Kenzo Jeans | Asistente Mantenimiento", layout="centered", page_icon="🎙️")

# Cargar animación Lottie de ondas de voz
@st.cache_data
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

lottie_voice = load_lottieurl("https://lottie.host/9e0004bc-6e4f-409b-a362-e64e9a8f4c39/iT1B3p4E7Y.json")

# Configuración del nuevo Cliente de Gemini (Soporta claves AQ.)
if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ No se encontró la GEMINI_API_KEY en los secretos.")
    client = None

VOZ_ASISTENTE = "es-CO-SalomeNeural" 

async def generar_audio(texto):
    communicate = edge_tts.Communicate(texto, VOZ_ASISTENTE)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

def hablar(texto, autoplay=True):
    try:
        audio_bytes = asyncio.run(generar_audio(texto))
        st.audio(audio_bytes, format="audio/mp3", autoplay=autoplay)
    except Exception as e:
        st.warning(f"Error generando el audio: {e}")

if "iniciado" not in st.session_state:
    st.session_state["iniciado"] = False

# -----------------------------------------------------------------------------
# PANTALLA DE BIENVENIDA
# -----------------------------------------------------------------------------
if not st.session_state["iniciado"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #4C8BF5;'>✨ Kenzo Jeans Voice</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #9AA0A6;'>Asistente Inteligente de Mantenimiento</p>", unsafe_allow_html=True)
    
    if lottie_voice:
        st_lottie(lottie_voice, height=200, key="voice_start")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🎙️ Tocar para Hablar", type="primary", use_container_width=True):
        st.session_state["iniciado"] = True
        st.rerun()

# -----------------------------------------------------------------------------
# INTERFAZ DE CONVERSACIÓN Y BIBLIOTECA
# -----------------------------------------------------------------------------
else:
    st.markdown("<h2 style='text-align: center; color: #4C8BF5;'>🎙️ Asistente de Mantenimiento</h2>", unsafe_allow_html=True)
    
    saludo = "Bienvenido a la aplicación para el reporte de mantenimiento Kenzo Jeans. ¿Qué reporte realizarás el día de hoy?"
    hablar(saludo, autoplay=True)
    
    st.markdown(
        """
        <div style='background-color: #1A1D24; padding: 15px; border-radius: 12px; border-left: 4px solid #4C8BF5; margin-bottom: 20px;'>
            <p style='margin:0; color: #F0F4F9; font-size: 1.05em;'><strong>🤖 Asistente:</strong> ¿Qué reporte realizarás el día de hoy?</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

    if lottie_voice:
        st_lottie(lottie_voice, height=140, key="voice_active")

    st.markdown("<p style='text-align: center; color: #9AA0A6;'>Presiona el micrófono para iniciar/detener tu dictado:</p>", unsafe_allow_html=True)

    audio_bytes = audio_recorder(
        text="",
        recording_color="#ea4335",
        neutral_color="#4C8BF5",
        icon_name="microphone",
        icon_size="3x"
    )

    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        
        if st.button("✨ Procesar Reporte", type="primary", use_container_width=True):
            with st.spinner("Interpretando voz..."):
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                        temp_audio.write(audio_bytes)
                        temp_audio_path = temp_audio.name

                    audio_file = client.files.upload(file=temp_audio_path)

                    prompt = """
                    Eres un asistente experto en mantenimiento industrial textil y de confección.
                    Escucha atentamente el audio e identifica la siguiente información en formato JSON válido:
                    {
                      "equipo_o_maquina": "Nombre o número de la máquina",
                      "falla_o_motivo": "Descripción del problema o motivo de intervención",
                      "trabajo_realizado": "Resumen claro del mantenimiento ejecutado",
                      "repuestos_utilizados": "Piezas sustituidas o 'Ninguno'",
                      "estado_final": "Operativa / En prueba / Fuera de servicio",
                      "observaciones_adicionales": "Notas o pendientes"
                    }
                    Si algún campo no es mencionado, asigna "No especificado".
                    """

                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=[audio_file, prompt]
                    )

                    texto_respuesta = response.text.replace("```json", "").replace("```", "").strip()
                    datos_reporte = json.loads(texto_respuesta)

                    st.markdown("---")
                    st.markdown("### 📋 Resumen del Mantenimiento")
                    
                    maquina = datos_reporte.get('equipo_o_maquina', 'No especificada')
                    estado = datos_reporte.get('estado_final', 'No especificado')
                    trabajo = datos_reporte.get('trabajo_realizado', 'No especificado')
                    
                    st.markdown(
                        f"""
                        <div style='background-color: #1A1D24; padding: 18px; border-radius: 12px; margin-top: 10px;'>
                            <p style='color: #4C8BF5; font-size: 1.2em; font-weight: bold; margin-bottom: 5px;'>🔧 {maquina}</p>
                            <p style='color: #34A853; font-weight: bold;'>Estado: {estado}</p>
                            <p style='color: #E8EAED;'><strong>Trabajo realizado:</strong> {trabajo}</p>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )

                    cierre_vocally = f"Entendido. Se ha guardado el reporte para {maquina} con estado {estado}."
                    hablar(cierre_vocally, autoplay=True)

                except Exception as e:
                    st.error(f"Error al analizar el audio: {e}")

    # -----------------------------------------------------------------------------
    # BIBLIOTECA TÉCNICA DE PLANTA (LECTOR DE MANUALES PDF CON ESPERA DE PROCESAMIENTO)
    # -----------------------------------------------------------------------------
    import time

    st.markdown("---")
    st.markdown("<h3 style='color: #4C8BF5;'>📚 Biblioteca Técnica de Planta</h3>", unsafe_allow_html=True)
    st.write("Sube el manual de la máquina en PDF y consulta dudas técnicas específicas.")

    archivo_pdf = st.file_uploader("Cargar manual técnico (PDF)", type=["pdf"])
    pregunta_mecanico = st.text_input("¿Qué necesitas saber de este manual?", placeholder="Ej: ¿Cómo calibro la presión de las ruedas?")

    if st.button("💡 Consultar Manual", type="primary"):
        if archivo_pdf is not None and pregunta_mecanico:
            with st.spinner("Procesando PDF y analizando manual con Gemini..."):
                try:
                    # 1. Guardar archivo temporalmente
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                        temp_pdf.write(archivo_pdf.read())
                        ruta_pdf = temp_pdf.name

                    # 2. Subir archivo a la API de Gemini
                    documento_cargado = client.files.upload(file=ruta_pdf)

                    # 3. Esperar a que el estado del archivo sea 'ACTIVE'
                    while documento_cargado.state.name == "PROCESSING":
                        time.sleep(2)
                        documento_cargado = client.files.get(name=documento_cargado.name)

                    if documento_cargado.state.name == "FAILED":
                        raise Exception("El procesamiento del archivo PDF falló en el servidor.")

                    # 4. Generar la respuesta
                    prompt_consulta = f"""
                    Eres un experto en mantenimiento industrial. Tu tarea es responder la pregunta del usuario basándote ÚNICA Y EXCLUSIVAMENTE en el documento PDF adjunto.
                    Si la respuesta no está en el documento, di claramente: "El manual no contiene información sobre esto."
                    Explica los pasos de forma clara y directa para un mecánico de planta.
                    
                    Pregunta del usuario: {pregunta_mecanico}
                    """

                    respuesta_tecnica = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=[documento_cargado, prompt_consulta]
                    )

                    # 5. Mostrar la respuesta de forma destacada
                    if respuesta_tecnica.text:
                        st.markdown("---")
                        st.markdown(
                            f"""
                            <div style='background-color: #1A1D24; padding: 18px; border-radius: 12px; border-left: 4px solid #34A853;'>
                                <p style='color: #34A853; font-size: 1.1em; font-weight: bold; margin-bottom: 8px;'>📖 Respuesta del Manual:</p>
                                <p style='color: #F0F4F9; font-size: 1em; line-height: 1.5;'>{respuesta_tecnica.text}</p>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                    else:
                        st.warning("No se pudo extraer texto de la respuesta.")

                    # Limpieza del archivo local
                    os.remove(ruta_pdf)

                except Exception as e:
                    st.error(f"Error al procesar el documento: {e}")
        else:
            st.warning("⚠️ Por favor, sube un manual en PDF y escribe una pregunta.")
