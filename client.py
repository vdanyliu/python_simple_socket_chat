import asyncio
import logging
from asyncio import StreamReader, StreamWriter, Task, CancelledError

import aioconsole

from socet_protocol import SocketProtocol, Message

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(level=logging.DEBUG)


class Connection:
    def __init__(self, reader: StreamReader, writer: StreamWriter):
        self.protocol = SocketProtocol(reader, writer)
        self.name = input("Enter your name:\n")
        self._serving_tasks: list[Task] = list()

    async def serve(self):
        await self.protocol.write(Message(self.name, "- new user"))
        read_task = asyncio.create_task(self._read_forever())
        write_task = asyncio.create_task(self._write_forever())
        self._serving_tasks = [read_task, write_task]
        for task in self._serving_tasks:
            task.add_done_callback(self._cancel_serve)
        try:
            await asyncio.gather(*(read_task, write_task))
        except CancelledError:
            LOGGER.info("Connect are closed")
        finally:
            await self.protocol.close()

    def _cancel_serve(self, *args):
        for task in self._serving_tasks[:]:
            task.cancel()
            self._serving_tasks.remove(task)

    async def _read_forever(self):
        data: Message
        while data := await self.protocol.read():
            print(data)

    async def _write_forever(self):
        while input_str := await aioconsole.ainput():
            await self.protocol.write(Message(sender=self.name, msg=input_str))


async def amain():
    user_host = input("Input host or press enter for localhost:\n")
    host = "127.0.0.1" if not user_host else user_host
    port = 8080
    await Connection(*await asyncio.open_connection(host=host, port=port)).serve()


if __name__ == '__main__':
    asyncio.run(amain())
