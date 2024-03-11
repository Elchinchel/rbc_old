from vk.user_bot.utils import find_mention_by_message
from vk.user_bot.service import kill_queue
from vk.user_bot import ND, dlp

from vk.group_bot.interact import send_message

from database.driver import (add_user, vk_users, method, Account,
                             VkDB, owner_id, remove_user)

from .admin import check_admin


@dlp.register('reg', 'рег', receive=True)
@dlp.wrap_handler(check_admin)
def register(nd: ND):
    uid = find_mention_by_message(nd.msg, nd.vk)
    if uid is None or uid < 0:
        return nd.msg_op('❗ Пользователь не найден')
    if method.is_user(uid):
        return nd.msg_op('🤔 Пользователь уже добавлен')
    try:
        add_user(uid)
        db = VkDB(uid)
        account = db.account_get()
        account.vk_longpoll = True
        account.added_by = nd.db.user_id
        db.account_set(account)
        vk_users.append(uid)
        nd.msg_op('🦆 registered bljad')
        send_message(
            owner_id, f'Новый [id{uid}|рег] от vk.me/id{nd.db.user_id}'
        )
    except Exception as e:
        nd.msg_op(
            f'❗ Произошла ошибка при добавлении пользователя {uid}\n\n{e}'
        )


@dlp.register('unreg', 'анрег', receive=True)
@dlp.wrap_handler(check_admin)
def unregister(nd: ND):
    uid = find_mention_by_message(nd.msg, nd.vk)
    if uid == nd.db.user_id:
        return nd.msg_op('🙄 Ты щас чуть сам себя не удалил...')
    user_acc = Account(method.get_account(uid))
    if nd.db.user_id != user_acc.added_by and nd.db.user_id != owner_id:
        return nd.msg_op('❗ Недоступно')
    try:
        remove_user(uid)
        kill_queue.append(uid)
        nd.msg_op('🚷 unregistered bljad')
    except Exception as e:
        nd.msg_op(f'❗ Произошла ошибка при udalenii пользователя {uid}\n\n{e}')
