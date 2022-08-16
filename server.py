import asyncio
import logging
from asyncio import StreamReader, StreamWriter

from socet_protocol import Message, SocketProtocol

ENCODING = "utf-8"

LOGGING = logging.getLogger(__name__)
LOGGING.setLevel(level=logging.DEBUG)


class Connection:
    server_connections: set["Connection"] = set()

    def __init__(self, reader: StreamReader, writer: StreamWriter):
        self.protocol = SocketProtocol(reader, writer)
        self.server_connections.add(self)

    async def serve(self):
        await self._listen_forever()
        await self.protocol.close()
        self.server_connections.discard(self)

    async def _listen_forever(self):
        while data := await self.protocol.read():
            await self._echo_to_all_connections(data)

    async def echo(self, data: Message):
        await self.protocol.write(data)

    async def _echo_to_all_connections(self, data: Message):
        tasks_result = await asyncio.gather(*(connection.echo(data=data) for connection in self.server_connections),
                                            return_exceptions=True)
        LOGGING.debug(tasks_result)


async def callback(reader: StreamReader, writer: StreamWriter):
    await Connection(reader, writer).serve()


async def amain():
    server = await asyncio.start_server(callback, host="0.0.0.0", port=8080)
    print(server)

    await server.serve_forever()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        pass
