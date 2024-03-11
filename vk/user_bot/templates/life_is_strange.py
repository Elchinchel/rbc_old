# называю модули как хочу
from database.client import method
from typing import List, Any
import asyncio
import time


class Rewind:
    data: Any
    desc: str
    type_: str
    ident: int = 1
    user_id: int
    expire_time: int

    def __init__(self, user_id: int, type_: str, data: Any,
                 expires_in: int = 300):
        self.expire_time = time.time() + expires_in
        self.user_id = user_id
        self.type_ = type_
        self.data = data
        for rewind in rewinds:
            if rewind.user_id == user_id:
                self.ident += 1
        self.desc = get_desc(type_, data)
        rewinds.append(self)

    def rewind_template(self):
        method.set_template(self.user_id, self.type_, self.data)

    def __call__(self):
        if self.type_ in {'common', 'voice', 'dutys'}:
            self.rewind_template()
        elif self.type_ in {'commonDelete', 'voiceDelete',
                            'dutysDelete'}:
            self.type_ = self.type_.replace('Delete', '')
            self.rewind_template()
        rewinds.remove(self)


rewinds: List[Rewind] = []


def get_desc(type_: str, data: dict) -> str:
    return {
        'common': f'Перезапись шаблона "{data["name"]}"',
        'voice': f'Перезапись голосового сообщения "{data["name"]}"',
        'dutys': f'Перезапись дежурного "{data["name"]}"',
        'anim': f'Перезапись анимки "{data["name"]}"',
        'commonDelete': f'Удаление шаблона "{data["name"]}"',
        'voiceDelete': f'Удаление голосового сообщения "{data["name"]}"',
        'dutysDelete': f'Удаление дежурного "{data["name"]}"',
        'animDelete': f'Удаление анимки "{data["name"]}"'
    }[type_]


async def async_rewind_checker():
    while True:
        c_time = time.time()
        for rewind in rewinds:
            if c_time > rewind.expire_time:
                rewinds.remove(rewind)
        await asyncio.sleep(250)
