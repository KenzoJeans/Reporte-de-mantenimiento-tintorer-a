import json
import tempfile
import io
import streamlit as st
from audio_recorder_streamlit import audio_recorder
import google.generativeai as genai
from gtts import gTTS

# Configuración de la página
st.set_page_config(page_title="Mantenimiento Kenzo Jeans", layout="centered", page_icon="🔧")

# Configuración de API Key
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ No se encontró la GEMINI_API_KEY en los secretos.")

# Función auxiliar para generar y reproducir audio
def hablar(texto, autoplay=True):
    tts = gTTS(text=texto, lang='es')
    audio_memoria = io.BytesIO()
    tts.write_to_fp(audio_memoria)
    audio_memoria.seek(0)
    st.audio(audio_memoria, format="audio/mp3", autoplay=autoplay)

# Control del estado de la aplicación
if "iniciado" not in st.session_state:
    st.session_state["iniciado"] = False

# -----------------------------------------------------------------------------
# PANTALLA 1: Bienvenida e Inicio de Sesión de Voz
# -----------------------------------------------------------------------------
if not st.session_state["iniciado"]:
    st.title("🏭 Mantenimiento Kenzo Jeans")
    st.write("Bienvenido al sistema de reportes por voz.")
    
    # Botón grande para iniciar interacción y desbloquear audio
    if st.button("🎙️ Iniciar Asistente de Voz", type="primary", use_container_width=True):
        st.session_state["iniciado"] = True
        st.rerun()

# -----------------------------------------------------------------------------
# PANTALLA 2: Interfaz Interactiva de Grabación
# -----------------------------------------------------------------------------
else:
    st.title("🔧 Mantenimiento Kenzo Jeans")
    
    # Saludo de voz automático (Funciona porque el usuario ya presionó el botón de inicio)
    saludo = "Bienvenido a la aplicación para el reporte de mantenimiento Kenzo Jeans. ¿Qué reporte realizarás el día de hoy?"
    hablar(saludo, autoplay=True)
    
    st.info("💡 **Asistente:** "¿Qué reporte realizarás el día de hoy?"")
    st.write("Presiona el micrófono a continuación para dictar tu respuesta:")

    # Grabador de audio
    audio_bytes = audio_recorder(
        text="",
        recording_color="#e74c3c",
        neutral_color="#3498db",
        icon_name="microphone",
        icon_size="3x"
    )

    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        
        if st.button("🚀 Procesar y Enviar Reporte", type="primary", use_container_width=True):
            with st.spinner("Analizando reporte con IA..."):
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

                    st.success("✅ ¡Reporte registrado!")
                    
                    # Presentación visual
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Máquina", datos_reporte.get("equipo_o_maquina"))
                        st.metric("Estado Final", datos_reporte.get("estado_final"))
                    with col2:
                        st.write("**Motivo:**", datos_reporte.get("falla_o_motivo"))
                        st.write("**Repuestos:**", datos_reporte.get("repuestos_utilizados"))

                    st.markdown(f"**Trabajo:** {datos_reporte.get('trabajo_realizado')}")
                    st.markdown(f"**Observaciones:** {datos_reporte.get('observaciones_adicionales')}")

                    # Respuesta por voz del cierre
                    maquina = datos_reporte.get("equipo_o_maquina", "el equipo")
                    estado = datos_reporte.get("estado_final", "registrado")
                    cierre_vocally = f"Entendido. Se ha guardado el reporte para {maquina} con estado {estado}."
                    
                    hablar(cierre_vocally, autoplay=True)

                except Exception as e:
                    st.error(f"Error procesando audio: {e}")

    # Opción para reiniciar el flujo
    st.write("---")
    if st.button("🔄 Crear otro reporte"):
        st.session_state["iniciado"] = False
        st.rerun()
