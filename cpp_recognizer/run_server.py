from SocketServer import ThreadingMixIn, TCPServer, StreamRequestHandler
import subprocess
import sys
import traceback

class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    pass

def run(port, cmd):
    class ProcTcpHandler(StreamRequestHandler):
        def handle(self):
            print "starting subprocess..."
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
            print "started."
            rfile = self.request.makefile("r")
            try:
                while True:
                    data = rfile.read(1024)
                    if len(data) < 1024:
                        break
                    proc.stdin.write(data)
                    self.request.sendall(proc.stdout.readline())
                    self.request.sendall(proc.stdout.readline())
                print "done."
            finally:
                proc.stdin.close()
                print "closed pipe to subprocess. waiting for it to terminate..."
                proc.wait()
                print "terminated with exit code", proc.returncode
    ThreadedTCPServer(('', port), ProcTcpHandler).serve_forever()

if __name__ == "__main__":
    port = int(sys.argv[1])
    cmd = sys.argv[2:]
    assert cmd
    run(port, cmd)

