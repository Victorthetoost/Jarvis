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

APPROVAL_CSV = "pending_events.csv"
CALENDAR_CSV = "events.csv"


def load_csv(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        return list(csv.DictReader(csvfile))


def save_csv(file_path, data):
    if not data:
        open(file_path, 'w').close()
        return
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)


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

        self.add_widget(self.layout)
        self.refresh()

    def refresh(self):
        self.task_grid.clear_widgets()
        tasks = load_csv(APPROVAL_CSV)
        for task in tasks:
            box = BoxLayout(size_hint_y=None, height=100)
            summary = f"{task['event_name']} on {task['event_date_start']} @ {task['start_time']}"
            label = Label(text=summary, halign='left', valign='middle')
            label.text_size = (Window.width - 150, None)
            approve_btn = Button(text="✔", size_hint_x=None, width=50, background_color=(0, 1, 0, 1))
            deny_btn = Button(text="✖", size_hint_x=None, width=50, background_color=(1, 0, 0, 1))
            approve_btn.bind(on_press=lambda _, t=task: self.approve(t))
            deny_btn.bind(on_press=lambda _, t=task: self.deny(t))
            box.add_widget(label)
            box.add_widget(approve_btn)
            box.add_widget(deny_btn)
            self.task_grid.add_widget(box)

    def approve(self, task):
        events = load_csv(CALENDAR_CSV)
        events.append(task)
        save_csv(CALENDAR_CSV, events)
        self.deny(task)  # Remove from pending list

    def deny(self, task):
        tasks = load_csv(APPROVAL_CSV)
        tasks = [t for t in tasks if t != task]
        save_csv(APPROVAL_CSV, tasks)
        self.refresh()


class CalendarScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        grid = GridLayout(cols=2, spacing=10, size_hint_y=0.8)
        today = datetime.today()
        for i in range(8):
            day = today + timedelta(days=i)
            date_str = day.strftime("%Y-%m-%d")
            btn = Button(text=day.strftime("%A\n%d %B"), size_hint_y=None, height=100)
            btn.bind(on_press=lambda btn, date=date_str: self.open_day(date))
            grid.add_widget(btn)
        layout.add_widget(grid)
        back_btn = Button(text="Back", size_hint_y=None, height=50)
        back_btn.bind(on_press=lambda *_: setattr(self.manager, 'current', 'main'))
        layout.add_widget(back_btn)
        self.add_widget(layout)

    def open_day(self, date):
        self.manager.get_screen('day_detail').show_day(date)
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
        print(f"Trying to parse day_str: '{day_str}'")
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
            delete_btn.bind(on_press=lambda btn, ev=event: self.delete_event(ev,parsed_date))
            row.add_widget(delete_btn)
    
            # Event name
            row.add_widget(Label(text=event['event_name'], size_hint_x=0.2))
    
            # Time
            row.add_widget(Label(text=f"{event['start_time']} - {event['end_time']}", size_hint_x=0.2))
    
            # Location
            row.add_widget(Label(text=event['event_location'], size_hint_x=0.2))
    
            # People and notes
            people_and_notes = f"people attending: {event['people_attending']}\nimportant details: {event['important_details']}"
            label = Label(text=people_and_notes, size_hint_x=0.3, halign='left', valign='middle')
            label.text_size = (Window.width * 0.3, 60)
            row.add_widget(label)
    
            self.events_grid.add_widget(row)

    def delete_event(self, event, date):
        events = load_csv(CALENDAR_CSV)
        events = [e for e in events if e != event]
        save_csv(CALENDAR_CSV, events)
        self.show_day(date)


class TaskApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(CalendarScreen(name='calendar'))
        sm.add_widget(DayDetailScreen(name='day_detail'))
        return sm


if __name__ == '__main__':
    TaskApp().run()
