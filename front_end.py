from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.floatlayout import FloatLayout
from kivy.metrics import sp
from kivy.core.window import Window
from datetime import datetime, timedelta
from kivy.uix.gridlayout import GridLayout
import os
import csv
import pandas

FILE_PATH = "Transcription copy.txt"


#TO DO CHANGES: MAKE THE MAIN PAGE ONLY SHOW THE PAST HOUR, MAKE THE TRANSCRIPTION ONLY SHOW THE LAST DAY
#ALSO MAKE THE SCROLLIN AUTOMATIC IF POSSIBLE AND COOL ASF. THEN MKE THE BUTTONS ACTUALLY DO SOMETHING AND MAKE A WAY TO 
# DOSPLAY THE CALENDAR ON TEH FRONT PAGE. 

# A shared method to update label height and allow scrolling
def make_scrollable_label():
    lbl = Label(
        text='',
        size_hint_y=None,
        halign='left',
        valign='top',
        markup=True
    )
    lbl.bind(
        texture_size=lambda inst, val: setattr(inst, 'height', val[1])
    )
    lbl.text_size = (Window.width - 20, None)  # Ensure text wraps
    return lbl

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        self.layout.canvas.before.clear()

        # Black background
        with self.layout.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0, 0, 0, 1)
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
            self.layout.bind(size=self._update_bg, pos=self._update_bg)

        # --- CALENDAR GRID ---
        self.calendar_grid = GridLayout(cols=2, spacing=10, size_hint_y=0.8)

        today = datetime.today()
        for i in range(8):  # today + 7
            day = today + timedelta(days=i)
            day_str = day.strftime("%A\n%d %B")
            btn = Button(
                text=day_str,
                font_size=18,
                halign='center',
                valign='middle',
                text_size=(150, None),
                size_hint_y=None,
                height=100,
                background_color=(0.2, 0.2, 0.2, 1),
                color=(1, 1, 1, 1)
            )
            btn.bind(on_press=self.open_day_view)
            self.calendar_grid.add_widget(btn)

        self.layout.add_widget(self.calendar_grid)

        # --- BOTTOM BUTTON ---
        self.press_button = Button(
            text='Hold Me',
            size_hint_y=None,
            height=60,
            background_normal='',
            background_color=(0.2, 0.2, 0.2, 1),
            color=(1, 1, 1, 1)
        )
        self.press_button.bind(on_press=self.on_press)
        self.press_button.bind(on_release=self.on_release)
        self.layout.add_widget(self.press_button)

        # --- NAVIGATION BAR ---
        nav = BoxLayout(size_hint_y=None, height=50, spacing=5)

        btn_settings = Button(text="settings", background_color=(1, 0.5, 0, 1), color=(1, 1, 1, 1))
        btn_transcript = Button(text="transcript", background_color=(0.3, 0.6, 1, 1), color=(1, 1, 1, 1))
        btn_main = Button(text="main", background_color=(0.4, 0.4, 1, 1), color=(1, 1, 1, 1))

        btn_settings.bind(on_press=lambda *_: setattr(self.manager, "current", "settings"))
        btn_transcript.bind(on_press=lambda *_: setattr(self.manager, "current", "transcript"))
        btn_main.bind(on_press=lambda *_: setattr(self.manager, "current", "main"))

        nav.add_widget(btn_settings)
        nav.add_widget(btn_transcript)
        nav.add_widget(btn_main)
        self.layout.add_widget(nav)

        self.add_widget(self.layout)

    def _update_bg(self, instance, value):
        self.bg_rect.size = instance.size
        self.bg_rect.pos = instance.pos

    def on_press(self, instance):
        instance.background_color = (1, 0, 0, 1)

    def on_release(self, instance):
        instance.background_color = (0.2, 0.2, 0.2, 1)

    def open_day_view(self, instance):
        selected_date = instance.text.replace('\n', ' ')
        detail_screen = self.manager.get_screen('day_detail')
        detail_screen.update_day(selected_date)
        self.manager.current = 'day_detail'

class DayDetailScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        with self.layout.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0, 0, 0, 1)
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
            self.layout.bind(size=self._update_bg, pos=self._update_bg)

        self.day_label = Label(
            text='',
            font_size=32,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=60
        )
        self.layout.add_widget(self.day_label)
        self.task_list = Label(
            text='',
            font_size=18,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            markup=True,
            halign='left',
            valign='top'
        )
        self.task_list.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
        self.task_list.text_size = (Window.width - 40, None)
        def update_day(self, day_str):
            self.day_label.text = day_str

            # Parse the actual date from display string (e.g., "Tuesday 05 August")
            try:
                parsed_date = datetime.strptime(day_str, "%A %d %B")
                parsed_date = parsed_date.replace(year=datetime.now().year)
                date_key = parsed_date.strftime("%Y-%m-%d")
            except Exception as e:
                self.task_list.text = f"[b]Error parsing date:[/b] {str(e)}"
                return

            # Load events from CSV
            events = []
            try:
                with open("events.csv", newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        if row["event_date_start"] == date_key:
                            events.append(row)
            except Exception as e:
                self.task_list.text = f"[b]Error reading CSV:[/b] {str(e)}"
                return

            if not events:
                self.task_list.text = f"[b]{day_str}[/b]\n\nNo events for this day."
            else:
                content = f"[b]{day_str} Events:[/b]\n\n"
                for event in events:
                    content += (
                        f"• [b]{event['event_name']}[/b] ({event['start_time']} - {event['end_time']})\n"
                        f"  Location: {event['event_location']}\n"
                        f"  Details: {event['important_details']}\n"
                        f"  Attendees: {event['people_attending']}\n\n"
                    )
                self.task_list.text = content
        
        self.task_list.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
        self.task_list.text_size = (Window.width - 40, None)

        scroll = ScrollView()
        scroll.add_widget(self.task_list)
        self.layout.add_widget(scroll)

        return_button = Button(
            text="Return to Calendar",
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.2, 0.2, 1),
            color=(1, 1, 1, 1)
        )
        return_button.bind(on_press=lambda *_: setattr(self.manager, "current", "main"))
        self.layout.add_widget(return_button)

        self.add_widget(self.layout)

    def _update_bg(self, instance, value):
        self.bg_rect.size = instance.size
        self.bg_rect.pos = instance.pos

    def update_day(self, day_str):
        self.day_label.text = day_str
        # Example static task list — could later be read from a file per day

        #CHANGE THSI TO MAKE THIS A BIT BETTER BECAUSE IT NEEDS TO UPDATE THE TASKS FROM THE CSV FILE OR LIKE DISPLAY THE CSV FILE 
        # ON THE SCRREEN WITH COLUMNS AND SHIT

        self.task_list.text = (
            f"[b]{day_str} Tasks[/b]\n\n"
            
        )

class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(Label(text="Settings Screen"))

        return_button = Button(text="Return to Main")
        return_button.bind(on_press=lambda *_: setattr(self.manager, "current", "main"))
        layout.add_widget(return_button)

        self.add_widget(layout)

class TranscriptScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation='vertical')
        layout.canvas.before.clear()

        # Set black background
        with layout.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0, 0, 0, 1)  # black
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
            layout.bind(size=self._update_bg, pos=self._update_bg)

        # Scrollable transcript area with white text
        self.transcript_label = make_scrollable_label()
        self.transcript_label.color = (1, 1, 1, 1)  # white text

        scroll = ScrollView()
        scroll.add_widget(self.transcript_label)
        layout.add_widget(scroll)

        # Return button (optional: style it dark too)
        return_button = Button(
            text="Return to Main",
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.2, 0.2, 1),
            color=(1, 1, 1, 1)
        )
        return_button.bind(on_press=lambda *_: setattr(self.manager, "current", "main"))
        layout.add_widget(return_button)

        self.add_widget(layout)

        Clock.schedule_interval(self.refresh_transcript, 1)

    def _update_bg(self, instance, value):
        self.bg_rect.size = instance.size
        self.bg_rect.pos = instance.pos

    def refresh_transcript(self, dt):
        if os.path.exists(FILE_PATH):
            with open(FILE_PATH, 'r') as f:
                self.transcript_label.text = f.read()

class MyApp(App):
    def build(self):
        Window.clearcolor = (1, 1, 1, 1)
    
        # ✅ Create the screen manager first
        sm = ScreenManager()
        
        # ✅ Then add screens to it
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(SettingsScreen(name='settings'))
        sm.add_widget(TranscriptScreen(name='transcript'))
        sm.add_widget(DayDetailScreen(name='day_detail'))
    
        # ✅ Optional: create transcription file if it doesn’t exist
        if not os.path.exists(FILE_PATH):
            with open(FILE_PATH, 'w') as f:
                f.write("Initial line\n")
    
        return sm

if __name__ == '__main__':
    MyApp().run()
