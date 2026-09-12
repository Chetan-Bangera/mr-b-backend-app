import sounddevice as sd
import scipy.io.wavfile as wav

# Voice Enrollment Parameters
SAMPLE_RATE = 16000
DURATION = 7  # Seconds to record

print("=" * 50)
print("🎙️ VOICE ENROLLMENT MODE")
print("Please speak clearly into your microphone for 7 seconds.")
print("Say something like: 'My name is Chetan and this is my voice authorization command.'")
print("=" * 50)

input("Press ENTER when you are ready to record...")

print("\n🔴 RECORDING NOW... Speak!")
audio_data = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
sd.wait()
print("🟢 RECORDING COMPLETE!")

# Save as reference file
wav.write("master_voice.wav", SAMPLE_RATE, audio_data)
print("Saved baseline sample to 'master_voice.wav'. You can now use JARVIS!")