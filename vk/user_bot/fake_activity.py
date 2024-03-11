from . import dlp, ND
from .utils import find_time
from time import time
from asyncio import sleep
from lib.vkmini import VkApi, VkResponseException


active_typers: ["Dict{peer_id: int, voice: bool, uid: int, api: VkApi, expire: float}"] = []


async def async_fake_typer():
    while True:
        timenow = time()
        for typer in active_typers:
            if timenow > typer['expire']:
                active_typers.remove(typer)
                continue
            try:
                if typer['voice']:
                    await typer['api']('messages.setActivity', type='audiomessage', peer_id=typer['peer_id'])
                else:
                    await typer['api']('messages.setActivity', type='typing', peer_id=typer['peer_id'])
            except VkResponseException:
                active_typers.remove(typer)
        await sleep(5)


def typer_exists(peer_id: int, uid: str) -> bool:
    for typer in active_typers:
        if typer['peer_id'] != peer_id: continue
        if typer['uid'] == uid:
            return True
    return False


def remove_typer(peer_id: int, uid: str) -> bool:
    for typer in active_typers:
        if typer['peer_id'] != peer_id: continue
        if typer['uid'] == uid:
            active_typers.remove(typer)
            return True
        return False


def new_typer(nd: ND, voice: bool, period: int):
    return {
        'api': VkApi(nd.db.access_token),
        'uid': nd.db.user_id,
        'voice': voice,
        'expire': time() + period,
        'peer_id': nd[3]
    }


@dlp.register('гсф', 'смсф')
def list_fake_typers(nd: ND):
    pids = []
    voices = []
    for typer in active_typers:
        if typer['uid'] == nd.db.user_id:
            pids.append(typer['peer_id'])
            if typer['voice']:
                voices.append(typer['peer_id'])
    if not pids:
        return nd.msg_op(2, 'Не запущено ни одной печаталки')
    message = 'Запущенные печаталки:'
    for conv in nd.vk('messages.getConversationsById', peer_ids=','.join([str(i) for i in pids]))['items']:
        if conv['peer']['type'] not in {'user', 'chat'}: continue
        if conv['peer']['type'] == 'user':
            message += f"\n-- vk.com/id{conv['peer']['id']}"
        elif conv['peer']['type'] == 'chat':
            message += f'\n-- {conv["chat_settings"]["title"]}'
        message += ' (голосовая)' if conv['peer']['id'] in voices else ''
    nd.msg_op(2, message)


@dlp.register('+смсф')
def add_fake_typer(nd: ND):
    if typer_exists(nd[3], nd.db.user_id):
        nd.msg_op(2, 'уже')
    else:
        period = find_time(nd[5])
        active_typers.append(new_typer(nd, False, period or 86400))
        nd.msg_op(2, '+')
    nd.msg_op(3)


@dlp.register('+гсф')
def add_fake_voicer(nd: ND):
    if typer_exists(nd[3], nd.db.user_id):
        nd.msg_op(2, 'Уже установлено')
    else:
        period = find_time(nd[5])
        active_typers.append(new_typer(nd, True, period or 86400))
        nd.msg_op(2, '+')
    nd.msg_op(3)


@dlp.register('-смсф')
def rem_fake_typer(nd: ND):
    if not remove_typer(nd[3], nd.db.user_id):
        nd.msg_op(2, 'нету')
    else:
        nd.msg_op(2, '-')
    nd.msg_op(3)


@dlp.register('-гсф')
def rem_fake_voicer(nd: ND):
    if not remove_typer(nd[3], nd.db.user_id):
        nd.msg_op(2, 'нету')
    else:
        nd.msg_op(2, '-')
    nd.msg_op(3)
