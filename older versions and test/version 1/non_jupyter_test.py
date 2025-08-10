import threading
import os
import numpy as np
import whisper
import sounddevice as sd
from scipy.io.wavfile import write
from pydub import AudioSegment
import time
from datetime import datetime


model = whisper.load_model("medium")
file_lock = threading.Lock()

duration = 30  # seconds
samplerate = 16000
stop_recording = False

recording_buffer = {
    "Thread-1": None,
    "Thread-2": None
}

def is_significant_audio(audio_data, threshold=150):
    return np.abs(audio_data).mean() > threshold

def record_audio(thread_name):
    print(f"{thread_name}: Recording for {duration}s...")
    recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    return recording

def save_and_transcribe(thread_name, audio_data):
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    wav_filename = f"{thread_name}_{current_datetime}.wav"
    #mp3_filename = f"{thread_name}_{current_datetime}.mp3"

    write(wav_filename, samplerate, audio_data)
    audio = AudioSegment.from_wav(wav_filename)
    #audio.export(mp3_filename, format="mp3")
    #os.remove(wav_filename)

    print(f"{thread_name}: Transcribing...")
    if is_significant_audio(audio_data):
        result = model.transcribe(wav_filename, temperature=0.0)
        clean_text = result["text"].replace('\n', ' ').replace('\r', ' ').strip()
    else:
        print(f"{thread_name}:no voice detected, skipping transcription.")
        clean_text = "..."

    with file_lock:
        with open("transcription-py.txt", "a") as f:
            f.write(f"[{datetime.now()}][{thread_name}] {clean_text}\n")

    os.remove(wav_filename)
    print(f"{thread_name}: Transcription complete and file cleaned up.")

def worker(my_name, partner_name):
    global stop_recording
    while not stop_recording:
        # Record audio
        audio_data = record_audio(my_name)
        # Store for the partner to process later (if needed)
        recording_buffer[my_name] = audio_data

        # Allow partner to record while this thread processes previous data
        if recording_buffer[partner_name] is not None:
            save_and_transcribe(partner_name, recording_buffer[partner_name])
            recording_buffer[partner_name] = None
        else:
            # If partner hasn't recorded yet, process own data
            save_and_transcribe(my_name, audio_data)
            recording_buffer[my_name] = None

def start_alternating_threads():
    thread1 = threading.Thread(target=worker, args=("Thread-1", "Thread-2"))
    thread2 = threading.Thread(target=worker, args=("Thread-2", "Thread-1"))

    thread1.start()
    # Stagger the second thread to alternate
    time.sleep(duration)
    thread2.start()

    return thread1, thread2

try:
    thread1, thread2 = start_alternating_threads()
    runtime = 5 * 60  # Run for 5 minutes, adjust as needed
    time.sleep(runtime)
    stop_recording = True
    thread1.join()
    thread2.join()
    print("Recording and transcription stopped.")
except KeyboardInterrupt:
    stop_recording = True
    print("Stopped by user.")
