import socket

from usbturret import LEFT, RIGHT, UP, DOWN, STOP
from server import LAUNCHER_EXIT

class RemoteLauncher(object):
    def __init__(self, address=("localhost", 9999)):
        self.address = address
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.last_command = None

    def _send(self, data):
        # if data == self.last_command:
        #     return
        # else:
        #     self.last_command = data
        if 1:
            self.socket.sendto(data, 0, self.address)

    def send_command(self, c):
        self._send(str(c))

    def fire(self):
        pass

    def prime(self):
        pass

    def shutdown(self):
        self._send(LAUNCHER_EXIT)

if __name__=="__main__":
    launcher = RemoteLauncher()
    launcher.send_command(LEFT)
    launcher.send_command(RIGHT)
    launcher.send_command(UP)
    launcher.send_command(DOWN)
    launcher.send_command(STOP)
