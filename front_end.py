from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.core.window import Window
from datetime import datetime
import itertools


#might not need this becuase i could just add it to the display list every time that i write it to the transcription.txt
##def Find_Time_start(time = datetime.now().strftime("%Y-%m-%d %H")):
##    line_count = 0
##    with open("Transcription.txt", "r") as f:
##        line_count = line_count + 1
##        for line in itertools.islice(f, 0, None):
##            if(time in line):
##                return line_count
##
##
##def Read_Transcript(time = datetime.now().strftime("%Y-%m-%d %H")):
##    last_break = Find_Time_start(time)
##    return_string = []
##    with open("Transcription.txt","r") as f:
##        for line in itertools.islice(f, last_break, None):
##            return_string.append(line)
##    return return_string


class ScrollingText(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text_size = (None, None)
        self.bind(texture_size=self.setter('size'))

class MyApp(App):
    def build(self):
        Window.clearcolor = (1, 1, 1, 1)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # --- SCROLLING TEXT BOX ---
        self.scroll_label = ScrollingText(text='', size_hint_y=0.5)
        scroll = ScrollView(size_hint_y=0.5)
        scroll.add_widget(self.scroll_label)
        layout.add_widget(scroll)

        # Read file content here (you can later hook it to a .txt file)
        self.lines = Read_Transcript()
        self.line_index = 0
        Clock.schedule_interval(self.add_line, 1.5)

        # --- MIDDLE BUTTON ---
        self.press_button = Button(
            text='Press Me',
            size_hint_y=None,
            height=60,
            background_normal='',
            background_color=(0.6, 1, 0.6, 1)
        )
        self.press_button.bind(on_press=self.on_button_press)
        self.press_button.bind(on_release=self.on_button_release)
        layout.add_widget(self.press_button)

        # --- BOTTOM NAV BAR ---
        bottom_bar = BoxLayout(size_hint_y=None, height=50, spacing=5)

        btn1 = Button(text='settings', background_color=(1, 0.5, 0, 1))  # orange
        btn2 = Button(text='transcript', background_color=(0.3, 0.6, 1, 1))  # blue
        btn3 = Button(text='settings', background_color=(0.3, 0.3, 1, 1))  # purple/blackish

        bottom_bar.add_widget(btn1)
        bottom_bar.add_widget(btn2)
        bottom_bar.add_widget(btn3)

        layout.add_widget(bottom_bar)

        return layout

    def add_line(self, dt):
        if self.line_index < len(self.lines):
            self.scroll_label.text += self.lines[self.line_index]
            self.line_index += 1

    def on_button_press(self, instance):
        instance.background_color = (1, 0, 0, 1)  # red

    def on_button_release(self, instance):
        instance.background_color = (0.6, 1, 0.6, 1)  # green

if __name__ == '__main__':
    MyApp().run()
