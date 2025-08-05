import kivy
import kivy.uix.screenmanager
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.label import Label


kivy.require('2.0.0')
class Application(App):
    def build(self):
        self.title = "My Kivy App"
        return Label(text="Hello, Kivy!")
        return Builder.load_file('front_end.kv')


