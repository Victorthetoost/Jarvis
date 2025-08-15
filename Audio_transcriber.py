import threading
import traceback
import queue
import sounddevice as sd
import numpy as np
from sympy import true
import whisper
import datetime
import time
import transcription_to_csv
import datetime
import re
import itertools
import os
import openai
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
import datetime

# Load Whisper model
model = whisper.load_model("medium")
stop = False
samplerate = 8000  # 8kHz sample rate
chunk_duration = 10  # seconds per chunk
audio_queue = queue.Queue()
stop_event = threading.Event()
output_file = "Transcript.txt"

def record_audio():
    print("Recording started...")
    while not stop_event.is_set():
        try:
            recording = sd.rec(int(chunk_duration * samplerate), samplerate=samplerate, channels=1, dtype='float32')
            sd.wait()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            audio_queue.put((recording.copy(), timestamp))
        except Exception as e:
            print("Error in record_audio:", e)
            traceback.print_exc()
    print("Recording stopped.")

def check_fact(transcript):
    if len(transcript) > 5:
    
        _ = load_dotenv(find_dotenv())
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))      
        temperature = 0.3
        fact_check = openai.chat.completions.create(
            model = "gpt-4o",
            messages=[
                {"role": "system","content": "you are a fact checking reporter who fact checks statements, and gives sources that either support or refure the statement"},
                {"role": "user","content": "if there is a \"fact check\" or anythign similar (ie, no way thats true, i dont believe that etc...) in this text: \n " + transcript +
                 "\n then please find the statement that needs fact checking and please return some text like: \" the statement \"( pate the statement here)\" is true/false because ______ and here are the sources\" \n"
                 " and then please list 2-5 sources from varied places (if its a political issue it will get both sides, provided both are factual) do not include links, just the names. also IGNORE EVYERHTIN INBETWEEN ----FACT CHECK---- AND ----FACT CHECK END----, IGNORE ALL OFTHAT"}
            ]
        )
        fact_check_response = fact_check.choices[0].message.content    
        with open("Transcript.txt","a") as f:
            f.write(f"----FACT CHECK---- \n----FACT CHECK---- \n" + fact_check_response + "\n----FACT CHECK END----\n----FACT CHECK END----\n")
        #saves to csv file for later use.      


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

                if "fact check" in transcription.lower() or "check that" in transcription.lower() or "is that true" in transcription.lower() or "are you sure" in transcription.lower():
                    print("Fact check trigger detected. Initiating fact check...")
                    check_fact(transcription)
   
        except queue.Empty:
            continue
        except Exception as e:
            print("Error in transcribe_audio:", e)
            traceback.print_exc()
    print("Transcription stopped.")

def chagpt_transcribe_audio():
    while not stop_event.is_set():
        time.sleep(60 )
        print("ChatGPT transcription started...")
        output_file = "Transcript.txt"
        transcription_to_csv.transcribe_to_csv(output_file)

def main():
    recorder_thread = threading.Thread(target=record_audio)
    transcriber_thread = threading.Thread(target=transcribe_audio)
    if transcriber_thread.is_alive() == False:
        Chatgpt_transcriber_thread = threading.Thread(target=chagpt_transcribe_audio)
        Chatgpt_transcriber_thread.start()
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




def run_transcription():
    while True:
        try:
            main()
        except Exception as e:
            traceback.print_exc()

if __name__ == "__main__":
    run_transcription() 