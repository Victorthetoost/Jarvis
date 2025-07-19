import threading
import queue
import sounddevice as sd
import numpy as np
import whisper
from datetime import datetime
import time

# Load Whisper model
model = whisper.load_model("medium")

samplerate = 16000  # 16kHz sample rate
chunk_duration = 10  # seconds per chunk
audio_queue = queue.Queue()
stop_event = threading.Event()
output_file = "Transcription.txt"

def record_audio():
    """Continuously record audio and push raw audio data with timestamps to the queue."""
    print("Recording started...")
    while not stop_event.is_set():
        recording = sd.rec(int(chunk_duration * samplerate), samplerate=samplerate, channels=1, dtype='float32')
        sd.wait()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        audio_queue.put((recording.copy(), timestamp))
    print("Recording stopped.")

def transcribe_audio():
    """Continuously transcribe audio from the queue and save transcriptions with timestamps."""
    print("Transcription started...")
    while not stop_event.is_set() or not audio_queue.empty():
        try:
            audio_data, timestamp = audio_queue.get(timeout=1)

            # Whisper expects a 1D numpy array
            audio_data = np.squeeze(audio_data)
            result = model.transcribe(audio_data, fp16=False)

            transcription = result['text'].strip()
            if transcription:
                log_entry = f"[{timestamp}] {transcription}\n"
                print(log_entry.strip())
                with open(output_file, 'a') as f:
                    f.write(log_entry)
        except queue.Empty:
            continue
    print("Transcription stopped.")

def main():
    recorder_thread = threading.Thread(target=record_audio)
    transcriber_thread = threading.Thread(target=transcribe_audio)

    recorder_thread.start()
    transcriber_thread.start()

    print("Recording and transcription are running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Stopping...")
        stop_event.set()
        recorder_thread.join()
        transcriber_thread.join()
        print("All processes stopped.")

if __name__ == "__main__":
    main()
