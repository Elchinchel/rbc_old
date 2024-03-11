from time import sleep
from .utils import find_mention_by_message, get_index, format_push, get_text_from_message
from lib.microvk import VkApiResponseException
from . import dlp, ND


@dlp.register('добавить', 'вернуть', receive=True)
def add_user(nd: ND):
    uid = find_mention_by_message(nd.msg, nd.vk)
    if uid:
        if nd[3] < 2000000000:
            nd.msg_op(2, '❗ Работает только в чатах (потом будет создавать беседу с указанным пользователем, но пока мне лень)')
        else:
            chat = nd[3] - 2000000000
            try:
                nd.vk('messages.addChatUser', chat_id=chat, user_id=uid)
                nd.msg_op(3)
            except VkApiResponseException as e:
                if e.error_code == 15:
                    if 'already' in e.error_msg:
                        nd.msg_op(2, '🤔 Пользователь уже в беседе')
                    else:
                        nd.msg_op(2, f'❗ Невозможно добавить указанного пользователя. Может он не в друзьях?')
                else:
                    nd.msg_op(2, f'❗ Ошибка VK: {e.error_msg}')
    else:
        nd.msg_op(2, '❗ Необходимо упоминание или ответ на сообщение')


@dlp.register('кик', 'выгнать', receive=True)
def kick_user(nd: ND):
    if get_index(nd.msg['args'], 0) == 'меня':
        uid = nd.db.user_id
    else:
        uid = find_mention_by_message(nd.msg, nd.vk)
    if uid:
        if nd[3] < 2000000000:
            nd.msg_op(2, '❗ Работает только в чатах (если есть идеи как кикнуть из личной переписки кого-нибудь - ' +
            'пиши на mysweetideas.com (да, это какой-то блог, хз че там, я вообще рандомно ссылку написал))', dont_parse_links=True)
        else:
            chat = nd[3] - 2000000000
            try:
                nd.vk('messages.removeChatUser', chat_id=chat, member_id=uid)
                if uid != nd.db.user_id:
                    nd.msg_op(3)
            except VkApiResponseException as e:
                if e.error_code == 15:
                    nd.msg_op(2, f'❗ Невозможно удалить указанного пользователя. Может не хватает прав в беседе?')
                elif e.error_code == 935:
                    nd.msg_op(2, f'❗ В этой беседе нет указанного пользователя')
                else:
                    nd.msg_op(2, f'❗ Ошибка VK: {e.error_msg}')
    else:
        nd.msg_op(2, '❗ Необходимо упоминание или ответ на сообщение')


@dlp.register('админы', receive=True)
def list_admins(nd: ND):  # noqa
    if nd[3] < 2e9:
        return nd.msg_op(2, '🤨 Админы в лс?')
    members = nd.vk('messages.getConversationMembers', peer_id=nd[3])
    owner = None
    admins = []
    for user in members['items']:
        if user.get('is_owner') is True:
            owner = user['member_id']
        elif user.get('is_admin') is True:
            admins.append(user['member_id'])
    message_o = '🌜 Создатель - '
    message = '🌛 Админы беседки:\n'
    for user in members['profiles']:
        if user['id'] in admins:
            message += '-- ' + format_push(user) + '\n'
        elif user['id'] == owner:
            message_o += format_push(user) + '\n\n'
    for group in members['groups']:
        if (0 - group['id']) in admins:
            message += '-- ' + format_push(group, True) + '\n'
        elif group['id'] == abs(owner):
            message_o += format_push(group, True) + '\n'
    if message == '🌛 Админы беседки:\n':
        message = ''
    nd.msg_op(1, message_o + message, delete_id=nd[1], disable_mentions=1)


@dlp.register('мегапуш')
def mega_push(nd: ND):
    nd.msg_op(3)
    messages = [get_text_from_message(nd.msg)]
    for user in nd.vk('messages.getConversationMembers', peer_id=nd[3])['profiles']:  # noqa
        if len(messages[-1]) < 4000:
            messages[-1] += f"[id{user['id']}|&#8300;]"
        else:
            messages.append(f"[id{user['id']}|&#8300;]")
    for message in messages:
        nd.msg_op(1, message)
        sleep(1)
