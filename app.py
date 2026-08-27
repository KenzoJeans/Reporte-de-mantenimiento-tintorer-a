import json
import tempfile
import io
import streamlit as st
from audio_recorder_streamlit import audio_recorder
import google.generativeai as genai
from gtts import gTTS

# 1. Configuración de API Key y Modelo
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ No se encontró la GEMINI_API_KEY en los secretos.")

st.set_page_config(page_title="Reporte de Mantenimiento", layout="centered", page_icon="🔧")

# Función para reproducir el mensaje de voz
def hablar(texto):
    tts = gTTS(text=texto, lang='es')
    audio_memoria = io.BytesIO()
    tts.write_to_fp(audio_memoria)
    audio_memoria.seek(0)
    st.audio(audio_memoria, format="audio/mp3", autoplay=True)

st.title("🔧 Reporte de Mantenimiento por Voz")
st.write("Presiona el micrófono, dicta las actividades de mantenimiento realizadas y vuelve a presionarlo para terminar.")

# 2. Grabador de Audio
audio_bytes = audio_recorder(
    text="",
    recording_color="#e74c3c",
    neutral_color="#3498db",
    icon_name="microphone",
    icon_size="3x"
)

if audio_bytes:
    st.audio(audio_bytes, format="audio/wav")
    
    if st.button("🚀 Procesar Reporte con IA", type="primary"):
        with st.spinner("Escuchando audio y analizando reporte..."):
            try:
                # Guardar el audio temporalmente para enviarlo a la API
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                    temp_audio.write(audio_bytes)
                    temp_audio_path = temp_audio.name

                # Subir el archivo de audio a la API de Gemini
                audio_file = genai.upload_file(path=temp_audio_path)

                # Prompt estructurado
                prompt = """
                Eres un asistente experto en mantenimiento industrial textil y de confección.
                Escucha atentamente el audio adjunto e identifica la siguiente información.
                Responde ÚNICAMENTE en formato JSON válido con las siguientes llaves:
                {
                  "equipo_o_maquina": "Nombre o número de la máquina (ej: Lavadora 2, Fileteadora 4, Caldera)",
                  "falla_o_motivo": "Descripción del problema reportado o la causa de intervención",
                  "trabajo_realizado": "Resumen claro del mantenimiento preventivo o correctivo ejecutado",
                  "repuestos_utilizados": "Lista de piezas, repuestos o insumos sustituidos (o 'Ninguno')",
                  "estado_final": "Operativa / En prueba / Fuera de servicio",
                  "observaciones_adicionales": "Notas suplementarias, recomendaciones o pendientes de compra"
                }
                Si algún campo no es mencionado en el audio, asigna el valor "No especificado".
                """

                # Generar respuesta con Gemini 1.5 Flash
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content([audio_file, prompt])

                # Limpiar texto para extraer solo el JSON
                texto_respuesta = response.text.replace("```json", "").replace("```", "").strip()
                datos_reporte = json.loads(texto_respuesta)

                # 3. Presentar los resultados en pantalla
                st.success("✅ ¡Reporte procesado exitosamente!")
                st.subheader("📋 Datos Extraídos")

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Máquina / Equipo", datos_reporte.get("equipo_o_maquina"))
                    st.metric("Estado Final", datos_reporte.get("estado_final"))
                with col2:
                    st.write("**Motivo / Falla:**", datos_reporte.get("falla_o_motivo"))
                    st.write("**Repuestos Usados:**", datos_reporte.get("repuestos_utilizados"))

                st.markdown("---")
                st.markdown(f"**Trabajo Realizado:**\n{datos_reporte.get('trabajo_realizado')}")
                st.markdown(f"**Observaciones:**\n{datos_reporte.get('observaciones_adicionales')}")

                # Guardar datos en la sesión
                st.session_state["ultimo_reporte"] = datos_reporte

                # 4. Confirmación por voz (dentro del flujo donde datos_reporte ya existe)
                maquina = datos_reporte.get("equipo_o_maquina", "el equipo")
                estado = datos_reporte.get("estado_final", "no especificado")
                mensaje_confirmacion = f"Reporte procesado correctamente para {maquina}. Quedó en estado {estado}."
                hablar(mensaje_confirmacion)

            except Exception as e:
                st.error(f"Ocurrió un error al procesar el audio: {e}")
