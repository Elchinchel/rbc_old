from asyncio import start_server, Queue
from asyncio.streams import StreamReader, StreamWriter
from lib.asyncio_utils import start_coro
from typing import List, Callable
import json

from .lp import send_to_lp


_SERVER_PORT = 55023


_is_copy_server_running = False

_copy_pollers: List['_CopyPoller'] = []


class Listener:
    destructor: Callable
    queue: Queue
    run: bool

    def __init__(self, uid: int):
        self.queue = Queue()
        self.destructor = _CopyPoller(uid, self)

    async def listen(self):
        self.run = True
        while self.run:
            yield await self.queue.get()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.run = False
        self.destructor()


class _CopyPoller:
    uid: int
    queue: Queue
    listeners: List[Listener] = []

    def __new__(cls, uid: int, listener: Listener) -> '_CopyPoller':
        for poller in _copy_pollers:
            if poller.uid == uid:
                poller.listeners.append(listener)
                return poller.get_destructor(listener)
        poller = object.__new__(cls)
        poller.__init__(uid, listener)
        return poller.get_destructor(listener)

    def __init__(self, uid: int, listener: Listener) -> None:
        if not _is_copy_server_running:
            _start_server()
        self.uid = uid
        self.queue = Queue()
        self.listeners.append(listener)
        start_coro(self.runner())
        _copy_pollers.append(self)
        send_to_lp('copy_events', uid=uid)

    def get_destructor(self, listener: Listener) -> Callable:
        def destructor():
            self.listeners.remove(listener)
        return destructor

    async def runner(self):
        while self.listeners != []:
            for update in await self.queue.get():
                for listener in self.listeners:
                    listener.queue.put_nowait(update)
        _copy_pollers.remove(self)


async def _connection_handler(reader: StreamReader, writer: StreamWriter):
    data = json.loads(await reader.read(8192))
    for poller in _copy_pollers:
        if poller.uid == data['uid']:
            poller.queue.put_nowait(data['updates'])
            writer.write(b"\"ok\"")
            writer.close()
            return
    writer.write(b"\"stop\"")
    writer.close()


def _start_server():
    global _is_copy_server_running
    start_coro(start_server(_connection_handler, 'localhost', _SERVER_PORT))
    _is_copy_server_running = True
    send_to_lp('start_copy_server', addr=f'localhost:{_SERVER_PORT}')
