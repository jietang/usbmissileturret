import usb.core, time, usb
import struct

DOWN = 1
UP = 2
LEFT = 4
RIGHT = 8
MOVE_MASK = 15
FIRE = 16
STOP = 32
PRIME = 64 # made up, doesn't really need to be 64
SHUTDOWN = 128
USB_CMD_TIMEOUT = 100
FIRE_TIMEOUT = 4
PRIME_TIMEOUT = 1.2
POLL_DELAY = 0.2

def validate_command(c, last_status=0):
    if (c & UP) and (c & DOWN):
        return STOP
    if (c & LEFT) and (c & RIGHT):
        return STOP
    if (c & STOP):
        return STOP
    for cmd in (UP, DOWN, LEFT, RIGHT):
        if (last_status & cmd) and (c & cmd):
            c = c ^ cmd
    return c

def initialize_usb_launcher():
    dev = usb.core.find(idVendor=0x2123, idProduct=0x1010)
    try:
        dev.set_configuration()
    except usb.core.USBError, e:
        if e.errno == 16:
            dev.detach_kernel_driver(0)
            dev.set_configuration()
        else:
            raise
    except AttributeError:
        print "Could not detect USB Missile Launcher"
        raise
    return dev

def get_launcher_status(dev):
    # 8 -- too far right
    # 4 -- too far left
    # 2 -- too far up
    # 1 -- too far down
    query = struct.pack("!BBBBBBBB", 1, 0, 0, 0, 0, 0, 0, 0)
    res = dev.ctrl_transfer(0x21, 0x09, 0x0200, 0x0000, query)
    if res:
        try:
            status = struct.unpack("!BBBBBBBB", dev.read(129, 8, 0, USB_CMD_TIMEOUT))
            # print status
            return status[1]
        except usb.core.USBError, e:
            if e.errno == 110:
                print "timeout"
            else:
                raise
    return 0

class FakeLauncher(object):
    def send_command(self, c):
        print "sending command: ", c

    def fire(self):
        print "fire"

    def prime (self):
        print "prime"

    def shutdown(self):
        print "shutdown"

class USBMissileLauncher(object):
    def __init__(self):
        self.dev = initialize_usb_launcher()
        self.last_status = get_launcher_status(self.dev)

    def send_command(self, c):
        c = validate_command(c, self.last_status)
        if c:
            bytes = [0]*8
            bytes[0] = 2
            bytes[1] = c
            try:
                self.dev.ctrl_transfer(0x21, 0x09, 0x0200, 0x0000, struct.pack("!"+"B"*8, *bytes), USB_CMD_TIMEOUT)
            except usb.core.USBError, e:
                if e.errno == 110:
                    print "timeout"
                else:
                    raise
            self.last_status = get_launcher_status(self.dev)
            return self.last_status
        return self.last_status

    def status(self):
        return get_launcher_status(self.dev)

    def fire(self, timeout=FIRE_TIMEOUT):
        self.send_command(FIRE)
        total_time = 0

        while not (self.last_status & FIRE) and total_time < timeout:
            time.sleep(POLL_DELAY)
            total_time += POLL_DELAY
            print total_time
            self.last_status = get_launcher_status(self.dev)
        # wait a bit after getting the ack
        time.sleep(POLL_DELAY)
        self.send_command(STOP)

    def prime(self):
        self.fire(timeout=PRIME_TIMEOUT)

    def shutdown(self):
        pass

if __name__=="__main__":
    
    launcher = USBMissileLauncher()
    launcher.send_command(LEFT)
    time.sleep(0.5)
    launcher.send_command(STOP)

