import time
from usbturret import LEFT, RIGHT, UP, DOWN, STOP, USBMissileLauncher, FIRE

launcher = USBMissileLauncher()

def reset_to_lower_left():
    down_done = False
    left_done = False
    while not down_done or not left_done:
        cmd = 0
        if not down_done:
            cmd = cmd | DOWN
        if not left_done:
            cmd = cmd | LEFT
        status = launcher.send_command(cmd)
        if status & DOWN:
            down_done = True
        if status & LEFT:
            left_done = True

def move_for_time(secs, cmd):
    start = time.time()
    # while time.time() - start < secs:
    #     status = launcher.send_command(cmd)

    status = launcher.send_command(cmd)
    time.sleep(max(0, secs - (time.time() - start)))
    launcher.send_command(STOP)

# reset_to_lower_left()
# move_for_time(3, RIGHT)
# move_for_time(1, UP)

# launcher.send_command(RIGHT)
# time.sleep(0.2)
# launcher.send_command(FIRE | RIGHT)
# time.sleep(1)
# launcher.send_command(STOP)

# move_for_time(0.1, RIGHT)
# for i in range(100):
#     status = launcher.send_command(RIGHT)
# status = launcher.send_command(STOP)
    # move_for_time(0.01, RIGHT)

