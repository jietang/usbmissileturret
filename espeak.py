import os
import random

from mail import PORTAL_TURRET_SAYINGS

def speak(text=None, voice='en+f2'):
    if not text:
        text = random.choice(PORTAL_TURRET_SAYINGS)
    cmd = 'espeak -p99 -v%s "%s" 2>/dev/null >/dev/null' % (voice, text)
    print cmd
    os.system(cmd)

if __name__=="__main__":
    speak()
# call(['espeak', '-p 99 -ven+f2 "%s" 2>/dev/null >/dev/null' % "I don't blame you"])
