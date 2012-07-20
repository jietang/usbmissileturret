import os
import random
from subprocess import Popen

from mail import PORTAL_TURRET_SAYINGS

def speak(text=None, voice='en+f2'):
    if not text:
        text = random.choice(PORTAL_TURRET_SAYINGS)
    cmd = 'espeak -p99 -v%s "%s" 2>/dev/null >/dev/null' % (voice, text)
    print cmd

    # os.system(cmd)
    with open('/dev/null', 'w') as f:
        Popen(['espeak','-p99', '-s 120', '-ven+f2', '"%s"'%text], stdout=f, stderr=f)

if __name__=="__main__":
    speak()
# call(['espeak', '-p 99 -ven+f2 "%s" 2>/dev/null >/dev/null' % "I don't blame you"])
