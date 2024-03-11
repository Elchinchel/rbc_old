from .data_classes import Settings, Account, SettingsTG, AccountTG
from lib.wtflog import get_boy_for_warden
from typing import List
import socket
import json
import time
import sys

logger = get_boy_for_warden('DB', 'Клиент базы данных')

db_port = None

for i, arg in enumerate(sys.argv):
    if arg == '-db':
        db_port = int(sys.argv[i+1])

if db_port is None:
    print('Не указан порт базы данных (аргумент -db)')
    sys.exit()

db_address = ('localhost', db_port)


def _make_request(method: str, type_='', uid=0, **kwargs) -> dict:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(db_address)
    to_send = {'method': method, 'type': type_, 'uid': uid}
    to_send.update(kwargs)
    data = json.dumps(to_send, ensure_ascii=False)
    client.send(bytes(data, encoding="utf-8"))
    logger(f'Отправлено на сервер: {data}')
    recvdata = bytes()
    while True:
        chunk_recvdata = client.recv(8096)
        if chunk_recvdata == b'':
            break
        recvdata += chunk_recvdata
    client.close()
    dataRecv = json.loads(recvdata)
    if "error" in dataRecv.keys():
        raise Exception(dataRecv['error'])
    return dataRecv['response']


def _make_req_tg(method: str, type_='', uid=0, **kwargs) -> dict:
    return _make_request(method, type_, uid, is_telegram=True, **kwargs)


# да, я знаю, что так делать нельзя... но похуй))0)
class _tg:
    @staticmethod
    def start():
        return _make_req_tg('start')

    @staticmethod
    def add_user(uid: int):
        _make_req_tg('add_user', uid=uid)

    @staticmethod
    def remove_user(uid: int):
        _make_req_tg('remove_user', uid=uid)

    @staticmethod
    def get_session(uid: int) -> str:
        return _make_req_tg('get', 'session', uid).get('session', '')

    @staticmethod
    def get_account(uid: int) -> dict:
        return _make_req_tg('get', 'account', uid)

    @staticmethod
    def get_settings(uid: int) -> dict:
        return _make_req_tg('get', 'settings', uid)

    @staticmethod
    def update_account(uid: int, account: AccountTG):
        _make_req_tg('update', 'account', uid,
                     account=_search_updates(account))

    @staticmethod
    def update_settings(uid: int, settings: SettingsTG):
        _make_req_tg('update', 'settings', uid,
                     settings=_search_updates(settings))

    @staticmethod
    def update_session(uid: int, session: str):
        return _make_req_tg('update', 'session', uid,
                            tokens={"session": session})

    @staticmethod
    def stickers_get(uid: int) -> List[dict]:
        return _make_req_tg('get', 'sticker', uid)

    @staticmethod
    def sticker_set(uid: int, sticker: dict) -> dict:
        return _make_req_tg('set', 'sticker', uid, template=sticker)

    @staticmethod
    def sticker_remove(uid: int, sticker: str) -> str:
        return _make_req_tg('remove', 'sticker', uid, template=sticker)

    @staticmethod
    def billing_get_accounts() -> List[dict]:
        return _make_req_tg('balance', 'get_users')


class method:
    tg = _tg

    @staticmethod
    def start() -> List[int]:
        return _make_request('start')

    @staticmethod
    def die() -> None:
        return _make_request('die')

    @staticmethod
    def ping() -> float:
        ct = time.time()
        _make_request('ping')
        return round((time.time() - ct) * 1000, 1)

    @staticmethod
    def is_user(uid: int) -> bool:
        return _make_request('is_user', uid=uid)

    @staticmethod
    def add_user(uid: int):
        _make_request('add_user', uid=uid)

    @staticmethod
    def remove_user(uid: int):
        _make_request('remove_user', uid=uid)

    @staticmethod
    def remove_template(uid: int, type_: str, data: dict):
        return _make_request('remove', type_, uid, template=data)

    @staticmethod
    def get_settings(uid: int) -> dict:
        return _make_request('get', 'settings', uid)

    @staticmethod
    def get_account(uid: int) -> dict:
        return _make_request('get', 'account', uid)

    @staticmethod
    def get_tokens(uid: int) -> dict:
        return _make_request('get', 'token', uid)

    @staticmethod
    def get_chats(uid: int) -> dict:
        return _make_request('get', 'chat', uid)

    @staticmethod
    def get_templates(uid: int, type_: str) -> dict:
        return _make_request('get', type_, uid)

    @staticmethod
    def get_all_templates_length() -> dict:
        return _make_request('info', 'templates')

    @staticmethod
    def set_template(uid: int, type_: str, data: dict) -> dict:
        return _make_request('set', type_, uid, template=data)

    @staticmethod
    def update_token(uid: int, access_token: str = '', me_token: str = '',
                     online_token: str = ''):
        tokens = {}
        if access_token:
            tokens.update({"access_token": access_token})
        if me_token:
            tokens.update({"me_token": me_token})
        if online_token:
            tokens.update({"online_token": online_token})
        if not tokens:
            raise ValueError()
        _make_request('update', 'token', uid, tokens=tokens)

    @staticmethod
    def update_account(uid: int, account: Account):
        _make_request('update', 'account', uid,
                      account=_search_updates(account))

    @staticmethod
    def update_settings(uid: int, settings: Settings):
        _make_request('update', 'settings', uid,
                      settings=_search_updates(settings))

    @staticmethod
    def billing_get_accounts() -> List[dict]:
        return _make_request('balance', 'get_users')

    @staticmethod
    def billing_get_balance(uid: int) -> float:
        return _make_request('balance', 'get', uid)

    @staticmethod
    def balance_increase(uid: int, value: float):
        _make_request('balance', 'increase', uid, value=value)

    @staticmethod
    def balance_decrease(uid: int, value: float):
        _make_request('balance', 'decrease', uid, value=value)

    @staticmethod
    def balance_set(uid: int, value: float):
        _make_request('balance', 'set', uid, value=value)


def _search_updates(instance) -> dict:
    data = {}
    for att in instance.attributes:
        if getattr(instance, att, "not setted") != "not setted":
            data.update({att: getattr(instance, att)})
    if not data:
        raise ValueError()
    return data
