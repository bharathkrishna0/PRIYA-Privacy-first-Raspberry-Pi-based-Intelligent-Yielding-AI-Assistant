import json
import time
import pyaudio
import numpy as np
from vosk import Model, KaldiRecognizer

from intent_engine import detect_intent
from actions import execute_intent
from tts import speak

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

MODEL_PATH = "model"
DEVICE_INDEX = None # On Raspberry Pi 2 set to 2 if mic index is 2
WAKE_WORDS = ["priya ji", "प्रिया जी", "प्रियाजी"]

# --------------------------------------------------
# CONTEXT MEMORY
# --------------------------------------------------

conversation_memory = {
    "last_intent": None,
    "last_response": None,
    "last_topic": None
}

# --------------------------------------------------
# STARTUP
# --------------------------------------------------

print("\n===================================")
print(" Astraeus Offline Voice Assistant")
print(" Wake Word: Priya Ji")
print("===================================\n")

time.sleep(1)
speak("नमस्ते प्रिया जी। मैं तैयार हूँ।")

# --------------------------------------------------
# LOAD MODEL
# --------------------------------------------------

print("Loading Vosk Hindi model...")
model = Model(MODEL_PATH)
rec = KaldiRecognizer(model, 16000)

# --------------------------------------------------
# AUDIO SETUP
# --------------------------------------------------

p = pyaudio.PyAudio()

stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=44100,
    input=True,
    input_device_index=DEVICE_INDEX,
    frames_per_buffer=4096
)

print("🎤 System Ready. Say 'Priya Ji' to activate.\n")

listening_mode = False

# --------------------------------------------------
# MAIN LOOP
# --------------------------------------------------

while True:
    data = stream.read(4096, exception_on_overflow=False)

    # Downsample 44100 → 16000
    audio = np.frombuffer(data, dtype=np.int16)
    audio = audio[::3]
    data16 = audio.tobytes()

    if rec.AcceptWaveform(data16):
        result = json.loads(rec.Result())
        text = result.get("text", "").lower()

        if text == "":
            continue

        print("\nTranscript:", text)

      
        # --------------------------------------------
        # WAKE WORD DETECTION
        # --------------------------------------------
        if any(wake in text for wake in WAKE_WORDS):
            listening_mode = True
            speak("जी प्रिया जी, बताइए।")
            continue

        # --------------------------------------------
        # SMALL TALK (Warm Personality)
        # --------------------------------------------
        if "कैसे हो" in text:
            speak("मैं बिल्कुल ठीक हूँ। आप कैसी हैं प्रिया जी?")
            continue

        if "धन्यवाद" in text:
            speak("आपका स्वागत है। हमेशा मदद के लिए यहाँ हूँ।")
            continue

        # --------------------------------------------
        # FOLLOW-UP HANDLING
        # --------------------------------------------
        intent = detect_intent(text)

        if intent == "unknown":
            if "और" in text and conversation_memory["last_intent"]:
                intent = conversation_memory["last_intent"]

        # --------------------------------------------
        # EXECUTE INTENT
        # --------------------------------------------
        if listening_mode:
            response = execute_intent(intent, text, conversation_memory)

            print("Detected Intent:", intent)
            print("Response:", response)

            speak(response)

            # Store context
            conversation_memory["last_intent"] = intent
            conversation_memory["last_response"] = response

            listening_mode = False
