import asyncio
from typing import Awaitable, Any


aio_loop = asyncio.get_event_loop()


def create_task(coro: Awaitable) -> asyncio.Task:
    'Планирует выполнение корутины в ближайшее время, не блокирует поток'
    return aio_loop.create_task(coro)


def start_coro(coro: Awaitable) -> asyncio.Future:
    'Начинает выполнение корутины, возвращает `asyncio.Future`'
    return asyncio.run_coroutine_threadsafe(coro, aio_loop)


def wait_coro(coro: Awaitable) -> Any:
    'Блокирует выполнение потока до выполнения корутины, возвращает результат'
    return asyncio.run_coroutine_threadsafe(coro, aio_loop).result()


async def wait_for_event(event: asyncio.Event, timeout: float) -> bool:
    try:
        await asyncio.wait_for(event.wait(), timeout)
    except asyncio.TimeoutError:
        pass
    return event.is_set()
