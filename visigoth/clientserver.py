import time
import socket
import threading
import Queue as queue


class SocketThread(threading.Thread):

    NEW_SCREEN, PARAM_REQUEST, NEW_PARAMS, OLD_PARAMS = "1234"

    def __init__(self):

        super(SocketThread, self).__init__()
        self.alive = threading.Event()
        self.alive.set()

    def join(self, timeout=None):

        self.alive.clear()
        threading.Thread.join(self, timeout)


class SocketClientThread(SocketThread):

    def __init__(self):

        pass

    def run(self):

        try:

            while self.alive.isSet():

                try:
                    kind, size = self.socket.recv(2)
                except socket.timeout:
                    time.sleep(.01)  # TODO make a parameter
                    continue

                # --- Handle the incoming data

                # Update gaze and stimulus information
                if kind == self.NEW_SCREEN:
                    try:
                        data = self.socket.recv(int(size))
                    except socket.timeout:
                        continue

                # Send current parameters up to the server
                elif kind == self.PARAM_REQUEST:

                    try:
                        new_params = self.param_q.get(block=False)
                        data = (self.NEW_PARAMS
                                + str(len(new_params))
                                + new_params)
                    except queue.Empty:
                        data = self.OLD_PARAMS + "0"
                    self.socket.sendall(data)

        finally:

            self.socket.close()


class SocketServerThread(SocketThread):

    def __init__(self, exp):

        self.screen_q = exp.screen_q
        self.param_q = exp.param_q
        self.cmd = exp.cmd_q

    def run(self):

        try:

            while self.alive.isSet():

                # Pass new screen information to the client
                try:
                    screen = self.screen_q.get(block=False)
                    data = (self.NEW_SCREEN
                            + str(len(screen))
                            + screen)
                    self.socket.sendall(data)
                    continue

                except queue.Empty:
                    pass

                # Check if it's time to get new parameters
                try:
                    cmd = self.cmd_q.get(block=False)

                    if cmd == self.PARAM_REQUEST:
                        data = self.PARAM_REQUEST + "0"
                        self.socket.sendall(data)

                        kind, size = self.socket.recv(2)
                        if kind == self.NEW_PARAMS:
                            try:
                                data = self.socket.recv(int(size))
                                self.param_q.put(data)
                            except socket.timeout:
                                continue
                        elif kind == self.OLD_PARAMS:
                            self.param_q.put("")

                except queue.Empty:
                    pass

        finally:

            self.socket.close()
