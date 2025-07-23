import threading
import traceback
import queue
import sounddevice as sd
import numpy as np
import whisper
from datetime import datetime
import time
import transcription_to_csv

# Load Whisper model
model = whisper.load_model("medium")

samplerate = 8000  # 8kHz sample rate
chunk_duration = 10  # seconds per chunk
audio_queue = queue.Queue()
stop_event = threading.Event()
output_file = "Transcription.txt"

def record_audio():
    print("Recording started...")
    while not stop_event.is_set():
        try:
            recording = sd.rec(int(chunk_duration * samplerate), samplerate=samplerate, channels=1, dtype='float32')
            sd.wait()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            audio_queue.put((recording.copy(), timestamp))
        except Exception as e:
            print("Error in record_audio:", e)
            traceback.print_exc()
    print("Recording stopped.")

def chagpt_transcribe_audio():
    while true:
        time.sleep(60*60)
        print("ChatGPT transcription started...")
        transcription_to_csv.transcribe_to_csv(output_file)


def transcribe_audio():
    print("Transcription started...")
    while not stop_event.is_set() or not audio_queue.empty():
        try:
            audio_data, timestamp = audio_queue.get(timeout=1)
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
        except Exception as e:
            print("Error in transcribe_audio:", e)
            traceback.print_exc()
    print("Transcription stopped.")

def main():
    recorder_thread = threading.Thread(target=record_audio)
    transcriber_thread = threading.Thread(target=transcribe_audio)
    Chatgpt_transcriber_thread = threading.Thread(target=chagpt_transcribe_audio)
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
    while True:
        try:
            main()
        except Exception as e:
            traceback.print_exc()

