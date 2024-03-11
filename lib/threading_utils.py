from threading import Thread
from time import sleep
from queue import Queue
from typing import Callable, NoReturn, Tuple, List


WORKERS = 4


_workers: List['Worker'] = []


class Worker:
    ready: bool
    queue: Queue

    def __init__(self, name: str):
        self.queue = Queue(1)
        Thread(target=self.runner, name=name).start()

    def runner(self) -> NoReturn:
        while True:
            self.ready = True
            data: Tuple[Callable, tuple, dict] = self.queue.get()
            self.ready = False
            data[0](*data[1], **data[2])


def run_in_pool(func: Callable, *args, **kwargs) -> None:
    for worker in _workers:
        if worker.ready:
            worker.queue.put((func, args, kwargs))
            return
    start_func(func, *args, **kwargs)


def _do_with_delay(func: Callable, delay: float, *args) -> None:
    sleep(delay)
    func(*args)


def do_with_delay(func: Callable, delay: float, *args) -> None:
    Thread(target=_do_with_delay, args=(func, delay, *args)).start()


def start_func(func: Callable, *args, **kwargs) -> None:
    Thread(target=func, args=args, kwargs=kwargs).start()


for i in range(WORKERS):
    _workers.append(Worker(f'Thread Worker #{i}'))
