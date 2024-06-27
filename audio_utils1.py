import pyaudio
import wave
from pydub import AudioSegment

def get_sample_rate_hertz_and_channels(wav_file_path):
    with wave.open(wav_file_path, 'rb') as wav_file:
        return wav_file.getframerate(), wav_file.getnchannels()

def convert_to_mono(audio_file_path):
    audio = AudioSegment.from_wav(audio_file_path)
    if audio.channels > 1:
        audio = audio.set_channels(1)
        mono_audio_file_path = 'mono_' + audio_file_path
        audio.export(mono_audio_file_path, format='wav')
        return mono_audio_file_path
    return audio_file_path

def record_audio_to_file(file_path, record_seconds=5, sample_rate=44100):
    chunk = 1024  # Record in chunks of 1024 samples
    format = pyaudio.paInt16  # 16-bit resolution
    channels = 2  # 2 channels for stereo
    rate = sample_rate  # 44100 samples per second

    p = pyaudio.PyAudio()

    stream = p.open(format=format,
                    channels=channels,
                    rate=rate,
                    input=True,
                    frames_per_buffer=chunk)

    frames = []

    print("Recording...")
    for _ in range(0, int(rate / chunk * record_seconds)):
        data = stream.read(chunk)
        frames.append(data)
    print("Finished recording.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(file_path, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()
