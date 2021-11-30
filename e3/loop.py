import socket, select

EOL1 = b'\n\n'
EOL2 = b'\n\r\n'

class Loop():

    def __init__(self):

        self._epoll = select.epoll()
        self.connections = {}
        self.requests = {}
        self.responses = {}

        self.server_fd = -1

        self._handlers = {}


    @classmethod
    def instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance

    def register_handler(self, fd):
        self._epoll.register(fd, select.EPOLLIN | select.EPOLLET)
        self.server_fd = fd

    def add_handler(self, fd, handler):
        self._handlers[fd] = handler

    def handle_connection(self, connection):
        self._epoll.register(connection.fileno(), select.EPOLLIN | select.EPOLLET)
        self.connections[connection.fileno()] = connection
        self.requests[connection.fileno()] = b''

    def start(self, server):
        while True:
            events = self._epoll.poll(1)
            for fileno, event in events:
                if fileno == self.server_fd:
                    accept_connection = self._handlers[fileno]
                    accept_connection()

                elif event & select.EPOLLIN:
                    try:
                        while True:
                            self.requests[fileno] += self.connections[fileno].recv(1024)
                    except socket.error:
                        pass
                    if EOL1 in self.requests[fileno] or EOL2 in self.requests[fileno]:
                        self._epoll.modify(fileno, select.EPOLLOUT | select.EPOLLET)
                        headercontent = self.requests[fileno].decode()[:].split("\r\n")[0]
                        url = headercontent.split()[1][1:]
                        if(len(url) == 0):
                            url = "Hello add characters to your url to see the echo"
                        response = 'HTTP/1.0 200 OK\r\nDate: Mon, 1 Jan 1996 01:01:01 GMT\r\n'
                        response += 'Content-Type: text/plain\r\nContent-Length: ' + str(len(url)) + '\r\n\r\n'
                        response += url
                        self.responses[fileno] = response.encode()

                elif event & select.EPOLLOUT:
                    try:
                        while len(self.responses[fileno]) > 0:
                            byteswritten = self.connections[fileno].send(self.responses[fileno])
                            self.responses[fileno] = self.responses[fileno][byteswritten:]
                    except socket.error:
                        pass
                    if len(self.responses[fileno]) == 0:
                        self._epoll.modify(fileno, select.EPOLLET)
                        self.connections[fileno].shutdown(socket.SHUT_RDWR)

                elif event & select.EPOLLHUP:
                    self._epoll.unregister(fileno)
                    self.connections[fileno].close()
                    del self.connections[fileno]

    def stop(self, fd):
        print("stopped epoll")
        self._epoll.unregister(fd)
        self._epoll.close()

