from vk.user_bot import dlp, ND
from vk.user_bot.utils import exe, find_mention_by_message, ExcReload
from vk.api_utils import execute_find_chat
from database import owner_id
from lib.microvk import VkApi


@dlp.register('+дов', receive=True)
def add_trusted_user(nd: ND):
    uid = find_mention_by_message(nd.msg, nd.vk)
    if not uid:
        return nd.msg_op(2, '⚠️ Необходимо указать пользователя')
    settings = nd.db.settings_get()

    if uid in settings.trusted_users:
        return nd.msg_op(2, '🤔 Пользователь уже добавлен')

    settings.trusted_users.append(uid)
    nd.db.settings_set(settings)
    uid = f'id{uid}' if uid > 0 else f'club{abs(uid)}'
    nd.msg_op(2, f"👌 vk.me/{uid} в доверенных")
    raise ExcReload(nd.vk)


@dlp.register('-дов', receive=True)
def remove_trusted_user(nd: ND):
    uid = find_mention_by_message(nd.msg, nd.vk)
    if not uid:
        return nd.msg_op(2, '⚠️ Необходимо указать пользователя')
    settings = nd.db.settings_get()

    if uid not in settings.trusted_users:
        return nd.msg_op(2, '🤔 Пользователь не в списке')

    settings.trusted_users.remove(uid)
    nd.db.settings_set(settings)
    uid = f'id{uid}' if uid > 0 else f'club{abs(uid)}'
    nd.msg_op(2, f"👌 vk.me/{uid} вне доверенных")
    raise ExcReload(nd.vk)


@dlp.register('довы', 'доверенные', receive=True)
def list_trusted_users(nd: ND):
    trusted = nd.db.settings_get().trusted_users

    message = '🤝 Список доверенных пользователей:\n'

    users = []
    groups = []

    for user in trusted:
        if user > 0:
            users.append(str(user))
        else:
            groups.append(user)

    users: list = nd.vk('users.get', user_ids=','.join(users))
    users.extend(groups)

    for i, user in enumerate(users, 1):
        if type(user) == dict:
            message += f"{i}. [id{user['id']}|{user['first_name']} {user['last_name']}]\n"  # noqa
        else:
            message += f"{i}. vk.me/club{abs(user)}\n"

    if message == '🤝 Список доверенных пользователей:\n':
        return nd.msg_op(2, '🤔 Список доверенных пуст')

    nd.msg_op(1, message, delete_id=nd[1], disable_mentions=1)


@dlp.register('у', 'унапиши', receive=True)
def remote_control(nd: ND):
    nd.msg_op(3)
    title = None
    if nd[3] < 2e9:
        uid = nd[3]
        chat = nd.db.user_id
    else:
        uid = find_mention_by_message(nd.msg, nd.vk)
        if uid is None:
            return nd.msg_op('⚠️ Пользователь не найден')
        title = nd.vk('messages.getConversationsById', peer_ids=nd[3]
                      )['items'][0]['chat_settings']['title']

    trusted = nd.db.method.get_settings(uid)['trusted_users']
    if nd.db.user_id not in trusted and nd.db.user_id != owner_id:
        return nd.msg_op(1, '⚠️ Этот пользователь тебе не доверяет')

    vk_ = VkApi(nd.db.method.get_tokens(uid)['access_token'])
    if title is not None:
        chat = vk_.exe(execute_find_chat(title))
    vk_.msg_op(1, chat, nd.msg['payload'])  # type: ignore
