from asyncio import Event
from typing import List
from .client import method


vk_users: List[int] = []

tg_users: List[int] = []

users_added = Event()

recheck = Event()


def _check():
    vk_users.clear()
    for account in method.billing_get_accounts():
        if account['vk_longpoll']:
            vk_users.append(account['user_id'])

    tg_users.clear()
    for account in method.tg.billing_get_accounts():
        if account['on']:
            tg_users.append(account['user_id'])


async def async_users_filler():
    _check()
    users_added.set()

    while True:
        await recheck.wait()
        recheck.clear()
        _check()
