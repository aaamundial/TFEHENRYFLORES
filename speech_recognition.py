import io
from google.cloud import speech
from audio_utils import get_sample_rate_hertz_and_channels, convert_to_mono
import os

# Configura la ruta al archivo de credenciales
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/Users/henry/proyecto1/eternal-trees-401903-1f41b5f4bd5b.json"


def interpretar_orden_de_voz(audio_file_path):
    client = speech.SpeechClient()

    sample_rate_hertz, channels = get_sample_rate_hertz_and_channels(audio_file_path)
    
    # Convert to mono if necessary
    if channels > 1:
        audio_file_path = convert_to_mono(audio_file_path)
        sample_rate_hertz, _ = get_sample_rate_hertz_and_channels(audio_file_path)
    
    with io.open(audio_file_path, 'rb') as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate_hertz,
        language_code='es-ES'
    )

    try:
        response = client.recognize(config=config, audio=audio)
        for result in response.results:
            return result.alternatives[0].transcript
    except Exception as e:
        print(f'Error: {e}')
        return None
