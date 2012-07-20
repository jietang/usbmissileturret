#uvcdynctrl -d video1 -s "White Balance Temperature, Auto" -- 0
import multiprocessing as mp
import time
import threading
import os
import socket
import struct

import numpy as np
import cv2
import cv2.cv as cv
import sharedmem as shm

from common import clock, draw_str
from video import create_capture

from targeting import Targeter
from util import detect, diff, draw_rects, size_and_center, norm, compare, contains

from usbturret import UP, DOWN, LEFT, RIGHT, STOP, USBMissileLauncher
from client import RemoteLauncher

help_message = '''
USAGE: facedetect.py [--cascade <cascade_fn>] [--nested-cascade <cascade_fn>] [<video_source>]
'''

VELOCITY_DECAY = 0.75
BUFFER = 50
REFIND_BUFFER = 30
MAX_MISSES = 5

high_proc = None
the_lock = mp.Lock()
stopping = mp.Value('c', chr(0), lock=False)
manager = mp.Manager()
possible_targets = manager.list()
targets = []
is_auto = False

controller_thread = None

controller_cv = threading.Condition()
# controller_cv = mp.Condition()

# [[x_timeout, x_cmd], [y_timeout, y_cmd]]
controller_state = []
# controller_state = manager.list()

controller_state.append([0.0, LEFT])
controller_state.append([0.0, DOWN])

def draw_command(img, command):
    if not command:
        return
    width, height = img.shape[0:2]
    if command & UP:
        w1 = 0.0
        w2 = 0.3
    elif command & DOWN:
        w1 = 0.7
        w2 = 1.0
    else:
        w1 = 0.33
        w2 = 0.66

    if command & LEFT:
        h1 = 0.0
        h2 = 0.3
    elif command & RIGHT:
        h1 = 0.7
        h2 = 1.0
    else:
        h1 = 0.33
        h2 = 0.66

    cv2.rectangle(img, (int(h1*height),int(w1*width)), (int(h2*height), int(w2*width)), (255, 0, 0), -1)

def lolz_thread(basepath, cam):
    start = time.time()
    last_time = time.time()
    i = 0
    os.mkdir(basepath)
    while time.time() - start < 1.6:
        ret, img = cam.read()
        if time.time() - last_time > 0.0:
            last_time = time.time()
            cv.SaveImage("%s/%d.jpg" % (basepath, i), cv.fromarray(img))
            i += 1

def controller(controller_state, should_stop, controller_cv, lock):
    launcher = RemoteLauncher()
    last_sent = [time.time()]

    def send_command(cmd):
        # print "CMD FREQ: ", time.time() - last_sent[0], cmd
        launcher.send_command(cmd)
        last_sent[0] = time.time()

    while True:
        if ord(should_stop.value):
            launcher.send_command(STOP)
            break

        with controller_cv:
            (x_timeout, x_cmd) = controller_state[0]
            (y_timeout, y_cmd) = controller_state[1]
            next_time = min(x_timeout, y_timeout)
            # print x_timeout, y_timeout, next_time, (next_time - time.time()), (x_timeout - time.time() < 0) and (y_timeout - time.time() < 0)

            # if 0.01 > next_time - time.time() > 0:
            #     print "fake sleep"
            #     time.sleep(next_time - time.time())
            if next_time - time.time() > 0:
                controller_cv.wait(next_time - time.time())
            else:
                # print "waiting to be notified"
                if (x_timeout - time.time() < 0) and (y_timeout - time.time() < 0):
                    send_command(STOP)
                controller_cv.wait()

            (x_timeout, x_cmd) = controller_state[0]
            (y_timeout, y_cmd) = controller_state[1]
        cur_time = time.time()

        # print
        # print
        # print x_timeout, y_timeout, (x_timeout > cur_time), (y_timeout > cur_time), cur_time, x_cmd, y_cmd
        # print
        # print

        cmd = 0
        if x_timeout > cur_time:
            cmd |= x_cmd
        if y_timeout > cur_time:
            cmd |= y_cmd
        if not cmd:
            cmd = STOP

        send_command(cmd)

launcher = USBMissileLauncher()
def add_controller_command(timeout_x, timeout_y, cmd):
    # given a launcher, execute this command completely
    cur_time = time.time()

    x_cmd = cmd & (LEFT | RIGHT)
    y_cmd = cmd & (UP | DOWN)

    cmds = [(timeout_x, x_cmd), (timeout_y, y_cmd)]
    while True:
        cmd = 0
        for t, c in cmds:
            if t > time.time():
                cmd |= c
        if not cmd:
            break
        next_time = max(sorted(cmds)[0][0] - time.time(), 0.01)

        launcher.send_command(cmd)
        time.sleep(next_time)
    launcher.send_command(STOP)

    # global controller_state, controller_cv
    # (new_x_timeout, new_x_cmd), (new_y_timeout, new_y_cmd) = controller_state

    # if (cmd & UP) or (cmd & DOWN):
    #     new_y_cmd = cmd
    #     new_y_timeout = timeout_y
    # if (cmd & LEFT) or (cmd & RIGHT):
    #     new_x_cmd = cmd
    #     new_x_timeout = timeout_x
    # if cmd & STOP:
    #     new_x_timeout = time.time()
    #     new_y_timeout = time.time()

    # with controller_cv:
    #     controller_state[0] = [new_x_timeout, new_x_cmd]
    #     controller_state[1] = [new_y_timeout, new_y_cmd]
    #     #print "SENDING CMD: ", controller_state, time.time()
    #     controller_cv.notify()



def high_level_tracker(image, should_stop, lock, targets, cascade):
    # 1 thread, high level tracking
    while True:
        with lock:
            if ord(should_stop.value):
                break
            high_image = image.copy()

        # t = clock()
        rects = detect(high_image, cascade)
        # with lock:
        #     print "high just took: ", clock() - t

        if len(rects) > 0:
            with lock:
                targets[:] = rects

if __name__ == '__main__':
    import sys, getopt
    print help_message
    
    args, video_src = getopt.getopt(sys.argv[1:], '', ['cascade=', 'nested-cascade='])
    try: video_src = video_src[0]
    except: video_src = 'synth:bg=../cpp/lena.jpg:noise=0.05'
    args = dict(args)
    cascade_fn = args.get('--cascade', "haarcascades/haarcascade_frontalface_alt.xml")

    cascade = cv2.CascadeClassifier(cascade_fn)
    cascade_nested = cv2.CascadeClassifier(cascade_fn)

    cam = create_capture(video_src)
    # print dir(cv), [x for x in dir(cv) if "exposure" in x.lower()]
    # print cam.get(cv.CV_CAP_PROP_EXPOSURE)
    ret, img = cam.read()

    width = img.shape[0]
    height = img.shape[1]
    low_image = shm.zeros(img.shape[0:2], dtype=img.dtype)

    # controller_thread = threading.Thread(target=controller, args=(controller_state, stopping, controller_cv, the_lock))
    # controller_thread = mp.Process(target=controller, args=(controller_state, stopping, controller_cv, the_lock))
    # controller_thread.start()

    targeter = Targeter(height, width, add_controller_command)

    primed = True
    firing = False
    locked_counter = 0

    while True:
        t = clock()
        ret, img = cam.read()

        with the_lock:
            low_image[:] = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            low_image[:] = cv2.equalizeHist(low_image)

        if high_proc is None:
            high_proc = mp.Process(target=high_level_tracker, args=(low_image, stopping, the_lock, possible_targets, cascade,))
            high_proc.start()

        with the_lock:
            if len(possible_targets) > 0:
                for rect in possible_targets:
                    if contains(targets, rect):
                        continue
                    targets.append((rect, 0, np.zeros(2)))
                possible_targets[:] = []

        vis = img.copy()
        next_targets = []

        for rect, misses, velocity in targets:
            x1, y1, x2, y2 = rect
            with the_lock:
                roi = low_image[max(0, y1-BUFFER):min(width, y2+BUFFER), max(0, x1-BUFFER):min(height, x2+BUFFER)]

            # draw_rects(vis, [[max(0, x1-BUFFER), max(0, y1-BUFFER), min(height, x2+BUFFER), min(width, y2+BUFFER)]], (255,0,0))

            subt = clock()
            s, c = size_and_center(rect)
            subtargets = detect(roi.copy(), cascade_nested, size=(max(30, s[0]-REFIND_BUFFER), max(30, s[1]-REFIND_BUFFER)))
            # with the_lock:
            #     print "subtarget detect: ", clock() - subt
            if len(subtargets) == 1:
                if not contains(next_targets, subtargets[0]):
                    sx1, sy1, sx2, sy2 = subtargets[0]
                    fixed_rect = [max(0, x1-BUFFER)+sx1,max(0, y1-BUFFER)+sy1,max(0, x1-BUFFER)+sx2,max(0, y1-BUFFER)+sy2]

                    s_last, c_last = size_and_center(fixed_rect)

                    next_targets.append((fixed_rect, 0, VELOCITY_DECAY*velocity+(1-VELOCITY_DECAY)*np.array(diff(c_last, c))))
                vis_roi = vis[max(0, y1-BUFFER):min(width, y2+BUFFER), max(0, x1-BUFFER):min(height, x2+BUFFER)]
                draw_rects(vis_roi, subtargets, (0, 255, 0))
            else:
                # draw_rects(vis, [rect], (0,0,255))
                if misses < MAX_MISSES:
                    next_targets.append((rect, misses+1, np.zeros(2)))

        targets = next_targets
        if is_auto:
            if firing and not primed:
                launcher.prime()
                primed = True
                locked_counter = 0
            else: # either not firing, or already primed
                last_cmd_sent = targeter.update_targets(targets)
                if last_cmd_sent == STOP and len(targets):
                    locked_counter += 1
                if locked_counter > 5 and firing and primed:
                    print "firing"
                    lolz = threading.Thread(target=lolz_thread, args=("pics/%d" % int(time.time()), cam))
                    lolz.start()
                    launcher.fire()
                    lolz.join()

                    primed = False
                    locked_counter = 0

            # draw_command(vis, last_cmd_sent)
        # print "targets: ", len(targets)

        dt = clock() - t
        # WARNING: DO NOT RE ENABLE
        # with the_lock:
        #     if dt*1000 > 30:
        #         print "long frame!"
        #         print "time: ", dt*1000 
        draw_str(vis, (20, 20), 'time: %.1f ms' % (dt*1000))

        cv2.imshow('facedetect', vis)

        key = cv2.waitKey(max(1,10-int(dt)))
        if key == 27:
            with the_lock:
                stopping.value = chr(1)
            with controller_cv:
                controller_cv.notify()
            high_proc.join()
            # controller_thread.join()
            break
        elif key == ord('a'):
            is_auto = not is_auto
            print "AUTONOMOUS: ", is_auto
        elif key == ord('t'):
            firing = not firing
            print "LIVE FIRE: ", firing
    cv2.destroyAllWindows()
