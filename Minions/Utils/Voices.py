
import pyttsx4
import random


class MinionVoices:
    UNWANTED_CHARS = "=[]()*"
    def __init__(self):
        self.engine = pyttsx4.init()
        self.voices = self.engine.getProperty('voices')
        self.messages = []

    def cleanText(self, text):
        for char in self.UNWANTED_CHARS:
            text = text.replace(char, "")
        return text.strip()

    def mainSpeak(self, text, rate=250, pitch=150, volume=0.5):
        print(f"\n{text}\n")
        text = self.cleanText(text)
        voice = self.voices[random.randint(6, 7)]
        self.engine.setProperty('voice', voice.id)
        self.engine.setProperty('rate', rate)
        self.engine.setProperty('pitch', pitch)
        self.engine.setProperty('volume', volume)
        self.engine.say(text)
        self.engine.runAndWait()

    def subSpeak(self, text, rate=300, pitch=150, volume=0.5):
        print(f"\n{text}\n")
        text = self.cleanText(text)
        voice = self.voices[random.randint(5, 6)]
        self.engine.setProperty('voice', voice.id)
        self.engine.setProperty('rate', rate)
        self.engine.setProperty('pitch', pitch)
        self.engine.setProperty('volume', volume)
        self.engine.say(text)
        self.engine.runAndWait()