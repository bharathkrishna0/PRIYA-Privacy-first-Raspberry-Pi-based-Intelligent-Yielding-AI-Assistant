from rapidfuzz import fuzz
import re

intents = {
    "time": ["समय क्या है", "अभी कितने बजे हैं"],
    "date": ["आज की तारीख क्या है"],
    "day": ["आज कौन सा दिन है"],
    "cpu": ["सीपीयू उपयोग", "सिस्टम लोड"],
    "memory": ["मेमोरी उपयोग", "रैम उपयोग"],
    "disk": ["डिस्क उपयोग", "स्टोरेज कितना है"],
    "battery": ["बैटरी स्थिति", "बैटरी कितनी है"],
    "shutdown": ["सिस्टम बंद करो"],
    "restart": ["सिस्टम रीस्टार्ट करो"],
    "joke": ["मजाक सुनाओ", "जोक सुनाओ"],
    "motivation": ["प्रेरणा दो", "मोटिवेशन दो"],
    "math": ["गणना करो", "जोड़ो", "घटाओ"],
    "note": ["नोट सेव करो", "लिख लो"],
    "reminder": ["रिमाइंडर सेट करो"],
    "open": ["ऐप खोलो"],
    "close": ["ऐप बंद करो"],
    "volume": ["आवाज़ बढ़ाओ", "आवाज़ कम करो"],
    "system_info": ["सिस्टम जानकारी"],
    "greeting": ["नमस्ते", "हेलो"],
    "conversation": ["बात करो", "कैसे हो"]
}

def detect_intent(text):
    best_match = None
    highest_score = 0

    for intent, phrases in intents.items():
        for phrase in phrases:
            score = fuzz.ratio(text, phrase)
            if score > highest_score:
                highest_score = score
                best_match = intent

    if highest_score > 60:
        return best_match
    return "unknown"

