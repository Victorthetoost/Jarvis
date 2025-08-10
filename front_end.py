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
            with open(self.transcript_file, "r", encoding="utf-8") as f:
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

        btn_start_rec = Button(text = "Transcriber")
        btn_start_rec.bind(on_press = lambda _: setattr(self.manager, 'current', 'transcriber'))
        nav.add_widget(btn_start_rec)

        

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

    #def approve(self, task):
    #    events = load_csv(CALENDAR_CSV)
    #    events.append(task)
    #    save_csv(CALENDAR_CSV, events)
    #    self.deny(task)  # Remove from pending list
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
        for i in range(12):  # 0 through 11 = 12 months
            month = today + relativedelta(months=i)
            date_str = month.strftime("%Y-%m")
            btn = Button(
                text=month.strftime("%B %Y"),  # e.g., "August 2025"
                size_hint_y=None,
                height=100
            )
            btn.bind(on_press=lambda _:setattr(self.manager, 'current','month_event_expansion'))
            grid_month.add_widget(btn)
        layout.add_widget(grid)
        layout.add_widget(grid_month)
        back_btn = Button(text="Back", size_hint_y=None, height=50)
        back_btn.bind(on_press=lambda *_: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

    def open_day(self, date):
        self.manager.get_screen('day_detail').show_day(date)
        self.manager.current = 'day_detail'

class MonthEventExpansion(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        grid = GridLayout(cols=7, spacing=10, size_hint_y=0.8)
        today = datetime.today()
        for i in range(30):
            day = today + timedelta(days=i)
            date_str = day.strftime("%Y-%m-%d")
            btn = Button(text=day.strftime("%A\n%d %B"), size_hint_y=None, height=100)
            btn.bind(on_press=lambda btn, date=date_str: self.open_day(date))
            grid.add_widget(btn)
        layout.add_widget(grid)
        back_btn = Button(text="Back", size_hint_y=None, height=50)
        back_btn.bind(on_press=lambda *_: setattr(self.manager, 'current', 'calendar'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

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
        return sm


if __name__ == '__main__':
    TaskApp().run()
