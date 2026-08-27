import streamlit as st
from audio_recorder_streamlit import audio_recorder
import datetime
from gtts import gTTS
import io

def hablar(texto):
    # Genera el audio en español
    tts = gTTS(text=texto, lang='es')
    audio_memoria = io.BytesIO()
    tts.write_to_fp(audio_memoria)
    audio_memoria.seek(0)
    # Reproduce el audio automáticamente
    st.audio(audio_memoria, format="audio/mp3", autoplay=True)

# Configuración de página adaptada para móviles
st.set_page_config(page_title="Reporte de Mantenimiento", layout="centered")

st.title("🔧 Dictar Reporte")
st.write("Toca el micrófono para empezar a hablar. Tócalo de nuevo para detener.")

# Generar el botón de grabación (puedes personalizar los colores)
audio_bytes = audio_recorder(
    text="", 
    recording_color="#ff4b4b", # Rojo cuando está grabando
    neutral_color="#808080",   # Gris cuando está inactivo
    icon_name="microphone",
    icon_size="3x"             # Tamaño grande para facilitar tocarlo en el celular
)

# Si el usuario grabó algo y se generaron los bytes del audio
if audio_bytes:
    # 1. Le mostramos el audio para que escuche si quedó bien
    st.audio(audio_bytes, format="audio/wav")
    
    # 2. Guardamos el archivo localmente con la fecha y hora actual
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"reporte_mantenimiento_{timestamp}.wav"
    
    with open(nombre_archivo, "wb") as f:
        f.write(audio_bytes)
        
    st.success("✅ Audio capturado correctamente.")
    
    # 3. Botón de acción para el siguiente paso
    if st.button("Procesar y Enviar", type="primary"):
        st.info("Aquí enviaremos el audio a la IA para transcribirlo...")
        # Más adelante, aquí irá el código para extraer el texto y 
        # enviarlo por webhook a tu Google Sheets.
