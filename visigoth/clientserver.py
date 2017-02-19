import time
import socket
import threading
import Queue as queue


class SocketThread(threading.Thread):

    NEW_SCREEN, TRIAL_DATA, PARAM_REQUEST, NEW_PARAMS, OLD_PARAMS = range(5)
    HEADER_SIZE = 10

    def __init__(self):

        super(SocketThread, self).__init__()
        self.alive = threading.Event()
        self.alive.set()

    def join(self, timeout=None):

        self.alive.clear()
        threading.Thread.join(self, timeout)

    def package(self, kind, data):

        kind = str(kind)
        size = str(len(data)).zfill(self.HEADER_SIZE - 1)

        package = "".join([kind, size, data])
        return package

    def recvall(self, size, source=None):

        if source is None:
            source = self.socket

        data = ""
        missing = size - len(data)
        while missing:
            data = "".join([data, source.recv(missing)])
            missing = size - len(data)
        return data

    def read_header(self, s):

        if s:
            kind = int(s[0])
            size = int(s[1:])
        else:
            kind, size = None, None
        return kind, size


class SocketClientThread(SocketThread):

    def __init__(self, remote):

        super(SocketClientThread, self).__init__()

        self.screen_q = remote.screen_q
        self.param_q = remote.param_q
        self.trial_q = remote.trial_q

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(("localhost", 50001))
        self.socket.settimeout(.005)

    def run(self):

        try:

            while self.alive.isSet():

                try:
                    kind, size = self.read_header(
                        self.socket.recv(self.HEADER_SIZE))
                except socket.timeout:
                    time.sleep(.01)  # TODO make a parameter
                    continue

                # --- Handle the incoming data

                # Update gaze and stimulus information
                if kind is None:
                    continue
                elif kind == self.NEW_SCREEN:
                    try:
                        data = self.recvall(size)
                        self.screen_q.put(data)
                    except socket.timeout:
                        continue

                # Update trial data
                elif kind == self.TRIAL_DATA:
                    try:
                        data = self.recvall(size)
                        self.trial_q.put(data)
                    except socket.timeout:
                        continue

                # Send current parameters up to the server
                elif kind == self.PARAM_REQUEST:

                    try:
                        new_params = self.param_q.get(block=False)
                        data = self.package(self.NEW_PARAMS, new_params)
                    except queue.Empty:
                        data = self.OLD_PARAMS + "0"
                    self.socket.sendall(data)

        finally:

            self.socket.close()


class SocketServerThread(SocketThread):

    def __init__(self, exp):

        super(SocketServerThread, self).__init__()

        self.cmd_q = exp.cmd_q
        self.param_q = exp.param_q
        self.trial_q = exp.trial_q
        self.screen_q = exp.screen_q

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("localhost", 50001))
        self.socket.listen(2)

    def run(self):

        # TODO can we make it so that the client can be persistent?
        clientsocket, _ = self.socket.accept()
        clientsocket.settimeout(.2)

        try:

            while self.alive.isSet():

                # Check for a command to get new parameters from client
                try:
                    cmd = self.cmd_q.get(block=False)

                    if cmd == self.PARAM_REQUEST:

                        data = self.package(self.PARAM_REQUEST, "")
                        clientsocket.sendall(data)

                        kind, size = self.read_header(
                            clientsocket.recv(self.HEADER_SIZE))
                        if kind == self.NEW_PARAMS:
                            try:
                                data = self.recvall(size, clientsocket)
                                self.param_q.put(data)
                            except socket.timeout:
                                continue
                        elif kind == self.OLD_PARAMS:
                            self.param_q.put("")

                except queue.Empty:
                    pass

                # Check if we have a trial result to send to the client
                try:
                    trial_data = self.trial_q.get(block=False)
                    data = self.package(self.TRIAL_DATA, trial_data)
                    clientsocket.sendall(data)

                except queue.Empty:
                    pass

                # Pass new screen information to the client
                try:

                    screen = self.screen_q.get(block=False)
                    data = self.package(self.NEW_SCREEN, screen)
                    clientsocket.sendall(data)
                    continue

                except queue.Empty:
                    pass

        finally:

            self.socket.close()
