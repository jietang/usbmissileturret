import multiprocessing as mp
import os
import socket
import subprocess
import time

import cv2
import cv2.cv as cv
import numpy
import sharedmem as shm

from common import clock, draw_str
from video import create_capture

from util import detect, draw_rects, size_and_center, norm, compare, contains

help_message = '''
USAGE: recognize.py [--cascade <cascade_fn>] [--nested-cascade <cascade_fn>] <video_source>
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
high_proc = None
the_lock = mp.Lock()
stopping = mp.Value('c', chr(0), lock=False)
manager = mp.Manager()
possible_targets = manager.list()
targets = []
is_auto = False



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


# the recognizer will be trained and run on square images this many pixels per side
RECOG_SIZE = 32
NUM_PIXELS = RECOG_SIZE * RECOG_SIZE

def scale_to_recognizer_input_size(image):
    mat = cv.CreateMat(RECOG_SIZE, RECOG_SIZE, cv.CV_8UC1)
    cv.Resize(image, mat)
    return mat

class Recognizer():
    HOSTPORT = ("karl-desktop0", 2232)

    def __init__(self):
        self.sock = None

    def __enter__(self):
        print "connecting to recognizer...",
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(Recognizer.HOSTPORT)
        self.rfile = self.sock.makefile("r")
        print "connected."
        return self

    def __exit__(self, *exc_info):
        print "closing connection to recognizer...",
        self.rfile.close()
        self.sock.close()
        print "closed."
    
    def predict(self, image):
        assert self.sock, "you must call predict inside a 'with' block"
        mat = scale_to_recognizer_input_size(image)
        data = "".join("".join(chr(int(mat[i, j])) for j in xrange(RECOG_SIZE)) for i in xrange(RECOG_SIZE))
        assert len(data) == NUM_PIXELS, "data had wrong length: %d" % len(data)
        self.sock.sendall(data)
        label = int(self.rfile.readline().strip())
        confidence = float(self.rfile.readline().strip())
        return label, confidence

if __name__ == '__main__':
    import sys, getopt
    print help_message

    args, (video_src,) = getopt.getopt(sys.argv[1:], '', ['cascade=', 'nested-cascade='])
    args = dict(args)
    cascade_fn = args.get('--cascade', "haarcascades/haarcascade_frontalface_alt.xml")

    cascade = cv2.CascadeClassifier(cascade_fn)
    cascade_nested = cv2.CascadeClassifier(cascade_fn)

    cam = create_capture(video_src)
    ret, img = cam.read()
    print ret

    width = img.shape[0]
    height = img.shape[1]
    low_image = shm.zeros(img.shape[0:2], dtype=img.dtype)

    with Recognizer() as recognizer:
        while True:
            ret, img = cam.read()
            t = clock()    

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
                        targets.append((rect, 0, None))
                    possible_targets[:] = []

            vis = img.copy()
            next_targets = []

            last_time = time.time()
            for rect, misses, _ in targets:
                x1, y1, x2, y2 = rect
                with the_lock:
                    roi = low_image[max(0, y1-BUFFER):min(width, y2+BUFFER), max(0, x1-BUFFER):min(height, x2+BUFFER)]

                # draw_rects(vis, [[max(0, x1-BUFFER), max(0, y1-BUFFER), min(height, x2+BUFFER), min(width, y2+BUFFER)]], (255,0,0))

                subt = clock()
                s, c = size_and_center(rect)
                roi_copy = roi.copy()
                subtargets = detect(roi_copy, cascade_nested, size=(max(30, s[0]-REFIND_BUFFER), max(30, s[1]-REFIND_BUFFER)))
                if len(subtargets) == 1:
                    sx1, sy1, sx2, sy2 = subtargets[0]
                    if not contains(next_targets, subtargets[0]):
                        next_targets.append(([max(0, x1-BUFFER)+sx1,max(0, y1-BUFFER)+sy1,max(0, x1-BUFFER)+sx2,max(0, y1-BUFFER)+sy2], 0, None))
                    vis_roi = vis[max(0, y1-BUFFER):min(width, y2+BUFFER), max(0, x1-BUFFER):min(height, x2+BUFFER)]
                    draw_rects(vis_roi, subtargets, (0, 255, 0))
                    
                    print "prediction:", recognizer.predict(cv.fromarray(roi[sx1:sx2, sy1:sy2]))

                else:
                    # draw_rects(vis, [rect], (0,0,255))
                    if misses < MAX_MISSES:
                        next_targets.append((rect, misses+1, None))

            targets = next_targets
            # print "targets: ", len(targets)

            dt = clock() - t
            # with the_lock:
            #     print "time: ", dt*1000
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

