from . import dlp
from .utils import parseByID, find_mention_by_message, ExcReload, msg_op
from time import sleep


@dlp.register('+игнор', receive=True)
def ignore_add(nd):
    sets = nd.db.settings_get()
    user_id = find_mention_by_message(nd.msg, nd.vk)
    if not user_id:
        msg = '❗ Необходимо пересланное сообщение или упоминание'
    else:
        if user_id == nd.db.user_id:
            msg = '🤨 Ты себя добавить хочешь?!'
        elif str(user_id) in sets.ignore_list:
            msg = '👀 Уже...'
        else:
            sets.ignore_list.append(str(user_id))
            msg = '🚷 Добавлено'
    nd.vk.msg_op(2, nd[3], msg, nd[1])
    sleep(1)
    nd.vk.msg_op(3, nd[3], msg_id = nd[1])
    if msg == '🚷 Добавлено':
        nd.db.settings_set(sets)
        raise ExcReload(nd.vk)


@dlp.register('-игнор', receive=True)
def ignore_add(nd):
    sets = nd.db.settings_get()
    user_id = find_mention_by_message(nd.msg, nd.vk)
    if not user_id:
        msg = '❗ Необходимо пересланное сообщение или упоминание'
    else:
        if str(user_id) in sets.ignore_list:
            sets.ignore_list.remove(str(user_id))
            msg = '💅🏻 Удалено'
        else:
            msg = '🤷‍♀ Не в списке'
    nd.vk.msg_op(2, nd[3], msg, nd[1])
    sleep(1)
    nd.vk.msg_op(3, nd[3], msg_id = nd[1])
    if msg == '💅🏻 Удалено':
        nd.db.settings_set(sets)
        raise ExcReload(nd.vk)


@dlp.register('-игнорвсе')
def ignore_add(nd):
    sets = nd.db.settings_get()
    sets.ignore_list = []
    nd.msg_op(2, '💆‍♀ Список игнора очищен', nd[1])
    nd.db.settings_set(sets)
    raise ExcReload(nd.vk)


@dlp.register('игнорлист', 'игнор')
def ignore_list(nd):
    sets = nd.db.settings_get()
    users = []
    groups = []
    message_u = message_g = ''
    for user in sets.ignore_list:
        if int(user) < 0:
            groups.append(user[1:])
        else:
            users.append(user)
    if users:
        message_u = '😶 Игнорируемые пользователи:\n'
        for i, user in enumerate(nd.vk('users.get', user_ids=','.join(users)), 1):
            message_u += f"{i}. [id{user['id']}|{user['first_name']} {user['last_name']}]\n"

    if groups:
        message_g = '😶 Игнорируемые группы:\n'
        for i, group in enumerate(nd.vk('groups.getById', group_ids=','.join(groups)), 1):
            message_g += f"{i}. [public{group['id']}|{group['name']}]\n"

    if not users and not groups:
        message = '💅🏻 Список игнора пуст'
    else:
        message = message_u + '\n' + message_g

    nd.vk.exe("""API.messages.send({"peer_id":%d,"message":"%s","random_id":0,"disable_mentions":1});
            API.messages.delete({"message_ids":%d,"delete_for_all":1});""" %
            (nd[3], message.replace('\n', '<br>'), nd[1]))
