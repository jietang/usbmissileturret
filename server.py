from usbturret import USBMissileLauncher

import socket
import select
import threading
import time

LAUNCHER_EXIT = "Shut"
POLL_RATE = 0.02
STATUS_INTERVAL = 0.5 # 250ms status poll

class LauncherServer(object):
    address_family = socket.AF_INET
    socket_type = socket.SOCK_DGRAM
    max_packet_size = 1024

    def __init__(self, address=("localhost", 9999)):
        self.address = address
        self.shutdown_event = threading.Event()
        self.should_shutdown = False

        self.socket = socket.socket(self.address_family, self.socket_type)
        print "bound to: ", address
        self.socket.bind(self.address)
        self.address = self.socket.getsockname()
        self.launcher = USBMissileLauncher()
        self.last_status_time = 0

    def fileno(self):
        return self.socket.fileno()

    def serve(self, sleep=0.01):
        self.shutdown_event.clear()

        try:
            while not self.should_shutdown:
                t = time.time()
                if t - self.last_status_time > STATUS_INTERVAL:
                    # heartbeat
                    self.launcher.status()

                r, w, e = select.select([self], [], [], sleep)
                if self in r:
                    self.handle_request()

                # sleep
                time.sleep(max(0.001, POLL_RATE - (time.time() - t)))
        finally:
            self.socket.close()
            self.should_shutdown = False
            self.shutdown_event.set()

    def handle_request(self):
        try:
            data, address = self.socket.recvfrom(self.max_packet_size)
            print "processing: ", data
            if data == LAUNCHER_EXIT:
                self.should_shutdown = True
            else:
                self.launcher.send_command(int(data))

        except socket.error:
            return

if __name__=="__main__":
    serve = LauncherServer()
    serve.serve()

