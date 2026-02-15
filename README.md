# 🌸 PRIYA  
## Privacy-First Real-Time Intelligent Yielding Assistant

PRIYA is a fully offline Hindi conversational AI assistant built to run on Raspberry Pi without any cloud dependency.  
It performs speech recognition, intent detection, and response generation entirely on-device.

Wake word: **"Priya Ji"**

---

## Structure 
Astraeus_Offline_Assistant/
│
├── main.py
├── asr.py              (optional if separated)
├── intent_engine.py
├── actions.py
├── tts.py
├── model/              (vosk model folder)
│
├── notes.txt
├── reminders.txt
│
├── requirements.txt
└── README.md
## 🚀 Features
- 🎙 Offline Hindi Speech Recognition using Vosk
- 🧠 Fuzzy Intent Detection using RapidFuzz
- 💬 Context Memory for follow-up conversations
- 🔊 Offline Text-to-Speech using pyttsx3 / espeak-ng
- 💻 System Monitoring:
  - Time, Date, Day
  - CPU Usage
  - Memory Usage
  - Disk Usage
  - Battery Status
- ⚙ System Control:
  - Shutdown (optional)
  - Restart (optional)
  - Volume Control
- 📝 Notes & Reminder Storage
- 😂 Jokes & Motivational Responses
- 🌸 Warm conversational personality

---

## 🏗 Architecture

Microphone  
↓  
Vosk Speech Recognition  
↓  
Intent Detection (RapidFuzz)  
↓  
Context Memory  
↓  
Action Execution  
↓  
Text-to-Speech Output  

All processing is fully offline.

---

## 🛠 Hardware Requirements

- Raspberry Pi 2 / 4 / 5
- USB Microphone
- Speaker / Headphones
- Raspberry Pi OS (32-bit recommended)

---

## 📦 Installation

Clone the repository:

```bash
git clone <your-repo-link>
cd voice_assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
sudo apt install espeak-ng portaudio19-dev
wget https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip
unzip vosk-model-small-hi-0.22.zip
mv vosk-model-small-hi-0.22 model
```
▶ Run
```
python main.py
```
Say:

Priya Ji

👨‍💻 Author

Built as an offline embedded AI system for Bharat AI-SoC Student Challenge
