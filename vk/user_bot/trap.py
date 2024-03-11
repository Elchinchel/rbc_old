from lib.asyncio_utils import wait_coro
from vk.user_bot import dlp, ND
from database.driver import owner_id
from longpoll.copy_server import Listener


async def catcher(uid: int, peer_id: int) -> int:
    'Блокирует выполнение до получения нового сообщения в указанном чате'
    with Listener(uid) as poller:
        async for update in poller.listen():
            if update[0] == 4:
                if update[3] == peer_id:
                    return update[6].get('from', 0)


traps = {
    '0': ('photo-196725454_457239021', 'photo-196725454_457239022'),
    '1': ('photo-196725454_457239019', 'photo-196725454_457239020'),
    '2': ('photo-196725454_457239017', 'photo-196725454_457239018')
}


@dlp.register('ловушка')
def trap(nd: ND):
    if nd[3] < 2e9:
        return nd.msg_op(2, '🐭 Эта штучка для бесед')
    pack = traps.get(nd.args.get(0, '0'), traps['0'])
    nd.msg_op(2, attachment=pack[0])
    uid = int(wait_coro(catcher(nd.db.user_id, nd[3])))
    if uid in {nd.db.user_id, owner_id}:
        nd.msg_op(3)
    else:
        nd.msg_op(1, attachment=pack[1])
