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
            if "--------------------" in line:
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

    if len(transcript) > 5:

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
                "the variables must be an exact match and they have to be set as labels for the csv. do not write anything like: csv:... just the variables for the column names and the appointments"+
                "give just the csv, no filler text, with the dates being formatted as numbers like this:\n"+
                "year-month-day (assume current year month and day unless otherwise specified) and times being formatted as hour:min. also IGNORE EVYERHTIN INBETWEEN ----FACT CHECK---- AND ----FACT CHECK END----, IGNORE ALL OFTHAT.\n"+
                "If there are no events, just return the header line with no data rows. make sure its 100 percent an event and not a fact check or anything else"+
                "it could be homework assignments, meetings, birthdays, anniversaries, reminders, anything that needs to be scheduled. an event has to have a reason to exist and time/date, place to meet, or both"}
            ]
        )
        csv_content = response.choices[0].message.content
        #fact_check = openai.chat.completions.create(
        #    model = "gpt-4o",
        #    messages=[
        #        {"role": "system","content": "you are a fact checking reporter who fact checks statements, and gives sources that either support or refure the statement"},
        #        {"role": "user","content": "if there is a \"fact check\" or anythign similar (ie, no way thats true, i dont believe that etc...) in this text: \n " + transcript +
        #         "\n then please find the statement that needs fact checking and please return some text like: \" the statement \"( pate the statement here)\" is true/false because ______ and here are the sources\" \n"
        #         " and then please list 2-5 sources from varied places (if its a political issue it will get both sides, provided both are factual) do not include links, just the names. also IGNORE EVYERHTIN INBETWEEN ----FACT CHECK---- AND ----FACT CHECK END----, IGNORE ALL OFTHAT"}
        #    ]
        #)
        #fact_check_response = fact_check.choices[0].message.content
#
        #with open("Transcript.txt","a") as f:
        #    f.write(f"----FACT CHECK---- \n----FACT CHECK---- \n" + fact_check_response + "\n----FACT CHECK END----\n----FACT CHECK END----\n")
        ##saves to csv file for later use.

        filename = temp_csv

        with open(temp_csv, 'a', encoding='utf-8') as f:
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
            if not (variables in first_line):
                print("First line is not correct, cleaning CSV...")
                clean_csv(filename)

        import pandas as pd
        data = pd.read_csv(filename)
        data.head()
    else:
        print("No transcription available to process.")
        os.remove(cleaned_file_name)