from time import sleep
from vk.api_utils import async_requester
from lib.vkmini import VkApi
from lib.microvk import VkApi as VkSync
from lib.asyncio_utils import start_coro
from . import dlp, ND
import time


def gen_all_unread_conversations(vk: VkSync):
    offset = 0
    while True:
        convs = vk.exe("""
        var i = 0;
        var convs = [];
        var items = API.messages.getConversations({"count":200,"offset":%d});
        while (i < 200) {
            var conv = items.items[i].conversation;
            if (conv == null) { i = 200; };
            if (conv.in_read != conv.last_message_id) {
                convs.push(conv.peer.id);
            };
            i = i + 1;
        };
        return convs;""" % (offset*200))
        if convs == []:
            return
        for conv in convs:
            yield conv
        if offset > 0:
            sleep(0.5)
        offset += 1


async def reader(token: str, to_read: list):
    vk = VkApi(token, True)
    to_execute = ''
    while len(to_read) > 0:
        for _ in range(25 if len(to_read) > 25 else len(to_read)):
            to_execute += 'API.messages.markAsRead({"peer_id": %s});' % to_read.pop()  # noqa
        await async_requester(vk, 'execute', code=to_execute)
        time.sleep(0.5)
        to_execute = ''


@dlp.register('прочитать', receive=True)
def readmessages(nd: ND) -> str:  # noqa
    allowed = lambda x: x > 1e9  # noqa
    if nd.msg['args']:
        if nd.msg['args'][0].lower() in {'все', 'всё'}:
            allowed = lambda _: True  # noqa
        elif nd.msg['args'][0].lower() == 'беседы':
            allowed = lambda x: x > 2e9  # noqa
        elif nd.msg['args'][0].lower() == 'группы':
            allowed = lambda x: x < 0  # noqa
    chats = private = groups = 0
    to_read = []
    for peer in gen_all_unread_conversations(nd.vk):
        if allowed(peer):
            to_read.append(peer)
            if peer > 2e9:
                chats += 1
            elif peer < 0:
                groups += 1
            else:
                private += 1

    start_coro(reader(nd.db.access_token, to_read))

    message = '⏩ Диалоги читаются:'
    if chats:
        message += f'\nБеседы: {chats}'
    if private:
        message += f'\nЛичные: {private}'
    if groups:
        message += f'\nГруппы: {groups}'
    if message == '⏩ Диалоги читаются:':
        message = '🤔 Непрочитанных сообщений нет'

    nd.msg_op(2, message)
    return "ok"
