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
import os

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

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.canvas.before.clear()

        # Set black background
        with layout.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0, 0, 0, 1)  # black
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
            layout.bind(size=self._update_bg, pos=self._update_bg)

        # --- SCROLLING TEXT AREA ---
        self.scroll_label = make_scrollable_label()
        self.scroll_label.color = (1, 1, 1, 1)  # white text

        scroll = ScrollView(size_hint_y=0.5)
        scroll.add_widget(self.scroll_label)
        layout.add_widget(scroll)

        # --- PRESS BUTTON ---
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
        layout.add_widget(self.press_button)

        # --- BOTTOM NAVIGATION ---
        nav = BoxLayout(size_hint_y=None, height=50, spacing=5)

        btn_settings = Button(
            text="settings",
            background_color=(1, 0.5, 0, 1),
            color=(1, 1, 1, 1)
        )
        btn_transcript = Button(
            text="transcript",
            background_color=(0.3, 0.6, 1, 1),
            color=(1, 1, 1, 1)
        )
        btn_main = Button(
            text="main",
            background_color=(0.4, 0.4, 1, 1),
            color=(1, 1, 1, 1)
        )

        btn_settings.bind(on_press=lambda *_: setattr(self.manager, "current", "settings"))
        btn_transcript.bind(on_press=lambda *_: setattr(self.manager, "current", "transcript"))
        btn_main.bind(on_press=lambda *_: setattr(self.manager, "current", "main"))

        nav.add_widget(btn_settings)
        nav.add_widget(btn_transcript)
        nav.add_widget(btn_main)
        layout.add_widget(nav)

        self.add_widget(layout)

        # File watcher
        self.last_position = 0
        Clock.schedule_interval(self.check_for_updates, 1)

    def _update_bg(self, instance, value):
        self.bg_rect.size = instance.size
        self.bg_rect.pos = instance.pos

    def on_press(self, instance):
        instance.background_color = (1, 0, 0, 1)  # red on press

    def on_release(self, instance):
        instance.background_color = (0.2, 0.2, 0.2, 1)  # dark again on release

    def check_for_updates(self, dt):
        if os.path.exists(FILE_PATH):
            with open(FILE_PATH, 'r') as f:
                f.seek(self.last_position)
                new_lines = f.readlines()
                if new_lines:
                    self.scroll_label.text += ''.join(new_lines)
                self.last_position = f.tell()


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

        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(SettingsScreen(name='settings'))
        sm.add_widget(TranscriptScreen(name='transcript'))

        if not os.path.exists(FILE_PATH):
            with open(FILE_PATH, 'w') as f:
                f.write("Initial line\n")

        return sm

if __name__ == '__main__':
    MyApp().run()
