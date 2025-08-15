# this one is responsible for fact checking whenever it sees it.
import datetime
import re
import itertools
import os
import openai
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
import datetime

temp_csv = "pending_events.csv"

def transcribe_to_csv(database):
    datetime_now = datetime.datetime.now().strftime("%Y-%m-%d_%H")
    # we only need to do this once ever hour so it uses less resources.
    #cleaning step:
    cleaned_file_name = (f"cleaned_transcription" + datetime_now + ".txt")
    with open(cleaned_file_name,"a") as f:
        f.write("\n")

    def remove_filler(text):
        fillers = [
            "uh", "um", "okay", "ok", "so", "actually", "anyways", "just", "basically", "kinda",
            "sort of", "I mean", "you know", "let me", "oh", "like", "gonna", "got to", "gotta",
            "wanna", "thanks", "thank you", "thanks for", "thanks for that", "right", "well",
            "you see", "I guess", "I think", "I suppose", "if you will", "I mean to say", "frankly", "honestly", "seriously",
            "i think", "i guess", "i mean", "you know what i mean", "you know what i mean?",
            "you know", "you know?", "you know what i mean", "kind of", "sort of",
            "like i said", "like i was saying", "like i said before", "like i said earlier",
            "like i mentioned", "like i mentioned before", "like i mentioned earlier",
            "i feel like i need to", "i feel like i should", "i feel like i could",
            "i feel like i would", "i feel like i might", "i feel like i can",
            "i feel like i will", "i feel like i am", "i feel like i have to", "um",
            "uhm", "uh-huh", "yeah", "yep", "yes", "no", "nah", "nope","thanks for watching",
            "thanks for watching","thanks for watching", "isn't it?", "don't you think?", "you know what I mean?", "hello",
            "hi", "how are you?", "how's it going?", "how's everything?", "how's life?",
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



    last_break = 1

    with open(database, "r") as f:
        lines = f.readlines()
        count = 0
        for line in lines:
            count += 1
            if "fact" in line:
                last_break = count


    with open(database, "r") as f:
        for line in itertools.islice(f, last_break, None):

            sentence = line.strip()

            #removes timestamp 
            sentence = remove_filler(sentence)

            if sentence == "": #if its empty, skip it
                continue
            
            try: 
                with open(cleaned_file_name, "a") as cleaned_file:
                    cleaned_file.write(sentence + "\n")
            except Exception as e:
                print("the cleaned file does not exist.")
    with open(database, "a") as f:
        f.write("-" * 20 + "\n")

    with open(cleaned_file_name, "r") as f:\
        transcript = f.read()

    