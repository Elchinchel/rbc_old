from queue import Queue
from threading import Thread
from typing import NoReturn


USE_THREADING = True


def _write_to_file(path: str, line: str) -> None:
    with open(path, 'a', encoding='utf-8') as log:
        log.write(line + '\n')


if USE_THREADING:
    _queue = Queue()

    def _writer() -> NoReturn:
        while True:
            _write_to_file(*_queue.get())

    def write(path: str, line: str) -> None:
        _queue.put((path, line))

    Thread(target=_writer, name='LoggerWriter').start()
else:
    write = _write_to_file
