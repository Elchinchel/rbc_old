from asyncio import sleep
from .utils import find_mention_by_message
import time
from longpoll.copy_server import Listener
from lib.vkmini import VkApi, VkResponseException
from lib.asyncio_utils import wait_coro
from . import dlp, ND

running_users = set()


def get_atts(atts: dict) -> str:
    result = []
    for key in atts:
        if key.endswith('_type'):
            result.append(atts[key]+atts[key.replace('_type', '')])
    return ','.join(result)

# на случай, если эта сука захочет вернуть отправку пушей
# async def push(vk: VkApi, update: list):
#     await vk.exe('''API.messages.delete({"message_id":%d,"delete_for_all":1});
#         API.messages.send({"peer_id":%d,"message":"%s","attachment":"%s","keep_forward_messages":1,"random_id":0});''' % (  # noqa
#         update[1], update[3], escape(update[5]).replace('\n', '<br>'),
#         get_atts(update[7])))


async def mentioner(token: str, peer_id: int, self_id: int, uid: int):  # noqa
    vk = VkApi(token, excepts=True)
    time_stop = time.time() + 900
    if uid > 0:
        ment = f"@id{uid} ("
    else:
        ment = f"@club{uid.__abs__()} ("
    with Listener(self_id) as lp:
        async for update in lp.listen():
            if update[0] != 4:
                continue
            if update[4] > time_stop:
                break
            if update[2] & 2 == 2:
                if update[5].lower() == 'хватит!':
                    break
                if update[3] == peer_id:
                    if update[5].startswith(ment):
                        continue
                    if type(update[7].get('attachments')) == str:
                        continue
                    await sleep(1)
                    update[5] = ment + update[5] + ')'
                    try:
                        await vk.msg_op(2, update[3], update[5], update[1],
                                        keep_forward_messages=1,
                                        attachment=get_atts(update[7]))
                    except VkResponseException:
                        pass


@dlp.register('упоминай', receive=True)
def start_mentioning(nd: ND):
    uid = find_mention_by_message(nd.msg, nd.vk)
    if not uid:
        return nd.msg_op(2, 'Необходимо указать пользователя')
    token = nd.db.access_token
    if nd.db.user_id not in running_users:
        running_users.add(nd.db.user_id)
        nd.msg_op(2, 'остановка - "хватит!", само сдохнет через 15 минут')
        wait_coro(mentioner(token, nd[3], nd.db.user_id, uid))
        running_users.remove(nd.db.user_id)
    else:
        nd.msg_op(2, 'уже где-то запущено...')
