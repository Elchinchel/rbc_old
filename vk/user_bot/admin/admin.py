from vk.user_bot.utils import find_mention_by_message
from vk.user_bot import ND, dlp
from database.driver import (owner_id, admins, moderators,
                             save_general, general_data)


def check_owner(nd: ND):
    if nd.db.user_id != owner_id:
        nd.msg_op(2, 'Нужно быть владельцем.')
        return None
    return nd


def check_admin(nd: ND):
    restrict = True
    if nd.db.user_id == owner_id:
        restrict = False
    if nd.db.user_id in admins:
        restrict = False
    if restrict:
        nd.msg_op(2, 'Нужно быть админом.')
        return None
    return nd


def check_moder(nd: ND):
    restrict = True
    if nd.db.user_id == owner_id:
        restrict = False
    if nd.db.user_id in admins:
        restrict = False
    if nd.db.user_id in moderators:
        restrict = False
    if restrict:
        nd.msg_op(2, 'Нужно быть модером.')
        return None
    return nd


@dlp.register('+скрипт админ', receive=True)
@dlp.wrap_handler(check_owner)
def add_admin(nd: ND) -> None:
    uid = find_mention_by_message(nd.msg, nd.vk)
    if uid is None or uid in admins:
        return
    general_data['admins'].append(uid)
    save_general()
    nd.msg_op('ok')


@dlp.register('-скрипт админ', receive=True)
@dlp.wrap_handler(check_owner)
def remove_admin(nd: ND) -> None:
    uid = find_mention_by_message(nd.msg, nd.vk)
    if uid is None or uid not in admins:
        return
    general_data['admins'].remove(uid)
    save_general()
    nd.msg_op('ok')


@dlp.register('+скрипт модер', receive=True)
@dlp.wrap_handler(check_owner)
def add_moder(nd: ND) -> None:
    uid = find_mention_by_message(nd.msg, nd.vk)
    if uid is None or uid in admins:
        return
    general_data['moders'].append(uid)
    save_general()
    nd.msg_op('ok')


@dlp.register('-скрипт модер', receive=True)
@dlp.wrap_handler(check_owner)
def remove_moder(nd: ND) -> None:
    uid = find_mention_by_message(nd.msg, nd.vk)
    if uid is None or uid not in admins:
        return
    general_data['moders'].remove(uid)
    save_general()
    nd.msg_op('ok')
