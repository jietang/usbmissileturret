from shutil import copyfileobj
from SocketServer import ThreadingMixIn, TCPServer, StreamRequestHandler
import subprocess
import sys
import threading
import traceback

class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    pass

'''
def sock_to_fileobj(sock, fileobj):
    while True:
        data = sock.recv(4096)
        if not data:
            break
        fileobj.write(data)

def fileobj_to_sock(fileobj, sock):
    while True:
        data = fileobj.read(4096)
        if not data:
            break
        sock.sendall(data)
'''

def run(port, cmd):
    class ProcTcpHandler(StreamRequestHandler):
        def handle(self):
            print "starting subprocess..."
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
            print "started."
            try:
                print "starting input/output threads..."
                t_in = threading.Thread(target=copyfileobj, args=(self.request.makefile("r"), proc.stdin))
                t_out = threading.Thread(target=copyfileobj, args=(proc.stdout, self.request.makefile("w")))
                for t in (t_in, t_out):
                    t.daemon = True
                    t.start()
                print "started."
                print "waiting for input thread to finish..."
                t_in.join()
                print "done."
            except:
                print "exception!"
                traceback.print_exc()
            finally:
                proc.stdin.close()
                print "closed pipe to subprocess. waiting for it to terminate..."
                proc.wait()
                print "terminated with exit code", proc.returncode
                t_out.join()
    ThreadedTCPServer(('', port), ProcTcpHandler).serve_forever()

if __name__ == "__main__":
    port = int(sys.argv[1])
    cmd = sys.argv[2:]
    assert cmd
    run(port, cmd)

