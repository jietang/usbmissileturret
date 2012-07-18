import numpy as np
import cv2
import cv2.cv as cv

def detect(img, cascade, size=(20, 20)):
    rects = cascade.detectMultiScale(img, scaleFactor=1.1, minNeighbors=4, minSize=size, flags = cv.CV_HAAR_SCALE_IMAGE)
    if len(rects) == 0:
        return []
    rects[:,2:] += rects[:,:2]
    return rects

def draw_rects(img, rects, color):
    for x1, y1, x2, y2 in rects:
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

def size_and_center(rect):
    x1, y1, x2, y2 = rect
    return (x2 - x1, y2 - y1), ((x1+x2)/2, (y1+y2)/2)

def norm(vec):
    return np.sqrt(sum(x*x for x in vec))

def diff(s1, s2):
    return (s2[0] - s1[0], s2[1] - s1[1])

def compare(r1, r2):
    s1, c1 = size_and_center(r1)
    s2, c2 = size_and_center(r2)

    facesize = 0.5*(norm(s1) + norm(s2))

    return 1/facesize * norm(diff(s1, s2)) + 1/facesize * norm(diff(c1, c2))
        
def contains(targets, rect):
    for r, misses in targets:
        if compare(r, rect) < 0.75:
            return True
    return False
