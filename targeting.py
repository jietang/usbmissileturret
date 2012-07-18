import random
import time

from usbturret import LEFT, RIGHT, UP, DOWN, STOP
from util import size_and_center, norm, diff

# Exposure auto priority 1 -> 0
# white balance temperature, auto 1 -> 0

# TODO set tolerances based on face size
TOLERANCE = 50
SUBTOLERANCE_X = TOLERANCE*0.25
SUBTOLERANCE_Y = TOLERANCE*1.0
MAX_MOVE_SLEEP_TIME = 0.04
P_MOVE_SLEEP_X = 0.000005
REFRESH_FREQUENCY = 0.1

class Targeter(object):
    def __init__(self, xmax, ymax, send_cmd_fn):
        print xmax, ymax
        self.center = (xmax / 2., ymax / 2.)
        self.correction = 0
        self.target = None
        self.last_time = time.time()

        self.send_cmd_fn = send_cmd_fn

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
        self.send_cmd_fn(0.0, 0.0, STOP)

    def visual_servo(self):
        if self.target is None:
            self.stop()
            return STOP

        delta = diff((self.center[0], self.center[1] + self.correction), self.target)
        if norm(delta) < TOLERANCE:
            self.stop()
            return STOP
        else:
            current_cmd = 0

            cur_time = time.time()
            timeout_x = 0.0
            timeout_y = 0.0

            cmd_to_add = None
            if delta[0] < -SUBTOLERANCE_X:
                cmd_to_add = LEFT
            elif delta[0] > SUBTOLERANCE_X:
                cmd_to_add = RIGHT

            if cmd_to_add:
                timeout_x = min(abs(delta[0])*P_MOVE_SLEEP_X, MAX_MOVE_SLEEP_TIME)
                print "move time: ", abs(delta[0])*P_MOVE_SLEEP_X
                current_cmd |= cmd_to_add

            # cmd_to_add = None
            # if delta[1] < -SUBTOLERANCE_Y:
            #     cmd_to_add = UP
            # elif delta[1] > SUBTOLERANCE_Y:
            #     cmd_to_add = DOWN
                
            # if cmd_to_add:
            #     timeout_y = 0.1*MOVE_SLEEP_TIME
            #     current_cmd |= cmd_to_add
            self.send_cmd_fn(timeout_x + cur_time, timeout_y + cur_time, current_cmd)
            return current_cmd
        # TODO adjust target based on face size
