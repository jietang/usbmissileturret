# requires libusb 1.0 (libusb-1.0-dev), pyusb, tkinter (python-tk)

import Tkinter as tk
import sys

from functools import partial

from usbturret import USBMissileLauncher, FakeLauncher
from usbturret import LEFT, RIGHT, UP, DOWN, STOP
from client import RemoteLauncher

launchers = [FakeLauncher,
             USBMissileLauncher,
             RemoteLauncher]

try:
    launcher_klass = launchers[int(sys.argv[1])]
except IndexError:
    launcher_klass = FakeLauncher

after_idle = None
keysdown = set()

# make a lock, acquire it when firing and priming and sending commands
# don't send more events if lock is acquired

def release(event):
    if event.keysym == 'Escape':
        root.destroy()
    elif event.keysym == 'space':
        launcher.fire()
    elif event.keysym == 'p':
        launcher.prime()
    else:
        if event.keysym in keysdown:
            keysdown.remove(event.keysym)
            update_status()

def keyup(event):
    global after_idle
    after_idle = root.after_idle(release, event)

keys_to_cmds = {
    "Left": LEFT,
    "Right": RIGHT,
    "Up": UP,
    "Down": DOWN,
    "space": 0,
    "p": 0,
    }

def update_status():
    if keysdown:
        cmd = 0
        for k in keysdown:
            cmd = cmd | keys_to_cmds[k]
        if cmd:
            return launcher.send_command(cmd)
    else:
        return launcher.send_command(STOP)

def doKey(key):
    if key not in keysdown:
        keysdown.add(key)
        return update_status()


callbacks = dict((k, partial(doKey, key=k)) for k in ('Left', 'Right', 'Up', 'Down'))
def keydown(event):
    global after_idle
    if after_idle is not None:
        root.after_cancel(after_idle)
        after_idle = None

    try:
        callbacks[event.keysym]()
    except KeyError:
        pass

launcher = launcher_klass()

root = tk.Tk()
print "Press a key (Escape key to exit):"
root.bind('<KeyPress>', keydown)
root.bind('<KeyRelease>', keyup)
# don't show the tk window
root.mainloop()
