import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.uix.gridlayout import GridLayout
import csv
import os
from datetime import datetime, timedelta
import subprocess
from kivy.clock import Clock
from kivy.uix.textinput import TextInput
import os
from dateutil.relativedelta import relativedelta
from datetime import date
import calendar

APPROVAL_CSV = "pending_events.csv"
CALENDAR_CSV = "events.csv"
process = None

def load_csv(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        return list(csv.DictReader(csvfile))


def save_csv(file_path, data):
    if not data:
        open(file_path, 'w').close()
        return
    
    # Remove None keys and unify headers across all rows
    all_keys = set()
    for row in data:
        all_keys.update(k for k in row.keys() if k is not None)
    
    fieldnames = list(all_keys)

    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            clean_row = {k: row.get(k, "") for k in fieldnames}
            writer.writerow(clean_row)

def start_external_script(instance):
    global process
    if process is None or process.poll() is not None:
        process = subprocess.Popen(['python', 'Audio_transcriber.py'])
        print("Subprocess launched successfully!")

def stop_external_script(instance):
    global process
    if process and process.poll() is None:
        process.terminate()
        process = None
        print("Subprocess terminated.")

class TranscriberScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation='vertical')

        # Transcript display
        self.transcript_display = TextInput(
            text="",
            readonly=True,
            size_hint_y=0.9,
            background_color=(0, 0, 0, 1),  # black background
            foreground_color=(1, 1, 1, 1),  # white text
            font_size=25
        )
        layout.add_widget(self.transcript_display)

        # Buttons row
        button_layout = BoxLayout(size_hint_y=0.1)
        back_btn = Button(text = "Back")
        back_btn.bind(on_press=lambda *_: setattr(self.manager, 'current', 'main'))
        button_layout.add_widget(back_btn)

        btn_stop = Button(text = "Stop Transcribing")
        btn_stop.bind(on_press = stop_external_script)
        button_layout.add_widget(btn_stop)

        btn_start = Button(text = "Start Transcribing")
        btn_start.bind(on_press = start_external_script)
        button_layout.add_widget(btn_start)


        layout.add_widget(button_layout)

        self.add_widget(layout)

        # Path to transcript file
        self.transcript_file = "Transcript.txt"

        # Update every 0.5 sec
        Clock.schedule_interval(self.update_transcript, 0.5)

    def update_transcript(self, dt):
        if os.path.exists(self.transcript_file):
            with open(self.transcript_file, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
                if text != self.transcript_display.text:
                    self.transcript_display.text = text
                    self.transcript_display.cursor = (0, len(self.transcript_display.text))

    


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')
        self.scroll = ScrollView()
        self.task_grid = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=10)
        self.task_grid.bind(minimum_height=self.task_grid.setter('height'))
        self.scroll.add_widget(self.task_grid)
        self.layout.add_widget(self.scroll)

        nav = BoxLayout(size_hint_y=None, height=50)
        btn_calendar = Button(text="Calendar")
        btn_calendar.bind(on_press=lambda _: setattr(self.manager, 'current', 'calendar'))
        nav.add_widget(btn_calendar)
        self.layout.add_widget(nav)

        btn_open_transcribe = Button(text = "Transcriber")
        btn_open_transcribe.bind(on_press = lambda _: setattr(self.manager, 'current', 'transcriber'))
        nav.add_widget(btn_open_transcribe)

        btn_manual_entry = Button(text="Manual Entry")
        btn_manual_entry.bind(on_press=lambda _: setattr(self.manager, 'current', 'manual_entry'))
        nav_2 = BoxLayout(size_hint_y=None, height=50)
        nav_2.add_widget(btn_manual_entry)
        nav.add_widget(nav_2)

        

        self.add_widget(self.layout)

        Clock.schedule_interval(self.refresh, 0.5)

    def refresh(self, dt = 0):
        self.task_grid.clear_widgets()
        tasks = load_csv(APPROVAL_CSV)
        for task in tasks:
            box = BoxLayout(size_hint_y=None, height=100)
            summary = f"{task['event_name']} on {task['event_date_start']} @ {task['start_time']}"
            label = Label(text=summary, halign='left', valign='middle')
            label.text_size = (Window.width - 150, None)
            approve_btn = Button(text="yes", size_hint_x=None, width=100, background_color=(0, 1, 0, 1))
            deny_btn = Button(text="naw", size_hint_x=None, width=100, background_color=(1, 0, 0, 1))
            approve_btn.bind(on_press=lambda _, t=task: self.approve(t))
            deny_btn.bind(on_press=lambda _, t=task: self.deny(t))
            box.add_widget(label)
            box.add_widget(approve_btn)
            box.add_widget(deny_btn)
            self.task_grid.add_widget(box)


    def approve(self, task):
        print("\n--- DEBUG: Approving Task ---")
        print("Task keys:", list(task.keys()))
        print("Task data:", task)

        events = load_csv(CALENDAR_CSV)
        print("Current CSV keys:", list(events[0].keys()) if events else "No existing events")

        events.append(task)
        save_csv(CALENDAR_CSV, events)
        print("--- DEBUG: Save complete ---\n")

        self.deny(task)  # Remove from pending list

    def deny(self, task):
        tasks = load_csv(APPROVAL_CSV)
        tasks = [t for t in tasks if t != task]
        save_csv(APPROVAL_CSV, tasks)
        self.refresh()


#MAKE THIS SCROLLABLE AND SHOW THE NEXT 2 WEEKS ASWELL AS A LIST OF ALL THE TASKS THAT ARE NOT
# FITTING ON THE 2 WEEKS.

class CalendarScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        grid = GridLayout(cols=7, spacing=10, size_hint_y=0.8)
        today = datetime.today()
        for i in range(21):
            day = today + timedelta(days=i)
            date_str = day.strftime("%Y-%m-%d")
            btn = Button(text=day.strftime("%A\n%d %B"), size_hint_y=None, height=100)
            btn.bind(on_press=lambda btn, date=date_str: self.open_day(date))
            grid.add_widget(btn)
        grid_month = GridLayout(cols=4, spacing=10,size_hint_y=0.8)
        today = date.today()
        for i in range(12):
            month = today + relativedelta(months=i)
            year = month.year
            month_num = month.month

            btn = Button(
                text=month.strftime("%B %Y"),  # e.g., "August 2025"
                size_hint_y=None,
                height=100
            )
            # Pass year & month but also go to month_event_expansion
            btn.bind(on_press=lambda _, y=year, m=month_num: self.open_month(y, m))
            grid_month.add_widget(btn)
        layout.add_widget(grid)
        layout.add_widget(grid_month)
        back_btn = Button(text="Back", size_hint_y=None, height=50)
        back_btn.bind(on_press=lambda *_: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

    def open_month(self, year, month):
        # Pass data to the month_event_expansion screen
        month_screen = self.manager.get_screen('month_event_expansion')
        month_screen.show_month(year, month)

        # Switch to that screen
        self.manager.current = 'month_event_expansion'

    def open_day(self, date):
        self.manager.get_screen('day_detail').show_day(date)
        self.manager.current = 'day_detail'


class MonthEventExpansion(Screen):
    def show_month(self, year, month):
        self.clear_widgets()
        layout = GridLayout(cols=7, spacing=5, padding=10)

        # Weekday headers (Sunday first)
        for day in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
            layout.add_widget(Label(text=day, bold=True))

        # Get month calendar data
        month_days = calendar.Calendar(firstweekday=6).monthdayscalendar(year, month)

        for week in month_days:
            for d in week:
                if d == 0:
                    layout.add_widget(Label(text=""))
                else:
                    btn = Button(text=str(d))

                    # Binding click to open day view
                    btn.bind(
                        on_press=lambda _, day=d: (
                            setattr(self.manager, 'current', 'day_detail'),
                            self.manager.get_screen('day_detail').show_day(
                                date(year, month, day).strftime("%Y-%m-%d")
                            )
                        )
                    )
                    layout.add_widget(btn)

        
        back_btn = Button(text = "Back")
        back_btn.bind(on_press = lambda _:setattr(self.manager, 'current', 'calendar'))
        back_button_layout = GridLayout(cols=1, spacing=5, padding=10)
        back_button_layout.add_widget(back_btn)
        layout.add_widget(back_button_layout)
        self.add_widget(layout)

class ManualEntryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        self.input = TextInput(hint_text="Enter event name", size_hint_y=None, height=200)
        self.layout.add_widget(self.input)
        self.input_date_start = TextInput(hint_text="Enter event start date (YYYY-MM-DD)", size_hint_y=None, height=50)
        self.layout.add_widget(self.input_date_start)
        self.input_date_end = TextInput(hint_text="Enter event end date (YYYY-MM-DD)", size_hint_y=None, height=50)
        self.layout.add_widget(self.input_date_end)
        self.input_time_start = TextInput(hint_text="Enter event start time (HH:MM)", size_hint_y=None, height=50)
        self.layout.add_widget(self.input_time_start)
        self.input_time_end = TextInput(hint_text="Enter event end time (HH:MM)", size_hint_y=None, height=50)
        self.layout.add_widget(self.input_time_end)
        self.input_location = TextInput(hint_text="Enter event location", size_hint_y=None, height=50)
        self.layout.add_widget(self.input_location)
        self.input_details = TextInput(hint_text="Enter important details", size_hint_y=None, height=100)
        self.layout.add_widget(self.input_details)
        self.input_people = TextInput(hint_text="Enter people attending (comma separated)", size_hint_y=None, height=50)
        self.layout.add_widget(self.input_people)


        submit_btn = Button(text="Submit", size_hint_y=None, height=40)
        submit_btn.bind(on_press=self.submit_event)
        self.layout.add_widget(submit_btn)

        back_btn = Button(text="Back", size_hint_y=None, height=40)
        back_btn.bind(on_press=lambda _: setattr(self.manager, 'current', 'main'))
        self.layout.add_widget(back_btn)

        self.add_widget(self.layout)

    def submit_event(self, instance):
        event_details = self.input.text.strip()
        if event_details:
            event_date_start = self.input_date_start.text.strip()
            event_date_end = self.input_date_end.text.strip()
            start_time = self.input_time_start.text.strip()
            end_time = self.input_time_end.text.strip()
            event_location = self.input_location.text.strip()
            important_details = self.input_details.text.strip()
            people_attending = self.input_people.text.strip()

            if not all([event_details, event_date_start]):
                print("Please fill in THE IMPORANTT fields.")
                return

            new_event = {
                "event_name": event_details,
                "event_date_start": event_date_start,
                "event_date_end": event_date_end,
                "start_time": start_time,
                "end_time": end_time,
                "event_location": event_location,
                "important_details": important_details,
                "people_attending": people_attending,
            }

            # Save to CSV
            events = load_csv(APPROVAL_CSV)
            events.append(new_event)
            save_csv(APPROVAL_CSV, events)

            # Clear inputs
            self.input.text = ""
            self.input_date_start.text = ""
            self.input_date_end.text = ""
            self.input_time_start.text = ""
            self.input_time_end.text = ""
            self.input_location.text = ""
            self.input_details.text = ""
            self.input_people.text = ""
            

class DayEventExpansion(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.label = Label(text="Event Details", halign='left', valign='top')
        self.label.text_size = (Window.width * 0.9, None)
        self.layout.add_widget(self.label)

        back_btn = Button(text="Back", size_hint_y=None, height=40)
        back_btn.bind(on_press=self.go_back)
        self.layout.add_widget(back_btn)

        self.add_widget(self.layout)

    def display_event(self, event):
        details = (
            f"Event: {event['event_name']}\n\n"
            f"Date: {event['event_date_start']}\n"
            f"Time: {event['start_time']} - {event['end_time']}\n"
            f"Location: {event['event_location']}\n"
            f"People Attending: {event['people_attending']}\n"
            f"Details: {event['important_details']}"
        )
        self.label.text = details

    def go_back(self, instance):
        self.manager.current = 'day_detail'


class DayDetailScreen(Screen):
    #i need to make a part that adds the blocks so that its easier to see when something is filled up
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation='vertical', spacing=10, padding=20)
        
        self.title = Label(text="Events on [date]", size_hint_y=None, height=40)
        layout.add_widget(self.title)

        scroll_view = ScrollView()
        self.events_grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.events_grid.bind(minimum_height=self.events_grid.setter('height'))
        scroll_view.add_widget(self.events_grid)

        layout.add_widget(scroll_view)

        return_button = Button(text="Back", size_hint_y=None, height=40)
        return_button.bind(on_press=self.go_back)
        layout.add_widget(return_button)

        self.add_widget(layout)

    def go_back(self, instance):
        self.manager.current = 'calendar'

    def show_day(self, day_str):
        self.title.text = f"Events on {day_str}"
        self.events_grid.clear_widgets()
        try:
            parsed_date = datetime.strptime(day_str, "%Y-%m-%d")
            date_key = parsed_date.replace(year=datetime.today().year).strftime("%Y-%m-%d")
        except:
            self.events_grid.add_widget(Label(text="Date parse error"))
            return
    
        events = load_csv(CALENDAR_CSV)
        todays_events = [e for e in events if e['event_date_start'] == date_key]
    
        for event in todays_events:
            event_duration = datetime.strptime(event['end_time'], "%H:%M") - datetime.strptime(event['start_time'], "%H:%M")
            if event_duration <= timedelta(0):
                event_duration = timedelta(hours=1)
            height = max(60, event_duration.hours * 60)  # Minimum height of 60
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=5)
    
            # Delete button
            delete_btn = Button(text='Delete', size_hint_x=0.1, background_color=(1, 0, 0, 1))
            delete_btn.bind(on_press=lambda btn, ev=event: self.delete_event(ev, day_str))
            row.add_widget(delete_btn)
    
            # Event name as a button (goes to DayEventExpansion screen)
            btn_event = Button(text=event['event_name'], size_hint_x=0.3)
            btn_event.bind(on_press=lambda _, ev=event: self.open_event_detail(ev))
            row.add_widget(btn_event)

            # Time and location
            row.add_widget(Label(text=f"{event['start_time']} - {event['end_time']}", size_hint_x=0.2))
            row.add_widget(Label(text=event['event_location'], size_hint_x=0.2))

            self.events_grid.add_widget(row)

    def delete_event(self, event, date):
        events = load_csv(CALENDAR_CSV)
        events = [e for e in events if e != event]
        save_csv(CALENDAR_CSV, events)
        self.show_day(date)

    def open_event_detail(self, event):
        event_screen = self.manager.get_screen('event_detail')
        event_screen.display_event(event)
        self.manager.current = 'event_detail'


class TaskApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(CalendarScreen(name='calendar'))
        sm.add_widget(DayDetailScreen(name='day_detail'))
        sm.add_widget(DayEventExpansion(name = 'event_detail'))
        sm.add_widget(TranscriberScreen(name = 'transcriber'))
        sm.add_widget(MonthEventExpansion(name = 'month_event_expansion'))
        sm.add_widget(ManualEntryScreen(name='manual_entry'))
        return sm


if __name__ == '__main__':
    TaskApp().run()
