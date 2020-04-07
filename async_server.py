#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports
from collections import deque


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").replace('\r\n', '').replace('\n', '')
                if login in [client.login for client in self.server.clients]:
                    self.transport.write(f"Login {login} has already taken, try another one please\n".encode())
                    self.connection_lost()
                else:
                    self.login = login
                    self.transport.write(
                        f"Hi, {self.login}!\n".encode()
                    )
                    self.send_history()
            else:
                self.transport.write(f"Wrong login!!!\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("New user has just connected ...")

    def connection_lost(self):
        self.server.clients.remove(self)
        if self.login is not None:
            print(f'{self.login} - logged off ... ')
        else:
            print("Unidentified user disconnected ... ")

    def send_message(self, content: str):
        message = f"<{self.login}>:  {content}\n".replace("\n\n", "\n")
        self.server.history.append(message)

        for user in self.server.clients:
            if user is not self:
                user.transport.write(message.encode())

    def send_history(self):
        for message in self.server.history:
            self.transport.write(message.encode())


class Server:
    clients: list
    history: deque = deque(maxlen=10)

    def __init__(self):
        self.clients = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        event_loop = asyncio.get_running_loop()

        coroutine = await event_loop.create_server(
            self.build_protocol,
            "127.0.0.1",
            9999
        )

        print("Server is running ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Server been stopped manually")
