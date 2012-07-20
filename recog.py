from collections import defaultdict
import socket
import threading
import time

import cv2
import cv2.cv as cv
import numpy


RECOG_SIZE = 32
NUM_PIXELS = RECOG_SIZE * RECOG_SIZE

NUM_MODELS = 3

LABELS = ["Jie", "Karl"]
LABEL_COLORS = [(100, 255, 100), (100, 100, 255)]

HOSTPORT = ("karl-desktop0", 2233)


def scale_to_recognizer_input_size(image):
    mat = cv.CreateMat(RECOG_SIZE, RECOG_SIZE, cv.CV_8UC1)
    cv.Resize(image, mat)
    return mat


class Recognizer(object):
    def __init__(self):
        print "connecting to recognizer...",
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(HOSTPORT)
        self.rfile = self.sock.makefile("r")
        print "connected."
        print "sleeping to let server train models...",
        time.sleep(5)
        print "done."

    def close(self):
        print "closing connection to recognizer...",
        self.rfile.close()
        self.sock.close()
        print "closed."
        self.sock = None
        
    def predict(self, image):
        mat = scale_to_recognizer_input_size(image)

        # there must be a better way to do this
        data = "".join("".join(chr(int(mat[i, j])) for j in xrange(RECOG_SIZE)) for i in xrange(RECOG_SIZE))

        assert len(data) == NUM_PIXELS, "data had wrong length: %d" % len(data)
        self.sock.sendall(data)

        results = []
        for i in xrange(NUM_MODELS):
            label = int(self.rfile.readline().strip())
            confidence = float(self.rfile.readline().strip())
            results.append((label, confidence))
        return results


class RecognizerManager(object):
    def __init__(self):
        self.r = None

    def __enter__(self):
        self.r = Recognizer()
        return self

    def __exit__(self, *exc_info):
        self.r.close()
        self.r = None

    def predict(self, image):
        assert self.r, "you must call predict inside a 'with RecognizerManager():' block"
        return self.r.predict(image)


def get_overall_prediction(predictions):
    label_counts = defaultdict(int)
    for label, confidence in predictions:
        label_counts[label] += 1
    return max(xrange(len(LABELS)), key=lambda x: label_counts[x])


