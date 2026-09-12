import os
import sys
import pathlib
import tempfile
import datetime
import subprocess
import requests
import warnings
import time
import ctypes
import sqlite3
import soundfile as sf
import pyttsx3
import speech_recognition as sr
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

# --- Load Environment ---
load_dotenv()
if not os.getenv("GEMINI_API_KEY"):
    print("❌ Error: GEMINI_API_KEY is missing or empty in .env!")
    sys.exit(1)

from google import genai

# --- Offline Face & Voice Imports ---
try:
    import cv2
    from deepface import DeepFace
    HAS_FACE_REC = True
except ImportError:
    HAS_FACE_REC = False

try:
    import torch
    from speechbrain.inference.speaker import SpeakerRecognition
    HAS_SPEECHBRAIN = True
except ImportError:
    HAS_SPEECHBRAIN = False

try:
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    HAS_PYCAW = True
except ImportError:
    HAS_PYCAW = False


# --- Database Memory ---
def init_db():
    conn = sqlite3.connect("mrb_memory.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS chat_history (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, message TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_message(role, message):
    conn = sqlite3.connect("mrb_memory.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_history (role, message) VALUES (?, ?)", (role, message))
    conn.commit()
    conn.close()

def load_history():
    conn = sqlite3.connect("mrb_memory.db")
    cursor = conn.cursor()
    cursor.execute("SELECT role, message FROM (SELECT id, role, message FROM chat_history ORDER BY id DESC LIMIT 20) ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [{"role": row[0], "parts": [{"text": row[1]}]} for row in rows]

# --- Initialize Gemini ---
IS_LOCKED = True
try:
    client = genai.Client()
    init_db()
    
    system_instruction = "You are Mr. B, a highly intelligent, polite, smooth, and witty AI assistant. You belong exclusively to Chetan. Keep answers brief and conversational."
    chat = client.chats.create(
        model="gemini-3.6-flash",
        config={"system_instruction": system_instruction},
        history=load_history()
    )
except Exception as e:
    print(f"Error initializing Gemini: {e}")
    sys.exit(1)

# --- Biometrics Setup ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_VOICE_PATH = os.path.join(SCRIPT_DIR, "master_voice.wav")
MASTER_FACE_PATH = os.path.join(SCRIPT_DIR, "master_face.jpg")
SIMILARITY_THRESHOLD = 0.01

try:
    verifier = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", savedir=str(pathlib.Path.home() / ".cache" / "speechbrain_model"), run_opts={"device": "cpu"})
    VOICE_SECURITY = True if os.path.exists(MASTER_VOICE_PATH) else False
except: VOICE_SECURITY = False

FACE_SECURITY = True if (HAS_FACE_REC and os.path.exists(MASTER_FACE_PATH)) else False

# --- Core Functions ---
def speak(text):
    print(f"\nMr. B: {text}")
    try:
        engine = pyttsx3.init('sapi5' if sys.platform == "win32" else None)
        engine.setProperty('rate', 170)
        engine.setProperty('volume', 1.0)
        voices = engine.getProperty('voices')
        if voices: engine.setProperty('voice', voices[0].id)
        engine.say(text)
        engine.runAndWait()
        time.sleep(0.5) 
    except: pass

def verify_biometrics(audio_data):
    if VOICE_SECURITY:
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                temp_path = temp_wav.name
                temp_wav.write(audio_data.get_wav_data())
            data1, _ = sf.read(MASTER_VOICE_PATH)
            data2, _ = sf.read(temp_path)
            if os.path.exists(temp_path): os.remove(temp_path)
            
            s1 = torch.tensor(data1, dtype=torch.float32).unsqueeze(0) if data1.ndim == 1 else torch.tensor(data1, dtype=torch.float32)
            s2 = torch.tensor(data2, dtype=torch.float32).unsqueeze(0) if data2.ndim == 1 else torch.tensor(data2, dtype=torch.float32)
            
            emb1, emb2 = verifier.encode_batch(s1).squeeze(), verifier.encode_batch(s2).squeeze()
            if emb1.ndim == 1: emb1 = emb1.unsqueeze(0)
            if emb2.ndim == 1: emb2 = emb2.unsqueeze(0)
            
            if float(torch.nn.functional.cosine_similarity(emb1, emb2, dim=-1).mean().item()) >= SIMILARITY_THRESHOLD: return True
        except: pass

    if FACE_SECURITY:
        speak("Voice failed. Activating visual scanner.")
        cam = cv2.VideoCapture(0)
        start = time.time()
        match = False
        while time.time() - start < 10:
            ret, frame = cam.read()
            if not ret: continue
            cv2.imshow('Scanner', frame)
            try:
                if DeepFace.verify(img1_path=MASTER_FACE_PATH, img2_path=frame, enforce_detection=False, silent=True).get("verified"):
                    match = True
                    break
            except: pass
            if cv2.waitKey(1) & 0xFF == ord('q'): break
        cam.release()
        cv2.destroyAllWindows()
        return match
    return False

def listen():
    global IS_LOCKED
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1.5
    with sr.Microphone() as source:
        print("\nListening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.8)
        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
            try: query = recognizer.recognize_google(audio)
            except sr.RequestError:
                try: query = recognizer.recognize_sphinx(audio)
                except: return None
            except: return None

            if IS_LOCKED:
                if "unlock" in query.lower():
                    if verify_biometrics(audio):
                        IS_LOCKED = False
                        speak("System unlocked. Welcome back, Chetan.")
                    else: speak("Identity unverified. System locked.")
                return None
            else:
                if "lock system" in query.lower():
                    IS_LOCKED = True
                    speak("System locked.")
                    return None
                return query
        except sr.WaitTimeoutError: return None

def handle_commands(cmd):
    if "time" in cmd: speak(f"It is {datetime.datetime.now().strftime('%I:%M %p')}."); return True
    elif "lock pc" in cmd: ctypes.windll.user32.LockWorkStation(); return True
    elif "sleep pc" in cmd: os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0"); return True
    return False

def run_mr_b():
    """Main loop to be called from main.py"""
    speak("Mr. B online. Voice lock active.")
    while True:
        user_input = listen()
        if not user_input: continue
        
        if "shutdown" in user_input.lower() or "exit" in user_input.lower():
            speak("Shutting down. Goodbye.")
            break
            
        if handle_commands(user_input.lower()): continue
        
        try:
            save_message("user", user_input)
            response = chat.send_message(user_input)
            save_message("model", response.text)
            speak(response.text)
        except Exception as e:
            print(f"API Error: {e}")