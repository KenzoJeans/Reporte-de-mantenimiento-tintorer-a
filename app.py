import json
import tempfile
import io
import asyncio
import requests
import streamlit as st
from audio_recorder_streamlit import audio_recorder
import google.generativeai as genai
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

# Animación de ondas de sonido estilo Gemini Live
lottie_voice = load_lottieurl("https://lottie.host/9e0004bc-6e4f-409b-a362-e64e9a8f4c39/iT1B3p4E7Y.json")

# Configuración de API Key
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ No se encontró la GEMINI_API_KEY en los secretos.")

# Configurar voz neuronal colombiana (Salomé)
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

# Estado de la sesión
if "iniciado" not in st.session_state:
    st.session_state["iniciado"] = False

# -----------------------------------------------------------------------------
# PANTALLA DE BIENVENIDA (ESTILO GEMINI LIVE)
# -----------------------------------------------------------------------------
if not st.session_state["iniciado"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #4C8BF5;'>✨ Kenzo Jeans Voice</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #9AA0A6;'>Asistente Inteligente de Mantenimiento</p>", unsafe_allow_html=True)
    
    # Animación central de inicio
    if lottie_voice:
        st_lottie(lottie_voice, height=200, key="voice_start")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🎙️ Tocar para Hablar", type="primary", use_container_width=True):
        st.session_state["iniciado"] = True
        st.rerun()

# -----------------------------------------------------------------------------
# INTERFAZ DE CONVERSACIÓN
# -----------------------------------------------------------------------------
else:
    st.markdown("<h2 style='text-align: center; color: #4C8BF5;'>🎙️ Asistente de Mantenimiento</h2>", unsafe_allow_html=True)
    
    # Saludo por voz e instrucción en pantalla
    saludo = "Bienvenido a la aplicación para el reporte de mantenimiento Kenzo Jeans. ¿Qué reporte realizarás el día de hoy?"
    hablar(saludo, autoplay=True)
    
    # Tarjeta de mensaje del asistente
    st.markdown(
        """
        <div style='background-color: #1A1D24; padding: 15px; border-radius: 12px; border-left: 4px solid #4C8BF5; margin-bottom: 20px;'>
            <p style='margin:0; color: #F0F4F9; font-size: 1.05em;'><strong>🤖 Asistente:</strong> ¿Qué reporte realizarás el día de hoy?</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

    # Animación de escucha viva
    if lottie_voice:
        st_lottie(lottie_voice, height=140, key="voice_active")

    st.markdown("<p style='text-align: center; color: #9AA0A6;'>Presiona el micrófono para iniciar/detener tu dictado:</p>", unsafe_allow_html=True)

    # Micrófono
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

                    audio_file = genai.upload_file(path=temp_audio_path)

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

                    model = genai.GenerativeModel("gemini-1.5-flash")
                    response = model.generate_content([audio_file, prompt])

                    texto_respuesta = response.text.replace("```json", "").replace("```", "").strip()
                    datos_reporte = json.loads(texto_respuesta)

                    st.markdown("---")
                    st.markdown("### 📋 Resumen del Mantenimiento")
                    
                    # Presentación visual estilizada estilo tarjeta
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

                    # Confirmación hablada del cierre
                    cierre_vocally = f"Entendido. Se ha guardado el reporte para {maquina} con estado {estado}."
                    hablar(cierre_vocally, autoplay=True)

                except Exception as e:
                    st.error(f"Error al analizar el audio: {e}")

    st.markdown("<br><hr>", unsafe_allow_html=True)
    if st.button("🔄 Nuevo Reporte"):
        st.session_state["iniciado"] = False
        st.rerun()
