import pyttsx3

engine = pyttsx3.init('sapi5')
engine.say("Testing voice system. Can you hear me now, sir?")
engine.runAndWait()