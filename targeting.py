import random
import time
import heapq

from usbturret import LEFT, RIGHT, UP, DOWN, STOP
from client import RemoteLauncher
from util import size_and_center, norm, diff

# Exposure auto priority 1 -> 0
# white balance temperature, auto 1 -> 0

# TODO set tolerances based on face size
TOLERANCE = 50
SUBTOLERANCE_X = TOLERANCE*0.25
SUBTOLERANCE_Y = TOLERANCE*1.0
MOVE_SLEEP_TIME = 0.02
REFRESH_FREQUENCY = 0.1

class Targeter(object):
    def __init__(self, xmax, ymax):
        print xmax, ymax
        self.center = (xmax / 2., ymax / 2.)
        self.correction = 0
        self.target = None
        self.cmd_queue = []
        self.last_time = time.time()

        self.launcher = RemoteLauncher()

    def update_target_rect(self, rect_misses):
        if rect_misses[1] == 0:
            size, center = size_and_center(rect_misses[0])
            self.target = center
        else:
            self.target = None

    def update_targets(self, targets):
        if time.time() - self.last_time <= REFRESH_FREQUENCY:
            return
        if len(targets) == 0:
            self.target = None
        elif len(targets) == 1:
            self.update_target_rect(targets[0])
        else:
            if self.target is None:
                self.update_target_rect(random.choice(targets))
            else:
                # multiple targets, and we have an old target
                # TODO choose new target closest to target here
                self.update_target_rect(targets[0])

        last_command_sent = self.visual_servo()
        self.last_time = time.time()
        return last_command_sent

    def stop(self):
        self.launcher.send_command(STOP)

    def visual_servo(self):
        if self.target is None:
            self.launcher.send_command(STOP)
            return STOP

        delta = diff((self.center[0], self.center[1] + self.correction), self.target)
        print delta[0], delta[1], norm(delta)
        if norm(delta) < TOLERANCE:
            self.launcher.send_command(STOP)
            return STOP
        else:
            current_cmd = 0
            cmd_to_add = None
            if delta[0] < -SUBTOLERANCE_X:
                cmd_to_add = LEFT
            elif delta[0] > SUBTOLERANCE_X:
                cmd_to_add = RIGHT

            if cmd_to_add:
                heapq.heappush(self.cmd_queue, (MOVE_SLEEP_TIME, cmd_to_add))
                current_cmd |= cmd_to_add

            if delta[1] < -SUBTOLERANCE_Y:
                cmd_to_add = UP
            elif delta[1] > SUBTOLERANCE_Y:
                cmd_to_add = DOWN
                
            if cmd_to_add:
                heapq.heappush(self.cmd_queue, (0.1*MOVE_SLEEP_TIME, cmd_to_add))
                current_cmd |= cmd_to_add

            last_cmd_sent = current_cmd

            start_time = time.time()
            while self.cmd_queue:
                self.launcher.send_command(STOP)
                self.launcher.send_command(current_cmd)
                sleep_time, cmd_to_remove = heapq.heappop(self.cmd_queue)
                current_cmd ^= cmd_to_remove
                time.sleep(max(0.0,sleep_time - (time.time() - start_time)))
            # self.launcher.send_command(STOP)
            return last_cmd_sent
        # TODO adjust target based on face size
