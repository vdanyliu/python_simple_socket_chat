import logging
import pickle
from asyncio import StreamReader, StreamWriter
from dataclasses import dataclass
from typing import Optional

LOGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
_ENCODING = "utf-8"


@dataclass(frozen=True)
class Message:
    sender: str
    msg: str

    def __str__(self):
        return f"[{self.sender}]: {self.msg}"


class SocketProtocol:
    _ENCODING = "utf-8"
    _header_len = 64

    def __init__(self, reader: StreamReader, writer: StreamWriter):
        self.reader = reader
        self.writer = writer

    async def read(self) -> Optional[Message]:
        header = await self.reader.read(self._header_len)
        try:
            data_len = int(header.decode(self._ENCODING))
            data = await self.reader.read(data_len)
            return pickle.loads(data)
        except ValueError:
            return None

    async def write(self, data: Message):
        p_data = pickle.dumps(data)
        data_len = len(p_data)
        header = str(data_len).encode(self._ENCODING).zfill(self._header_len)
        self.writer.write(data=header+p_data)
        await self.writer.drain()

    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()
