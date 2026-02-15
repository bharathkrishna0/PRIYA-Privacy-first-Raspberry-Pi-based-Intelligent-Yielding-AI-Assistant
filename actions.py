import datetime
import psutil
import random
import os

notes_file = "notes.txt"
reminder_file = "reminders.txt"

def execute_intent(intent, text=""):
    if intent == "time":
        return "अभी समय है " + datetime.datetime.now().strftime("%H:%M")

    elif intent == "date":
        return "आज की तारीख है " + datetime.datetime.now().strftime("%d %B %Y")

    elif intent == "day":
        return "आज " + datetime.datetime.now().strftime("%A")

    elif intent == "cpu":
        return f"सीपीयू उपयोग {psutil.cpu_percent()} प्रतिशत है"

    elif intent == "memory":
        return f"मेमोरी उपयोग {psutil.virtual_memory().percent} प्रतिशत है"

    elif intent == "disk":
        return f"डिस्क उपयोग {psutil.disk_usage('/').percent} प्रतिशत है"

    elif intent == "battery":
        battery = psutil.sensors_battery()
        if battery:
            return f"बैटरी {battery.percent} प्रतिशत है"
        return "बैटरी जानकारी उपलब्ध नहीं है"

    elif intent == "shutdown":
        os.system("sudo shutdown now")
        return "सिस्टम बंद किया जा रहा है"

    elif intent == "restart":
        os.system("sudo reboot")
        return "सिस्टम रीस्टार्ट हो रहा है"

    elif intent == "joke":
        return random.choice([
            "प्रोग्रामर शादी क्यों नहीं करते? क्योंकि commit कर चुके होते हैं।",
            "Bug नहीं है, undocumented feature है।"
        ])

    elif intent == "motivation":
        return "कभी हार मत मानो। हर दिन एक नया अवसर है।"

    elif intent == "note":
        with open(notes_file, "a") as f:
            f.write(text + "\n")
        return "नोट सेव कर दिया गया है"

    elif intent == "reminder":
        with open(reminder_file, "a") as f:
            f.write(text + "\n")
        return "रिमाइंडर सेव कर दिया गया है"

    elif intent == "greeting":
        return "नमस्ते, मैं एस्ट्रेयस हूँ।"

    elif intent == "conversation":
        return "मैं पूरी तरह ऑफलाइन काम कर रहा हूँ।"

    elif intent == "system_info":
        return f"CPU {psutil.cpu_percent()}%, RAM {psutil.virtual_memory().percent}%"

    else:
        return "माफ़ कीजिए, मैं समझ नहीं पाया।"
