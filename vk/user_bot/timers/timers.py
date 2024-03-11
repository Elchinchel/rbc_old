import json
from asyncio import Event, sleep, Task, CancelledError
from datetime import datetime
import traceback
from lib.microvk.api import VkApiResponseException
from threading import Thread
from time import time as timenow
from os.path import dirname, join
from typing import List, Tuple, Union

from database.driver import VkDB
from lib.microvk import VkApi
from lib.wtflog import get_boy_for_warden
from lib.asyncio_utils import wait_for_event, start_coro

from vk.user_bot import ND, dlp

logger = get_boy_for_warden('TIMER', 'Таймеры')

path = join(dirname(__file__), 'timer_list.json')

_timers: List['Timer'] = []
_cycles: List['Cycle'] = []

_timers_updated = Event()

__timer_counter = 0


def _get_count() -> int:
    global __timer_counter
    __timer_counter += 1
    return __timer_counter


def load_timers() -> None:
    global _timers
    global _cycles
    with open(path, 'r', encoding='utf-8') as file:
        data = json.loads(file.read())
    _timers = [Timer.from_dict(t) for t in data['timers']]
    _cycles = [Cycle.from_dict(t) for t in data['cycles']]


def save_timers() -> None:
    data = {
        'timers': [t.to_dict() for t in _timers],
        'cycles': [t.to_dict() for t in _cycles]
    }
    with open(path, 'w', encoding='utf-8') as file:
        file.write(json.dumps(data, ensure_ascii=False, indent=4))


class Timer:
    ident: int = 1
    user_id: int
    target_time: int
    data: Tuple[ND, VkDB, VkApi]
    msg: dict

    def __init__(self, nd: ND, msg: dict, delay: int):
        self.data = (
            [0, nd[1], nd[2], nd[3], nd[4], msg['command'], nd[6]],
            nd.db,
            nd.vk
        )
        self.msg = msg
        self.target_time = round(timenow() + delay)
        self.add(nd.db.user_id)

    def add(self, user_id: int):
        for timer in _timers:
            if timer.user_id == user_id:
                self.ident = timer.ident + 1
        self.user_id = user_id
        _timers.append(self)
        _timers_updated.set()
        save_timers()

    def __call__(self):
        Thread(target=dlp.launch,
               args=(self.data) + (timenow(), self.msg),
               name=f"Timer Executor #{_get_count()}").start()
        self.remove()

    def remove(self):
        _timers.remove(self)
        save_timers()

    def to_dict(self) -> dict:
        data = {}
        data['msg'] = self.msg
        data['update'] = self.data[0]
        data['user_id'] = self.user_id
        data['target_time'] = self.target_time
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Timer':
        db = VkDB(data['user_id'])
        nd = ND(data['update'], db, VkApi(db.access_token, True), timenow(), data['msg'])  # noqa
        timer = cls(nd, data['msg'], 0)
        timer.target_time = data['target_time']
        return timer


class Cycle(Timer):
    delay: int
    is_running: bool
    task: Task

    def add(self, user_id):
        self.delay = round(self.target_time - timenow())
        for cycle in _cycles:
            if cycle.user_id == user_id:
                self.ident = cycle.ident + 1
        self.task = start_coro(self.runner())
        self.user_id = user_id
        _cycles.append(self)

    def __call__(self):
        Thread(target=self._run,
               name=f"Cycle Timer Executor #{_get_count()}").start()

    def _run(self):
        try:
            dlp.launch(*self.data, timenow(), self.msg)
        except VkApiResponseException as e:
            logger.warning(f'Циклотаймер #{self.ident} UID: {self.user_id}\n'
                           f'Ошибка VK #{e.error_code}: {e.error_msg}')
        except Exception:
            logger.error(f'Циклотаймер #{self.ident} UID: {self.user_id}\n' +
                         traceback.format_exc())
            self.remove()

    async def runner(self):
        self.is_running = True
        try:
            while True:
                await sleep(self.target_time - timenow())
                self.target_time = round(timenow() + self.delay)
                save_timers()
                self()
        except CancelledError:
            self.is_running = False

    def remove(self):
        _cycles.remove(self)
        save_timers()
        if self.is_running:
            self.task.cancel()

    def to_dict(self) -> dict:
        data = super().to_dict()
        data['delay'] = self.delay
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Timer':
        db = VkDB(data['user_id'])
        nd = ND(data['update'], db, VkApi(db.access_token, True), timenow(), data['msg'])  # noqa
        cycle = cls(nd, data['msg'], 0)
        cycle.target_time = data['target_time']
        cycle.delay = data['delay']
        return cycle


def get_cycles(uid) -> Tuple[Union[str, None], int]:
    msg = ''
    count = 0
    for timer in _cycles:
        if timer.user_id != uid: continue  # noqa
        date = datetime.fromtimestamp(timer.target_time).strftime("%d.%m в %H:%M:%S")  # noqa
        msg += (
            f"#{timer.ident} - {timer.msg['command']} ({date}|каждые {timer.delay} сек.)\n"  # noqa
        )
        count += 1
    return (msg, count) if count > 0 else (None, 0)


def get_timers(uid) -> Union[str, None]:
    msg = ''
    count = 0
    for timer in _timers:
        if timer.user_id != uid: continue  # noqa
        date = datetime.fromtimestamp(timer.target_time).strftime("%d.%m в %H:%M:%S")  # noqa
        msg += f"#{timer.ident} - {timer.msg['command']} ({date})\n"
        count += 1
    return (msg, count) if count > 0 else (None, 0)


def del_timer(uid: int, ident: int, cycle: bool) -> bool:
    removed = False
    timers = _cycles if cycle else _timers
    for timer in timers:
        if timer.user_id == uid and timer.ident == ident:
            timer.remove()
            removed = True
    return removed


async def async_timers_checker():
    while True:
        sleep_time = 2e10
        time = timenow()
        for timer in _timers:
            if timer.target_time - time < sleep_time:
                sleep_time = timer.target_time - time
        for timer in _timers:
            if timer.target_time - time <= 0:
                timer()
        await wait_for_event(_timers_updated, sleep_time)
        _timers_updated.clear()


try:
    load_timers()
except FileNotFoundError:
    with open(path, 'w', encoding='utf-8') as file:
        file.write(json.dumps({'timers': [], 'cycles': []}, indent=4))
    load_timers()
