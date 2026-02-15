Create:

touch README.md

Paste this:

# Astraeus - Offline Hindi Voice Assistant

## Overview
Astraeus is a fully offline Hindi voice assistant built to run on Raspberry Pi CPU without cloud dependency.

It uses:
- Vosk for offline Hindi ASR
- RapidFuzz for intent detection
- psutil for system monitoring
- pyttsx3 for text-to-speech

Wake word: "Priya Ji"

---

## Features

- Fully offline operation
- 20+ supported intents
- Context memory
- Wake word activation
- Confidence score display
- Transcript output
- System monitoring (CPU, memory, disk)
- Notes and reminders
- Warm conversational tone

---

## Hardware

- Raspberry Pi 2 / 4 / 5
- USB Microphone
- Speaker

---

## Installation

```bash
pip install -r requirements.txt
sudo apt install espeak-ng portaudio19-dev
python main.py
```
Architecture

Mic → Vosk ASR → Intent Engine → Action Executor → TTS

Fully Offline Guarantee

No cloud APIs are used.
All processing occurs on-device.


# 📝 REPORT STRUCTURE (For Submission)

In your report PDF include:

### 1. Abstract
Explain offline privacy + Hindi language focus.

### 2. Architecture Diagram

Draw this:


Mic → Audio Buffer → Vosk ASR → Intent Engine → Context Memory → Action Layer → TTS


### 3. Optimization for Raspberry Pi 2

Mention:
- Small Hindi model
- Downsampling 44100 → 16000
- CPU-only execution
- No GPU

### 4. Performance Metrics

Include:

- Avg latency
- Confidence score range
- RAM usage
- CPU usage

### 5. Challenges

- Hindi ASR accuracy
- Accent handling
- Low-resource hardware
- Offline NLP limitations

Judges LOVE this section.

---

# 🎥 DEMO FLOW THAT WINS

Start recording.

Boot system.

Assistant says:
> “नमस्ते प्रिया जी। मैं तैयार हूँ।”

Say:
“Priya ji”

Assistant:
“जी प्रिया जी, बताइए।”

Then show:

• Time  
• CPU usage  
• Joke  
• Note saving  
• Follow-up question  
• Context memory  

Then say:
“यह पूरी तरह ऑफलाइन चलता है।”

Boom. Mic drop.



# 📁 Transfer to Raspberry Pi via USB

1. Copy full project folder to USB.
2. Plug into Pi.
3. Copy:

```bash
cp -r Astraeus_Offline_Assistant ~/
cd Astraeus_Offline_Assistant
pip install -r requirements.txt
python main.py
