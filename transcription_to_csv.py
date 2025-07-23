import datetime
import re
import itertools
import os
import openai
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from datetime import datetime


database = "Transcription.txt"

def remove_filler(text):
    fillers = [
        "uh", "um", "okay", "ok", "so", "actually", "anyways", "just", "basically", "kinda",
        "sort of", "I mean", "you know", "let me", "oh", "like", "gonna", "got to", "gotta",
        "wanna", "thanks", "thank you", "thanks for", "thanks for that", "right", "well",
        "you see", "I guess", "I think", "I suppose", "if you will", "I mean to say",
        "in other words", "to be honest", "to tell the truth", "frankly", "honestly", "seriously",
        "i think", "i guess", "i mean", "you know what i mean", "you know what i mean?",
        "you know", "you know?", "you know what i mean", "kind of", "sort of",
        "like i said", "like i was saying", "like i said before", "like i said earlier",
        "like i mentioned", "like i mentioned before", "like i mentioned earlier", "i feel like",
        "i feel like i need to", "i feel like i should", "i feel like i could",
        "i feel like i would", "i feel like i might", "i feel like i can",
        "i feel like i will", "i feel like i am", "i feel like i have to", "um",
        "uhm", "uh-huh", "yeah", "yep", "yes", "no", "nah", "nope","thanks for watching",
        "thanks for watching","thanks for watching",
        "right?", "isn't it?", "don't you think?", "you know what I mean?", "hello",
        "hi", "hey", "how are you?", "how's it going?", "how's everything?", "how's life?",
        "whats up?", "what's going on?", "what's new?", "what's happening?",
        "what's good?", "what's up with you?", "what's up with that?", "what's up with this?",
        "what's up with everything?", "what's up with life?", "what's up with the world?", "watching"
    ]

    # Sort by length to match longer phrases first

    fillers = sorted(fillers, key=len, reverse=True)
    for filler in fillers:

        # Remove filler word/phrase with optional leading/trailing spaces and punctuation

        text = re.sub(rf'(\s|^|[.,!?;:]){re.escape(filler)}(\s|[.,!?;:]|$)', ' ', text, flags=re.IGNORECASE)

    # Clean extra spaces and punctuation

    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s([.,!?;:])', r'\1', text)
    return text.strip()

datetime_now = datetime.datetime.now().strftime("%Y-%m-%d_%H")
# we only need to do this once ever hour so it uses less resources.
#cleaning step:
cleaned_file_name = (f"cleaned_transcription" + datetime_now + ".txt")

last_break = 1

with open(database, "r") as f:
    lines = f.readlines()
    count = 0
    for line in lines:
        count += 1
        if "--------------------" in line:
            last_break = count


with open(database, "r") as f:
    for line in itertools.islice(f, last_break, None):
        
        sentence = line.strip()

        #removes timestamp 

        sentence = re.sub(r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]\s*', '', sentence)
        sentence = remove_filler(sentence)

        if sentence == "": #if its empty, skip it
            continue
        
        
        with open(cleaned_file_name, "a") as cleaned_file:
            cleaned_file.write(sentence + "\n")
with open(database, "a") as f:
    f.write("-" * 20 + "\n")

with open(cleaned_file_name, "r") as f:\
    transcript = f.read()

#load api key
_ = load_dotenv(find_dotenv())
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
 
temperature = 0.3
variables = "event_name,event_date_start,event_date_end,start_time,end_time,event_location,important_details,people_attending"
response = openai.chat.completions.create(
    model = "gpt-4o",
    messages=[
        {"role": "system", "content": "You are an event extraction assistant."},
        {"role": "user", "content": "Extract all events from this transcript: \n" + transcript + 
        "\n and return it as a csv file formatted like this: \n" + variables + "\n" +
        "give just the csv, no filler text, with the dates being formatted as numbers like this: year-month-day (assume current year month and day unless otherwise specified) and times being formatted as hour:min \n"}
    ]
)
csv_content = response.choices[0].message.content

#saves to csv file for later use.
timestamp = datetime.now().strftime("%Y-%m-%d_%H")
filename = f"extraction_{timestamp}.csv"


with open(filename, 'w', encoding='utf-8') as f:
    f.write(csv_content)

print(f"CSV saved as: {filename}")
os.remove(cleaned_file_name)

def clean_csv(filename):
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()
    # Remove first and last lines 
    lines = lines[1:-1]
    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(lines)

with open(filename, "r", encoding="utf-8") as f:
    first_line = f.readline().strip()
    print(f"First line: {first_line.strip()}")
    if first_line != variables:
        print("First line is not correct, cleaning CSV...")
        clean_csv(filename)

import pandas as pd
data = pd.read_csv(filename)
data.head()