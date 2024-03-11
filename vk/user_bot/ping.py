from database.client import method
from datetime import datetime
from .warnings import get_warns
from . import dlp, ND
import time


pings = {
    "пинг": "ПОНГ",
    "кинг": "КОНГ",
    "пиу": "ПАУ",
    "тик": "ТОК",
    "ping": "PONG",
    "биба": "БОБА",
    "king": "The Lion King*"
}


def pingvk(vk, method='', **kwargs) -> float:
    ct = time.time()
    if method:
        vk(method, **kwargs)
    else:
        vk.exe('return 0;')
    return round((time.time() - ct) * 1000, 1)


@dlp.register(*pings.keys())
def ping(nd: ND):
    delta = round(nd.time - nd[4], 1)

    msg = f"{pings.get(nd[5], 'короче ответ')} LP\nПолучено за {delta}(±0.5)с."

    nd.vk.msg_op(2, nd[3], msg + get_warns(), nd[1])


@dlp.register('пенг')
def peng(nd: ND):
    delta = round(nd.time - nd[4], 3)
    msg = f"""
    Ping:
    Received for {delta} s
    Processed for {round((datetime.now().timestamp() - nd.time) * 1000, 1)} ms
    Ping DB: {method.ping()} ms
    Ping VK: {pingvk(nd.vk)} ms""".replace('    ', '')
    nd.msg_op(2, msg)
