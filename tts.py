import os

def speak(text):
    print("Assistant:", text)
    os.system(f'espeak-ng -v hi "{text}"')
