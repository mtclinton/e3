import socket
import e3.loop as loop




class Server():

    def __init__(self):
        self.loop = loop.Loop.instance()
        self._socket = None

    def listen(self, port):
        assert not self._socket
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.setblocking(False)
        self._socket.bind(("", port))
        self._socket.listen(128)
        self.loop.register_handler(self._socket.fileno())
        self.loop.add_handler(self._socket.fileno(), self.start_server)

    def start_server(self):
        connection, address = self._socket.accept()
        connection.setblocking(0)
        self.loop.handle_connection(connection)
