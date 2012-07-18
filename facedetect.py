import multiprocessing as mp
import time
import threading

import cv2
import cv2.cv as cv
import sharedmem as shm

from common import clock, draw_str
from video import create_capture

from targeting import Targeter
from util import detect, draw_rects, size_and_center, norm, compare, contains

from usbturret import UP, DOWN, LEFT, RIGHT

help_message = '''
USAGE: facedetect.py [--cascade <cascade_fn>] [--nested-cascade <cascade_fn>] [<video_source>]
'''

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

    targeter = Targeter(height, width)

    while True:
        t = clock()
        ret, img = cam.read()
        print (clock() - t)*1000

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
                    targets.append((rect, 0))
                possible_targets[:] = []

        vis = img.copy()
        next_targets = []

        for rect, misses in targets:
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
                    next_targets.append(([max(0, x1-BUFFER)+sx1,max(0, y1-BUFFER)+sy1,max(0, x1-BUFFER)+sx2,max(0, y1-BUFFER)+sy2], 0))
                vis_roi = vis[max(0, y1-BUFFER):min(width, y2+BUFFER), max(0, x1-BUFFER):min(height, x2+BUFFER)]
                draw_rects(vis_roi, subtargets, (0, 255, 0))
            else:
                # draw_rects(vis, [rect], (0,0,255))
                if misses < MAX_MISSES:
                    next_targets.append((rect, misses+1))

        targets = next_targets
        if is_auto:
            last_cmd_sent = targeter.update_targets(targets)
            # draw_command(vis, last_cmd_sent)
        # print "targets: ", len(targets)

        dt = clock() - t
        with the_lock:
            if dt*1000 > 30:
                print "long frame!"
                print "time: ", dt*1000
        draw_str(vis, (20, 20), 'time: %.1f ms' % (dt*1000))

        cv2.imshow('facedetect', vis)

        key = cv2.waitKey(max(1,10-int(dt)))
        if key == 27:
            with the_lock:
                stopping.value = chr(1)
            high_proc.join()
            break
        elif key == ord('a'):
            is_auto = not is_auto
            print is_auto
